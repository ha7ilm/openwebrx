**2019-11-24**
- There is now a new way to interface with SDR hardware, [owrx_connectors](https://github.com/jketterl/owrx_connector).
  They talk directly to the hardware (no rtl_sdr / rx_sdr necessary) and offer I/Q data on a socket, just like nmux
  did before. They additionally offer a control socket that allows openwebrx to control the SDR parameters directly,
  without the need for repeated restarts. This allows for quicker profile changes, and also reduces the risk of your
  SDR hardware from failing during the switchover. See `config_webrx.py` for further information and instructions.
- Offset tuning using the `lfo_offset` has been reworked in a way that `center_freq` has to be set to the frequency you
  actually want to listen to. If you're using an `lfo_offset` already, you will probably need to change its sign.
- `initial_squelch_level` can now be set on each profile.
- As usual, plenty of fixes and improvements.

**2019-10-27**
- Part of the frontend code has been reworked
  - Audio buffer minimums have been completely stripped. As a result, you should get better latency. Unfortunately,
    this also means there will be some skipping when audio starts.
  - Now also supports AudioWorklets (for those browser that have it). The Raspberry Pi image has been updated to include
    https due to the SecureContext requirement.
  - Mousewheel controls for the receiver sliders
- Error handling for failed SDR devices

**2019-09-29**
- One of the most-requested features is finally coming to OpenWebRX: Bookmarks (sometimes also referred to as labels).
  There's two kinds of bookmarks available:
  - Serverside bookmarks that are set up by the receiver administrator. Check the file `bookmarks.json` for examples!
  - Clientside bookmarks which every user can store for themselves. They are stored in the browser's localStorage.
- Some more bugs in the websocket handling have been fixed.

**2019-09-25**
- Automatic reporting of spots to [pskreporter](https://pskreporter.info/) is now possible. Please have a look at the
  configuration on how to set it up.
- Websocket communication has been overhauled in large parts. It should now be more reliable, and failing connections
  should now have no impact on other users.
- Profile scheduling allows to set up band-hopping if you are running background services.
- APRS now has the ability to show symbols on the map, if a corresponding symbol set has been installed. Check the
  config!
- Debug logging has been disabled in a handful of modules, expect vastly reduced output on the shell.

**2019-09-13**
- New set of APRS-related features
  - Decode Packet transmissions using [direwolf](https://github.com/wb2osz/direwolf) (1k2 only for now)
  - APRS packets are mostly decoded and shown both in a new panel and on the map
  - APRS is also available as a background service
  - direwolfs I-gate functionality can be enabled, which allows your receiver to work as a receive-only I-gate for the
    APRS network in the background
- Demodulation for background services has been optimized to use less total bandwidth, saving CPU
- More metrics have been added; they can be used together with collectd and its curl_json plugin for now, with some
  limitations.

**2019-07-21**
- Latest Features:
  - More WSJT-X modes have been added, including the new FT4 mode
  - I started adding a bandplan feature, the first thing visible is the "dial" indicator that brings you right to the
    dial frequency for digital modes
  - fixed some bugs in the websocket communication which broke the map

**2019-07-13**
- Latest Features:
  - FT8 Integration (using wsjt-x demodulators)
  - New Map Feature that shows both decoded grid squares from FT8 and Locations decoded from YSF digital voice
  - New Feature report that will show what functionality is available
- There's a new Raspbian SD Card image available (see below)

**2019-06-30**
- I have done some major rework on the openwebrx core, and I am planning to continue adding more features in the near
  future. Please check this place for updates.
- My work has not been accepted into the upstream repository, so you will need to chose between my fork and the official
  version.
- I have enabled the issue tracker on this project, so feel free to file bugs or suggest enhancements there!
- This version sports the following new and amazing features:
  - Support of multiple SDR devices simultaneously
  - Support for multiple profiles per SDR that allow the user to listen to different frequencies
  - Support for digital voice decoding
  - Feature detection that will disable functionality when dependencies are not available (if you're missing the digital
    buttons, this is probably why)
- Raspbian SD Card Images and Docker builds available (see below)
- I am currently working on the feature set for a stable release, but you are more than welcome to test development
  versions!
