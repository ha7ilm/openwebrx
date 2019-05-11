"""
OpenWebRX csdr plugin: do the signal processing with csdr

    This file is part of OpenWebRX,
    an open-source SDR receiver software with a web UI.
    Copyright (c) 2013-2015 by Andras Retzler <randras@sdr.hu>

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
import time
import os
import signal
import threading

import logging
logger = logging.getLogger(__name__)

class dsp:

    def __init__(self):
        self.samp_rate = 250000
        self.output_rate = 11025 #this is default, and cannot be set at the moment
        self.fft_size = 1024
        self.fft_fps = 5
        self.offset_freq = 0
        self.low_cut = -4000
        self.high_cut = 4000
        self.bpf_transition_bw = 320 #Hz, and this is a constant
        self.ddc_transition_bw_rate = 0.15 # of the IF sample rate
        self.running = False
        self.secondary_processes_running = False
        self.audio_compression = "none"
        self.fft_compression = "none"
        self.demodulator = "nfm"
        self.name = "csdr"
        self.base_bufsize = 512
        self.nc_port = 4951
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
        self.pipe_names=["bpf_pipe", "shift_pipe", "squelch_pipe", "smeter_pipe", "iqtee_pipe", "iqtee2_pipe"]
        self.secondary_pipe_names=["secondary_shift_pipe"]
        self.secondary_offset_freq = 1000
        self.modification_lock = threading.Lock()

    def chain(self,which):
        any_chain_base="nc -v 127.0.0.1 {nc_port} | "
        if self.csdr_dynamic_bufsize: any_chain_base+="csdr setbuf {start_bufsize} | "
        if self.csdr_through: any_chain_base+="csdr through | "
        if which == "fft":
            fft_chain_base = any_chain_base+"csdr fft_cc {fft_size} {fft_block_size} | " + \
                ("csdr logpower_cf -70 | " if self.fft_averages == 0 else "csdr logaveragepower_cf -70 {fft_size} {fft_averages} | ") + \
                "csdr fft_exchange_sides_ff {fft_size}"
            if self.fft_compression=="adpcm":
                return fft_chain_base+" | csdr compress_fft_adpcm_f_u8 {fft_size}"
            else:
                return fft_chain_base
        chain_begin=any_chain_base+"csdr shift_addition_cc --fifo {shift_pipe} | csdr fir_decimate_cc {decimation} {ddc_transition_bw} HAMMING | csdr bandpass_fir_fft_cc --fifo {bpf_pipe} {bpf_transition_bw} HAMMING | csdr squelch_and_smeter_cc --fifo {squelch_pipe} --outfifo {smeter_pipe} 5 1 | "
        if self.secondary_demodulator:
            chain_begin+="csdr tee {iqtee_pipe} | "
            chain_begin+="csdr tee {iqtee2_pipe} | " 
        chain_end = ""
        if self.audio_compression=="adpcm":
            chain_end = " | csdr encode_ima_adpcm_i16_u8"
        if which == "nfm": return chain_begin + "csdr fmdemod_quadri_cf | csdr limit_ff | csdr old_fractional_decimator_ff {last_decimation} | csdr deemphasis_nfm_ff 11025 | csdr fastagc_ff 1024 | csdr convert_f_s16"+chain_end
        elif which == "am": return chain_begin + "csdr amdemod_cf | csdr fastdcblock_ff | csdr old_fractional_decimator_ff {last_decimation} | csdr agc_ff | csdr limit_ff | csdr convert_f_s16"+chain_end
        elif which == "ssb": return chain_begin + "csdr realpart_cf | csdr old_fractional_decimator_ff {last_decimation} | csdr agc_ff | csdr limit_ff | csdr convert_f_s16"+chain_end

    def secondary_chain(self, which):
        secondary_chain_base="cat {input_pipe} | "
        if which == "fft":
            return secondary_chain_base+"csdr realpart_cf | csdr fft_fc {secondary_fft_input_size} {secondary_fft_block_size} | csdr logpower_cf -70 " + (" | csdr compress_fft_adpcm_f_u8 {secondary_fft_size}" if self.fft_compression=="adpcm" else "")
        elif which == "bpsk31":
            return secondary_chain_base + "csdr shift_addition_cc --fifo {secondary_shift_pipe} | " + \
                    "csdr bandpass_fir_fft_cc -{secondary_bpf_cutoff} {secondary_bpf_cutoff} {secondary_bpf_cutoff} | " + \
                    "csdr simple_agc_cc 0.001 0.5 | " + \
                    "csdr timing_recovery_cc GARDNER {secondary_samples_per_bits} 0.5 2 --add_q | " + \
                    "CSDR_FIXED_BUFSIZE=1 csdr dbpsk_decoder_c_u8 | " + \
                    "CSDR_FIXED_BUFSIZE=1 csdr psk31_varicode_decoder_u8_u8"

    def set_secondary_demodulator(self, what):
        self.secondary_demodulator = what

    def secondary_fft_block_size(self):
        return (self.samp_rate/self.decimation)/(self.fft_fps*2) #*2 is there because we do FFT on real signal here

    def secondary_decimation(self):
        return 1 #currently unused

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
            return int(round(self.if_samp_rate()/31.25))&~3
        return 0

    def secondary_bw(self):
        if self.secondary_demodulator == "bpsk31":
            return 31.25

    def start_secondary_demodulator(self):
        if not self.secondary_demodulator: return
        logger.debug("[openwebrx] starting secondary demodulator from IF input sampled at %d"%self.if_samp_rate())
        secondary_command_fft=self.secondary_chain("fft")
        secondary_command_demod=self.secondary_chain(self.secondary_demodulator)
        self.try_create_pipes(self.secondary_pipe_names, secondary_command_demod + secondary_command_fft)

        secondary_command_fft=secondary_command_fft.format(
            input_pipe=self.iqtee_pipe,
            secondary_fft_input_size=self.secondary_fft_size,
            secondary_fft_size=self.secondary_fft_size,
            secondary_fft_block_size=self.secondary_fft_block_size(),
            )
        secondary_command_demod=secondary_command_demod.format(
            input_pipe=self.iqtee2_pipe,
            secondary_shift_pipe=self.secondary_shift_pipe,
            secondary_decimation=self.secondary_decimation(),
            secondary_samples_per_bits=self.secondary_samples_per_bits(),
            secondary_bpf_cutoff=self.secondary_bpf_cutoff(),
            secondary_bpf_transition_bw=self.secondary_bpf_transition_bw(),
            if_samp_rate=self.if_samp_rate()
            )

        logger.debug("[openwebrx-dsp-plugin:csdr] secondary command (fft) = %s", secondary_command_fft)
        logger.debug("[openwebrx-dsp-plugin:csdr] secondary command (demod) = %s", secondary_command_demod)
        my_env=os.environ.copy()
        #if self.csdr_dynamic_bufsize: my_env["CSDR_DYNAMIC_BUFSIZE_ON"]="1";
        if self.csdr_print_bufsizes: my_env["CSDR_PRINT_BUFSIZES"]="1";
        self.secondary_process_fft = subprocess.Popen(secondary_command_fft, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setpgrp, env=my_env)
        logger.debug("[openwebrx-dsp-plugin:csdr] Popen on secondary command (fft)")
        self.secondary_process_demod = subprocess.Popen(secondary_command_demod, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setpgrp, env=my_env) #TODO digimodes
        logger.debug("[openwebrx-dsp-plugin:csdr] Popen on secondary command (demod)") #TODO digimodes
        self.secondary_processes_running = True

        #open control pipes for csdr and send initialization data
        if self.secondary_shift_pipe != None: #TODO digimodes
            self.secondary_shift_pipe_file=open(self.secondary_shift_pipe,"w") #TODO digimodes
            self.set_secondary_offset_freq(self.secondary_offset_freq) #TODO digimodes

    def set_secondary_offset_freq(self, value):
        self.secondary_offset_freq=value
        if self.secondary_processes_running:
            self.secondary_shift_pipe_file.write("%g\n"%(-float(self.secondary_offset_freq)/self.if_samp_rate()))
            self.secondary_shift_pipe_file.flush()

    def stop_secondary_demodulator(self):
        if self.secondary_processes_running == False: return
        self.try_delete_pipes(self.secondary_pipe_names)
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

    def read_secondary_demod(self, size):
        return self.secondary_process_demod.stdout.read(size)

    def read_secondary_fft(self, size):
        return self.secondary_process_fft.stdout.read(size)

    def get_secondary_demodulator(self):
        return self.secondary_demodulator

    def set_secondary_fft_size(self,secondary_fft_size):
        #to change this, restart is required
        self.secondary_fft_size=secondary_fft_size

    def set_audio_compression(self,what):
        self.audio_compression = what

    def set_fft_compression(self,what):
        self.fft_compression = what

    def get_fft_bytes_to_read(self):
        if self.fft_compression=="none": return self.fft_size*4
        if self.fft_compression=="adpcm": return (self.fft_size/2)+(10/2)

    def get_secondary_fft_bytes_to_read(self):
        if self.fft_compression=="none": return self.secondary_fft_size*4
        if self.fft_compression=="adpcm": return (self.secondary_fft_size/2)+(10/2)

    def set_samp_rate(self,samp_rate):
        self.samp_rate=samp_rate
        self.calculate_decimation()
        if self.running: self.restart()

    def calculate_decimation(self):
        self.decimation=1
        while self.samp_rate/(self.decimation+1)>self.output_rate:
            self.decimation+=1
        self.last_decimation=float(self.if_samp_rate())/self.output_rate

    def if_samp_rate(self):
        return self.samp_rate/self.decimation

    def get_name(self):
        return self.name

    def get_output_rate(self):
        return self.output_rate

    def set_output_rate(self,output_rate):
        self.output_rate=output_rate
        self.calculate_decimation()

    def set_demodulator(self,demodulator):
        if (self.demodulator == demodulator): return
        self.demodulator=demodulator
        self.restart()

    def get_demodulator(self):
        return self.demodulator

    def set_fft_size(self,fft_size):
        self.fft_size=fft_size
        self.restart()

    def set_fft_fps(self,fft_fps):
        self.fft_fps=fft_fps
        self.restart()

    def set_fft_averages(self,fft_averages):
        self.fft_averages=fft_averages
        self.restart()

    def fft_block_size(self):
        if self.fft_averages == 0: return self.samp_rate/self.fft_fps
        else: return self.samp_rate/self.fft_fps/self.fft_averages

    def set_offset_freq(self,offset_freq):
        self.offset_freq=offset_freq
        if self.running:
            self.modification_lock.acquire()
            self.shift_pipe_file.write("%g\n"%(-float(self.offset_freq)/self.samp_rate))
            self.shift_pipe_file.flush()
            self.modification_lock.release()

    def set_bpf(self,low_cut,high_cut):
        self.low_cut=low_cut
        self.high_cut=high_cut
        if self.running:
            self.modification_lock.acquire()
            self.bpf_pipe_file.write( "%g %g\n"%(float(self.low_cut)/self.if_samp_rate(), float(self.high_cut)/self.if_samp_rate()) )
            self.bpf_pipe_file.flush()
            self.modification_lock.release()

    def get_bpf(self):
        return [self.low_cut, self.high_cut]

    def set_squelch_level(self, squelch_level):
        self.squelch_level=squelch_level
        if self.running:
            self.modification_lock.acquire()
            self.squelch_pipe_file.write( "%g\n"%(float(self.squelch_level)) )
            self.squelch_pipe_file.flush()
            self.modification_lock.release()

    def get_smeter_level(self):
        if self.running:
            line=self.smeter_pipe_file.readline()
            try:
                return float(line[:-1])
            except ValueError:
                return 0
        else:
            time.sleep(1)

    def mkfifo(self,path):
        try:
            os.unlink(path)
        except:
            pass
        os.mkfifo(path)

    def ddc_transition_bw(self):
        return self.ddc_transition_bw_rate*(self.if_samp_rate()/float(self.samp_rate))

    def try_create_pipes(self, pipe_names, command_base):
        for pipe_name in pipe_names:
            if "{"+pipe_name+"}" in command_base:
                setattr(self, pipe_name, self.pipe_base_path+pipe_name)
                self.mkfifo(getattr(self, pipe_name))
            else:
                setattr(self, pipe_name, None)

    def try_delete_pipes(self, pipe_names):
        for pipe_name in pipe_names:
            pipe_path = getattr(self,pipe_name,None)
            if pipe_path:
                try: os.unlink(pipe_path)
                except Exception:
                    logger.exception("try_delete_pipes()")

    def start(self):
        self.modification_lock.acquire()
        if (self.running):
            self.modification_lock.release()
            return
        self.running = True

        command_base=self.chain(self.demodulator)

        #create control pipes for csdr
        self.pipe_base_path="/tmp/openwebrx_pipe_{myid}_".format(myid=id(self))

        self.try_create_pipes(self.pipe_names, command_base)

        #run the command
        command=command_base.format( bpf_pipe=self.bpf_pipe, shift_pipe=self.shift_pipe, decimation=self.decimation,
            last_decimation=self.last_decimation, fft_size=self.fft_size, fft_block_size=self.fft_block_size(), fft_averages=self.fft_averages,
            bpf_transition_bw=float(self.bpf_transition_bw)/self.if_samp_rate(), ddc_transition_bw=self.ddc_transition_bw(),
            flowcontrol=int(self.samp_rate*2), start_bufsize=self.base_bufsize*self.decimation, nc_port=self.nc_port,
            squelch_pipe=self.squelch_pipe, smeter_pipe=self.smeter_pipe, iqtee_pipe=self.iqtee_pipe, iqtee2_pipe=self.iqtee2_pipe )

        logger.debug("[openwebrx-dsp-plugin:csdr] Command = %s", command)
        my_env=os.environ.copy()
        if self.csdr_dynamic_bufsize: my_env["CSDR_DYNAMIC_BUFSIZE_ON"]="1";
        if self.csdr_print_bufsizes: my_env["CSDR_PRINT_BUFSIZES"]="1";
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setpgrp, env=my_env)

        def watch_thread():
            rc = self.process.wait()
            logger.debug("dsp thread ended with rc=%d", rc)
            if (rc == 0 and self.running and not self.modification_lock.locked()):
                logger.debug("restarting since rc = 0, self.running = true, and no modification")
                self.restart()

        threading.Thread(target = watch_thread).start()

        # open control pipes for csdr
        if self.bpf_pipe != None:
            self.bpf_pipe_file=open(self.bpf_pipe,"w")
        if self.shift_pipe:
            self.shift_pipe_file=open(self.shift_pipe,"w")
        if self.squelch_pipe:
            self.squelch_pipe_file=open(self.squelch_pipe,"w")

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
            self.smeter_pipe_file=open(self.smeter_pipe,"r")

    def read(self,size):
        return self.process.stdout.read(size)

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
        if not self.running: return
        self.stop()
        self.start()

    def __del__(self):
        self.stop()
        del(self.process)
