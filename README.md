OpenWebRX
=========

[:floppy_disk: Setup guide for Ubuntu](http://blog.sdr.hu/2015/06/30/quick-setup-openwebrx.html)  |  [:blue_book: Knowledge base on the Wiki](https://github.com/simonyiszk/openwebrx/wiki/)  |  [:earth_americas: Receivers on SDR.hu](http://sdr.hu/) 

OpenWebRX is a multi-user SDR receiver software with a web interface.

![OpenWebRX](http://blog.sdr.hu/images/openwebrx/screenshot.png)

It has the following features:

- [csdr](https://github.com/jketterl/csdr) based demodulators (AM/FM/SSB/CW/BPSK31),
- filter passband can be set from GUI,
- it extensively uses HTML5 features like WebSocket, Web Audio API, and Canvas
- it works in Google Chrome, Chromium and Mozilla Firefox
- currently supports RTL-SDR, HackRF, SDRplay, AirSpy
- Multiple SDR devices can be used simultaneously
- [digiham](https://github.com/jketterl/digiham) based demodularors (DMR, YSF)
- [dsd](https://github.com/f4exb/dsdcc) based demodulators (D-Star, NXDN)
- [wsjt-x](https://physics.princeton.edu/pulsar/k1jt/wsjtx.html) based demodulators (FT8, FT4, WSPR, JT65, JT9)

## OpenWebRX servers on SDR.hu

[SDR.hu](http://sdr.hu) is a site which lists the active, public OpenWebRX servers. Your receiver [can also be part of it](http://sdr.hu/openwebrx), if you want.

![sdr.hu](http://blog.sdr.hu/images/openwebrx/screenshot-sdrhu.png)

## Setup

### Raspberry Pi SD Card Images

Probably the quickest way to get started is to download the [latest Raspberry Pi SD Card Image](https://s3.eu-central-1.amazonaws.com/de.dd5jfk.openwebrx/2019-11-24-OpenWebRX-full.zip). It contains all the depencencies out of the box, and should work on all Raspberries up to the 3B+.

This is based off the Raspbian Lite distribution, so [their installation instructions](https://www.raspberrypi.org/documentation/installation/installing-images/) apply.

Please note: I have not updated this to include the Raspberry Pi 4 yet. (It seems to be impossible to build Rasbpian Buster images on x86 hardware right now. Stay tuned!)

Once you have booted a Raspberry with the SD Card, it will appear in your network with the hostname "openwebrx", which should make it available as https://openwebrx/ on most networks. This may vary depending on your specific setup.

For Digital voice, the minimum requirement right now seems to be a Rasbperry Pi 3B+. I would like to work on optimizing this for lower specs, but at this point I am not sure how much can be done. 

### Docker Images

For those familiar with docker, I am providing [recent builds and Releases for both x86 and arm processors on the Docker hub](https://hub.docker.com/r/jketterl/openwebrx). You can find a short introduction there.

### Manual Installation

OpenWebRX currently requires Linux and python >= 3.6 to run. 

First you will need to install the dependencies:

- [csdr](https://github.com/jketterl/csdr)
- [rtl-sdr](http://sdr.osmocom.org/trac/wiki/rtl-sdr)

Optional dependency for improved hardware access (to become mandatory at some point):

- [owrx_connector](https://github.com/jketterl/owrx_connector)

Optional dependencies if you want to be able to listen do digital voice:

- [digiham](https://github.com/jketterl/digiham)
- [dsd](https://github.com/f4exb/dsdcc)

Optional dependency if you want to decode WSJT-X modes:

- [wsjt-x](https://physics.princeton.edu/pulsar/k1jt/wsjtx.html)

After cloning this repository and connecting an RTL-SDR dongle to your computer, you can run the server:

	./openwebrx.py
	
You can now open the GUI at <a href="http://localhost:8073">http://localhost:8073</a>.

Please note that the server is also listening on the following ports (on localhost only):

- ports 4950 to 4960 for the multi-user I/Q servers.

Now the next step is to customize the parameters of your server in `config_webrx.py`.

Actually, if you do something cool with OpenWebRX, please drop me a mail:  
*Jakob Ketterl, DD5JFK &lt;dd5jfk@darc.de&gt;*

## Usage tips

You can zoom the waterfall display by the mouse wheel. You can also drag the waterfall to pan across it.

The filter envelope can be dragged at its ends and moved around to set the passband.

However, if you hold down the shift key, you can drag the center line (BFO) or the whole passband (PBS).

## Setup tips

If you have any problems installing OpenWebRX, you should check out the <a href="https://github.com/simonyiszk/openwebrx/wiki">Wiki</a> about it, which has a page on the <a href="https://github.com/simonyiszk/openwebrx/wiki/Common-problems-and-their-solutions">common problems and their solutions</a>.

Sometimes the actual error message is not at the end of the terminal output, you may have to look at the whole output to find it.

## Licensing

OpenWebRX is available under Affero GPL v3 license (<a href="https://tldrlegal.com/license/gnu-affero-general-public-license-v3-(agpl-3.0)">summary</a>).

OpenWebRX is also available under a commercial license on request. Please contact me at the address *&lt;randras@sdr.hu&gt;* for licensing options. 
