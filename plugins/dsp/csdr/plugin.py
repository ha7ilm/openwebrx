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

class dsp_plugin:

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
		self.real_input = False

	def chain(self,which):
		any_chain_base="ncat -v 127.0.0.1 {nc_port} | "
		if self.csdr_dynamic_bufsize: any_chain_base+="csdr setbuf {start_bufsize} | "
		if self.csdr_through: any_chain_base+="csdr through | "
		any_chain_base+=self.format_conversion+(" | " if  self.format_conversion!="" else "") ##"csdr flowcontrol {flowcontrol} auto 1.5 10 | "
		if which == "fft":
			fft_chain_base = any_chain_base + "csdr " + \
			("fft_fc" if self.real_input else "fft_cc") + \
			" {fft_size} {fft_block_size} | " + \
			("csdr logpower_cf -70" if self.fft_averages == 0 else "csdr logaveragepower_cf -70 {fft_size} {fft_averages}")

			if not self.real_input:
				fft_chain_base += " | csdr fft_exchange_sides_ff {fft_size}"

			if self.fft_compression=="adpcm":
				return fft_chain_base+" | csdr compress_fft_adpcm_f_u8 {fft_size}"
			else:
				return fft_chain_base

		if self.real_input:
			chain_begin=any_chain_base+"csdr shift_addition_fc --fifo {shift_pipe}"
		else:
			chain_begin=any_chain_base+"csdr shift_addition_cc --fifo {shift_pipe}"
		chain_begin += "| csdr fir_decimate_cc {decimation} {ddc_transition_bw} HAMMING | csdr bandpass_fir_fft_cc --fifo {bpf_pipe} {bpf_transition_bw} HAMMING | csdr squelch_and_smeter_cc --fifo {squelch_pipe} --outfifo {smeter_pipe} 5 1 | "
		chain_end = ""
		if self.audio_compression=="adpcm":
			chain_end = " | csdr encode_ima_adpcm_i16_u8"
		if which == "nfm": return chain_begin + "csdr fmdemod_quadri_cf | csdr limit_ff | csdr fractional_decimator_ff {last_decimation} | csdr deemphasis_nfm_ff 11025 | csdr fastagc_ff 1024 | csdr convert_f_s16"+chain_end
		elif which == "am":	return chain_begin + "csdr amdemod_cf | csdr fastdcblock_ff | csdr fractional_decimator_ff {last_decimation} | csdr agc_ff | csdr limit_ff | csdr convert_f_s16"+chain_end
		elif which == "ssb": return chain_begin + "csdr realpart_cf | csdr fractional_decimator_ff {last_decimation} | csdr agc_ff | csdr limit_ff | csdr convert_f_s16"+chain_end

	def set_audio_compression(self,what):
		self.audio_compression = what

	def set_fft_compression(self,what):
		self.fft_compression = what

	def get_fft_bytes_to_read(self):
		if self.fft_compression=="none": return self.fft_size*4
		if self.fft_compression=="adpcm": return (self.fft_size/2)+(10/2)

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

	def set_real_input(self,real_input):
		self.real_input=real_input

	def set_offset_freq(self,offset_freq):
		self.offset_freq=offset_freq
		if self.running:
			if self.real_input:
				# for real signal, the "center frequency" is actually offset by samp_rate/4
				self.shift_pipe_file.write("%g\n"%(-float(self.offset_freq)/self.samp_rate - 0.25))
			else:
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

	def start(self):
		command_base=self.chain(self.demodulator)

		#create control pipes for csdr
		pipe_base_path="/tmp/openwebrx_pipe_{myid}_".format(myid=id(self))
		self.bpf_pipe = self.shift_pipe = self.squelch_pipe = self.smeter_pipe = None
		if "{bpf_pipe}" in command_base:
			self.bpf_pipe=pipe_base_path+"bpf"
			self.mkfifo(self.bpf_pipe)
		if "{shift_pipe}" in command_base:
			self.shift_pipe=pipe_base_path+"shift"
			self.mkfifo(self.shift_pipe)
		if "{squelch_pipe}" in command_base:
			self.squelch_pipe=pipe_base_path+"squelch"
			self.mkfifo(self.squelch_pipe)
		if "{smeter_pipe}" in command_base:
			self.smeter_pipe=pipe_base_path+"smeter"
			self.mkfifo(self.smeter_pipe)

		#run the command
		command=command_base.format( bpf_pipe=self.bpf_pipe, shift_pipe=self.shift_pipe, decimation=self.decimation, \
			last_decimation=self.last_decimation, fft_size=self.fft_size, fft_block_size=self.fft_block_size(), fft_averages=self.fft_averages, \
			bpf_transition_bw=float(self.bpf_transition_bw)/self.if_samp_rate(), ddc_transition_bw=self.ddc_transition_bw(), \
			flowcontrol=int(self.samp_rate*2), start_bufsize=self.base_bufsize*self.decimation, nc_port=self.nc_port, \
			squelch_pipe=self.squelch_pipe, smeter_pipe=self.smeter_pipe )

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
			fcntl.fcntl(self.smeter_pipe_file, fcntl.F_SETFL, os.O_NONBLOCK)

	def read(self,size):
		return self.process.stdout.read(size)

	def stop(self):
		os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
		#if(self.process.poll()!=None):return # returns None while subprocess is running
		#while(self.process.poll()==None):
		#	#self.process.kill()
		#	print "killproc",os.getpgid(self.process.pid),self.process.pid
		#	os.killpg(self.process.pid, signal.SIGTERM)
		#
		#	time.sleep(0.1)
		if self.bpf_pipe:
			try: os.unlink(self.bpf_pipe)
			except: print "[openwebrx-dsp-plugin:csdr] stop() :: unlink failed: " + self.bpf_pipe
		if self.shift_pipe:
			try: os.unlink(self.shift_pipe)
			except: print "[openwebrx-dsp-plugin:csdr] stop() :: unlink failed: " + self.shift_pipe
		if self.squelch_pipe:
			try: os.unlink(self.squelch_pipe)
			except: print "[openwebrx-dsp-plugin:csdr] stop() :: unlink failed: " + self.squelch_pipe
		if self.smeter_pipe:
			try: os.unlink(self.smeter_pipe)
			except: print "[openwebrx-dsp-plugin:csdr] stop() :: unlink failed: " + self.smeter_pipe
		self.running = False

	def restart(self):
		self.stop()
		self.start()

	def __del__(self):
		self.stop()
		del(self.process)
