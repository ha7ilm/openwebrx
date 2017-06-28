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
import code
import signal
import fcntl

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
        self.format_conversion = "csdr convert_u8_f"
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

    def chain(self,which):
        any_chain_base="nc -v 127.0.0.1 {nc_port} | "
        if self.csdr_dynamic_bufsize: any_chain_base+="csdr setbuf {start_bufsize} | "
        if self.csdr_through: any_chain_base+="csdr through | "
        any_chain_base+=self.format_conversion+(" | " if  self.format_conversion!="" else "") ##"csdr flowcontrol {flowcontrol} auto 1.5 10 | "
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
                    "csdr bandpass_fir_fft_cc $(csdr '=-(31.25)/{if_samp_rate}') $(csdr '=(31.25)/{if_samp_rate}') $(csdr '=31.25/{if_samp_rate}') | " + \
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
             return (31.25/2) / self.if_samp_rate()
        return 0

    def secondary_bpf_transition_bw(self):
        if self.secondary_demodulator == "bpsk31":
            return (31.25/2) / self.if_samp_rate()
        return 0

    def secondary_samples_per_bits(self):
        if self.secondary_demodulator == "bpsk31":
            return int(round(self.if_samp_rate()/31.25))&~3
        return 0

    def secondary_bw(self):
        if self.secondary_demodulator == "bpsk31":
            return 31.25

    def start_secondary_demodulator(self):
        if(not self.secondary_demodulator): return
        print "[openwebrx] starting secondary demodulator from IF input sampled at %d"%self.if_samp_rate()
        secondary_command_fft=self.secondary_chain("fft")
        secondary_command_demod=self.secondary_chain(self.secondary_demodulator)
        self.try_create_pipes(self.secondary_pipe_names, secondary_command_demod + secondary_command_fft)

        secondary_command_fft=secondary_command_fft.format( \
            input_pipe=self.iqtee_pipe, \
            secondary_fft_input_size=self.secondary_fft_size, \
            secondary_fft_size=self.secondary_fft_size, \
            secondary_fft_block_size=self.secondary_fft_block_size(), \
            )
        secondary_command_demod=secondary_command_demod.format( \
            input_pipe=self.iqtee2_pipe, \
            secondary_shift_pipe=self.secondary_shift_pipe, \
            secondary_decimation=self.secondary_decimation(), \
            secondary_samples_per_bits=self.secondary_samples_per_bits(), \
            secondary_bpf_cutoff=self.secondary_bpf_cutoff(), \
            secondary_bpf_transition_bw=self.secondary_bpf_transition_bw(), \
            if_samp_rate=self.if_samp_rate()
            )

        print "[openwebrx-dsp-plugin:csdr] secondary command (fft) =", secondary_command_fft
        print "[openwebrx-dsp-plugin:csdr] secondary command (demod) =", secondary_command_demod
        #code.interact(local=locals())
        my_env=os.environ.copy()
        #if self.csdr_dynamic_bufsize: my_env["CSDR_DYNAMIC_BUFSIZE_ON"]="1";
        if self.csdr_print_bufsizes: my_env["CSDR_PRINT_BUFSIZES"]="1";
        self.secondary_process_fft = subprocess.Popen(secondary_command_fft, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setpgrp, env=my_env)
        print "[openwebrx-dsp-plugin:csdr] Popen on secondary command (fft)"
        self.secondary_process_demod = subprocess.Popen(secondary_command_demod, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setpgrp, env=my_env) #TODO digimodes
        print "[openwebrx-dsp-plugin:csdr] Popen on secondary command (demod)" #TODO digimodes
        self.secondary_processes_running = True

        #open control pipes for csdr and send initialization data
        # print "==========> 1"
        if self.secondary_shift_pipe != None: #TODO digimodes
            # print "==========> 2", self.secondary_shift_pipe
            self.secondary_shift_pipe_file=open(self.secondary_shift_pipe,"w") #TODO digimodes
            # print "==========> 3"
            self.set_secondary_offset_freq(self.secondary_offset_freq) #TODO digimodes
            # print "==========> 4"

        self.set_pipe_nonblocking(self.secondary_process_demod.stdout)
        self.set_pipe_nonblocking(self.secondary_process_fft.stdout)

    def set_secondary_offset_freq(self, value):
        self.secondary_offset_freq=value
        if self.secondary_processes_running:
            self.secondary_shift_pipe_file.write("%g\n"%(-float(self.secondary_offset_freq)/self.if_samp_rate()))
            self.secondary_shift_pipe_file.flush()

    def stop_secondary_demodulator(self):
        if self.secondary_processes_running == False: return
        self.try_delete_pipes(self.secondary_pipe_names)
        if self.secondary_process_fft: os.killpg(os.getpgid(self.secondary_process_fft.pid), signal.SIGTERM)
        if self.secondary_process_demod: os.killpg(os.getpgid(self.secondary_process_demod.pid), signal.SIGTERM)
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
        #to change this, restart is required
        self.samp_rate=samp_rate
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
        self.set_samp_rate(self.samp_rate) #as it depends on output_rate

    def set_demodulator(self,demodulator):
        #to change this, restart is required
        self.demodulator=demodulator

    def get_demodulator(self):
        return self.demodulator

    def set_fft_size(self,fft_size):
        #to change this, restart is required
        self.fft_size=fft_size

    def set_fft_fps(self,fft_fps):
        #to change this, restart is required
        self.fft_fps=fft_fps

    def set_fft_averages(self,fft_averages):
        #to change this, restart is required
        self.fft_averages=fft_averages

    def fft_block_size(self):
        if self.fft_averages == 0: return self.samp_rate/self.fft_fps
        else: return self.samp_rate/self.fft_fps/self.fft_averages

    def set_format_conversion(self,format_conversion):
        self.format_conversion=format_conversion

    def set_offset_freq(self,offset_freq):
        self.offset_freq=offset_freq
        if self.running:
            self.shift_pipe_file.write("%g\n"%(-float(self.offset_freq)/self.samp_rate))
            self.shift_pipe_file.flush()

    def set_bpf(self,low_cut,high_cut):
        self.low_cut=low_cut
        self.high_cut=high_cut
        if self.running:
            self.bpf_pipe_file.write( "%g %g\n"%(float(self.low_cut)/self.if_samp_rate(), float(self.high_cut)/self.if_samp_rate()) )
            self.bpf_pipe_file.flush()

    def get_bpf(self):
        return [self.low_cut, self.high_cut]

    def set_squelch_level(self, squelch_level):
        self.squelch_level=squelch_level
        if self.running:
            self.squelch_pipe_file.write( "%g\n"%(float(self.squelch_level)) )
            self.squelch_pipe_file.flush()

    def get_smeter_level(self):
        if self.running:
            line=self.smeter_pipe_file.readline()
            return float(line[:-1])

    def mkfifo(self,path):
        try:
            os.unlink(path)
        except:
            pass
        os.mkfifo(path)

    def ddc_transition_bw(self):
        return self.ddc_transition_bw_rate*(self.if_samp_rate()/float(self.samp_rate))

    def try_create_pipes(self, pipe_names, command_base):
        # print "try_create_pipes"
        for pipe_name in pipe_names:
            # print "\t"+pipe_name
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
                except Exception as e: print "[openwebrx-dsp-plugin:csdr] try_delete_pipes() ::", e

    def set_pipe_nonblocking(self, pipe):
        flags = fcntl.fcntl(pipe, fcntl.F_GETFL)
        fcntl.fcntl(pipe, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def start(self):
        command_base=self.chain(self.demodulator)

        #create control pipes for csdr
        self.pipe_base_path="/tmp/openwebrx_pipe_{myid}_".format(myid=id(self))
        # self.bpf_pipe = self.shift_pipe = self.squelch_pipe = self.smeter_pipe = None

        self.try_create_pipes(self.pipe_names, command_base)

        # if "{bpf_pipe}" in command_base:
            # self.bpf_pipe=pipe_base_path+"bpf"
            # self.mkfifo(self.bpf_pipe)
        # if "{shift_pipe}" in command_base:
            # self.shift_pipe=pipe_base_path+"shift"
            # self.mkfifo(self.shift_pipe)
        # if "{squelch_pipe}" in command_base:
            # self.squelch_pipe=pipe_base_path+"squelch"
            # self.mkfifo(self.squelch_pipe)
        # if "{smeter_pipe}" in command_base:
            # self.smeter_pipe=pipe_base_path+"smeter"
            # self.mkfifo(self.smeter_pipe)
        # if "{iqtee_pipe}" in command_base:
            # self.iqtee_pipe=pipe_base_path+"iqtee"
            # self.mkfifo(self.iqtee_pipe)
        # if "{iqtee2_pipe}" in command_base:
            # self.iqtee2_pipe=pipe_base_path+"iqtee2"
            # self.mkfifo(self.iqtee2_pipe)

        #run the command
        command=command_base.format( bpf_pipe=self.bpf_pipe, shift_pipe=self.shift_pipe, decimation=self.decimation, \
            last_decimation=self.last_decimation, fft_size=self.fft_size, fft_block_size=self.fft_block_size(), fft_averages=self.fft_averages, \
            bpf_transition_bw=float(self.bpf_transition_bw)/self.if_samp_rate(), ddc_transition_bw=self.ddc_transition_bw(), \
            flowcontrol=int(self.samp_rate*2), start_bufsize=self.base_bufsize*self.decimation, nc_port=self.nc_port, \
            squelch_pipe=self.squelch_pipe, smeter_pipe=self.smeter_pipe, iqtee_pipe=self.iqtee_pipe, iqtee2_pipe=self.iqtee2_pipe )

        print "[openwebrx-dsp-plugin:csdr] Command =",command
        #code.interact(local=locals())
        my_env=os.environ.copy()
        if self.csdr_dynamic_bufsize: my_env["CSDR_DYNAMIC_BUFSIZE_ON"]="1";
        if self.csdr_print_bufsizes: my_env["CSDR_PRINT_BUFSIZES"]="1";
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setpgrp, env=my_env)
        self.running = True

        #open control pipes for csdr and send initialization data
        if self.bpf_pipe != None:
            self.bpf_pipe_file=open(self.bpf_pipe,"w")
            self.set_bpf(self.low_cut,self.high_cut)
        if self.shift_pipe != None:
            self.shift_pipe_file=open(self.shift_pipe,"w")
            self.set_offset_freq(self.offset_freq)
        if self.squelch_pipe != None:
            self.squelch_pipe_file=open(self.squelch_pipe,"w")
            self.set_squelch_level(self.squelch_level)
        if self.smeter_pipe != None:
            self.smeter_pipe_file=open(self.smeter_pipe,"r")
            self.set_pipe_nonblocking(self.smeter_pipe_file)

        self.start_secondary_demodulator()

    def read(self,size):
        return self.process.stdout.read(size)

    def stop(self):
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        self.stop_secondary_demodulator()
        #if(self.process.poll()!=None):return # returns None while subprocess is running
        #while(self.process.poll()==None):
        #   #self.process.kill()
        #   print "killproc",os.getpgid(self.process.pid),self.process.pid
        #   os.killpg(self.process.pid, signal.SIGTERM)
        #
        #   time.sleep(0.1)

        self.try_delete_pipes(self.pipe_names)

        # if self.bpf_pipe:
            # try: os.unlink(self.bpf_pipe)
            # except: print "[openwebrx-dsp-plugin:csdr] stop() :: unlink failed: " + self.bpf_pipe
        # if self.shift_pipe:
            # try: os.unlink(self.shift_pipe)
            # except: print "[openwebrx-dsp-plugin:csdr] stop() :: unlink failed: " + self.shift_pipe
        # if self.squelch_pipe:
            # try: os.unlink(self.squelch_pipe)
            # except: print "[openwebrx-dsp-plugin:csdr] stop() :: unlink failed: " + self.squelch_pipe
        # if self.smeter_pipe:
            # try: os.unlink(self.smeter_pipe)
            # except: print "[openwebrx-dsp-plugin:csdr] stop() :: unlink failed: " + self.smeter_pipe
        # if self.iqtee_pipe:
            # try: os.unlink(self.iqtee_pipe)
            # except: print "[openwebrx-dsp-plugin:csdr] stop() :: unlink failed: " + self.iqtee_pipe
        # if self.iqtee2_pipe:
            # try: os.unlink(self.iqtee2_pipe)
            # except: print "[openwebrx-dsp-plugin:csdr] stop() :: unlink failed: " + self.iqtee2_pipe

        self.running = False

    def restart(self):
        self.stop()
        self.start()

    def __del__(self):
        self.stop()
        del(self.process)
