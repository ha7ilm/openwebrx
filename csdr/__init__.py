"""
OpenWebRX csdr plugin: do the signal processing with csdr

    This file is part of OpenWebRX,
    an open-source SDR receiver software with a web UI.
    Copyright (c) 2013-2015 by Andras Retzler <randras@sdr.hu>
    Copyright (c) 2019-2021 by Jakob Ketterl <dd5jfk@darc.de>

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
import math
from functools import partial

from csdr.output import Output

from owrx.kiss import KissClient, DirewolfConfig, DirewolfConfigSubscriber
from owrx.audio.chopper import AudioChopper

from csdr.pipe import Pipe

from pycsdr.modules import Buffer
from pycsdr.types import Format
from csdr.chain.demodulator import DemodulatorChain
from csdr.chain.fm import NFm, WFm
from csdr.chain.am import Am
from csdr.chain.ssb import Ssb
from csdr.chain.digiham import Dstar
from csdr.chain.clientaudio import ClientAudioChain

import logging

logger = logging.getLogger(__name__)


class Dsp(DirewolfConfigSubscriber):
    def __init__(self, output: Output):
        self.pycsdr_enabled = True
        self.pycsdr_chain = None
        self.pycsdr_client_chain = None
        self.pycsdr_reader = None
        self.pycsdr_power_reader = None
        self.buffer = None

        self.samp_rate = 250000
        self.output_rate = 11025
        self.hd_output_rate = 44100
        self.fft_fps = 5
        self.center_freq = 0
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
        self.decimation = None
        self.last_decimation = None
        self.nc_port = None
        self.squelch_level = -150
        self.fft_averages = 50
        self.wfm_deemphasis_tau = 50e-6
        self.iqtee = False
        self.iqtee2 = False
        self.secondary_demodulator = None
        self.secondary_fft_size = 1024
        self.secondary_process_fft = None
        self.secondary_process_demod = None
        self.pipe_names = {
            "bpf_pipe": Pipe.WRITE,
            "shift_pipe": Pipe.WRITE,
            "squelch_pipe": Pipe.WRITE,
            "smeter_pipe": Pipe.READ,
            "meta_pipe": Pipe.READ,
            "iqtee_pipe": Pipe.NONE,
            "iqtee2_pipe": Pipe.NONE,
            "dmr_control_pipe": Pipe.WRITE,
        }
        self.pipes = {}
        self.secondary_pipe_names = {"secondary_shift_pipe": Pipe.WRITE}
        self.secondary_offset_freq = 1000
        self.codecserver = None
        self.modification_lock = threading.Lock()
        self.output = output

        self.temporary_directory = None
        self.pipe_base_path = None
        self.set_temporary_directory("/tmp")

        self.is_service = False
        self.direwolf_config = None
        self.direwolf_config_path = None
        self.process = None

    def setBuffer(self, buffer):
        self.buffer = buffer
        if self.pycsdr_chain is not None:
            self.pycsdr_chain.setInput(buffer)

    def set_service(self, flag=True):
        self.is_service = flag

    def set_temporary_directory(self, what):
        self.temporary_directory = what
        self.pipe_base_path = "{tmp_dir}/openwebrx_pipe_".format(tmp_dir=self.temporary_directory)

    def chain(self, which):
        if self.pycsdr_enabled:
            if which == "nfm":
                self.pycsdr_chain = DemodulatorChain(self.samp_rate, self.get_audio_rate(), 0.0, NFm(self.get_audio_rate()))
                return self.pycsdr_chain
            elif which == "am":
                self.pycsdr_chain = DemodulatorChain(self.samp_rate, self.get_audio_rate(), 0.0, Am())
                return self.pycsdr_chain
            elif which == "ssb":
                self.pycsdr_chain = DemodulatorChain(self.samp_rate, self.get_audio_rate(), 0.0, Ssb())
                return self.pycsdr_chain
            elif which == "wfm":
                self.pycsdr_chain = DemodulatorChain(self.samp_rate, 200000, 0.0, WFm(self.get_audio_rate(), self.wfm_deemphasis_tau))
                return self.pycsdr_chain
            elif which == "dstar":
                self.pycsdr_chain = DemodulatorChain(self.samp_rate, 48000, 0.0, Dstar(self.codecserver))
                return self.pycsdr_chain

        chain = ["nc -v 127.0.0.1 {nc_port}"]
        chain += ["csdr shift_addfast_cc --fifo {shift_pipe}"]
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
        last_decimation_block = []
        if self.last_decimation >= 2.0:
            # activate prefilter if signal has been oversampled, e.g. WFM
            last_decimation_block = ["csdr fractional_decimator_ff {last_decimation} 12 --prefilter"]
        elif self.last_decimation != 1.0:
            last_decimation_block = ["csdr fractional_decimator_ff {last_decimation}"]
        if which == "nfm":
            chain += ["csdr fmdemod_quadri_cf", "csdr limit_ff"]
            chain += last_decimation_block
            chain += [
                "csdr deemphasis_nfm_ff {audio_rate}",
                "csdr agc_ff --profile slow --max 3",
            ]
            if self.get_audio_rate() != self.get_output_rate():
                chain += [
                    "sox -t raw -r {audio_rate} -e floating-point -b 32 -c 1 --buffer 32 - -t raw -r {output_rate} -e signed-integer -b 16 -c 1 - "
                ]
            else:
                chain += ["csdr convert_f_s16"]
        elif which == "wfm":
            chain += [
                "csdr fmdemod_quadri_cf",
                "csdr limit_ff",
            ]
            chain += last_decimation_block
            chain += ["csdr deemphasis_wfm_ff {audio_rate} {wfm_deemphasis_tau}", "csdr convert_f_s16"]
        elif self.isDigitalVoice(which):
            chain += ["csdr fmdemod_quadri_cf"]
            chain += last_decimation_block
            chain += ["dc_block"]
            # m17
            if which == "m17":
                chain += [
                    "csdr limit_ff",
                    "csdr convert_f_s16",
                    "m17-demod",
                ]
            else:
                # digiham modes
                if which == "dstar":
                    chain += [
                        "fsk_demodulator -s 10",
                        "dstar_decoder --fifo {meta_pipe}",
                        "mbe_synthesizer -d {codecserver_arg}",
                    ]
                elif which == "nxdn":
                    chain += [
                        "rrc_filter --narrow",
                        "gfsk_demodulator --samples 20",
                        "nxdn_decoder --fifo {meta_pipe}",
                        "mbe_synthesizer {codecserver_arg}",
                    ]
                else:
                    chain += ["rrc_filter", "gfsk_demodulator"]
                    if which == "dmr":
                        chain += [
                            "dmr_decoder --fifo {meta_pipe} --control-fifo {dmr_control_pipe}",
                            "mbe_synthesizer {codecserver_arg}",
                        ]
                    elif which == "ysf":
                        chain += ["ysf_decoder --fifo {meta_pipe}", "mbe_synthesizer -y {codecserver_arg}"]
                chain += ["digitalvoice_filter"]
            chain += [
                "CSDR_FIXED_BUFSIZE=32 csdr agc_s16 --max 30 --initial 3",
                "sox -t raw -r 8000 -e signed-integer -b 16 -c 1 --buffer 32 - -t raw -r {output_rate} -e signed-integer -b 16 -c 1 - ",
            ]
        elif which == "am":
            chain += ["csdr amdemod_cf", "csdr fastdcblock_ff"]
            chain += last_decimation_block
            chain += [
                "csdr agc_ff --profile slow --initial 200",
                "csdr convert_f_s16",
            ]
        elif self.isFreeDV(which):
            chain += ["csdr realpart_cf"]
            chain += last_decimation_block
            chain += [
                "csdr agc_ff",
                "csdr convert_f_s16",
                "freedv_rx 1600 - -",
                "csdr agc_s16 --max 30 --initial 3",
                "sox -t raw -r 8000 -e signed-integer -b 16 -c 1 --buffer 32 - -t raw -r {output_rate} -e signed-integer -b 16 -c 1 - ",
            ]
        elif self.isDrm(which):
            if self.last_decimation != 1.0:
                # we are still dealing with complex samples here, so the regular last_decimation_block doesn't fit
                chain += ["csdr fractional_decimator_cc {last_decimation}"]
            chain += [
                "csdr convert_f_s16",
                "dream -c 6 --sigsrate 48000 --audsrate 48000 -I - -O -",
                "sox -t raw -r 48000 -e signed-integer -b 16 -c 2 - -t raw -r {output_rate} -e signed-integer -b 16 -c 1 - ",
            ]
        elif which == "ssb":
            chain += ["csdr realpart_cf"]
            chain += last_decimation_block
            chain += ["csdr agc_ff"]
            # fixed sample rate necessary for the wsjt-x tools. fix with sox...
            if self.get_audio_rate() != self.get_output_rate():
                chain += [
                    "sox -t raw -r {audio_rate} -e floating-point -b 32 -c 1 --buffer 32 - -t raw -r {output_rate} -e signed-integer -b 16 -c 1 - "
                ]
            else:
                chain += ["csdr convert_f_s16"]

        if self.audio_compression == "adpcm":
            chain += ["csdr++ adpcm -e --sync"]
        return chain

    def secondary_chain(self, which):
        chain = ["cat {input_pipe}"]
        if which == "fft":
            chain += [
                "csdr fft_cc {secondary_fft_input_size} {secondary_fft_block_size}",
                "csdr logpower_cf -70"
                if self.fft_averages == 0
                else "csdr logaveragepower_cf -70 {secondary_fft_size} {fft_averages}",
                "csdr fft_exchange_sides_ff {secondary_fft_input_size}",
            ]
            if self.fft_compression == "adpcm":
                chain += ["csdr compress_fft_adpcm_f_u8 {secondary_fft_size}"]
            return chain
        elif which == "bpsk31" or which == "bpsk63":
            return chain + [
                "csdr shift_addfast_cc --fifo {secondary_shift_pipe}",
                "csdr bandpass_fir_fft_cc -{secondary_bpf_cutoff} {secondary_bpf_cutoff} {secondary_bpf_cutoff}",
                "csdr simple_agc_cc 0.001 0.5",
                "csdr timing_recovery_cc GARDNER {secondary_samples_per_bits} 0.5 2 --add_q",
                "CSDR_FIXED_BUFSIZE=1 csdr dbpsk_decoder_c_u8",
                "CSDR_FIXED_BUFSIZE=1 csdr psk31_varicode_decoder_u8_u8",
            ]
        elif self.isWsjtMode(which) or self.isJs8(which):
            chain += ["csdr realpart_cf"]
            if self.last_decimation != 1.0:
                chain += ["csdr fractional_decimator_ff {last_decimation}"]
            return chain + ["csdr agc_ff", "csdr convert_f_s16"]
        elif which == "packet":
            chain += ["csdr fmdemod_quadri_cf"]
            if self.last_decimation != 1.0:
                chain += ["csdr fractional_decimator_ff {last_decimation}"]
            return chain + ["csdr convert_f_s16", "direwolf -c {direwolf_config} -r {audio_rate} -t 0 -q d -q h 1>&2"]
        elif which == "pocsag":
            chain += ["csdr fmdemod_quadri_cf"]
            if self.last_decimation != 1.0:
                chain += ["csdr fractional_decimator_ff {last_decimation}"]
            return chain + ["fsk_demodulator -i", "pocsag_decoder"]

    def set_secondary_demodulator(self, what):
        if self.get_secondary_demodulator() == what:
            return
        self.secondary_demodulator = what
        self.calculate_decimation()
        self.restart()

    def secondary_fft_block_size(self):
        base = (self.samp_rate / self.decimation) / (self.fft_fps * 2)
        if self.fft_averages == 0:
            return base
        return base / self.fft_averages

    def secondary_decimation(self):
        return 1  # currently unused

    def secondary_bpf_cutoff(self):
        if self.secondary_demodulator == "bpsk31":
            return 31.25 / self.if_samp_rate()
        elif self.secondary_demodulator == "bpsk63":
            return 62.5 / self.if_samp_rate()
        return 0

    def secondary_bpf_transition_bw(self):
        if self.secondary_demodulator == "bpsk31":
            return 31.25 / self.if_samp_rate()
        elif self.secondary_demodulator == "bpsk63":
            return 62.5 / self.if_samp_rate()
        return 0

    def secondary_samples_per_bits(self):
        if self.secondary_demodulator == "bpsk31":
            return int(round(self.if_samp_rate() / 31.25)) & ~3
        elif self.secondary_demodulator == "bpsk63":
            return int(round(self.if_samp_rate() / 62.5)) & ~3
        return 0

    def secondary_bw(self):
        if self.secondary_demodulator == "bpsk31":
            return 31.25
        elif self.secondary_demodulator == "bpsk63":
            return 62.5

    def start_secondary_demodulator(self):
        if not self.secondary_demodulator:
            return
        logger.debug("starting secondary demodulator from IF input sampled at %d" % self.if_samp_rate())
        secondary_command_demod = " | ".join(self.secondary_chain(self.secondary_demodulator))
        self.try_create_pipes(self.secondary_pipe_names, secondary_command_demod)
        self.try_create_configs(secondary_command_demod)

        secondary_command_demod = secondary_command_demod.format(
            input_pipe=self.pipes["iqtee2_pipe"],
            secondary_shift_pipe=self.pipes["secondary_shift_pipe"],
            secondary_decimation=self.secondary_decimation(),
            secondary_samples_per_bits=self.secondary_samples_per_bits(),
            secondary_bpf_cutoff=self.secondary_bpf_cutoff(),
            secondary_bpf_transition_bw=self.secondary_bpf_transition_bw(),
            if_samp_rate=self.if_samp_rate(),
            last_decimation=self.last_decimation,
            audio_rate=self.get_audio_rate(),
            direwolf_config=self.direwolf_config_path,
        )

        logger.debug("secondary command (demod) = %s", secondary_command_demod)
        if self.output.supports_type("secondary_fft"):
            secondary_command_fft = " | ".join(self.secondary_chain("fft"))
            secondary_command_fft = secondary_command_fft.format(
                input_pipe=self.pipes["iqtee_pipe"],
                secondary_fft_input_size=self.secondary_fft_size,
                secondary_fft_size=self.secondary_fft_size,
                secondary_fft_block_size=self.secondary_fft_block_size(),
                fft_averages=self.fft_averages,
            )
            logger.debug("secondary command (fft) = %s", secondary_command_fft)

            self.secondary_process_fft = subprocess.Popen(
                secondary_command_fft, stdout=subprocess.PIPE, shell=True, start_new_session=True
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
            secondary_command_demod, stdout=secondary_output, shell=True, start_new_session=True
        )
        self.secondary_processes_running = True

        if self.isWsjtMode() or self.isJs8():
            chopper = AudioChopper(self, self.get_secondary_demodulator())
            chopper.send_output("audio", self.secondary_process_demod.stdout.read)
            output_type = "js8_demod" if self.isJs8() else "wsjt_demod"
            self.output.send_output(output_type, chopper.read)
        elif self.isPacket():
            # we best get the ax25 packets from the kiss socket
            kiss = KissClient(self.direwolf_config.getPort())
            self.output.send_output("packet_demod", kiss.read)
        elif self.isPocsag():
            self.output.send_output("pocsag_demod", self.secondary_process_demod.stdout.readline)
        else:
            self.output.send_output("secondary_demod", partial(self.secondary_process_demod.stdout.read, 1))

        # open control pipes for csdr and send initialization data
        if self.has_pipe("secondary_shift_pipe"):  # TODO digimodes
            self.set_secondary_offset_freq(self.secondary_offset_freq)  # TODO digimodes

    def set_secondary_offset_freq(self, value):
        self.secondary_offset_freq = value
        if self.secondary_processes_running and self.has_pipe("secondary_shift_pipe"):
            self.pipes["secondary_shift_pipe"].write(
                "%g\n" % (-float(self.secondary_offset_freq) / self.if_samp_rate())
            )

    def stop_secondary_demodulator(self):
        if not self.secondary_processes_running:
            return
        self.try_delete_pipes(self.secondary_pipe_names)
        self.try_delete_configs()
        if self.secondary_process_fft:
            try:
                os.killpg(os.getpgid(self.secondary_process_fft.pid), signal.SIGTERM)
                # drain any leftover data to free file descriptors
                self.secondary_process_fft.communicate()
                self.secondary_process_fft = None
            except ProcessLookupError:
                # been killed by something else, ignore
                pass
        if self.secondary_process_demod:
            try:
                os.killpg(os.getpgid(self.secondary_process_demod.pid), signal.SIGTERM)
                # drain any leftover data to free file descriptors
                self.secondary_process_demod.communicate()
                self.secondary_process_demod = None
            except ProcessLookupError:
                # been killed by something else, ignore
                pass
        self.secondary_processes_running = False

    def get_secondary_demodulator(self):
        return self.secondary_demodulator

    def set_secondary_fft_size(self, secondary_fft_size):
        if self.secondary_fft_size == secondary_fft_size:
            return
        self.secondary_fft_size = secondary_fft_size
        self.restart()

    def set_audio_compression(self, what):
        if self.audio_compression == what:
            return
        self.audio_compression = what
        self.restart()

    def get_audio_bytes_to_read(self):
        # desired latency: 5ms
        # uncompressed audio has 16 bits = 2 bytes per sample
        base = self.output_rate * 0.005 * 2
        # adpcm compresses the bitstream by 4
        if self.audio_compression == "adpcm":
            base = base / 4
        return int(base)

    def set_fft_compression(self, what):
        if self.fft_compression == what:
            return
        self.fft_compression = what
        self.restart()

    def get_secondary_fft_bytes_to_read(self):
        if self.fft_compression == "none":
            return self.secondary_fft_size * 4
        if self.fft_compression == "adpcm":
            return (self.secondary_fft_size / 2) + (10 / 2)

    def set_samp_rate(self, samp_rate):
        if self.samp_rate == samp_rate:
            return
        self.samp_rate = samp_rate
        self.calculate_decimation()
        if self.running:
            self.restart()

    def calculate_decimation(self):
        (self.decimation, self.last_decimation) = self.get_decimation(self.samp_rate, self.get_audio_rate())

    def get_decimation(self, input_rate, output_rate):
        if output_rate <= 0:
            raise ValueError("invalid output rate: {rate}".format(rate=output_rate))
        decimation = 1
        target_rate = output_rate
        # wideband fm has a much higher frequency deviation (75kHz).
        # we cannot cover this if we immediately decimate to the sample rate the audio will have later on, so we need
        # to compensate here.
        if self.get_demodulator() == "wfm" and output_rate < 200000:
            target_rate = 200000
        while input_rate / (decimation + 1) >= target_rate:
            decimation += 1
        fraction = float(input_rate / decimation) / output_rate
        return decimation, fraction

    def if_samp_rate(self):
        return self.samp_rate / self.decimation

    def get_name(self):
        return self.name

    def get_output_rate(self):
        return self.output_rate

    def get_hd_output_rate(self):
        return self.hd_output_rate

    def get_audio_rate(self):
        if self.isDigitalVoice() or self.isPacket() or self.isPocsag() or self.isDrm():
            return 48000
        elif self.isWsjtMode() or self.isJs8():
            return 12000
        elif self.isFreeDV():
            return 8000
        elif self.isHdAudio():
            return self.get_hd_output_rate()
        return self.get_output_rate()

    def isDigitalVoice(self, demodulator=None):
        if demodulator is None:
            demodulator = self.get_demodulator()
        return demodulator in ["dmr", "dstar", "nxdn", "ysf", "m17"]

    def isWsjtMode(self, demodulator=None):
        if demodulator is None:
            demodulator = self.get_secondary_demodulator()
        return demodulator in ["ft8", "wspr", "jt65", "jt9", "ft4", "fst4", "fst4w", "q65"]

    def isJs8(self, demodulator=None):
        if demodulator is None:
            demodulator = self.get_secondary_demodulator()
        return demodulator == "js8"

    def isPacket(self, demodulator=None):
        if demodulator is None:
            demodulator = self.get_secondary_demodulator()
        return demodulator == "packet"

    def isPocsag(self, demodulator=None):
        if demodulator is None:
            demodulator = self.get_secondary_demodulator()
        return demodulator == "pocsag"

    def isFreeDV(self, demodulator=None):
        if demodulator is None:
            demodulator = self.get_demodulator()
        return demodulator == "freedv"

    def isHdAudio(self, demodulator=None):
        if demodulator is None:
            demodulator = self.get_demodulator()
        return demodulator == "wfm"

    def isDrm(self, demodulator=None):
        if demodulator is None:
            demodulator = self.get_demodulator()
        return demodulator == "drm"

    def set_output_rate(self, output_rate):
        if self.output_rate == output_rate:
            return
        self.output_rate = output_rate
        self.calculate_decimation()
        self.restart()

    def set_hd_output_rate(self, hd_output_rate):
        if self.hd_output_rate == hd_output_rate:
            return
        self.hd_output_rate = hd_output_rate
        self.calculate_decimation()
        self.restart()

    def set_demodulator(self, demodulator):
        if demodulator in ["usb", "lsb", "cw"]:
            demodulator = "ssb"
        if self.demodulator == demodulator:
            return
        self.demodulator = demodulator
        self.calculate_decimation()
        self.restart()

    def get_demodulator(self):
        return self.demodulator

    def set_offset_freq(self, offset_freq):
        if offset_freq is None:
            return
        self.offset_freq = offset_freq
        if self.running:
            if self.pycsdr_chain is not None and isinstance(self.pycsdr_chain, DemodulatorChain):
                self.pycsdr_chain.setShiftRate(-float(self.offset_freq) / self.samp_rate)
            else:
                self.pipes["shift_pipe"].write("%g\n" % (-float(self.offset_freq) / self.samp_rate))


    def set_center_freq(self, center_freq):
        # dsp only needs to know this to be able to pass it to decoders in the form of get_operating_freq()
        self.center_freq = center_freq

    def get_operating_freq(self):
        return self.center_freq + self.offset_freq

    def set_bandpass(self, bandpass):
        self.set_bpf(bandpass.low_cut, bandpass.high_cut)

    def set_bpf(self, low_cut, high_cut):
        self.low_cut = low_cut
        self.high_cut = high_cut
        if self.running:
            if self.pycsdr_chain is not None and isinstance(self.pycsdr_chain, DemodulatorChain):
                self.pycsdr_chain.setBandpass(float(self.low_cut) / self.if_samp_rate(), float(self.high_cut) / self.if_samp_rate())
            else:
                self.pipes["bpf_pipe"].write(
                    "%g %g\n" % (float(self.low_cut) / self.if_samp_rate(), float(self.high_cut) / self.if_samp_rate())
                )

    def get_bpf(self):
        return [self.low_cut, self.high_cut]

    def convertToLinear(self, db):
        return float(math.pow(10, db / 10))

    def set_squelch_level(self, squelch_level):
        self.squelch_level = squelch_level
        # no squelch required on digital voice modes
        actual_squelch = (
            -150
            if self.isDigitalVoice() or self.isPacket() or self.isPocsag() or self.isFreeDV() or self.isDrm()
            else self.squelch_level
        )
        if self.running:
            if self.pycsdr_chain is not None and isinstance(self.pycsdr_chain, DemodulatorChain):
                self.pycsdr_chain.setSquelchLevel(self.convertToLinear(actual_squelch))
            else:
                self.pipes["squelch_pipe"].write("%g\n" % (self.convertToLinear(actual_squelch)))

    def set_codecserver(self, s):
        if self.codecserver == s:
            return
        self.codecserver = s
        self.restart()

    def get_codecserver_arg(self):
        return "-s {}".format(self.codecserver) if self.codecserver else ""

    def set_dmr_filter(self, filter):
        if self.has_pipe("dmr_control_pipe"):
            self.pipes["dmr_control_pipe"].write("{0}\n".format(filter))

    def set_wfm_deemphasis_tau(self, tau):
        if self.wfm_deemphasis_tau == tau:
            return
        self.wfm_deemphasis_tau = tau
        self.restart()

    def ddc_transition_bw(self):
        return self.ddc_transition_bw_rate * (self.if_samp_rate() / float(self.samp_rate))

    def try_create_pipes(self, pipe_names, command_base):
        for pipe_name, pipe_type in pipe_names.items():
            if self.has_pipe(pipe_name):
                logger.warning("{pipe_name} is still in use", pipe_name=pipe_name)
                self.pipes[pipe_name].close()
            if "{" + pipe_name + "}" in command_base:
                p = self.pipe_base_path + pipe_name
                encoding = None
                # TODO make digiham output unicode and then change this here
                #      the whole pipe enoding feature onlye exists because of this
                if pipe_name == "meta_pipe":
                    encoding = "cp437"
                self.pipes[pipe_name] = Pipe.create(p, pipe_type, encoding=encoding)
            else:
                self.pipes[pipe_name] = None

    def has_pipe(self, name):
        return name in self.pipes and self.pipes[name] is not None

    def try_delete_pipes(self, pipe_names):
        for pipe_name in pipe_names:
            if self.has_pipe(pipe_name):
                self.pipes[pipe_name].close()
                self.pipes[pipe_name] = None

    def try_create_configs(self, command):
        if "{direwolf_config}" in command:
            self.direwolf_config_path = "{tmp_dir}/openwebrx_direwolf_{myid}.conf".format(
                tmp_dir=self.temporary_directory, myid=id(self)
            )
            self.direwolf_config = DirewolfConfig()
            self.direwolf_config.wire(self)
            file = open(self.direwolf_config_path, "w")
            file.write(self.direwolf_config.getConfig(self.is_service))
            file.close()
        else:
            self.direwolf_config = None
            self.direwolf_config_path = None

    def try_delete_configs(self):
        if self.direwolf_config is not None:
            self.direwolf_config.unwire(self)
            self.direwolf_config = None
        if self.direwolf_config_path is not None:
            try:
                os.unlink(self.direwolf_config_path)
            except FileNotFoundError:
                # result suits our expectations. fine :)
                pass
            except Exception:
                logger.exception("try_delete_configs()")
            self.direwolf_config_path = None

    def onConfigChanged(self):
        self.restart()

    def start(self):
        with self.modification_lock:
            if self.running:
                return
            self.running = True

            chain = self.chain(self.demodulator)
            if self.pycsdr_enabled and isinstance(chain, DemodulatorChain):
                self.set_squelch_level(self.squelch_level)
                self.set_bpf(self.low_cut, self.high_cut)
                self.set_offset_freq(self.offset_freq)

                chain.setInput(self.buffer)

                output_rate = self.get_hd_output_rate() if self.isHdAudio() else self.get_output_rate()
                audio_rate = 8000 if self.isDigitalVoice() else self.get_audio_rate()
                self.pycsdr_client_chain = ClientAudioChain(chain.getOutputFormat(), audio_rate, output_rate, self.audio_compression)
                buffer = Buffer(chain.getOutputFormat())
                chain.setWriter(buffer)
                self.pycsdr_client_chain.setInput(buffer)

                outputBuffer = Buffer(self.pycsdr_client_chain.getOutputFormat())
                self.pycsdr_client_chain.setWriter(outputBuffer)
                self.pycsdr_reader = outputBuffer.getReader()
                audio_type = "hd_audio" if self.isHdAudio() else "audio"
                self.output.send_output(audio_type, self.pycsdr_reader.read)

                powerBuffer = Buffer(Format.FLOAT)
                chain.setPowerWriter(powerBuffer)
                self.pycsdr_power_reader = powerBuffer.getReader()
                self.output.send_output("smeter", self.pycsdr_power_reader.read)
                return

            command_base = " | ".join(chain)

            # create control pipes for csdr
            self.try_create_pipes(self.pipe_names, command_base)

            # send initial config through the pipes
            if self.has_pipe("bpf_pipe"):
                self.set_bpf(self.low_cut, self.high_cut)
            if self.has_pipe("shift_pipe"):
                self.set_offset_freq(self.offset_freq)
            if self.has_pipe("squelch_pipe"):
                self.set_squelch_level(self.squelch_level)
            if self.has_pipe("dmr_control_pipe"):
                self.set_dmr_filter(3)

            # run the command
            command = command_base.format(
                bpf_pipe=self.pipes["bpf_pipe"],
                shift_pipe=self.pipes["shift_pipe"],
                squelch_pipe=self.pipes["squelch_pipe"],
                smeter_pipe=self.pipes["smeter_pipe"],
                meta_pipe=self.pipes["meta_pipe"],
                iqtee_pipe=self.pipes["iqtee_pipe"],
                iqtee2_pipe=self.pipes["iqtee2_pipe"],
                dmr_control_pipe=self.pipes["dmr_control_pipe"],
                decimation=self.decimation,
                last_decimation=self.last_decimation,
                bpf_transition_bw=float(self.bpf_transition_bw) / self.if_samp_rate(),
                ddc_transition_bw=self.ddc_transition_bw(),
                flowcontrol=int(self.samp_rate * 2),
                start_bufsize=self.base_bufsize * self.decimation,
                nc_port=self.nc_port,
                output_rate=self.get_output_rate(),
                smeter_report_every=int(self.if_samp_rate() / 6000),
                codecserver_arg=self.get_codecserver_arg(),
                audio_rate=self.get_audio_rate(),
                wfm_deemphasis_tau=self.wfm_deemphasis_tau,
            )

            logger.debug("Command = %s", command)

            out = subprocess.PIPE if self.output.supports_type("audio") else subprocess.DEVNULL
            self.process = subprocess.Popen(command, stdout=out, shell=True, start_new_session=True)

            def watch_thread():
                rc = self.process.wait()
                logger.debug("dsp thread ended with rc=%d", rc)
                if rc == 0 and self.running and not self.modification_lock.locked():
                    logger.debug("restarting since rc = 0, self.running = true, and no modification")
                    self.restart()

            threading.Thread(target=watch_thread, name="csdr_watch_thread").start()

            audio_type = "hd_audio" if self.isHdAudio() else "audio"
            if self.output.supports_type(audio_type):
                self.output.send_output(
                    audio_type,
                    partial(
                        self.process.stdout.read,
                        self.get_audio_bytes_to_read(),
                    ),
                )

            self.start_secondary_demodulator()

        if self.has_pipe("smeter_pipe"):

            def read_smeter():
                raw = self.pipes["smeter_pipe"].readline()
                if len(raw) == 0:
                    return None
                else:
                    return float(raw.rstrip("\n"))

            self.output.send_output("smeter", read_smeter)
        if self.has_pipe("meta_pipe"):

            def read_meta():
                raw = self.pipes["meta_pipe"].readline()
                if len(raw) == 0:
                    return None
                else:
                    return raw.rstrip("\n")

            self.output.send_output("meta", read_meta)

    def stop(self):
        with self.modification_lock:
            self.running = False
            if self.pycsdr_enabled and self.pycsdr_chain is not None:
                self.pycsdr_chain.stop()
                self.pycsdr_chain = None
                self.pycsdr_reader.stop()
                self.pycsdr_reader = None
                self.pycsdr_power_reader.stop()
                self.pycsdr_power_reader = None
                self.pycsdr_client_chain.stop()
                self.pycsdr_client_chain = None
            if self.process is not None:
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                    # drain any leftover data to free file descriptors
                    self.process.communicate()
                    self.process = None
                except ProcessLookupError:
                    # been killed by something else, ignore
                    pass
            self.stop_secondary_demodulator()

            self.try_delete_pipes(self.pipe_names)
            self.try_delete_configs()

    def restart(self):
        if not self.running:
            return
        self.stop()
        self.start()
