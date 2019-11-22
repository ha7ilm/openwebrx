"""
OpenWebRX csdr plugin: do the signal processing with csdr

    This file is part of OpenWebRX,
    an open-source SDR receiver software with a web UI.
    Copyright (c) 2013-2015 by Andras Retzler <randras@sdr.hu>
    Copyright (c) 2019 by Jakob Ketterl <dd5jfk@darc.de>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import subprocess
import os
import signal
import threading
from functools import partial

from owrx.kiss import KissClient, DirewolfConfig
from owrx.wsjt import Ft8Chopper, WsprChopper, Jt9Chopper, Jt65Chopper, Ft4Chopper

import logging

logger = logging.getLogger(__name__)


class output(object):
    def send_output(self, t, read_fn):
        if not self.supports_type(t):
            # TODO rewrite the output mechanism in a way that avoids producing unnecessary data
            logger.warning("dumping output of type %s since it is not supported.", t)
            threading.Thread(target=self.pump(read_fn, lambda x: None)).start()
            return
        self.receive_output(t, read_fn)

    def receive_output(self, t, read_fn):
        pass

    def pump(self, read, write):
        def copy():
            run = True
            while run:
                data = read()
                if data is None or (isinstance(data, bytes) and len(data) == 0):
                    run = False
                else:
                    write(data)

        return copy

    def supports_type(self, t):
        return True


class dsp(object):
    def __init__(self, output):
        self.samp_rate = 250000
        self.output_rate = 11025
        self.fft_size = 1024
        self.fft_fps = 5
        self.offset_freq = 0
        self.low_cut = -4000
        self.high_cut = 4000
        self.bpf_transition_bw = 320  # Hz, and this is a constant
        self.ddc_transition_bw_rate = 0.15  # of the IF sample rate
        self.running = False
        self.secondary_processes_running = False
        self.audio_compression = "none"
        self.fft_compression = "none"
        self.demodulator = "nfm"
        self.name = "csdr"
        self.base_bufsize = 512
        self.nc_port = None
        self.csdr_dynamic_bufsize = False
        self.csdr_print_bufsizes = False
        self.csdr_through = False
        self.squelch_level = 0
        self.fft_averages = 50
        self.iqtee = False
        self.iqtee2 = False
        self.secondary_demodulator = None
        self.secondary_fft_size = 1024
        self.secondary_process_fft = None
        self.secondary_process_demod = None
        self.pipe_names = [
            "bpf_pipe",
            "shift_pipe",
            "squelch_pipe",
            "smeter_pipe",
            "meta_pipe",
            "iqtee_pipe",
            "iqtee2_pipe",
            "dmr_control_pipe",
        ]
        self.secondary_pipe_names = ["secondary_shift_pipe"]
        self.secondary_offset_freq = 1000
        self.unvoiced_quality = 1
        self.modification_lock = threading.Lock()
        self.output = output
        self.temporary_directory = "/tmp"
        self.is_service = False
        self.direwolf_config = None
        self.direwolf_port = None

    def set_service(self, flag=True):
        self.is_service = flag

    def set_temporary_directory(self, what):
        self.temporary_directory = what

    def chain(self, which):
        chain = ["nc -v 127.0.0.1 {nc_port}"]
        if self.csdr_dynamic_bufsize:
            chain += ["csdr setbuf {start_bufsize}"]
        if self.csdr_through:
            chain += ["csdr through"]
        if which == "fft":
            chain += [
                "csdr fft_cc {fft_size} {fft_block_size}",
                "csdr logpower_cf -70"
                if self.fft_averages == 0
                else "csdr logaveragepower_cf -70 {fft_size} {fft_averages}",
                "csdr fft_exchange_sides_ff {fft_size}",
            ]
            if self.fft_compression == "adpcm":
                chain += ["csdr compress_fft_adpcm_f_u8 {fft_size}"]
            return chain
        chain += ["csdr shift_addition_cc --fifo {shift_pipe}"]
        if self.decimation > 1:
            chain += ["csdr fir_decimate_cc {decimation} {ddc_transition_bw} HAMMING"]
        chain += ["csdr bandpass_fir_fft_cc --fifo {bpf_pipe} {bpf_transition_bw} HAMMING"]
        if self.output.supports_type("smeter"):
            chain += [
                "csdr squelch_and_smeter_cc --fifo {squelch_pipe} --outfifo {smeter_pipe} 5 {smeter_report_every}"
            ]
        if self.secondary_demodulator:
            if self.output.supports_type("secondary_fft"):
                chain += ["csdr tee {iqtee_pipe}"]
            chain += ["csdr tee {iqtee2_pipe}"]
            # early exit if we don't want audio
            if not self.output.supports_type("audio"):
                return chain
        # safe some cpu cycles... no need to decimate if decimation factor is 1
        last_decimation_block = (
            ["csdr fractional_decimator_ff {last_decimation}"] if self.last_decimation != 1.0 else []
        )
        if which == "nfm":
            chain += ["csdr fmdemod_quadri_cf", "csdr limit_ff"]
            chain += last_decimation_block
            chain += ["csdr deemphasis_nfm_ff {audio_rate}"]
            if self.get_audio_rate() != self.get_output_rate():
                chain += [
                    "sox -t raw -r {audio_rate} -e floating-point -b 32 -c 1 --buffer 32 - -t raw -r {output_rate} -e signed-integer -b 16 -c 1 - "
                ]
            else:
                chain += ["csdr convert_f_s16"]
        elif self.isDigitalVoice(which):
            chain += ["csdr fmdemod_quadri_cf", "dc_block "]
            chain += last_decimation_block
            # dsd modes
            if which in ["dstar", "nxdn"]:
                chain += ["csdr limit_ff", "csdr convert_f_s16"]
                if which == "dstar":
                    chain += ["dsd -fd -i - -o - -u {unvoiced_quality} -g -1 "]
                elif which == "nxdn":
                    chain += ["dsd -fi -i - -o - -u {unvoiced_quality} -g -1 "]
                chain += ["CSDR_FIXED_BUFSIZE=32 csdr convert_s16_f"]
                max_gain = 5
            # digiham modes
            else:
                chain += ["rrc_filter", "gfsk_demodulator"]
                if which == "dmr":
                    chain += [
                        "dmr_decoder --fifo {meta_pipe} --control-fifo {dmr_control_pipe}",
                        "mbe_synthesizer -f -u {unvoiced_quality}",
                    ]
                elif which == "ysf":
                    chain += ["ysf_decoder --fifo {meta_pipe}", "mbe_synthesizer -y -f -u {unvoiced_quality}"]
                max_gain = 0.0005
            chain += [
                "digitalvoice_filter -f",
                "CSDR_FIXED_BUFSIZE=32 csdr agc_ff 160000 0.8 1 0.0000001 {max_gain}".format(max_gain=max_gain),
                "sox -t raw -r 8000 -e floating-point -b 32 -c 1 --buffer 32 - -t raw -r {output_rate} -e signed-integer -b 16 -c 1 - ",
            ]
        elif which == "am":
            chain += ["csdr amdemod_cf", "csdr fastdcblock_ff"]
            chain += last_decimation_block
            chain += ["csdr agc_ff", "csdr limit_ff", "csdr convert_f_s16"]
        elif which == "ssb":
            chain += ["csdr realpart_cf"]
            chain += last_decimation_block
            chain += ["csdr agc_ff", "csdr limit_ff"]
            # fixed sample rate necessary for the wsjt-x tools. fix with sox...
            if self.get_audio_rate() != self.get_output_rate():
                chain += [
                    "sox -t raw -r {audio_rate} -e floating-point -b 32 -c 1 --buffer 32 - -t raw -r {output_rate} -e signed-integer -b 16 -c 1 - "
                ]
            else:
                chain += ["csdr convert_f_s16"]

        if self.audio_compression == "adpcm":
            chain += ["csdr encode_ima_adpcm_i16_u8"]
        return chain

    def secondary_chain(self, which):
        chain = ["cat {input_pipe}"]
        if which == "fft":
            chain += [
                "csdr realpart_cf",
                "csdr fft_fc {secondary_fft_input_size} {secondary_fft_block_size}",
                "csdr logpower_cf -70",
            ]
            if self.fft_compression == "adpcm":
                chain += ["csdr compress_fft_adpcm_f_u8 {secondary_fft_size}"]
            return chain
        elif which == "bpsk31":
            return chain + [
                "csdr shift_addition_cc --fifo {secondary_shift_pipe}",
                "csdr bandpass_fir_fft_cc -{secondary_bpf_cutoff} {secondary_bpf_cutoff} {secondary_bpf_cutoff}",
                "csdr simple_agc_cc 0.001 0.5",
                "csdr timing_recovery_cc GARDNER {secondary_samples_per_bits} 0.5 2 --add_q",
                "CSDR_FIXED_BUFSIZE=1 csdr dbpsk_decoder_c_u8",
                "CSDR_FIXED_BUFSIZE=1 csdr psk31_varicode_decoder_u8_u8",
            ]
        elif self.isWsjtMode(which):
            chain += ["csdr realpart_cf"]
            if self.last_decimation != 1.0:
                chain += ["csdr fractional_decimator_ff {last_decimation}"]
            return chain + ["csdr limit_ff", "csdr convert_f_s16"]
        elif which == "packet":
            chain += ["csdr fmdemod_quadri_cf"]
            if self.last_decimation != 1.0:
                chain += ["csdr fractional_decimator_ff {last_decimation}"]
            return chain + ["csdr convert_f_s16", "direwolf -c {direwolf_config} -r {audio_rate} -t 0 -q d -q h - 1>&2"]

    def set_secondary_demodulator(self, what):
        if self.get_secondary_demodulator() == what:
            return
        self.secondary_demodulator = what
        self.calculate_decimation()
        self.restart()

    def secondary_fft_block_size(self):
        return (self.samp_rate / self.decimation) / (
            self.fft_fps * 2
        )  # *2 is there because we do FFT on real signal here

    def secondary_decimation(self):
        return 1  # currently unused

    def secondary_bpf_cutoff(self):
        if self.secondary_demodulator == "bpsk31":
            return 31.25 / self.if_samp_rate()
        return 0

    def secondary_bpf_transition_bw(self):
        if self.secondary_demodulator == "bpsk31":
            return 31.25 / self.if_samp_rate()
        return 0

    def secondary_samples_per_bits(self):
        if self.secondary_demodulator == "bpsk31":
            return int(round(self.if_samp_rate() / 31.25)) & ~3
        return 0

    def secondary_bw(self):
        if self.secondary_demodulator == "bpsk31":
            return 31.25

    def start_secondary_demodulator(self):
        if not self.secondary_demodulator:
            return
        logger.debug("starting secondary demodulator from IF input sampled at %d" % self.if_samp_rate())
        secondary_command_demod = " | ".join(self.secondary_chain(self.secondary_demodulator))
        self.try_create_pipes(self.secondary_pipe_names, secondary_command_demod)
        self.try_create_configs(secondary_command_demod)

        secondary_command_demod = secondary_command_demod.format(
            input_pipe=self.iqtee2_pipe,
            secondary_shift_pipe=self.secondary_shift_pipe,
            secondary_decimation=self.secondary_decimation(),
            secondary_samples_per_bits=self.secondary_samples_per_bits(),
            secondary_bpf_cutoff=self.secondary_bpf_cutoff(),
            secondary_bpf_transition_bw=self.secondary_bpf_transition_bw(),
            if_samp_rate=self.if_samp_rate(),
            last_decimation=self.last_decimation,
            audio_rate=self.get_audio_rate(),
            direwolf_config=self.direwolf_config,
        )

        logger.debug("secondary command (demod) = %s", secondary_command_demod)
        my_env = os.environ.copy()
        # if self.csdr_dynamic_bufsize: my_env["CSDR_DYNAMIC_BUFSIZE_ON"]="1";
        if self.csdr_print_bufsizes:
            my_env["CSDR_PRINT_BUFSIZES"] = "1"
        if self.output.supports_type("secondary_fft"):
            secondary_command_fft = " | ".join(self.secondary_chain("fft"))
            secondary_command_fft = secondary_command_fft.format(
                input_pipe=self.iqtee_pipe,
                secondary_fft_input_size=self.secondary_fft_size,
                secondary_fft_size=self.secondary_fft_size,
                secondary_fft_block_size=self.secondary_fft_block_size(),
            )
            logger.debug("secondary command (fft) = %s", secondary_command_fft)

            self.secondary_process_fft = subprocess.Popen(
                secondary_command_fft, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setpgrp, env=my_env
            )
            self.output.send_output(
                "secondary_fft",
                partial(self.secondary_process_fft.stdout.read, int(self.get_secondary_fft_bytes_to_read())),
            )

        # direwolf does not provide any meaningful data on stdout
        # more specifically, it doesn't provide any data. if however, for any strange reason, it would start to do so,
        # it would block if not read. by piping it to devnull, we avoid a potential pitfall here.
        secondary_output = subprocess.DEVNULL if self.isPacket() else subprocess.PIPE
        self.secondary_process_demod = subprocess.Popen(
            secondary_command_demod, stdout=secondary_output, shell=True, preexec_fn=os.setpgrp, env=my_env
        )
        self.secondary_processes_running = True

        if self.isWsjtMode():
            smd = self.get_secondary_demodulator()
            if smd == "ft8":
                chopper = Ft8Chopper(self.secondary_process_demod.stdout)
            elif smd == "wspr":
                chopper = WsprChopper(self.secondary_process_demod.stdout)
            elif smd == "jt65":
                chopper = Jt65Chopper(self.secondary_process_demod.stdout)
            elif smd == "jt9":
                chopper = Jt9Chopper(self.secondary_process_demod.stdout)
            elif smd == "ft4":
                chopper = Ft4Chopper(self.secondary_process_demod.stdout)
            chopper.start()
            self.output.send_output("wsjt_demod", chopper.read)
        elif self.isPacket():
            # we best get the ax25 packets from the kiss socket
            kiss = KissClient(self.direwolf_port)
            self.output.send_output("packet_demod", kiss.read)
        else:
            self.output.send_output("secondary_demod", partial(self.secondary_process_demod.stdout.read, 1))

        # open control pipes for csdr and send initialization data
        if self.secondary_shift_pipe != None:  # TODO digimodes
            self.secondary_shift_pipe_file = open(self.secondary_shift_pipe, "w")  # TODO digimodes
            self.set_secondary_offset_freq(self.secondary_offset_freq)  # TODO digimodes

    def set_secondary_offset_freq(self, value):
        self.secondary_offset_freq = value
        if self.secondary_processes_running and hasattr(self, "secondary_shift_pipe_file"):
            self.secondary_shift_pipe_file.write("%g\n" % (-float(self.secondary_offset_freq) / self.if_samp_rate()))
            self.secondary_shift_pipe_file.flush()

    def stop_secondary_demodulator(self):
        if self.secondary_processes_running == False:
            return
        self.try_delete_pipes(self.secondary_pipe_names)
        self.try_delete_configs()
        if self.secondary_process_fft:
            try:
                os.killpg(os.getpgid(self.secondary_process_fft.pid), signal.SIGTERM)
            except ProcessLookupError:
                # been killed by something else, ignore
                pass
        if self.secondary_process_demod:
            try:
                os.killpg(os.getpgid(self.secondary_process_demod.pid), signal.SIGTERM)
            except ProcessLookupError:
                # been killed by something else, ignore
                pass
        self.secondary_processes_running = False

    def get_secondary_demodulator(self):
        return self.secondary_demodulator

    def set_secondary_fft_size(self, secondary_fft_size):
        # to change this, restart is required
        self.secondary_fft_size = secondary_fft_size

    def set_audio_compression(self, what):
        self.audio_compression = what

    def get_audio_bytes_to_read(self):
        # desired latency: 5ms
        # uncompressed audio has 16 bits = 2 bytes per sample
        base = self.output_rate * 0.005 * 2
        # adpcm compresses the bitstream by 4
        if self.audio_compression == "adpcm":
            base = base / 4
        return int(base)

    def set_fft_compression(self, what):
        self.fft_compression = what

    def get_fft_bytes_to_read(self):
        if self.fft_compression == "none":
            return self.fft_size * 4
        if self.fft_compression == "adpcm":
            return int((self.fft_size / 2) + (10 / 2))

    def get_secondary_fft_bytes_to_read(self):
        if self.fft_compression == "none":
            return self.secondary_fft_size * 4
        if self.fft_compression == "adpcm":
            return (self.secondary_fft_size / 2) + (10 / 2)

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.calculate_decimation()
        if self.running:
            self.restart()

    def calculate_decimation(self):
        (self.decimation, self.last_decimation, _) = self.get_decimation(self.samp_rate, self.get_audio_rate())

    def get_decimation(self, input_rate, output_rate):
        decimation = 1
        while input_rate / (decimation + 1) >= output_rate:
            decimation += 1
        fraction = float(input_rate / decimation) / output_rate
        intermediate_rate = input_rate / decimation
        return (decimation, fraction, intermediate_rate)

    def if_samp_rate(self):
        return self.samp_rate / self.decimation

    def get_name(self):
        return self.name

    def get_output_rate(self):
        return self.output_rate

    def get_audio_rate(self):
        if self.isDigitalVoice() or self.isPacket():
            return 48000
        elif self.isWsjtMode():
            return 12000
        return self.get_output_rate()

    def isDigitalVoice(self, demodulator=None):
        if demodulator is None:
            demodulator = self.get_demodulator()
        return demodulator in ["dmr", "dstar", "nxdn", "ysf"]

    def isWsjtMode(self, demodulator=None):
        if demodulator is None:
            demodulator = self.get_secondary_demodulator()
        return demodulator in ["ft8", "wspr", "jt65", "jt9", "ft4"]

    def isPacket(self, demodulator=None):
        if demodulator is None:
            demodulator = self.get_secondary_demodulator()
        return demodulator == "packet"

    def set_output_rate(self, output_rate):
        if self.output_rate == output_rate:
            return
        self.output_rate = output_rate
        self.calculate_decimation()
        self.restart()

    def set_demodulator(self, demodulator):
        if self.demodulator == demodulator:
            return
        self.demodulator = demodulator
        self.calculate_decimation()
        self.restart()

    def get_demodulator(self):
        return self.demodulator

    def set_fft_size(self, fft_size):
        self.fft_size = fft_size
        self.restart()

    def set_fft_fps(self, fft_fps):
        self.fft_fps = fft_fps
        self.restart()

    def set_fft_averages(self, fft_averages):
        self.fft_averages = fft_averages
        self.restart()

    def fft_block_size(self):
        if self.fft_averages == 0:
            return self.samp_rate / self.fft_fps
        else:
            return self.samp_rate / self.fft_fps / self.fft_averages

    def set_offset_freq(self, offset_freq):
        self.offset_freq = offset_freq
        if self.running:
            self.modification_lock.acquire()
            self.shift_pipe_file.write("%g\n" % (-float(self.offset_freq) / self.samp_rate))
            self.shift_pipe_file.flush()
            self.modification_lock.release()

    def set_bpf(self, low_cut, high_cut):
        self.low_cut = low_cut
        self.high_cut = high_cut
        if self.running:
            self.modification_lock.acquire()
            self.bpf_pipe_file.write(
                "%g %g\n" % (float(self.low_cut) / self.if_samp_rate(), float(self.high_cut) / self.if_samp_rate())
            )
            self.bpf_pipe_file.flush()
            self.modification_lock.release()

    def get_bpf(self):
        return [self.low_cut, self.high_cut]

    def set_squelch_level(self, squelch_level):
        self.squelch_level = squelch_level
        # no squelch required on digital voice modes
        actual_squelch = 0 if self.isDigitalVoice() or self.isPacket() else self.squelch_level
        if self.running:
            self.modification_lock.acquire()
            self.squelch_pipe_file.write("%g\n" % (float(actual_squelch)))
            self.squelch_pipe_file.flush()
            self.modification_lock.release()

    def set_unvoiced_quality(self, q):
        self.unvoiced_quality = q
        self.restart()

    def get_unvoiced_quality(self):
        return self.unvoiced_quality

    def set_dmr_filter(self, filter):
        if self.dmr_control_pipe_file:
            self.dmr_control_pipe_file.write("{0}\n".format(filter))
            self.dmr_control_pipe_file.flush()

    def mkfifo(self, path):
        try:
            os.unlink(path)
        except:
            pass
        os.mkfifo(path)

    def ddc_transition_bw(self):
        return self.ddc_transition_bw_rate * (self.if_samp_rate() / float(self.samp_rate))

    def try_create_pipes(self, pipe_names, command_base):
        for pipe_name in pipe_names:
            if "{" + pipe_name + "}" in command_base:
                setattr(self, pipe_name, self.pipe_base_path + pipe_name)
                self.mkfifo(getattr(self, pipe_name))
            else:
                setattr(self, pipe_name, None)

    def try_delete_pipes(self, pipe_names):
        for pipe_name in pipe_names:
            pipe_path = getattr(self, pipe_name, None)
            if pipe_path:
                try:
                    os.unlink(pipe_path)
                except FileNotFoundError:
                    # it seems like we keep calling this twice. no idea why, but we don't need the resulting error.
                    pass
                except Exception:
                    logger.exception("try_delete_pipes()")

    def try_create_configs(self, command):
        if "{direwolf_config}" in command:
            self.direwolf_config = "{tmp_dir}/openwebrx_direwolf_{myid}.conf".format(
                tmp_dir=self.temporary_directory, myid=id(self)
            )
            self.direwolf_port = KissClient.getFreePort()
            file = open(self.direwolf_config, "w")
            file.write(DirewolfConfig().getConfig(self.direwolf_port, self.is_service))
            file.close()
        else:
            self.direwolf_config = None
            self.direwolf_port = None

    def try_delete_configs(self):
        if self.direwolf_config:
            try:
                os.unlink(self.direwolf_config)
            except FileNotFoundError:
                # result suits our expectations. fine :)
                pass
            except Exception:
                logger.exception("try_delete_configs()")
            self.direwolf_config = None

    def start(self):
        self.modification_lock.acquire()
        if self.running:
            self.modification_lock.release()
            return
        self.running = True

        command_base = " | ".join(self.chain(self.demodulator))

        # create control pipes for csdr
        self.pipe_base_path = "{tmp_dir}/openwebrx_pipe_{myid}_".format(tmp_dir=self.temporary_directory, myid=id(self))

        self.try_create_pipes(self.pipe_names, command_base)

        # run the command
        command = command_base.format(
            bpf_pipe=self.bpf_pipe,
            shift_pipe=self.shift_pipe,
            decimation=self.decimation,
            last_decimation=self.last_decimation,
            fft_size=self.fft_size,
            fft_block_size=self.fft_block_size(),
            fft_averages=self.fft_averages,
            bpf_transition_bw=float(self.bpf_transition_bw) / self.if_samp_rate(),
            ddc_transition_bw=self.ddc_transition_bw(),
            flowcontrol=int(self.samp_rate * 2),
            start_bufsize=self.base_bufsize * self.decimation,
            nc_port=self.nc_port,
            squelch_pipe=self.squelch_pipe,
            smeter_pipe=self.smeter_pipe,
            meta_pipe=self.meta_pipe,
            iqtee_pipe=self.iqtee_pipe,
            iqtee2_pipe=self.iqtee2_pipe,
            output_rate=self.get_output_rate(),
            smeter_report_every=int(self.if_samp_rate() / 6000),
            unvoiced_quality=self.get_unvoiced_quality(),
            dmr_control_pipe=self.dmr_control_pipe,
            audio_rate=self.get_audio_rate(),
        )

        logger.debug("Command = %s", command)
        my_env = os.environ.copy()
        if self.csdr_dynamic_bufsize:
            my_env["CSDR_DYNAMIC_BUFSIZE_ON"] = "1"
        if self.csdr_print_bufsizes:
            my_env["CSDR_PRINT_BUFSIZES"] = "1"

        out = subprocess.PIPE if self.output.supports_type("audio") else subprocess.DEVNULL
        self.process = subprocess.Popen(command, stdout=out, shell=True, preexec_fn=os.setpgrp, env=my_env)

        def watch_thread():
            rc = self.process.wait()
            logger.debug("dsp thread ended with rc=%d", rc)
            if rc == 0 and self.running and not self.modification_lock.locked():
                logger.debug("restarting since rc = 0, self.running = true, and no modification")
                self.restart()

        threading.Thread(target=watch_thread).start()

        if self.output.supports_type("audio"):
            self.output.send_output(
                "audio",
                partial(
                    self.process.stdout.read,
                    self.get_fft_bytes_to_read() if self.demodulator == "fft" else self.get_audio_bytes_to_read(),
                ),
            )

        # open control pipes for csdr
        if self.bpf_pipe:
            self.bpf_pipe_file = open(self.bpf_pipe, "w")
        if self.shift_pipe:
            self.shift_pipe_file = open(self.shift_pipe, "w")
        if self.squelch_pipe:
            self.squelch_pipe_file = open(self.squelch_pipe, "w")
        self.start_secondary_demodulator()

        self.modification_lock.release()

        # send initial config through the pipes
        if self.squelch_pipe:
            self.set_squelch_level(self.squelch_level)
        if self.shift_pipe:
            self.set_offset_freq(self.offset_freq)
        if self.bpf_pipe:
            self.set_bpf(self.low_cut, self.high_cut)
        if self.smeter_pipe:
            self.smeter_pipe_file = open(self.smeter_pipe, "r")

            def read_smeter():
                raw = self.smeter_pipe_file.readline()
                if len(raw) == 0:
                    return None
                else:
                    return float(raw.rstrip("\n"))

            self.output.send_output("smeter", read_smeter)
        if self.meta_pipe != None:
            # TODO make digiham output unicode and then change this here
            self.meta_pipe_file = open(self.meta_pipe, "r", encoding="cp437")

            def read_meta():
                raw = self.meta_pipe_file.readline()
                if len(raw) == 0:
                    return None
                else:
                    return raw.rstrip("\n")

            self.output.send_output("meta", read_meta)

        if self.dmr_control_pipe:
            self.dmr_control_pipe_file = open(self.dmr_control_pipe, "w")

    def stop(self):
        self.modification_lock.acquire()
        self.running = False
        if hasattr(self, "process"):
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except ProcessLookupError:
                # been killed by something else, ignore
                pass
        self.stop_secondary_demodulator()

        self.try_delete_pipes(self.pipe_names)

        self.modification_lock.release()

    def restart(self):
        if not self.running:
            return
        self.stop()
        self.start()

    def __del__(self):
        self.stop()
        del self.process
