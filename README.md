OpenWebRX
=========

OpenWebRX is a multi-user SDR receiver software with a web interface.

![OpenWebRX](/screenshot.jpg?raw=true)

It has the following features:

- <a href="https://github.com/simonyiszk/csdr">libcsdr</a> based demodulators (AM/FM/SSB),
- filter passband can be set from GUI,
- waterfall display can be shifted back in time,
- it extensively uses HTML5 features like WebSocket, Web Audio API, and &lt;canvas&gt;.
- it works in Google Chrome, Chromium (above version 37) and Mozilla Firefox (above version 28),
- currently only supports RTL-SDR, but other SDR hardware may be easily added.

## Setup

OpenWebRX currently requires a Linux machine to run. 

First you will need to install the dependencies:

- <a href="https://github.com/simonyiszk/csdr">libcsdr</a>
- <a href="http://sdr.osmocom.org/trac/wiki/rtl-sdr">rtl-sdr</a>

After cloning this repository and connecting an RTL-SDR dongle to your computer, you can run the server:

	python openwebrx.py

You can now open the GUI at <a href="http://localhost:8073">http://localhost:8073</a>.

Please note that the server is also listening on the following ports (on localhost only):

- port 8888 for the I/Q source,
- port 4951 for the multi-user I/Q server.

Now the next step is to customize the parameters of your server in `config_webrx.py`.

Actually, if you do something cool with OpenWebRX (or just have a problem), please drop me a mail:  
*Andras Retzler, HA7ILM &lt;randras@sdr.hu&gt;*

I would like to maintain a list of online amateur radio receivers on <a href="http://sdr.hu/">sdr.hu</a>.

## Usage tips

The filter envelope can be dragged at its ends and moved around to set the passband.

However, if you hold the shift key, you can drag the center line (BFO) or the whole passband (PBS).

## Configuration tips

If you want to run OpenWebRX on a remote server instead of localhost, do not forget to set *server_hostname* in `config_webrx.py`, or you may get a WebSocket error.

DSP CPU usage can be fine-tuned in `plugins/dsp/csdr/plugin.py`: you can set transition bandwidths higher (thus degrade filter performance by decreasing the length of the kernel, but also decrease CPU usage).

## Todo

Currently, clients use up a lot of bandwidth. This will be improved later.
