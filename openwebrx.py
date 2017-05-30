#!/usr/bin/python2
print "" # python2.7 is required to run OpenWebRX instead of python3. Please run me by: python2 openwebrx.py
"""

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
sw_version="v0.17"
#0.15 (added nmux)

import os
import code
import importlib
import csdr
import thread
import time
import datetime
import subprocess
import os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import fcntl
import time
import md5
import random
import threading
import sys
import traceback
from collections import namedtuple
import Queue
import ctypes

#import rtl_mus
import rxws
import uuid
import signal
import socket

try: import sdrhu
except: sdrhu=False
avatar_ctime=""

#pypy compatibility
try: import dl
except: pass
try: import __pypy__
except: pass
pypy="__pypy__" in globals()

"""
def import_all_plugins(directory):
    for subdir in os.listdir(directory):
        if os.path.isdir(directory+subdir) and not subdir[0]=="_":
            exact_path=directory+subdir+"/plugin.py"
            if os.path.isfile(exact_path):
                importname=(directory+subdir+"/plugin").replace("/",".")
                print "[openwebrx-import] Found plugin:",importname
                importlib.import_module(importname)
"""

class MultiThreadHTTPServer(ThreadingMixIn, HTTPServer):
    pass

def handle_signal(sig, frame):
    global spectrum_dsp
    if sig == signal.SIGUSR1:
        print "[openwebrx] Verbose status information on USR1 signal"
        print
        print "time.time() =", time.time()
        print "clients_mutex.locked() =", clients_mutex.locked()
        print "clients_mutex_locker =", clients_mutex_locker
        if server_fail: print "server_fail = ", server_fail
        print "spectrum_thread_watchdog_last_tick =", spectrum_thread_watchdog_last_tick
        print
        print "clients:",len(clients)
        for client in clients:
            print
            for key in client._fields:
                print "\t%s = %s"%(key,str(getattr(client,key)))
    elif sig == signal.SIGUSR2:
        code.interact(local=globals())
    else:
        print "[openwebrx] Ctrl+C: aborting."
        cleanup_clients(True)
        spectrum_dsp.stop()
        os._exit(1) #not too graceful exit

def access_log(data):
    global logs
    logs.access_log.write("["+datetime.datetime.now().isoformat()+"] "+data+"\n")
    logs.access_log.flush()

receiver_failed=spectrum_thread_watchdog_last_tick=rtl_thread=spectrum_dsp=server_fail=None

def main():
    global clients, clients_mutex, pypy, lock_try_time, avatar_ctime, cfg, logs
    global serverfail, rtl_thread
    print
    print "OpenWebRX - Open Source SDR Web App for Everyone!  | for license see LICENSE file in the package"
    print "_________________________________________________________________________________________________"
    print
    print "Author contact info:    Andras Retzler, HA7ILM <randras@sdr.hu>"
    print

    no_arguments=len(sys.argv)==1
    if no_arguments: print "[openwebrx-main] Configuration script not specified. I will use: \"config_webrx.py\""
    cfg=__import__("config_webrx" if no_arguments else sys.argv[1])
    for option in ("access_log","csdr_dynamic_bufsize","csdr_print_bufsizes","csdr_through"):
        if not option in dir(cfg): setattr(cfg, option, False) #initialize optional config parameters

    #Open log files
    logs = type("logs_class", (object,), {"access_log":open(cfg.access_log if cfg.access_log else "/dev/null","a"), "error_log":""})()

    #Set signal handler
    signal.signal(signal.SIGINT, handle_signal) #http://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
    signal.signal(signal.SIGUSR1, handle_signal)
    signal.signal(signal.SIGUSR2, handle_signal)

    #Pypy
    if pypy: print "pypy detected (and now something completely different: c code is expected to run at a speed of 3*10^8 m/s?)"

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
    if os.system("csdr 2> /dev/null") == 32512: #check for csdr
        print "[openwebrx-main] You need to install \"csdr\" to run OpenWebRX!\n"
        return
    if os.system("nmux --help 2> /dev/null") == 32512: #check for nmux
        print "[openwebrx-main] You need to install an up-to-date version of \"csdr\" that contains the \"nmux\" tool to run OpenWebRX! Please upgrade \"csdr\"!\n"
        return
    if cfg.start_rtl_thread:
        nmux_bufcnt = nmux_bufsize = 0
        while nmux_bufsize < cfg.samp_rate/4: nmux_bufsize += 4096
        while nmux_bufsize * nmux_bufcnt < cfg.nmux_memory * 1e6: nmux_bufcnt += 1
        if nmux_bufcnt == 0 or nmux_bufsize == 0: 
            print "[openwebrx-main] Error: nmux_bufsize or nmux_bufcnt is zero. These depend on nmux_memory and samp_rate options in config_webrx.py"
            return
        print "[openwebrx-main] nmux_bufsize = %d, nmux_bufcnt = %d" % (nmux_bufsize, nmux_bufcnt)
        cfg.start_rtl_command += "| nmux --bufsize %d --bufcnt %d --port %d --address 127.0.0.1" % (nmux_bufsize, nmux_bufcnt, cfg.iq_server_port)
        rtl_thread=threading.Thread(target = lambda:subprocess.Popen(cfg.start_rtl_command, shell=True),  args=())
        rtl_thread.start()
        print "[openwebrx-main] Started rtl_thread: "+cfg.start_rtl_command
    print "[openwebrx-main] Waiting for I/Q server to start..."
    while True:
        testsock=socket.socket()
        try: testsock.connect(("127.0.0.1", cfg.iq_server_port))
        except:
            time.sleep(0.1)
            continue
        testsock.close()
        break
    print "[openwebrx-main] I/Q server started."

    #Initialize clients
    clients=[]
    clients_mutex=threading.Lock()
    lock_try_time=0

    #Start watchdog thread
    print "[openwebrx-main] Starting watchdog threads."
    mutex_test_thread=threading.Thread(target = mutex_test_thread_function, args = ())
    mutex_test_thread.start()
    mutex_watchdog_thread=threading.Thread(target = mutex_watchdog_thread_function, args = ())
    mutex_watchdog_thread.start()


    #Start spectrum thread
    print "[openwebrx-main] Starting spectrum thread."
    spectrum_thread=threading.Thread(target = spectrum_thread_function, args = ())
    spectrum_thread.start()
    #spectrum_watchdog_thread=threading.Thread(target = spectrum_watchdog_thread_function, args = ())
    #spectrum_watchdog_thread.start()

    get_cpu_usage()
    bcastmsg_thread=threading.Thread(target = bcastmsg_thread_function, args = ())
    bcastmsg_thread.start()

    #threading.Thread(target = measure_thread_function, args = ()).start()

    #Start sdr.hu update thread
    if sdrhu and cfg.sdrhu_key and cfg.sdrhu_public_listing:
        print "[openwebrx-main] Starting sdr.hu update thread..."
        avatar_ctime=str(os.path.getctime("htdocs/gfx/openwebrx-avatar.png"))
        sdrhu_thread=threading.Thread(target = sdrhu.run, args = ())
        sdrhu_thread.start()

    #Start HTTP thread
    httpd = MultiThreadHTTPServer(('', cfg.web_port), WebRXHandler)
    print('[openwebrx-main] Starting HTTP server.')
    access_log("Starting OpenWebRX...")
    httpd.serve_forever()


# This is a debug function below:
measure_value=0
def measure_thread_function():
    global measure_value
    while True:
        print "[openwebrx-measure] value is",measure_value
        measure_value=0
        time.sleep(1)

def bcastmsg_thread_function():
    global clients
    while True:
        time.sleep(3)
        try: cpu_usage=get_cpu_usage()
        except: cpu_usage=0
        cma("bcastmsg_thread")
        for i in range(0,len(clients)):
            clients[i].bcastmsg="MSG cpu_usage={0} clients={1}".format(int(cpu_usage*100),len(clients))
        cmr()

def mutex_test_thread_function():
    global clients_mutex, lock_try_time
    while True:
        time.sleep(0.5)
        lock_try_time=time.time()
        clients_mutex.acquire()
        clients_mutex.release()
        lock_try_time=0

def cma(what): #clients_mutex acquire
    global clients_mutex
    global clients_mutex_locker
    if not clients_mutex.locked(): clients_mutex_locker = what
    clients_mutex.acquire()

def cmr():
    global clients_mutex
    global clients_mutex_locker
    clients_mutex_locker = None
    clients_mutex.release()

def mutex_watchdog_thread_function():
    global lock_try_time
    global clients_mutex_locker
    global clients_mutex
    while True:
        if lock_try_time != 0 and time.time()-lock_try_time > 3.0:
            #if 3 seconds pass without unlock
            print "[openwebrx-mutex-watchdog] Mutex unlock timeout. Locker: \""+str(clients_mutex_locker)+"\" Now unlocking..."
            clients_mutex.release()
        time.sleep(0.5)

def spectrum_watchdog_thread_function():
    global spectrum_thread_watchdog_last_tick, receiver_failed
    while True:
        time.sleep(60)
        if spectrum_thread_watchdog_last_tick and time.time()-spectrum_thread_watchdog_last_tick > 60.0:
            print "[openwebrx-spectrum-watchdog] Spectrum timeout. Seems like no I/Q data is coming from the receiver.\nIf you're using RTL-SDR, the receiver hardware may randomly fail under some circumstances:\n1) high temperature,\n2) insufficient current available from the USB port."
            print "[openwebrx-spectrum-watchdog] Deactivating receiver."
            receiver_failed="spectrum"
            return

def check_server():
    global spectrum_dsp, server_fail, rtl_thread
    if server_fail: return server_fail
    #print spectrum_dsp.process.poll()
    if spectrum_dsp and spectrum_dsp.process.poll()!=None: server_fail = "spectrum_thread dsp subprocess failed"
    #if rtl_thread and not rtl_thread.is_alive(): server_fail = "rtl_thread failed"
    if server_fail: print "[openwebrx-check_server] >>>>>>> ERROR:", server_fail
    return server_fail

def apply_csdr_cfg_to_dsp(dsp):
    dsp.csdr_dynamic_bufsize = cfg.csdr_dynamic_bufsize
    dsp.csdr_print_bufsizes = cfg.csdr_print_bufsizes
    dsp.csdr_through = cfg.csdr_through

def spectrum_thread_function():
    global clients, spectrum_dsp, spectrum_thread_watchdog_last_tick
    spectrum_dsp=dsp=csdr.dsp()
    dsp.nc_port=cfg.iq_server_port
    dsp.set_demodulator("fft")
    dsp.set_samp_rate(cfg.samp_rate)
    dsp.set_fft_size(cfg.fft_size)
    dsp.set_fft_fps(cfg.fft_fps)
    dsp.set_fft_averages(int(round(1.0 * cfg.samp_rate / cfg.fft_size / cfg.fft_fps / (1.0 - cfg.fft_voverlap_factor))) if cfg.fft_voverlap_factor>0 else 0)
    dsp.set_fft_compression(cfg.fft_compression)
    dsp.set_format_conversion(cfg.format_conversion)
    apply_csdr_cfg_to_dsp(dsp)
    sleep_sec=0.87/cfg.fft_fps
    print "[openwebrx-spectrum] Spectrum thread initialized successfully."
    dsp.start()
    if cfg.csdr_dynamic_bufsize:
        dsp.read(8) #dummy read to skip bufsize & preamble
        print "[openwebrx-spectrum] Note: CSDR_DYNAMIC_BUFSIZE_ON = 1"
    print "[openwebrx-spectrum] Spectrum thread started."
    bytes_to_read=int(dsp.get_fft_bytes_to_read())
    spectrum_thread_counter=0
    while True:
        data=dsp.read(bytes_to_read)
        #print "gotcha",len(data),"bytes of spectrum data via spectrum_thread_function()"
        if spectrum_thread_counter >= cfg.fft_fps:
            spectrum_thread_counter=0
            spectrum_thread_watchdog_last_tick = time.time() #once every second
        else: spectrum_thread_counter+=1
        cma("spectrum_thread")
        correction=0
        for i in range(0,len(clients)):
            i-=correction
            if (clients[i].ws_started):
                if clients[i].spectrum_queue.full():
                    print "[openwebrx-spectrum] client spectrum queue full, closing it."
                    close_client(i, False)
                    correction+=1
                else:
                    clients[i].spectrum_queue.put([data]) # add new string by "reference" to all clients
        cmr()

def get_client_by_id(client_id, use_mutex=True):
    global clients
    output=-1
    if use_mutex: cma("get_client_by_id")
    for i in range(0,len(clients)):
        if(clients[i].id==client_id):
            output=i
            break
    if use_mutex: cmr()
    if output==-1:
        raise ClientNotFoundException
    else:
        return output

def log_client(client, what):
    print "[openwebrx-httpd] client {0}#{1} :: {2}".format(client.ip,client.id,what)

def cleanup_clients(end_all=False):
    # - if a client doesn't open websocket for too long time, we drop it
    # - or if end_all is true, we drop all clients
    global clients
    cma("cleanup_clients")
    correction=0
    for i in range(0,len(clients)):
        i-=correction
        #print "cleanup_clients:: len(clients)=", len(clients), "i=", i
        if end_all or ((not clients[i].ws_started) and (time.time()-clients[i].gen_time)>45):
            if not end_all: print "[openwebrx] cleanup_clients :: client timeout to open WebSocket"
            close_client(i, False)
            correction+=1
    cmr()

def generate_client_id(ip):
    #add a client
    global clients
    new_client=namedtuple("ClientStruct", "id gen_time ws_started sprectum_queue ip closed bcastmsg dsp loopstat")
    new_client.id=md5.md5(str(random.random())).hexdigest()
    new_client.gen_time=time.time()
    new_client.ws_started=False # to check whether client has ever tried to open the websocket
    new_client.spectrum_queue=Queue.Queue(1000)
    new_client.ip=ip
    new_client.bcastmsg=""
    new_client.closed=[False] #byref, not exactly sure if required
    new_client.dsp=None
    cma("generate_client_id")
    clients.append(new_client)
    log_client(new_client,"client added. Clients now: {0}".format(len(clients)))
    cmr()
    cleanup_clients()
    return new_client.id

def close_client(i, use_mutex=True):
    global clients
    log_client(clients[i],"client being closed.")
    if use_mutex: cma("close_client")
    try:
        clients[i].dsp.stop()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print "[openwebrx] close_client dsp.stop() :: error -",exc_type,exc_value
        traceback.print_tb(exc_traceback)
    clients[i].closed[0]=True
    access_log("Stopped streaming to client: "+clients[i].ip+"#"+str(clients[i].id)+" (users now: "+str(len(clients)-1)+")")
    del clients[i]
    if use_mutex: cmr()

# http://www.codeproject.com/Articles/462525/Simple-HTTP-Server-and-Client-in-Python
# some ideas are used from the artice above

class WebRXHandler(BaseHTTPRequestHandler):
    def proc_read_thread():
        pass

    def send_302(self,what):
        self.send_response(302)
        self.send_header('Content-type','text/html')
        self.send_header("Location", "http://{0}:{1}/{2}".format(cfg.server_hostname,cfg.web_port,what))
        self.end_headers()
        self.wfile.write("<html><body><h1>Object moved</h1>Please <a href=\"/{0}\">click here</a> to continue.</body></html>".format(what))


    def do_GET(self):
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        global dsp_plugin, clients_mutex, clients, avatar_ctime, sw_version, receiver_failed
        rootdir = 'htdocs'
        self.path=self.path.replace("..","")
        path_temp_parts=self.path.split("?")
        self.path=path_temp_parts[0]
        request_param=path_temp_parts[1] if(len(path_temp_parts)>1) else ""
        access_log("GET "+self.path+" from "+self.client_address[0])
        try:
            if self.path=="/":
                self.path="/index.wrx"
            # there's even another cool tip at http://stackoverflow.com/questions/4419650/how-to-implement-timeout-in-basehttpserver-basehttprequesthandler-python
            #if self.path[:5]=="/lock": cma("do_GET /lock/") # to test mutex_watchdog_thread. Do not uncomment in production environment!
            if self.path[:4]=="/ws/":
                print "[openwebrx-ws] Client requested WebSocket connection"
                if receiver_failed: self.send_error(500,"Internal server error")
                try:
                    # ========= WebSocket handshake  =========
                    ws_success=True
                    try:
                        rxws.handshake(self)
                        cma("do_GET /ws/")
                        client_i=get_client_by_id(self.path[4:], False)
                        myclient=clients[client_i]
                    except rxws.WebSocketException: ws_success=False
                    except ClientNotFoundException: ws_success=False
                    finally:
                        if clients_mutex.locked(): cmr()
                    if not ws_success:
                        self.send_error(400, 'Bad request.')
                        return

                    # ========= Client handshake =========
                    if myclient.ws_started:
                        print "[openwebrx-httpd] error: second WS connection with the same client id, throwing it."
                        self.send_error(400, 'Bad request.') #client already started
                        return
                    rxws.send(self, "CLIENT DE SERVER openwebrx.py")
                    client_ans=rxws.recv(self, True)
                    if client_ans[:16]!="SERVER DE CLIENT":
                        rxws.send("ERR Bad answer.")
                        return
                    myclient.ws_started=True
                    #send default parameters
                    rxws.send(self, "MSG center_freq={0} bandwidth={1} fft_size={2} fft_fps={3} audio_compression={4} fft_compression={5} max_clients={6} setup".format(str(cfg.shown_center_freq),str(cfg.samp_rate),cfg.fft_size,cfg.fft_fps,cfg.audio_compression,cfg.fft_compression,cfg.max_clients))

                    # ========= Initialize DSP =========
                    dsp=csdr.dsp()
                    dsp_initialized=False
                    dsp.set_audio_compression(cfg.audio_compression)
                    dsp.set_fft_compression(cfg.fft_compression) #used by secondary chains
                    dsp.set_format_conversion(cfg.format_conversion)
                    dsp.set_offset_freq(0)
                    dsp.set_bpf(-4000,4000)
                    dsp.set_secondary_fft_size(cfg.digimodes_fft_size)
                    dsp.nc_port=cfg.iq_server_port
                    apply_csdr_cfg_to_dsp(dsp)
                    myclient.dsp=dsp
                    do_secondary_demod=False
                    access_log("Started streaming to client: "+self.client_address[0]+"#"+myclient.id+" (users now: "+str(len(clients))+")")

                    while True:
                        myclient.loopstat=0
                        if myclient.closed[0]:
                            print "[openwebrx-httpd:ws] client closed by other thread"
                            break

                        # ========= send audio =========
                        if dsp_initialized:
                            myclient.loopstat=10
                            temp_audio_data=dsp.read(256)
                            myclient.loopstat=11
                            rxws.send(self, temp_audio_data, "AUD ")

                        # ========= send spectrum =========
                        while not myclient.spectrum_queue.empty():
                            myclient.loopstat=20
                            spectrum_data=myclient.spectrum_queue.get()
                            #spectrum_data_mid=len(spectrum_data[0])/2
                            #rxws.send(self, spectrum_data[0][spectrum_data_mid:]+spectrum_data[0][:spectrum_data_mid], "FFT ")
                            # (it seems GNU Radio exchanges the first and second part of the FFT output, we correct it)
                            myclient.loopstat=21
                            rxws.send(self, spectrum_data[0],"FFT ")

                        # ========= send smeter_level =========
                        smeter_level=None
                        while True:
                            try:
                                myclient.loopstat=30
                                smeter_level=dsp.get_smeter_level()
                                if smeter_level == None: break
                            except:
                                break
                        if smeter_level!=None:
                            myclient.loopstat=31
                            rxws.send(self, "MSG s={0}".format(smeter_level))

                        # ========= send bcastmsg =========
                        if myclient.bcastmsg!="":
                            myclient.loopstat=40
                            rxws.send(self,myclient.bcastmsg)
                            myclient.bcastmsg=""

                        # ========= send secondary =========
                        if do_secondary_demod:
                            myclient.loopstat=41
                            while True:
                                try: 
                                    secondary_spectrum_data=dsp.read_secondary_fft(dsp.get_secondary_fft_bytes_to_read())
                                    if len(secondary_spectrum_data) == 0: break
                                    # print "len(secondary_spectrum_data)", len(secondary_spectrum_data) #TODO digimodes
                                    rxws.send(self, secondary_spectrum_data, "FFTS")
                                except: break
                            myclient.loopstat=42
                            while True:
                                try:
                                    myclient.loopstat=422
                                    secondary_demod_data=dsp.read_secondary_demod(1)
                                    myclient.loopstat=423
                                    if len(secondary_demod_data) == 0: break
                                    # print "len(secondary_demod_data)", len(secondary_demod_data), secondary_demod_data #TODO digimodes
                                    rxws.send(self, secondary_demod_data, "DAT ")
                                except: break

                        # ========= process commands =========
                        while True:
                            myclient.loopstat=50
                            rdata=rxws.recv(self, False)
                            myclient.loopstat=51
                            #try:
                            if not rdata: break
                            elif rdata[:3]=="SET":
                                print "[openwebrx-httpd:ws,%d] command: %s"%(client_i,rdata)
                                pairs=rdata[4:].split(" ")
                                bpf_set=False
                                new_bpf=dsp.get_bpf()
                                filter_limit=dsp.get_output_rate()/2
                                for pair in pairs:
                                    param_name, param_value = pair.split("=")
                                    if param_name == "low_cut" and -filter_limit <= int(param_value) <= filter_limit:
                                        bpf_set=True
                                        new_bpf[0]=int(param_value)
                                    elif param_name == "high_cut" and -filter_limit <= int(param_value) <= filter_limit:
                                        bpf_set=True
                                        new_bpf[1]=int(param_value)
                                    elif param_name == "offset_freq" and -cfg.samp_rate/2 <= int(param_value) <= cfg.samp_rate/2:
                                        myclient.loopstat=510
                                        dsp.set_offset_freq(int(param_value))
                                    elif param_name == "squelch_level" and float(param_value) >= 0:
                                        myclient.loopstat=520
                                        dsp.set_squelch_level(float(param_value))
                                    elif param_name=="mod":
                                        if (dsp.get_demodulator()!=param_value):
                                            myclient.loopstat=530
                                            if dsp_initialized: dsp.stop()
                                            dsp.set_demodulator(param_value)
                                            if dsp_initialized: dsp.start()
                                    elif param_name == "output_rate":
                                        if not dsp_initialized:
                                            myclient.loopstat=540
                                            dsp.set_output_rate(int(param_value))
                                            myclient.loopstat=541
                                            dsp.set_samp_rate(cfg.samp_rate)
                                    elif param_name=="action" and param_value=="start":
                                        if not dsp_initialized:
                                            myclient.loopstat=550
                                            dsp.start()
                                            dsp_initialized=True
                                    elif param_name=="secondary_mod" and cfg.digimodes_enable:
                                        if (dsp.get_secondary_demodulator() != param_value):
                                            if dsp_initialized: dsp.stop()
                                            if param_value == "off":
                                                dsp.set_secondary_demodulator(None)
                                                do_secondary_demod = False
                                            else:
                                                dsp.set_secondary_demodulator(param_value)
                                                do_secondary_demod = True
                                                rxws.send(self, "MSG secondary_fft_size={0} if_samp_rate={1} secondary_bw={2} secondary_setup".format(cfg.digimodes_fft_size, dsp.if_samp_rate(), dsp.secondary_bw()))
                                            if dsp_initialized: dsp.start()
                                    elif param_name=="secondary_offset_freq" and 0 <= int(param_value) <= dsp.if_samp_rate()/2 and cfg.digimodes_enable:
                                        dsp.set_secondary_offset_freq(int(param_value))
                                    else:
                                        print "[openwebrx-httpd:ws] invalid parameter"
                                if bpf_set:
                                    myclient.loopstat=560
                                    dsp.set_bpf(*new_bpf)
                                #code.interact(local=locals())
                except:
                    myclient.loopstat=990
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    print "[openwebrx-httpd:ws] exception: ",exc_type,exc_value
                    traceback.print_tb(exc_traceback) #TODO digimodes
                    #if exc_value[0]==32: #"broken pipe", client disconnected
                    #    pass
                    #elif exc_value[0]==11: #"resource unavailable" on recv, client disconnected
                    #    pass
                    #else:
                    #    print "[openwebrx-httpd] error in /ws/ handler: ",exc_type,exc_value
                    #    traceback.print_tb(exc_traceback)

                #stop dsp for the disconnected client
                myclient.loopstat=991
                try:
                    dsp.stop()
                    del dsp
                except:
                    print "[openwebrx-httpd] error in dsp.stop()"

                #delete disconnected client
                myclient.loopstat=992
                try:
                    cma("do_GET /ws/ delete disconnected")
                    id_to_close=get_client_by_id(myclient.id,False)
                    close_client(id_to_close,False)
                except:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    print "[openwebrx-httpd] client cannot be closed: ",exc_type,exc_value
                    traceback.print_tb(exc_traceback)
                finally:
                    cmr()
                myclient.loopstat=1000
                return
            elif self.path in ("/status", "/status/"):
                #self.send_header('Content-type','text/plain')
                getbands=lambda: str(int(cfg.shown_center_freq-cfg.samp_rate/2))+"-"+str(int(cfg.shown_center_freq+cfg.samp_rate/2))
                self.wfile.write("status="+("inactive" if receiver_failed else "active")+"\nname="+cfg.receiver_name+"\nsdr_hw="+cfg.receiver_device+"\nop_email="+cfg.receiver_admin+"\nbands="+getbands()+"\nusers="+str(len(clients))+"\nusers_max="+str(cfg.max_clients)+"\navatar_ctime="+avatar_ctime+"\ngps="+str(cfg.receiver_gps)+"\nasl="+str(cfg.receiver_asl)+"\nloc="+cfg.receiver_location+"\nsw_version="+sw_version+"\nantenna="+cfg.receiver_ant+"\n")
                print "[openwebrx-httpd] GET /status/ from",self.client_address[0]
            else:
                f=open(rootdir+self.path)
                data=f.read()
                extension=self.path[(len(self.path)-4):len(self.path)]
                extension=extension[2:] if extension[1]=='.' else extension[1:]
                checkresult=check_server()
                if extension == "wrx" and (checkresult or receiver_failed):
                    self.send_302("inactive.html")
                    return
                anyStringsPresentInUserAgent=lambda a: reduce(lambda x,y:x or y, map(lambda b:self.headers['user-agent'].count(b), a), False)
                if extension == "wrx" and ( (not anyStringsPresentInUserAgent(("Chrome","Firefox","Googlebot","iPhone","iPad","iPod"))) if 'user-agent' in self.headers.keys() else True ) and (not request_param.count("unsupported")):
                    self.send_302("upgrade.html")
                    return
                if extension == "wrx":
                    cleanup_clients(False)
                    if cfg.max_clients<=len(clients):
                        self.send_302("retry.html")
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
                        ("%[CLIENT_ID]", generate_client_id(self.client_address[0])) if "%[CLIENT_ID]" in data else "",
                        ("%[WS_URL]","ws://"+cfg.server_hostname+":"+str(cfg.web_port)+"/ws/"),
                        ("%[RX_TITLE]",cfg.receiver_name),
                        ("%[RX_LOC]",cfg.receiver_location),
                        ("%[RX_QRA]",cfg.receiver_qra),
                        ("%[RX_ASL]",str(cfg.receiver_asl)),
                        ("%[RX_GPS]",str(cfg.receiver_gps[0])+","+str(cfg.receiver_gps[1])),
                        ("%[RX_PHOTO_HEIGHT]",str(cfg.photo_height)),("%[RX_PHOTO_TITLE]",cfg.photo_title),
                        ("%[RX_ADMIN]",cfg.receiver_admin),
                        ("%[RX_ANT]",cfg.receiver_ant),
                        ("%[RX_DEVICE]",cfg.receiver_device),
                        ("%[AUDIO_BUFSIZE]",str(cfg.client_audio_buffer_size)),
                        ("%[START_OFFSET_FREQ]",str(cfg.start_freq-cfg.center_freq)),
                        ("%[START_MOD]",cfg.start_mod),
                        ("%[WATERFALL_COLORS]",cfg.waterfall_colors),
                        ("%[WATERFALL_MIN_LEVEL]",str(cfg.waterfall_min_level)),
                        ("%[WATERFALL_MAX_LEVEL]",str(cfg.waterfall_max_level)),
                        ("%[WATERFALL_AUTO_LEVEL_MARGIN]","[%d,%d]"%cfg.waterfall_auto_level_margin),
                        ("%[DIGIMODES_ENABLE]",("true" if cfg.digimodes_enable else "false")),
                        ("%[MATHBOX_WATERFALL_FRES]",str(cfg.mathbox_waterfall_frequency_resolution)),
                        ("%[MATHBOX_WATERFALL_THIST]",str(cfg.mathbox_waterfall_history_length)),
                        ("%[MATHBOX_WATERFALL_COLORS]",cfg.mathbox_waterfall_colors)
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
            print "[openwebrx-httpd] error (@outside):", exc_type, exc_value
            traceback.print_tb(exc_traceback)


class ClientNotFoundException(Exception):
    pass

last_worktime=0
last_idletime=0

def get_cpu_usage():
    global last_worktime, last_idletime
    try:
        f=open("/proc/stat","r")
    except:
        return 0 #Workaround, possibly we're on a Mac
    line=""
    while not "cpu " in line: line=f.readline()
    f.close()
    spl=line.split(" ")
    worktime=int(spl[2])+int(spl[3])+int(spl[4])
    idletime=int(spl[5])
    dworktime=(worktime-last_worktime)
    didletime=(idletime-last_idletime)
    rate=float(dworktime)/(didletime+dworktime)
    last_worktime=worktime
    last_idletime=idletime
    if(last_worktime==0): return 0
    return rate


if __name__=="__main__":
    main()
