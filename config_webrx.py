# -*- coding: utf-8 -*- 

"""
config_webrx: configuration options for OpenWebRX

OpenWebRX (c) Copyright 2013-2014 Andras Retzler <randras@sdr.hu>

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

"""
#Server settings
web_port=8073
server_hostname="localhost" # If this contains an incorrect value, the web UI may freeze on load (it can't open websocket)

#Web GUI configuration
receiver_name="[Callsign]"
receiver_location="Budapest, Hungary"
receiver_qra="JN97ML"
receiver_asl=182
receiver_ant="Longwire"
receiver_device="RTL-SDR"
receiver_admin="localhost@localhost"
receiver_gps=(47.000000,19.000000)
photo_height=350
photo_title="Panorama of Budapest from Schönherz Zoltán Dormitory"
photo_desc="""
You can add your own background photo and receiver information.<br />
Receiver is operated by: <a href="mailto:%[RX_ADMIN]">%[RX_ADMIN]</a><br/>
Device: %[RX_DEVICE]<br />
Antenna: %[RX_ANT]<br />
Website: <a href="http://localhost" target="_blank">http://localhost</a>
"""

#DSP/RX settings
dsp_plugin="csdr"
fft_fps=9
fft_size=4096
samp_rate = 250000
center_freq = 145525000
rf_gain = 5

start_rtl_thread=True #rtl_sdr is more stable than rtl_tcp...
start_rtl_command="rtl_sdr -s {samp_rate} -f {center_freq}  - | nc -vvl 127.0.0.1 8888".format(rf_gain=rf_gain, center_freq=center_freq, samp_rate=samp_rate) 
#start_rtl_tcp_command="rtl_tcp -s 250000 -f 145525000 -g 0 -p 8888"
#You can use other SDR hardware as well, but if the command above outputs samples in a format other than [unsigned char], then the dsp plugin has to be slightly modified (at the csdr convert_u8_f part).

