"""
rxws: WebSocket methods implemented for OpenWebRX

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

import base64
import sha
import select
import code

class WebSocketException(Exception):
    pass

def handshake(myself):
    my_client_id=myself.path[4:]
    my_headers=myself.headers.items()
    my_header_keys=map(lambda x:x[0],my_headers)
    h_key_exists=lambda x:my_header_keys.count(x)
    h_value=lambda x:my_headers[my_header_keys.index(x)][1]
    #print "The Lambdas(tm)"
    #print h_key_exists("upgrade")
    #print h_value("upgrade")
    #print h_key_exists("sec-websocket-key")
    if (not h_key_exists("upgrade")) or not (h_value("upgrade")=="websocket") or (not h_key_exists("sec-websocket-key")):
        raise WebSocketException
    ws_key=h_value("sec-websocket-key")
    ws_key_toreturn=base64.b64encode(sha.new(ws_key+"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
    #A sample list of keys we get: [('origin', 'http://localhost:8073'), ('upgrade', 'websocket'), ('sec-websocket-extensions', 'x-webkit-deflate-frame'), ('sec-websocket-version', '13'), ('host', 'localhost:8073'), ('sec-websocket-key', 't9J1rgy4fc9fg2Hshhnkmg=='), ('connection', 'Upgrade'), ('pragma', 'no-cache'), ('cache-control', 'no-cache')]
    myself.wfile.write("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: "+ws_key_toreturn+"\r\nCQ-CQ-de: HA5KFU\r\n\r\n")

def get_header(size):
    #this does something similar: https://github.com/lemmingzshadow/php-websocket/blob/master/server/lib/WebSocket/Connection.php
    ws_first_byte=0b10000010 # FIN=1, OP=2
    if(size>125):
        ws_second_byte=126 # The following two bytes will indicate frame size
        extended_size=chr((size>>8)&0xff)+chr(size&0xff) #Okay, it uses reverse byte order (little-endian) compared to anything else sent on TCP
    else:
        ws_second_byte=size
        #256 bytes binary message in a single unmasked frame | 0x82 0x7E 0x0100 [256 bytes of binary data]
        extended_size=""
    return chr(ws_first_byte)+chr(ws_second_byte)+extended_size

def code_payload(data, masking_key=""):
    # both encode or decode
    if masking_key=="":
        key = (61, 84, 35, 6)
    else:
        key = [ord(i) for i in masking_key]
    encoded=""
    for i in range(0,len(data)):
        encoded+=chr(ord(data[i])^key[i%4])
    return encoded

def xxdg(data):
    output=""
    for i in range(0,len(data)/8):
        output+=xxd(data[i:i+8])
        if i%2: output+="\n"
        else: output+="  "
    return output
        

def xxd(data):
    #diagnostic purposes only
    output=""
    for d in data:
        output+=hex(ord(d))[2:].zfill(2)+" " 
    return output

#for R/W the WebSocket, use recv/send
#for reading the TCP socket, use readsock 
#for writing the TCP socket, use myself.wfile.write and flush

def readsock(myself,size,blocking):
    #http://thenestofheliopolis.blogspot.hu/2011/01/how-to-implement-non-blocking-two-way.html
    if blocking:
        return myself.rfile.read(size)
    else:
        poll = select.poll()
        poll.register(myself.rfile.fileno(), select.POLLIN or select.POLLPRI)
        fd = poll.poll(0) #timeout is 0
        if len(fd):
            f = fd[0]
            if f[1] > 0:
                return myself.rfile.read(size)
    return ""


def recv(myself, blocking=False, debug=False):
    bufsize=70000
    #myself.connection.setblocking(blocking) #umm... we cannot do that with rfile
    if debug: print "ws_recv begin"
    try:
        data=readsock(myself,6,blocking)
        #print "rxws.recv bytes:",xxd(data) 
    except:
        if debug: print "ws_recv error" 
        return ""
    if debug: print "ws_recv recved"
    if(len(data)==0): return ""
    fin=ord(data[0])&128!=0
    is_text_frame=ord(data[0])&15==1
    length=ord(data[1])&0x7f
    data+=readsock(myself,length,blocking)
    #print "rxws.recv length is ",length," (multiple packets together?) len(data) =",len(data)
    has_one_byte_length=length<125
    masked=ord(data[1])&0x80!=0
    #print "len=", length, len(data)-2
    #print "fin, is_text_frame, has_one_byte_length, masked = ", (fin, is_text_frame, has_one_byte_length, masked)
    #print xxd(data)
    if fin and is_text_frame and has_one_byte_length:
        if masked:
            return code_payload(data[6:], data[2:6])
        else:
            return data[2:]

#Useful links for ideas on WebSockets:
#  http://stackoverflow.com/questions/8125507/how-can-i-send-and-receive-websocket-messages-on-the-server-side
#  https://developer.mozilla.org/en-US/docs/WebSockets/Writing_WebSocket_server
#  http://tools.ietf.org/html/rfc6455#section-5.2   


def flush(myself): 
    myself.wfile.flush()
    #or the socket, not the rfile:
    #lR,lW,lX = select.select([],[myself.connection,],[],60)
    

def send(myself, data, begin_id="", debug=0):
    base_frame_size=35000 #could guess by MTU?
    debug=0
    #try:
    while True:
        counter=0
        from_end=len(data)-counter
        if from_end+len(begin_id)>base_frame_size:
            data_to_send=begin_id+data[counter:counter+base_frame_size-len(begin_id)]
            header=get_header(len(data_to_send))
            flush(myself)
            myself.wfile.write(header+data_to_send)
            flush(myself)
            if debug: print "rxws.send ==================== #1 if branch :: from={0} to={1} dlen={2} hlen={3}".format(counter,counter+base_frame_size-len(begin_id),len(data_to_send),len(header))
        else:
            data_to_send=begin_id+data[counter:]
            header=get_header(len(data_to_send))
            flush(myself)
            myself.wfile.write(header+data_to_send)
            flush(myself)
            if debug: print "rxws.send :: #2 else branch :: dlen={0} hlen={1}".format(len(data_to_send),len(header))
            #if debug: print "header:\n"+xxdg(header)+"\n\nws data:\n"+xxdg(data_to_send)
            break
        counter+=base_frame_size-len(begin_id)
    #except:
    #   pass
