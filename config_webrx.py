# -*- coding: utf-8 -*-

"""
config_webrx: configuration options for OpenWebRX

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

	++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	In addition, as a special exception, the copyright holders
	state that config_rtl.py and config_webrx.py are not part of the
	Corresponding Source defined in GNU AGPL version 3 section 1.

	(It means that you do not have to redistribute config_rtl.py and
	config_webrx.py if you make any changes to these two configuration files,
	and use them for running your web service with OpenWebRX.)
"""

# NOTE: you can find additional information about configuring OpenWebRX in the Wiki:
#       https://github.com/simonyiszk/openwebrx/wiki

# ==== Server settings ====
web_port=8073
server_hostname="localhost" # If this contains an incorrect value, the web UI may freeze on load (it can't open websocket)
max_clients=20

# ==== Web GUI configuration ====
receiver_name="[Callsign]"
receiver_location="Budapest, Hungary"
receiver_qra="JN97ML"
receiver_asl=200
receiver_ant="Longwire"
receiver_device="RTL-SDR"
receiver_admin="example@example.com"
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

# ==== sdr.hu listing ====
# If you want your ham receiver to be listed publicly on sdr.hu, then take the following steps:
# 1. Register at: http://sdr.hu/register
# 2. You will get an unique key by email. Copy it and paste here:
sdrhu_key = ""
# 3. Set this setting to True to enable listing:
sdrhu_public_listing = False

# ==== DSP/RX settings ====
dsp_plugin="csdr"
fft_fps=9
fft_size=4096
fft_enable_average = True  # Set to False if you want to save CPU time
fft_voverlap_factor=0.3 # How much successive averaged FFT windows overlap in time domain (zero for no overlap, negative to skip samples between FFTs)
samp_rate = 250000
center_freq = 145525000
rf_gain = 5 #in dB. For an RTL-SDR, rf_gain=0 will set the tuner to auto gain mode, else it will be in manual gain mode.
ppm = 0

audio_compression="adpcm" #valid values: "adpcm", "none"
fft_compression="adpcm" #valid values: "adpcm", "none"

start_rtl_thread=True

# ==== I/Q sources ====
# (Uncomment the appropriate by removing # characters at the beginning of the corresponding lines.)

# There are guides for setting may different SDR hardware including AirSpy, AFEDRI-SDR, RTL-SDR in direct sampling mode, etc. in the Wiki:
#       https://github.com/simonyiszk/openwebrx/wiki

# You can use other SDR hardware as well, by giving your own command that outputs the I/Q samples... Some examples of configuration are available here (default is RTL-SDR):

# >> RTL-SDR via rtl_sdr

start_rtl_command="rtl_sdr -s {samp_rate} -f {center_freq} -p {ppm} -g {rf_gain} -".format(rf_gain=rf_gain, center_freq=center_freq, samp_rate=samp_rate, ppm=ppm)
format_conversion="csdr convert_u8_f"
real_input = False

#start_rtl_command="hackrf_transfer -s {samp_rate} -f {center_freq} -g {rf_gain} -l16 -a0 -q -r-".format(rf_gain=rf_gain, center_freq=center_freq, samp_rate=samp_rate, ppm=ppm)
#format_conversion="csdr convert_s8_f"
"""
To use a HackRF, compile the HackRF host tools from its "stdout" branch:
 git clone https://github.com/mossmann/hackrf/
 cd hackrf
 git fetch
 git checkout origin/stdout
 cd host
 mkdir build
 cd build
 cmake .. -DINSTALL_UDEV_RULES=ON
 make
 sudo make install
"""

# >> Sound card SDR (needs ALSA)
# I did not have the chance to properly test it.
#samp_rate = 96000
#start_rtl_command="arecord -t raw -D default -f S16_LE -r {samp_rate} -c2 -".format(samp_rate=samp_rate)
#format_conversion="csdr convert_s16_f | csdr gain_ff 30"
#real_input = False

# >> Sound card SDR with real (mono) input, for example, VLF receiver with antenna going directly to sound card
#samp_rate = 96000
#start_rtl_command="arecord -t raw -D default -f S16_LE -r {samp_rate} -c1 -".format(samp_rate=samp_rate)
#format_conversion="csdr convert_s16_f | csdr gain_ff 30"
#real_input = True
#center_freq = samp_rate/4  # for direct sampling

# >> /dev/urandom test signal source
#samp_rate = 2400000
#start_rtl_command="cat /dev/urandom | (pv -qL `python -c 'print int({samp_rate} * 2.2)'` 2>&1)".format(rf_gain=rf_gain, center_freq=center_freq, samp_rate=samp_rate)
#format_conversion="csdr convert_u8_f"

# >> Pre-recorded raw I/Q file as signal source
# You will have to correctly specify: samp_rate, center_freq, format_conversion in order to correctly play an I/Q file.
#start_rtl_command="(while true; do cat my_iq_file.raw; done) | csdr flowcontrol {sr} 20 ".format(sr=samp_rate*2*1.05)
#format_conversion="csdr convert_u8_f"

# >> gr-osmosdr signal source using GNU Radio (follow this guide: https://github.com/simonyiszk/openwebrx/wiki/Using-GrOsmoSDR-as-signal-source)
#start_rtl_command="cat /tmp/osmocom_fifo"
#format_conversion=""

# ==== Misc settings ====

shown_center_freq = center_freq #you can change this if you use an upconverter

client_audio_buffer_size = 5
#increasing client_audio_buffer_size will:
# - also increase the latency
# - decrease the chance of audio underruns

start_freq = center_freq
start_mod = "nfm" #nfm, am, lsb, usb, cw

iq_server_port = 4951 #TCP port for ncat to listen on. It will send I/Q data over its connections, for internal use in OpenWebRX. It is only accessible from the localhost by default.

#access_log = "~/openwebrx_access.log"

# ==== Color themes ====

#A guide is available to help you set these values: https://github.com/simonyiszk/openwebrx/wiki/Calibrating-waterfall-display-levels

### default theme by tejeez:
waterfall_colors = "[0x000000ff,0x0000ffff,0x00c0ffff,0x80ff00ff,0xff8000ff,0xff0080ff,0xff00ffff,0xffffffff]"
waterfall_min_level = -88 #in dB
waterfall_max_level = -20
waterfall_auto_level_margin = (5, 40)
### old theme by HA7ILM:
#waterfall_colors = "[0x000000ff,0x2e6893ff, 0x69a5d0ff, 0x214b69ff, 0x9dc4e0ff,  0xfff775ff, 0xff8a8aff, 0xb20000ff]"
#waterfall_min_level = -115 #in dB
#waterfall_max_level = 0
#waterfall_auto_level_margin = (20, 30)

#Note: When the auto waterfall level button is clicked, the following happens:
#	[waterfall_min_level] = [current_min_power_level] - [waterfall_auto_level_margin[0]]
#	[waterfall_max_level] = [current_max_power_level] + [waterfall_auto_level_margin[1]]
#
#   ___|____________________________________|____________________________________|____________________________________|___> signal power
#        \_waterfall_auto_level_margin[0]_/ |__ current_min_power_level          | \_waterfall_auto_level_margin[1]_/
#                                                      current_max_power_level __|
# ==== Experimental settings ===

#Warning! These are very experimental.
csdr_dynamic_bufsize = False # This allows you to change the buffering mode of csdr.
csdr_print_bufsizes = False  # This prints the buffer sizes used for csdr processes.
csdr_through = False # Setting this True will print out how much data is going into the DSP chains.

#Look up external IP address automatically from icanhazip.com, and use it as [server_hostname]
"""
print "[openwebrx-config] Detecting external IP address..."
import urllib2
server_hostname=urllib2.urlopen("http://icanhazip.com").read()[:-1]
print "[openwebrx-config] External IP address detected:", server_hostname
"""
