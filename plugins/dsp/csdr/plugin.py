import subprocess
import time
import os
import code

class dsp_plugin:

	def __init__(self):
		self.samp_rate = 250000
		self.output_rate = 44100 #this is default, and cannot be set at the moment
		self.fft_size = 1024
		self.fft_fps = 5
		self.offset_freq = 0
		self.low_cut = -4000
		self.high_cut = 4000
		self.bpf_transition_bw = 300 #Hz, and this is a constant
		self.running = False
		chain_begin="nc localhost 4951 | csdr convert_u8_f | csdr shift_addition_cc --fifo {shift_pipe} | csdr fir_decimate_cc {decimation} 0.005 HAMMING | csdr bandpass_fir_fft_cc --fifo {bpf_pipe} {bpf_transition_bw} HAMMING | "
		self.chains = {
			"nfm" :  chain_begin + "csdr fmdemod_quadri_cf | csdr limit_ff | csdr fractional_decimator_ff {last_decimation} | csdr deemphasis_nfm_ff 48000 | csdr fastagc_ff | csdr convert_f_i16",
			"am" :  chain_begin + "csdr amdemod_cf | csdr fastdcblock_ff | csdr fractional_decimator_ff {last_decimation} | csdr agc_ff | csdr limit_ff | csdr convert_f_i16",
			"ssb" :  chain_begin + "csdr realpart_cf | csdr fractional_decimator_ff {last_decimation} | csdr agc_ff | csdr limit_ff | csdr convert_f_i16",
			"fft" : "nc -vv localhost 4951 | csdr convert_u8_f | csdr fft_cc {fft_size} {fft_block_size} | csdr logpower_cf -70"
			}
		self.demodulator = "nfm"
		self.name = "csdr"
		try:	
			subprocess.Popen("nc",stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		except:
			print "[openwebrx-plugin:csdr] error: netcat not found, please install netcat!"

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


	def set_demodulator(self,demodulator):
		#to change this, restart is required
		self.demodulator=demodulator

	def set_fft_size(self,fft_size):
		#to change this, restart is required
		self.fft_size=fft_size

	def set_fft_fps(self,fft_fps):
		#to change this, restart is required
		self.fft_fps=fft_fps
	
	def fft_block_size(self):
		return self.samp_rate/self.fft_fps

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

	def mkfifo(self,path):
		try:
			os.unlink(path)
		except:
			pass
		os.mkfifo(path)	

	def start(self):
		command_base=self.chains[self.demodulator]
		
		#create control pipes for csdr
		pipe_base_path="/tmp/openwebrx_pipe_{myid}_".format(myid=id(self))
		self.bpf_pipe = self.shift_pipe = None
		if "{bpf_pipe}" in command_base:
			self.bpf_pipe=pipe_base_path+"bpf"
			self.mkfifo(self.bpf_pipe)
		if "{shift_pipe}" in command_base:
			self.shift_pipe=pipe_base_path+"shift"
			self.mkfifo(self.shift_pipe)

		#run the command
		command=command_base.format(bpf_pipe=self.bpf_pipe,shift_pipe=self.shift_pipe,decimation=self.decimation,last_decimation=self.last_decimation,fft_size=self.fft_size,fft_block_size=self.fft_block_size(),bpf_transition_bw=float(self.bpf_transition_bw)/self.if_samp_rate())
		print "[openwebrx-dsp-plugin:csdr] Command =",command
		#code.interact(local=locals())
		self.process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
		self.running = True

		#open control pipes for csdr and send initialization data
		if self.bpf_pipe != None: 
			self.bpf_pipe_file=open(self.bpf_pipe,"w")
			self.set_bpf(self.low_cut,self.high_cut)
		if self.shift_pipe != None: 
			self.shift_pipe_file=open(self.shift_pipe,"w")
			self.set_offset_freq(self.offset_freq)

	def read(self,size):
		return self.process.stdout.read(size)
		
	def stop(self):
		if(self.process!=None):return # returns None while subprocess is running
		while(self.process.poll()==None):
			self.process.kill()
			time.sleep(0.1)
		os.unlink(self.bpf_pipe)
		os.unlink(self.shift_pipe)
		self.running = False

	def restart(self):
		self.stop()
		self.start()

	def __del__(self):
		self.stop()
		del(self.process)
	
