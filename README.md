OpenWebRX
=========

OpenWebRX is a multi-user SDR receiver software with a web interface.

![OpenWebRX](/screenshot.png?raw=true)

It has the following features:

- <a href="https://github.com/simonyiszk/csdr">libcsdr</a> based demodulators (AM/FM/SSB),
- filter passband can be set from GUI,
- waterfall display can be shifted back in time,
- it extensively uses HTML5 features like WebSocket, Web Audio API, and &lt;canvas&gt;.
- it works in Google Chrome, Chromium (above version 37) and Mozilla Firefox (above version 28),
- currently supports RTL-SDR and HackRF; other SDR hardware may be easily added.

**News:**
- My BSc. thesis written on OpenWebRX is <a href="http://openwebrx.org/bsc-thesis.pdf">available here.</a>
- Several bugs were fixed to improve reliability and stability.
- OpenWebRX now supports compression of audio and waterfall stream, so the required network uplink bandwidth has been decreased from 2 Mbit/s to about 200 kbit/s per client! (Measured with the default settings. It is also dependent on `fft_size`.)
- OpenWebRX now uses <a href="https://github.com/simonyiszk/csdr#sdrjs">sdr.js</a> (*libcsdr* compiled to JavaScript) for some client-side DSP tasks. 
- Receivers can now be listed on <a href="http://sdr.hu/">sdr.hu</a>.
- License for OpenWebRX is now Affero GPL v3. 

## Setup

OpenWebRX currently requires Linux and python 2.7 to run. 

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

## Usage tips

You can zoom the waterfall display by the mouse wheel. You can also drag the waterfall to pan across it.

The filter envelope can be dragged at its ends and moved around to set the passband.

However, if you hold down the shift key, you can drag the center line (BFO) or the whole passband (PBS).

## Setup tips

If you have any problems installing OpenWebRX, you should check out the <a href="https://github.com/simonyiszk/openwebrx/wiki">Wiki</a> about it, which has a page on the <a href="https://github.com/simonyiszk/openwebrx/wiki/Common-problems-and-their-solutions">common problems and their solutions</a>.

Sometimes the actual error message is not at the end of the terminal output, you may have to look at the whole output to find it.

If you want to run OpenWebRX on a remote server instead of localhost, do not forget to set *server_hostname* in `config_webrx.py`.
