# -*- coding: utf-8 -*-

"""
config_webrx: configuration options for OpenWebRX

    This file is part of OpenWebRX,
    an open-source SDR receiver software with a web UI.
    Copyright (c) 2013-2015 by Andras Retzler <randras@sdr.hu>
    Copyright (c) 2019-2020 by Jakob Ketterl <dd5jfk@darc.de>

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

# configuration version. please only modify if you're able to perform the associated migration steps.
version = 2

# NOTE: you can find additional information about configuring OpenWebRX in the Wiki:
# https://github.com/jketterl/openwebrx/wiki/Configuration-guide

# ==== Server settings ====
web_port = 8073
max_clients = 20

# ==== Web GUI configuration ====
receiver_name = "[Callsign]"
receiver_location = "Budapest, Hungary"
receiver_asl = 200
receiver_admin = "example@example.com"
receiver_gps = {"lat": 47.000000, "lon": 19.000000}
photo_title = "Panorama of Budapest from Schönherz Zoltán Dormitory"
# photo_desc allows you to put pretty much any HTML you like into the receiver description.
# The lines below should give you some examples of what's possible.
photo_desc = """
You can add your own background photo and receiver information.<br />
Receiver is operated by: <a href="mailto:openwebrx@localhost" target="_blank">Receiver Operator</a><br/>
Device: Receiver Device<br />
Antenna: Receiver Antenna<br />
Website: <a href="http://localhost" target="_blank">http://localhost</a>
"""

# ==== Public receiver listings ====
# You can publish your receiver on online receiver directories, like https://www.receiverbook.de
# You will receive a receiver key from the directory that will authenticate you as the operator of this receiver.
# Please note that you not share your receiver keys publicly since anyone that obtains your receiver key can take over
# your public listing.
# Your receiver keys should be placed into this array:
receiver_keys = []
# If you list your receiver on multiple sites, you can place all your keys into the array above, or you can append
# keys to the arraylike this:
# receiver_keys += ["my-receiver-key"]

# If you're not sure, simply copy & paste the code you received from your listing site below this line:

# ==== DSP/RX settings ====
fft_fps = 9
fft_size = 4096  # Should be power of 2
fft_voverlap_factor = (
    0.3  # If fft_voverlap_factor is above 0, multiple FFTs will be used for creating a line on the diagram.
)

audio_compression = "adpcm"  # valid values: "adpcm", "none"
fft_compression = "adpcm"  # valid values: "adpcm", "none"

digimodes_enable = True  # Decoding digimodes come with higher CPU usage.
digimodes_fft_size = 1024

# determines the quality, and thus the cpu usage, for the ambe codec used by digital voice modes
# if you're running on a Raspi (up to 3B+) you'll want to leave this on 1
digital_voice_unvoiced_quality = 1
# enables lookup of DMR ids using the radioid api
digital_voice_dmr_id_lookup = True

"""
Note: if you experience audio underruns while CPU usage is 100%, you can: 
- decrease `samp_rate`,
- set `fft_voverlap_factor` to 0,
- decrease `fft_fps` and `fft_size`,
- limit the number of users by decreasing `max_clients`.
"""

# ==== I/Q sources ====
# (Uncomment the appropriate by removing # characters at the beginning of the corresponding lines.)

###############################################################################
# Is my SDR hardware supported?                                               #
# Check here: https://github.com/jketterl/openwebrx/wiki/Supported-Hardware   #
###############################################################################

# Currently supported types of sdr receivers:
# "rtl_sdr", "rtl_sdr_soapy", "sdrplay", "hackrf", "airspy", "airspyhf", "fifi_sdr",
# "perseussdr", "lime_sdr", "pluto_sdr", "soapy_remote"
#
# In order to use rtl_sdr, you will need to install librtlsdr-dev and the connector.
# In order to use sdrplay, airspy or airspyhf, you will need to install soapysdr, the corresponding driver, and the
# connector.
#
# https://github.com/jketterl/owrx_connector
#
# In order to use Perseus HF you need to install the libperseus-sdr
#
# https://github.com/Microtelecom/libperseus-sdr
#
# and do the proper changes to the sdrs object below
# (see also Wiki in https://github.com/jketterl/openwebrx/wiki/Sample-configuration-for-Perseus-HF-receiver).
#

sdrs = {
    "rtlsdr": {
        "name": "RTL-SDR USB Stick",
        "type": "rtl_sdr",
        "ppm": 0,
        # you can change this if you use an upconverter. formula is:
        # center_freq + lfo_offset = actual frequency on the sdr
        # "lfo_offset": 0,
        "profiles": {
            "70cm": {
                "name": "70cm Relais",
                "center_freq": 438800000,
                "rf_gain": 30,
                "samp_rate": 2400000,
                "start_freq": 439275000,
                "start_mod": "nfm",
            },
            "2m": {
                "name": "2m komplett",
                "center_freq": 145000000,
                "rf_gain": 30,
                "samp_rate": 2400000,
                "start_freq": 145725000,
                "start_mod": "nfm",
            },
        },
    },
    "airspy": {
        "name": "Airspy HF+",
        "type": "airspyhf",
        "ppm": 0,
        "rf_gain": "auto",
        "profiles": {
            "20m": {
                "name": "20m",
                "center_freq": 14150000,
                "samp_rate": 384000,
                "start_freq": 14070000,
                "start_mod": "usb",
            },
            "30m": {
                "name": "30m",
                "center_freq": 10125000,
                "samp_rate": 192000,
                "start_freq": 10142000,
                "start_mod": "usb",
            },
            "40m": {
                "name": "40m",
                "center_freq": 7100000,
                "samp_rate": 256000,
                "start_freq": 7070000,
                "start_mod": "lsb",
            },
            "80m": {
                "name": "80m",
                "center_freq": 3650000,
                "samp_rate": 384000,
                "start_freq": 3570000,
                "start_mod": "lsb",
            },
            "49m": {
                "name": "49m Broadcast",
                "center_freq": 6050000,
                "samp_rate": 384000,
                "start_freq": 6070000,
                "start_mod": "am",
            },
        },
    },
    "sdrplay": {
        "name": "SDRPlay RSP2",
        "type": "sdrplay",
        "ppm": 0,
        "antenna": "Antenna A",
        "profiles": {
            "20m": {
                "name": "20m",
                "center_freq": 14150000,
                "rf_gain": 0,
                "samp_rate": 500000,
                "start_freq": 14070000,
                "start_mod": "usb",
            },
            "30m": {
                "name": "30m",
                "center_freq": 10125000,
                "rf_gain": 0,
                "samp_rate": 250000,
                "start_freq": 10142000,
                "start_mod": "usb",
            },
            "40m": {
                "name": "40m",
                "center_freq": 7100000,
                "rf_gain": 0,
                "samp_rate": 500000,
                "start_freq": 7070000,
                "start_mod": "lsb",
            },
            "80m": {
                "name": "80m",
                "center_freq": 3650000,
                "rf_gain": 0,
                "samp_rate": 500000,
                "start_freq": 3570000,
                "start_mod": "lsb",
            },
            "49m": {
                "name": "49m Broadcast",
                "center_freq": 6000000,
                "rf_gain": 0,
                "samp_rate": 500000,
                "start_freq": 6070000,
                "start_mod": "am",
            },
        },
    },
}

# ==== Color themes ====

### google turbo colormap (see: https://ai.googleblog.com/2019/08/turbo-improved-rainbow-colormap-for.html)
waterfall_colors = [0x30123bff, 0x311542ff, 0x33184aff, 0x341b51ff, 0x351e58ff, 0x36215fff, 0x372466ff, 0x38266cff, 0x392973ff, 0x3a2c79ff, 0x3b2f80ff, 0x3c3286ff, 0x3d358bff, 0x3e3891ff, 0x3e3a97ff, 0x3f3d9cff, 0x4040a2ff, 0x4043a7ff, 0x4146acff, 0x4248b1ff, 0x424bb6ff, 0x434ebaff, 0x4351bfff, 0x4453c3ff, 0x4456c7ff, 0x4559cbff, 0x455bcfff, 0x455ed3ff, 0x4561d7ff, 0x4663daff, 0x4666ddff, 0x4669e1ff, 0x466be4ff, 0x466ee7ff, 0x4671e9ff, 0x4673ecff, 0x4676eeff, 0x4678f1ff, 0x467bf3ff, 0x467df5ff, 0x4680f7ff, 0x4682f9ff, 0x4685faff, 0x4587fcff, 0x458afdff, 0x448cfeff, 0x448ffeff, 0x4391ffff, 0x4294ffff, 0x4196ffff, 0x3f99ffff, 0x3e9bffff, 0x3d9efeff, 0x3ba1fdff, 0x3aa3fdff, 0x38a6fbff, 0x36a8faff, 0x35abf9ff, 0x33adf7ff, 0x31b0f6ff, 0x2fb2f4ff, 0x2db5f2ff, 0x2cb7f0ff, 0x2ab9eeff, 0x28bcecff, 0x26beeaff, 0x25c0e7ff, 0x23c3e5ff, 0x21c5e2ff, 0x20c7e0ff, 0x1fc9ddff, 0x1dccdbff, 0x1cced8ff, 0x1bd0d5ff, 0x1ad2d3ff, 0x19d4d0ff, 0x18d6cdff, 0x18d8cbff, 0x18dac8ff, 0x17dbc5ff, 0x17ddc3ff, 0x17dfc0ff, 0x18e0beff, 0x18e2bbff, 0x19e3b9ff, 0x1ae5b7ff, 0x1be6b4ff, 0x1de8b2ff, 0x1ee9afff, 0x20eaadff, 0x22ecaaff, 0x24eda7ff, 0x27eea4ff, 0x29efa1ff, 0x2cf09eff, 0x2ff19bff, 0x32f298ff, 0x35f394ff, 0x38f491ff, 0x3cf58eff, 0x3ff68bff, 0x43f787ff, 0x46f884ff, 0x4af980ff, 0x4efa7dff, 0x51fa79ff, 0x55fb76ff, 0x59fc73ff, 0x5dfc6fff, 0x61fd6cff, 0x65fd69ff, 0x69fe65ff, 0x6dfe62ff, 0x71fe5fff, 0x75ff5cff, 0x79ff59ff, 0x7dff56ff, 0x80ff53ff, 0x84ff50ff, 0x88ff4eff, 0x8bff4bff, 0x8fff49ff, 0x92ff46ff, 0x96ff44ff, 0x99ff42ff, 0x9cfe40ff, 0x9ffe3eff, 0xa2fd3dff, 0xa4fd3bff, 0xa7fc3aff, 0xaafc39ff, 0xacfb38ff, 0xaffa37ff, 0xb1f936ff, 0xb4f835ff, 0xb7f835ff, 0xb9f634ff, 0xbcf534ff, 0xbff434ff, 0xc1f334ff, 0xc4f233ff, 0xc6f033ff, 0xc9ef34ff, 0xcbee34ff, 0xceec34ff, 0xd0eb34ff, 0xd2e934ff, 0xd5e835ff, 0xd7e635ff, 0xd9e435ff, 0xdbe236ff, 0xdde136ff, 0xe0df37ff, 0xe2dd37ff, 0xe4db38ff, 0xe6d938ff, 0xe7d738ff, 0xe9d539ff, 0xebd339ff, 0xedd139ff, 0xeecf3aff, 0xf0cd3aff, 0xf1cb3aff, 0xf3c93aff, 0xf4c73aff, 0xf5c53aff, 0xf7c33aff, 0xf8c13aff, 0xf9bf39ff, 0xfabd39ff, 0xfaba38ff, 0xfbb838ff, 0xfcb637ff, 0xfcb436ff, 0xfdb135ff, 0xfdaf35ff, 0xfeac34ff, 0xfea933ff, 0xfea732ff, 0xfea431ff, 0xffa12fff, 0xff9e2eff, 0xff9c2dff, 0xff992cff, 0xfe962bff, 0xfe932aff, 0xfe9028ff, 0xfe8d27ff, 0xfd8a26ff, 0xfd8724ff, 0xfc8423ff, 0xfc8122ff, 0xfb7e20ff, 0xfb7b1fff, 0xfa781eff, 0xf9751cff, 0xf8721bff, 0xf86f1aff, 0xf76c19ff, 0xf66917ff, 0xf56616ff, 0xf46315ff, 0xf36014ff, 0xf25d13ff, 0xf05b11ff, 0xef5810ff, 0xee550fff, 0xed530eff, 0xeb500eff, 0xea4e0dff, 0xe94b0cff, 0xe7490bff, 0xe6470aff, 0xe4450aff, 0xe34209ff, 0xe14009ff, 0xdf3e08ff, 0xde3c07ff, 0xdc3a07ff, 0xda3806ff, 0xd83606ff, 0xd63405ff, 0xd43205ff, 0xd23105ff, 0xd02f04ff, 0xce2d04ff, 0xcc2b03ff, 0xca2903ff, 0xc82803ff, 0xc62602ff, 0xc32402ff, 0xc12302ff, 0xbf2102ff, 0xbc1f01ff, 0xba1e01ff, 0xb71c01ff, 0xb41b01ff, 0xb21901ff, 0xaf1801ff, 0xac1601ff, 0xaa1501ff, 0xa71401ff, 0xa41201ff, 0xa11101ff, 0x9e1001ff, 0x9b0f01ff, 0x980d01ff, 0x950c01ff, 0x920b01ff, 0x8e0a01ff, 0x8b0901ff, 0x880801ff, 0x850701ff, 0x810602ff, 0x7e0502ff, 0x7a0402ff]

### original theme by teejez:
#waterfall_colors = [0x000000FF, 0x0000FFFF, 0x00FFFFFF, 0x00FF00FF, 0xFFFF00FF, 0xFF0000FF, 0xFF00FFFF, 0xFFFFFFFF]

### old theme by HA7ILM:
# waterfall_colors = "[0x000000ff,0x2e6893ff, 0x69a5d0ff, 0x214b69ff, 0x9dc4e0ff,  0xfff775ff, 0xff8a8aff, 0xb20000ff]"
# waterfall_min_level = -115 #in dB
# waterfall_max_level = 0
# waterfall_auto_level_margin = {"min": 20, "max": 30}
##For the old colors, you might also want to set [fft_voverlap_factor] to 0.

waterfall_min_level = -88  # in dB
waterfall_max_level = -20
waterfall_auto_level_margin = {"min": 5, "max": 10}

# Note: When the auto waterfall level button is clicked, the following happens:
#   [waterfall_min_level] = [current_min_power_level] - [waterfall_auto_level_margin["min"]]
#   [waterfall_max_level] = [current_max_power_level] + [waterfall_auto_level_margin["max"]]
#
#   ___|________________________________________|____________________________________|________________________________________|___> signal power
#        \_waterfall_auto_level_margin["min"]_/ |__ current_min_power_level          | \_waterfall_auto_level_margin["max"]_/
#                                                          current_max_power_level __|

# === Experimental settings ===
# Warning! The settings below are very experimental.
csdr_dynamic_bufsize = False  # This allows you to change the buffering mode of csdr.
csdr_print_bufsizes = False  # This prints the buffer sizes used for csdr processes.
csdr_through = False  # Setting this True will print out how much data is going into the DSP chains.

nmux_memory = 50  # in megabytes. This sets the approximate size of the circular buffer used by nmux.

google_maps_api_key = ""

# how long should positions be visible on the map?
# they will start fading out after half of that
# in seconds; default: 2 hours
map_position_retention_time = 2 * 60 * 60

# decoder queue configuration
# due to the nature of some operating modes (ft8, ft8, jt9, jt65, wspr and js8), the data is recorded for a given amount
# of time (6 seconds up to 2 minutes) and decoded at the end. this can lead to very high peak loads.
# to mitigate this, the recordings will be queued and processed in sequence.
# the number of workers will limit the total amount of work (one worker will losely occupy one cpu / thread)
decoding_queue_workers = 2
# the maximum queue length will cause decodes to be dumped if the workers cannot keep up
# if you are running background services, make sure this number is high enough to accept the task influx during peaks
# i.e. this should be higher than the number of decoding services running at the same time
decoding_queue_length = 10

# wsjt decoding depth will allow more results, but will also consume more cpu
wsjt_decoding_depth = 3
# can also be set for each mode separately
# jt65 seems to be somewhat prone to erroneous decodes, this setting handles that to some extent
wsjt_decoding_depths = {"jt65": 1}

# JS8 comes in different speeds: normal, slow, fast, turbo. This setting controls which ones are enabled.
js8_enabled_profiles = ["normal", "slow"]
# JS8 decoding depth; higher value will get more results, but will also consume more cpu
js8_decoding_depth = 3

temporary_directory = "/tmp"

services_enabled = False
services_decoders = ["ft8", "ft4", "wspr", "packet"]

# === aprs igate settings ===
# if you want to share your APRS decodes with the aprs network, configure these settings accordingly
aprs_callsign = "N0CALL"
aprs_igate_enabled = False
aprs_igate_server = "euro.aprs2.net"
aprs_igate_password = ""
# beacon uses the receiver_gps setting, so if you enable this, make sure the location is correct there
aprs_igate_beacon = False

# path to the aprs symbols repository (get it here: https://github.com/hessu/aprs-symbols)
aprs_symbols_path = "/opt/aprs-symbols/png"

# === PSK Reporter setting ===
# enable this if you want to upload all ft8, ft4 etc spots to pskreporter.info
# this also uses the receiver_gps setting from above, so make sure it contains a correct locator
pskreporter_enabled = False
pskreporter_callsign = "N0CALL"

# === Web admin settings ===
# this feature is experimental at the moment. it should not be enabled on shared receivers since it allows remote
# changes to the receiver settings. enable for testing in controlled environment only.
# webadmin_enabled = False
