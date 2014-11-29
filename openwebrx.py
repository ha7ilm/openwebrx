#!/usr/bin/python
print "" # python2.7 is required to run OpenWebRX instead of python3. Please run me by: python2 openwebrx.py
"""
OpenWebRX: open-source web based SDR for everyone!

This file is part of OpenWebRX.

    OpenWebRX is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenWebRX is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OpenWebRX.  If not, see <http://www.gnu.org/licenses/>.

Authors:
    Andras Retzler, HA7ILM <randras@sdr.hu>

"""

# http://www.codeproject.com/Articles/462525/Simple-HTTP-Server-and-Client-in-Python
# some ideas are used from the artice above


import os
import code
import importlib
import plugins
import plugins.dsp
import thread
import time
import subprocess
import os 
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import fcntl
import time
import md5
import random
import threading
import dl
import sys
import traceback
from collections import namedtuple
import Queue
import ctypes

#import rtl_mus
import rxws
import uuid
import config_webrx as cfg

def import_all_plugins(directory):
	for subdir in os.listdir(directory):
		if os.path.isdir(directory+subdir) and not subdir[0]=="_":
			exact_path=directory+subdir+"/plugin.py"
			if os.path.isfile(exact_path):
				importname=(directory+subdir+"/plugin").replace("/",".")
				print "[openwebrx-import] Found plugin:",importname
				importlib.import_module(importname)

class MultiThreadHTTPServer(ThreadingMixIn, HTTPServer):
    pass 

def main():
	global clients
	global clients_mutex

	print
	print "OpenWebRX - Open Source Web Based SDR for Everyone  | for license see LICENSE file in the package"
	print "_________________________________________________________________________________________________"
	print 
	print "Author contact info:    Andras Retzler, HA7ILM <randras@sdr.hu>"
	print 

	#Load plugins
	import_all_plugins("plugins/dsp/")

	#Change process name to "openwebrx" (to be seen in ps)
	try:
		for libcpath in ["/lib/i386-linux-gnu/libc.so.6","/lib/libc.so.6"]:
			if os.path.exists(libcpath):
				libc = dl.open(libcpath)
				libc.call("prctl", 15, "openwebrx", 0, 0, 0)
				break
	except:
		pass

	#Start rtl thread
	if cfg.start_rtl_thread:
		rtl_thread=threading.Thread(target = lambda:subprocess.Popen(cfg.start_rtl_command, shell=True), args=())
		rtl_thread.start()
		print "[openwebrx-main] Started rtl thread: "+cfg.start_rtl_command

	#Run rtl_mus.py in a different OS thread
	rtl_mus_thread=threading.Thread(target = lambda:subprocess.Popen("python rtl_mus.py config_rtl", shell=True), args=())
	rtl_mus_thread.start() # The new feature in GNU Radio 3.7: top_block() locks up ALL python threads until it gets the TCP connection.
	print "[openwebrx-main] Started rtl_mus"
	time.sleep(1) #wait until it really starts	

	#Initialize clients
	clients=[]
	clients_mutex=threading.Lock()

	#Start spectrum thread
	print "[openwebrx-main] Starting spectrum thread."
	spectrum_thread=threading.Thread(target = spectrum_thread_function, args = ())
	spectrum_thread.start()
	
	#threading.Thread(target = measure_thread_function, args = ()).start()
	
	#Start HTTP thread
	httpd = MultiThreadHTTPServer(('', cfg.web_port), WebRXHandler)
	print('[openwebrx-main] Starting HTTP server.')
	httpd.serve_forever()


# This is a debug function below:
measure_value=0
def measure_thread_function():
	global measure_value
	while True:	
		print "[openwebrx-measure] value is",measure_value
		measure_value=0
		time.sleep(1)


def spectrum_thread_function():
	global clients_mutex
	global clients
	dsp=getattr(plugins.dsp,cfg.dsp_plugin).plugin.dsp_plugin()
	dsp.set_demodulator("fft")
	dsp.set_samp_rate(cfg.samp_rate)
	dsp.set_fft_size(cfg.fft_size)
	dsp.set_fft_fps(cfg.fft_fps)
	sleep_sec=0.87/cfg.fft_fps
	print "[openwebrx-spectrum] Spectrum thread initialized successfully."
	dsp.start()
	print "[openwebrx-spectrum] Spectrum thread started." 
	while True:
		data=dsp.read(cfg.fft_size*4)
		#print "gotcha",len(data),"bytes of spectrum data via spectrum_thread_function()"
		clients_mutex.acquire()
		for i in range(0,len(clients)):
			if (clients[i].ws_started):
				if clients[i].spectrum_queue.full():
					close_client(i, False)
				else:
					clients[i].spectrum_queue.put([data]) # add new string by "reference" to all clients
		clients_mutex.release()
	
def get_client_by_id(client_id, use_mutex=True):
	global clients_mutex
	global clients
	output=-1
	if use_mutex: clients_mutex.acquire()
	for i in range(0,len(clients)):
		if(clients[i].id==client_id):
			output=i
			break
	if use_mutex: clients_mutex.release()
	if output==-1:
		raise ClientNotFoundException
	else:
		return output

def log_client(client, what):
	print "[openwebrx-httpd] client {0}#{1} :: {2}".format(client.ip,client.id,what)

def cleanup_clients():
	# if client doesn't open websocket for too long time, we drop it
	global clients_mutex
	global clients
	clients_mutex.acquire()
	correction=0
	for i in range(0,len(clients)):
		i-=correction
		#print "cleanup_clients:: len(clients)=", len(clients), "i=", i
		if (not clients[i].ws_started) and (time.time()-clients[i].gen_time)>180:
			close_client(i, False)
			correction+=1
	clients_mutex.release()

def generate_client_id(ip):
	#add a client
	global clients
	global clients_mutex
	new_client=namedtuple("ClientStruct", "id gen_time ws_started sprectum_queue ip")	
	new_client.id=md5.md5(str(random.random())).hexdigest()
	new_client.gen_time=time.time()
	new_client.ws_started=False # to check whether client has ever tried to open the websocket
	new_client.spectrum_queue=Queue.Queue(1000)
	new_client.ip=ip
	clients_mutex.acquire()
	clients.append(new_client)
	log_client(new_client,"client added. Clients now: {0}".format(len(clients)))
	clients_mutex.release()
	cleanup_clients()
	return new_client.id

def close_client(i, use_mutex=True):
	global clients_mutex
	global clients
	log_client(clients[i],"client being closed.")
	if use_mutex: clients_mutex.acquire()
	del clients[i]
	if use_mutex: clients_mutex.release()
	
class WebRXHandler(BaseHTTPRequestHandler):    
	def proc_read_thread():
		pass

	def do_GET(self):
		global dsp_plugin
		rootdir = 'htdocs' 
		self.path=self.path.replace("..","")
		path_temp_parts=self.path.split("?")
		self.path=path_temp_parts[0]
		request_param=path_temp_parts[1] if(len(path_temp_parts)>1) else "" 
		try:
			if self.path=="/":
				self.path="/index.wrx"
			# there's even another cool tip at http://stackoverflow.com/questions/4419650/how-to-implement-timeout-in-basehttpserver-basehttprequesthandler-python
			if self.path[:4]=="/ws/":
				try:
					# ========= WebSocket handshake  =========
					try:				
						rxws.handshake(self)
						clients_mutex.acquire()				
						client_i=get_client_by_id(self.path[4:], False)
						myclient=clients[client_i]
						clients_mutex.release()
					except rxws.WebSocketException:
						self.send_error(400, 'Bad request.')
						return
					except ClientNotFoundException:
						self.send_error(400, 'Bad request.')
						return

					# ========= Client handshake =========
					rxws.send(self, "CLIENT DE SERVER openwebrx.py")
					client_ans=rxws.recv(self, True)
					if client_ans[:16]!="SERVER DE CLIENT":
						rxws.send("ERR Bad answer.")
						return
					myclient.ws_started=True
					#send default parameters
					rxws.send(self, "MSG center_freq={0} bandwidth={1} fft_size={2} fft_fps={3} setup".format(str(cfg.center_freq),str(cfg.samp_rate),cfg.fft_size,cfg.fft_fps))

					# ========= Initialize DSP =========
					dsp=getattr(plugins.dsp,cfg.dsp_plugin).plugin.dsp_plugin()
					dsp.set_samp_rate(cfg.samp_rate)
					dsp.set_demodulator("nfm")
					dsp.set_offset_freq(0)
					dsp.set_bpf(-4000,4000)
					dsp.start()
					
					while True:
						# ========= send audio =========
						temp_audio_data=dsp.read(1024*8)
						rxws.send(self, temp_audio_data, "AUD ")

						# ========= send spectrum =========
						while not myclient.spectrum_queue.empty():
							spectrum_data=myclient.spectrum_queue.get()
							spectrum_data_mid=len(spectrum_data[0])/2
							rxws.send(self, spectrum_data[0][spectrum_data_mid:]+spectrum_data[0][:spectrum_data_mid], "FFT ") 
							# (it seems GNU Radio exchanges the first and second part of the FFT output, we correct it)

						# ========= process commands =========
						while True:
							rdata=rxws.recv(self, False)
							if not rdata: break
							#try:
							elif rdata[:3]=="SET":
								print "[openwebrx-httpd:ws,%d] command: %s"%(client_i,rdata)
								pairs=rdata[4:].split(" ")
								bpf_set=False
								new_bpf=dsp.get_bpf()
								filter_limit=dsp.get_output_rate()/2
								for pair in pairs:
									param_name, param_value = pair.split("=")
									if param_name == "low_cut" and -filter_limit <= float(param_value) <= filter_limit:
										bpf_set=True
										new_bpf[0]=param_value
									elif param_name == "high_cut" and -filter_limit <= float(param_value) <= filter_limit:
										bpf_set=True
										new_bpf[1]=param_value
									elif param_name == "offset_freq" and -cfg.samp_rate/2 <= float(param_value) <= cfg.samp_rate/2:
										dsp.set_offset_freq(param_value)
									elif param_name=="mod":
										dsp.stop()
										dsp.set_demodulator(param_value)
										dsp.start()
									else:
										print "[openwebrx-httpd:ws] invalid parameter"
								if bpf_set:
									dsp.set_bpf(*new_bpf)
								#code.interact(local=locals())
				except:
					print "[openwebrx-httpd] exception happened at all"
					exc_type, exc_value, exc_traceback = sys.exc_info()
					if exc_value[0]==32: #"broken pipe", client disconnected
						pass
					elif exc_value[0]==11: #"resource unavailable" on recv, client disconnected					
						pass
					else:	
						print "[openwebrx-httpd] error: ",exc_type,exc_value
						traceback.print_tb(exc_traceback)
				#delete disconnected client
				try:
					dsp.stop()
					del dsp
				except:
					pass
				clients_mutex.acquire()
				id_to_close=get_client_by_id(myclient.id,False)
				close_client(id_to_close,False)
				clients_mutex.release()
				return
			else:
				f=open(rootdir+self.path)
				data=f.read()
				extension=self.path[(len(self.path)-4):len(self.path)]
				extension=extension[2:] if extension[1]=='.' else extension[1:]
				if extension == "wrx" and ((self.headers['user-agent'].count("Chrome")==0 and self.headers['user-agent'].count("Firefox")==0) if 'user-agent' in self.headers.keys() else True) and (not request_param.count("unsupported")):
					self.send_response(302)
					self.send_header('Content-type','text/html')
					self.send_header("Location", "http://{0}:{1}/upgrade.html".format(cfg.server_hostname,cfg.web_port))
					self.end_headers()
					self.wfile.write("<html><body><h1>Object moved</h1>Please <a href=\"/upgrade.html\">click here</a> to continue.</body></html>")
					return
				self.send_response(200)
				if(("wrx","html","htm").count(extension)):
					self.send_header('Content-type','text/html')
				elif(extension=="js"):
					self.send_header('Content-type','text/javascript')
				elif(extension=="css"):
					self.send_header('Content-type','text/css')
				self.end_headers()
				if extension == "wrx":
					replace_dictionary=(
						("%[RX_PHOTO_DESC]",cfg.photo_desc),
						("%[CLIENT_ID]",generate_client_id(self.client_address[0])),
						("%[WS_URL]","ws://"+cfg.server_hostname+":"+str(cfg.web_port)+"/ws/"),
						("%[RX_TITLE]",cfg.receiver_name),
						("%[RX_LOC]",cfg.receiver_location),
						("%[RX_QRA]",cfg.receiver_qra),
						("%[RX_ASL]",str(cfg.receiver_asl)),
						("%[RX_GPS]",str(cfg.receiver_gps[0])+","+str(cfg.receiver_gps[1])),
						("%[RX_PHOTO_HEIGHT]",str(cfg.photo_height)),("%[RX_PHOTO_TITLE]",cfg.photo_title),
						("%[RX_ADMIN]",cfg.receiver_admin),
						("%[RX_ANT]",cfg.receiver_ant),
						("%[RX_DEVICE]",cfg.receiver_device)
					)
					for rule in replace_dictionary:
						while data.find(rule[0])!=-1:
							data=data.replace(rule[0],rule[1])
				self.wfile.write(data)
				f.close()
			return
		except IOError:
			self.send_error(404, 'Invalid path.')
		except:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			print "[openwebrx-httpd] exception happened (outside):", exc_type, exc_value
			traceback.print_tb(exc_traceback)

class ClientNotFoundException(Exception):
	pass

if __name__=="__main__":
	main()

