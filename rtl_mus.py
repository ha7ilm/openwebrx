'''
This file is part of RTL Multi-User Server, 
	that makes multi-user access to your DVB-T dongle used as an SDR.
Copyright (c) 2013-2014 by Andras Retzler, HA7ILM <randras@sdr.hu>

RTL Multi-User Server is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

RTL Multi-User Server is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with RTL Multi-User Server.  If not, see <http://www.gnu.org/licenses/>.

-----

2013-11?  Asyncore version
2014-03   Fill with null on no data

'''

import socket 
import sys
import array
import time
import logging
import os
import time
import subprocess
import fcntl
import thread
import pdb
import asyncore
import multiprocessing
import signal
#pypy compatiblity
try: import dl
except: pass

import code
import traceback

def handle_signal(signal, frame):
	log.info("Ctrl+C: aborting.")
	os._exit(1) #not too graceful exit

def ip_match(this,ip_ranges,for_allow):
	if not len(ip_ranges):
		return 1 #empty list matches all ip addresses
	for ip_range in ip_ranges:
		#print this[0:len(ip_range)], ip_range
		if this[0:len(ip_range)]==ip_range:
			return 1
	return 0

def ip_access_control(ip):
	if(not cfg.use_ip_access_control): return 1
	allowed=0
	if(cfg.order_allow_deny):
		if ip_match(ip,cfg.allowed_ip_ranges,1): allowed=1
		if ip_match(ip,cfg.denied_ip_ranges,0): allowed=0
	else:
		if ip_match(ip,cfg.denied_ip_ranges,0): 
			allowed=0
		if ip_match(ip,cfg.allowed_ip_ranges,1): 
			allowed=1
	return allowed

def add_data_to_clients(new_data):
	# might be called from:
	# -> dsp_read
	# -> rtl_tcp_asyncore.handle_read
	global clients
	global clients_mutex
	clients_mutex.acquire()
	for client in clients:
		#print "client %d size: %d"%(client[0].ident,client[0].waiting_data.qsize())
		if(client[0].waiting_data.full()):
			if cfg.cache_full_behaviour == 0:
				log.error("client cache full, dropping samples: "+str(client[0].ident)+"@"+client[0].socket[1][0])
				while not client[0].waiting_data.empty(): # clear queue
					client[0].waiting_data.get(False, None)
			elif cfg.cache_full_behaviour == 1:
				#rather closing client:
				log.error("client cache full, dropping client: "+str(client[0].ident)+"@"+client[0].socket[1][0])
				client[0].close(False)
			elif cfg.cache_full_behaviour == 2:
				pass #client cache full, just not taking care
			else: log.error("invalid value for cfg.cache_full_behaviour")
		else:
			client[0].waiting_data.put(new_data)
	clients_mutex.release()

def dsp_read_thread():
	global proc
	global dsp_data_count
	while True:
		try:
			my_buffer=proc.stdout.read(1024)
		except IOError:
			log.error("DSP subprocess is not ready for reading.")
			time.sleep(1)
			continue
		add_data_to_clients(my_buffer)
		if cfg.debug_dsp_command:
			dsp_data_count+=len(my_buffer)	

def dsp_write_thread():
	global proc
	global dsp_input_queue
	global original_data_count
	while True:
		try:
			my_buffer=dsp_input_queue.get(timeout=0.3)
		except:
			continue
		proc.stdin.write(my_buffer)
		proc.stdin.flush()
		if cfg.debug_dsp_command:
			original_data_count+=len(my_buffer)

class client_handler(asyncore.dispatcher):

	def __init__(self,client_param):
		self.client=client_param
		self.client[0].asyncore=self
		self.sent_dongle_id=False
		self.last_waiting_buffer=""
		asyncore.dispatcher.__init__(self, self.client[0].socket[0])
		self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

	def handle_read(self):
		global commands
		new_command = self.recv(5)
		if len(new_command)>=5:
			if handle_command(new_command, self.client):
				commands.put(new_command)

	def handle_error(self):
		exc_type, exc_value, exc_traceback = sys.exc_info()
		log.info("client error: "+str(self.client[0].ident)+"@"+self.client[0].socket[1][0])
		traceback.print_tb(exc_traceback)
		self.close()

	def handle_close(self):
		self.client[0].close()
		log.info("client disconnected: "+str(self.client[0].ident)+"@"+self.client[0].socket[1][0])

	def writable(self):
		#print "queryWritable",not self.client[0].waiting_data.empty()
		return not self.client[0].waiting_data.empty()

	def handle_write(self):
		global last_waiting
		global rtl_dongle_identifier
		global sample_rate
		if not self.sent_dongle_id:
			self.send(rtl_dongle_identifier)
			self.sent_dongle_id=True
			return
		#print "write2client",self.client[0].waiting_data.qsize()
		next=self.last_waiting_buffer+self.client[0].waiting_data.get()
		sent=asyncore.dispatcher.send(self, next)
		self.last_waiting_buffer=next[sent:]

class server_asyncore(asyncore.dispatcher):

	def __init__(self):
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind((cfg.my_ip, cfg.my_listening_port))
		self.listen(5)
		self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		log.info("Server listening on port: "+str(cfg.my_listening_port))

	def handle_accept(self):
		global max_client_id
		global clients_mutex
		global clients
		my_client=[client()]
		my_client[0].socket=self.accept()
		if (my_client[0].socket is None): # not sure if required
			return 
		if (ip_access_control(my_client[0].socket[1][0])):
			my_client[0].ident=max_client_id
			max_client_id+=1
			my_client[0].start_time=time.time()
			my_client[0].waiting_data=multiprocessing.Queue(500)
			clients_mutex.acquire()
			clients.append(my_client)
			clients_mutex.release()
			handler = client_handler(my_client)
			log.info("client accepted: "+str(len(clients)-1)+"@"+my_client[0].socket[1][0]+":"+str(my_client[0].socket[1][1])+"  users now: "+str(len(clients)))
		else:
			log.info("client denied: "+str(len(clients)-1)+"@"+my_client[0].socket[1][0]+":"+str(my_client[0].socket[1][1])+" blocked by ip")
			my_client.socket.close()

rtl_tcp_resetting=False #put me away

def rtl_tcp_asyncore_reset(timeout):
	global rtl_tcp_core
	global rtl_tcp_resetting
	if rtl_tcp_resetting: return
	#print "rtl_tcp_asyncore_reset"
	rtl_tcp_resetting=True
	time.sleep(timeout)
	try:
		rtl_tcp_core.close()
	except:
		pass
	try:
		del rtl_tcp_core
	except:
		pass
	rtl_tcp_core=rtl_tcp_asyncore()
	#print asyncore.socket_map
	rtl_tcp_resetting=False

class rtl_tcp_asyncore(asyncore.dispatcher):
	def __init__(self):
		global server_missing_logged
		asyncore.dispatcher.__init__(self)
		self.ok=True
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		try:		
			self.connect((cfg.rtl_tcp_host, cfg.rtl_tcp_port))
			self.socket.settimeout(0.1)
		except:
			log.error("rtl_tcp connection refused. Retrying.")
			thread.start_new_thread(rtl_tcp_asyncore_reset, (1,))
			self.close()
			return

	def handle_error(self):
		global server_missing_logged
		global rtl_tcp_connected
		rtl_tcp_connected=False
		exc_type, exc_value, exc_traceback = sys.exc_info()
		self.ok=False
		server_is_missing=hasattr(exc_value,"errno") and exc_value.errno==111
		if (not server_is_missing) or (not server_missing_logged):
			log.error("with rtl_tcp host connection: "+str(exc_value))
			#traceback.print_tb(exc_traceback)
			server_missing_logged|=server_is_missing
		try:
			self.close()
		except:
			pass
		thread.start_new_thread(rtl_tcp_asyncore_reset, (2,))

	def handle_connect(self):
		global server_missing_logged
		global rtl_tcp_connected
		self.socket.settimeout(0.1)
		rtl_tcp_connected=True
		if self.ok:
			log.info("rtl_tcp host connection estabilished")
			server_missing_logged=False

	def handle_close(self):
		global rtl_tcp_connected
		global rtl_tcp_core
		rtl_tcp_connected=False
		log.error("rtl_tcp host connection has closed, now trying to reopen")
		try:
			self.close()
		except:
			pass
		thread.start_new_thread(rtl_tcp_asyncore_reset, (2,))

	def handle_read(self):
		global rtl_dongle_identifier
		global dsp_input_queue
		global watchdog_data_count
		if(len(rtl_dongle_identifier)==0):
			rtl_dongle_identifier=self.recv(12)
			return
		new_data_buffer=self.recv(1024*16)
		if cfg.watchdog_interval:
			watchdog_data_count+=1024*16
		if cfg.use_dsp_command:
			dsp_input_queue.put(new_data_buffer)
			#print "did put anyway"
		else:
			add_data_to_clients(new_data_buffer)

	def writable(self):
		#check if any new commands to write
		global commands
		return not commands.empty()

	def handle_write(self):
		global commands
		while not commands.empty():
			mcmd=commands.get()
			self.send(mcmd)

def xxd(data):
	#diagnostic purposes only
	output=""
	for d in data:
		output+=hex(ord(d))[2:].zfill(2)+" " 
	return output

def handle_command(command, client_param):
	global sample_rate
	client=client_param[0]
	param=array.array("I", command[1:5])[0]
	param=socket.ntohl(param)
	command_id=ord(command[0])
	client_info=str(client.ident)+"@"+client.socket[1][0]+":"+str(client.socket[1][1])
	if(time.time()-client.start_time<cfg.client_cant_set_until and not (cfg.first_client_can_set and client.ident==0) ):
		log.info("deny: "+client_info+" -> client can't set anything until "+str(cfg.client_cant_set_until)+" seconds")
		return 0
	if command_id == 1:
		if max(map((lambda r: param>=r[0] and param<=r[1]),cfg.freq_allowed_ranges)):
			log.debug("allow: "+client_info+" -> set freq "+str(param))
			return 1
		else:
			log.debug("deny: "+client_info+" -> set freq - out of range: "+str(param))
	elif command_id == 2:
		log.debug("deny: "+client_info+" -> set sample rate: "+str(param))
		sample_rate=param
		return 0 # ordinary clients are not allowed to do this
	elif command_id == 3:
		log.debug("deny/allow: "+client_info+" -> set gain mode: "+str(param))
		return cfg.allow_gain_set
	elif command_id == 4:
		log.debug("deny/allow: "+client_info+" -> set gain: "+str(param))
		return cfg.allow_gain_set 
	elif command_id == 5:
		log.debug("deny: "+client_info+" -> set freq correction: "+str(param))
		return 0 
	elif command_id == 6:
		log.debug("deny/allow: set if stage gain")
		return cfg.allow_gain_set
	elif command_id == 7:
		log.debug("deny: set test mode")
		return 0
	elif command_id == 8:
		log.debug("deny/allow: set agc mode")
		return cfg.allow_gain_set
	elif command_id == 9:
		log.debug("deny: set direct sampling")
		return 0
	elif command_id == 10:
		log.debug("deny: set offset tuning")
		return 0
	elif command_id == 11:
		log.debug("deny: set rtl xtal")
		return 0
	elif command_id == 12:
		log.debug("deny: set tuner xtal")
		return 0
	elif command_id == 13:
		log.debug("deny/allow: set tuner gain by index")
		return cfg.allow_gain_set
	else:
		log.debug("deny: "+client_info+" sent an ivalid command: "+str(param))
	return 0

def watchdog_thread():
	global rtl_tcp_connected
	global rtl_tcp_core	
	global watchdog_data_count
	global sample_rate
	zero_buffer_size=16348
	second_frac=10
	zero_buffer='\x7f'*zero_buffer_size
	watchdog_data_count=0
	rtl_tcp_connected=False
	null_fill=False
	time.sleep(4) # wait before activating this thread
	log.info("watchdog started")
	first_start=True
	n=0
	while True:
		wait_altogether=cfg.watchdog_interval if rtl_tcp_connected or first_start else cfg.reconnect_interval	
		first_start=False
		if null_fill:
			log.error("watchdog: filling buffer with zeros.")	
			while wait_altogether>0:
				wait_altogether-=1.0/second_frac
				for i in range(0,((2*sample_rate)/second_frac)/zero_buffer_size):	
					add_data_to_clients(zero_buffer)
					n+=len(zero_buffer)
					time.sleep(0) #yield
					if watchdog_data_count: break
				if watchdog_data_count: break
				time.sleep(1.0/second_frac)
				#print "sent altogether",n
		else:
			time.sleep(wait_altogether)
		null_fill=not watchdog_data_count
		if not watchdog_data_count:
			log.error("watchdog: restarting rtl_tcp_asyncore() now.")
			rtl_tcp_asyncore_reset(0)
		watchdog_data_count=0
			
		

def dsp_debug_thread():
	global dsp_data_count
	global original_data_count
	while 1:	
		time.sleep(1)
		print "[rtl-mus] DSP | Original data: "+str(int(original_data_count/1000))+"kB/sec | Processed data: "+str(int(dsp_data_count/1000))+"kB/sec"
		dsp_data_count = original_data_count=0
		
class client:
	ident=None #id
	to_close=False
	waiting_data=None
	start_time=None	
	socket=None
	asyncore=None

	def close(self, use_mutex=True):
		global clients_mutex
		global clients
		if use_mutex: clients_mutex.acquire()
		correction=0
		for i in range(0,len(clients)):
			i-=correction
			if clients[i][0].ident==self.ident:
				try:
					self.socket.close()
				except:
					pass
				try:
					self.asyncore.close()
					del self.asyncore
				except:
					pass
				del clients[i]
				correction+=1
		if use_mutex: clients_mutex.release()


def main():
	global server_missing_logged
	global rtl_dongle_identifier
	global log
	global clients
	global clients_mutex
	global original_data_count
	global dsp_input_queue
	global dsp_data_count
	global proc
	global commands
	global max_client_id
	global rtl_tcp_core
	global sample_rate

	#Set signal handler
	signal.signal(signal.SIGINT, handle_signal) #http://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python

	# set up logging
	log = logging.getLogger("rtl_mus")
	log.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	stream_handler = logging.StreamHandler()
	stream_handler.setLevel(logging.DEBUG)
	stream_handler.setFormatter(formatter)
	log.addHandler(stream_handler)
	file_handler = logging.FileHandler(cfg.log_file_path)
	file_handler.setLevel(logging.INFO)
	file_handler.setFormatter(formatter)
	log.addHandler(file_handler)
	log.info("Server is UP")
	
	server_missing_logged=0	# Not to flood the screen with messages related to rtl_tcp disconnect
	rtl_dongle_identifier='' # rtl_tcp sends some identifier on dongle type and gain values in the first few bytes right after connection
	clients=[]
	dsp_data_count=original_data_count=0
	commands=multiprocessing.Queue()
	dsp_input_queue=multiprocessing.Queue()
	clients_mutex=multiprocessing.Lock()
	max_client_id=0
	sample_rate=250000 # so far only watchdog thread uses it to fill buffer up with zeros on missing input

	# start dsp threads
	if cfg.use_dsp_command:
		print "[rtl_mus] Opening DSP process..."
		proc = subprocess.Popen (cfg.dsp_command.split(" "), stdin = subprocess.PIPE, stdout = subprocess.PIPE) #!! should fix the split :-S
		dsp_read_thread_v=thread.start_new_thread(dsp_read_thread, ())
		dsp_write_thread_v=thread.start_new_thread(dsp_write_thread, ())
		if cfg.debug_dsp_command:
			dsp_debug_thread_v=thread.start_new_thread(dsp_debug_thread,())

	# start watchdog thread
	if cfg.watchdog_interval != 0:
		watchdog_thread_v=thread.start_new_thread(watchdog_thread,())

	# start asyncores
	rtl_tcp_core = rtl_tcp_asyncore()
	server_core = server_asyncore()

	asyncore.loop(0.1)


if __name__=="__main__":
	print
	print "rtl_mus: Multi-User I/Q Data Server for RTL-SDR v0.22, made at HA5KFU Amateur Radio Club (http://ha5kfu.hu)"
	print "    code by Andras Retzler, HA7ILM <randras@sdr.hu>"
	print "    distributed under GNU GPL v3"
	print 

	try:
		for libcpath in ["/lib/i386-linux-gnu/libc.so.6","/lib/libc.so.6"]:
			if os.path.exists(libcpath):
				libc = dl.open(libcpath)
				libc.call("prctl", 15, "rtl_mus", 0, 0, 0)
				break
	except:
		pass

	# === Load configuration script ===
	if len(sys.argv)==1:
		print "[rtl_mus] Warning! Configuration script not specified. I will use: \"config_rtl.py\""
		config_script="config_rtl"
	else:
		config_script=sys.argv[1]
	cfg=__import__(config_script)
	if cfg.setuid_on_start:
		os.setuid(cfg.uid)
	main()
