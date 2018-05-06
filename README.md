OpenWebRX
=========

[:floppy_disk: Setup guide for Ubuntu](http://blog.sdr.hu/2015/06/30/quick-setup-openwebrx.html)  |  [:blue_book: Knowledge base on the Wiki](https://github.com/simonyiszk/openwebrx/wiki/)  |  [:earth_americas: Receivers on SDR.hu](http://sdr.hu/) 

OpenWebRX is a multi-user SDR receiver software with a web interface.

![OpenWebRX](http://blog.sdr.hu/images/openwebrx/screenshot.png)

It has the following features:

- <a href="https://github.com/simonyiszk/csdr">csdr</a> based demodulators (AM/FM/SSB/CW/BPSK31),
- filter passband can be set from GUI,
- waterfall display can be shifted back in time,
- it extensively uses HTML5 features like WebSocket, Web Audio API, and &lt;canvas&gt;,
- it works in Google Chrome, Chromium (above version 37) and Mozilla Firefox (above version 28),
- currently supports RTL-SDR, HackRF, SDRplay, AirSpy and many other devices, see the <a href="https://github.com/simonyiszk/openwebrx/wiki/">OpenWebRX Wiki</a>,
- it has a 3D waterfall display:

![OpenWebRX 3D waterfall](http://blog.sdr.hu/images/openwebrx/screenshot-3d.gif)

**News (2015-08-18)**
- My BSc. thesis written on OpenWebRX is <a href="https://sdr.hu/static/bsc-thesis.pdf">available here.</a>
- Several bugs were fixed to improve reliability and stability.
- OpenWebRX now supports compression of audio and waterfall stream, so the required network uplink bandwidth has been decreased from 2 Mbit/s to about 200 kbit/s per client! (Measured with the default settings. It is also dependent on `fft_size`.)
- OpenWebRX now uses <a href="https://github.com/simonyiszk/csdr#sdrjs">sdr.js</a> (*libcsdr* compiled to JavaScript) for some client-side DSP tasks. 
- Receivers can now be listed on <a href="http://sdr.hu/">SDR.hu</a>.
- License for OpenWebRX is now Affero GPL v3. 

**News (2016-02-14)**
- The DDC in *csdr* has been manually optimized for ARM NEON, so it runs around 3 times faster on the Raspberry Pi 2 than before. 
- Also we use *ncat* instead of *rtl_mus*, and it is 3 times faster in some cases.
- OpenWebRX now supports URLs like: `http://localhost:8073/#freq=145555000,mod=usb`
- UI improvements were made, thanks to John Seamons and Gnoxter.

**News (2017-04-04)**
- *ncat* has been replaced with a custom implementation called *nmux* due to a bug that caused regular crashes on some machines. The *nmux* tool is part of the *csdr* package.
- Most consumer SDR devices are supported via <a href="https://github.com/rxseger/rx_tools">rx_tools</a>, see the <a href="https://github.com/simonyiszk/openwebrx/wiki/Using-rx_tools-with-OpenWebRX">OpenWebRX Wiki</a> on that.

**News (2017-07-12)**
- OpenWebRX now has a BPSK31 demodulator and a 3D waterfall display.

> When upgrading OpenWebRX, please make sure that you also upgrade *csdr*!

## OpenWebRX servers on SDR.hu

[SDR.hu](http://sdr.hu) is a site which lists the active, public OpenWebRX servers. Your receiver [can also be part of it](http://sdr.hu/openwebrx), if you want.

![sdr.hu](http://blog.sdr.hu/images/openwebrx/screenshot-sdrhu.png)

## Setup

OpenWebRX currently requires Linux and python 2.7 to run. 

First you will need to install the dependencies:

- <a href="https://github.com/simonyiszk/csdr">libcsdr</a>
- <a href="http://sdr.osmocom.org/trac/wiki/rtl-sdr">rtl-sdr</a>

After cloning this repository and connecting an RTL-SDR dongle to your computer, you can run the server:

	python openwebrx.py

You can now open the GUI at <a href="http://localhost:8073">http://localhost:8073</a>.

Please note that the server is also listening on the following ports (on localhost only):

- port 4951 for the multi-user I/Q server.

Now the next step is to customize the parameters of your server in `config_webrx.py`.

Actually, if you do something cool with OpenWebRX, please drop me a mail:  
*Andras Retzler, HA7ILM &lt;randras@sdr.hu&gt;*

## Usage tips

You can zoom the waterfall display by the mouse wheel. You can also drag the waterfall to pan across it.

The filter envelope can be dragged at its ends and moved around to set the passband.

However, if you hold down the shift key, you can drag the center line (BFO) or the whole passband (PBS).

## Setup tips

If you have any problems installing OpenWebRX, you should check out the <a href="https://github.com/simonyiszk/openwebrx/wiki">Wiki</a> about it, which has a page on the <a href="https://github.com/simonyiszk/openwebrx/wiki/Common-problems-and-their-solutions">common problems and their solutions</a>.

Sometimes the actual error message is not at the end of the terminal output, you may have to look at the whole output to find it.

If you want to run OpenWebRX on a remote server instead of *localhost*, do not forget to set *server_hostname* in `config_webrx.py`.

## Licensing

OpenWebRX is available under Affero GPL v3 license (<a href="https://tldrlegal.com/license/gnu-affero-general-public-license-v3-(agpl-3.0)">summary</a>).

OpenWebRX is also available under a commercial license on request. Please contact me at the address *&lt;randras@sdr.hu&gt;* for licensing options. 
