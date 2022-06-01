import subprocess
from functools import reduce
from operator import and_
import re
from distutils.version import LooseVersion, StrictVersion
import inspect
from owrx.config.core import CoreConfig
from owrx.config import Config
import shlex
import os
from datetime import datetime, timedelta

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UnknownFeatureException(Exception):
    pass


class FeatureCache(object):
    sharedInstance = None

    @staticmethod
    def getSharedInstance():
        if FeatureCache.sharedInstance is None:
            FeatureCache.sharedInstance = FeatureCache()
        return FeatureCache.sharedInstance

    def __init__(self):
        self.cache = {}
        self.cachetime = timedelta(hours=2)

    def has(self, feature):
        if feature not in self.cache:
            return False
        now = datetime.now()
        if self.cache[feature]["valid_to"] < now:
            return False
        return True

    def get(self, feature):
        return self.cache[feature]["value"]

    def set(self, feature, value):
        valid_to = datetime.now() + self.cachetime
        self.cache[feature] = {"value": value, "valid_to": valid_to}


class FeatureDetector(object):
    features = {
        # core features; we won't start without these
        "core": ["csdr"],
        # different types of sdrs and their requirements
        "rtl_sdr": ["rtl_connector"],
        "rtl_sdr_soapy": ["soapy_connector", "soapy_rtl_sdr"],
        "rtl_tcp": ["rtl_tcp_connector"],
        "sdrplay": ["soapy_connector", "soapy_sdrplay"],
        "hackrf": ["soapy_connector", "soapy_hackrf"],
        "perseussdr": ["perseustest", "nmux"],
        "airspy": ["soapy_connector", "soapy_airspy"],
        "airspyhf": ["soapy_connector", "soapy_airspyhf"],
        "lime_sdr": ["soapy_connector", "soapy_lime_sdr"],
        "fifi_sdr": ["alsa", "rockprog", "nmux"],
        "pluto_sdr": ["soapy_connector", "soapy_pluto_sdr"],
        "soapy_remote": ["soapy_connector", "soapy_remote"],
        "uhd": ["soapy_connector", "soapy_uhd"],
        "radioberry": ["soapy_connector", "soapy_radioberry"],
        "fcdpp": ["soapy_connector", "soapy_fcdpp"],
        "bladerf": ["soapy_connector", "soapy_bladerf"],
        "sddc": ["sddc_connector"],
        "hpsdr": ["hpsdr_connector"],
        "runds": ["runds_connector"],
        # optional features and their requirements
        "digital_voice_digiham": ["digiham", "codecserver_ambe"],
        "digital_voice_freedv": ["freedv_rx"],
        "digital_voice_m17": ["m17_demod", "digiham"],
        "wsjt-x": ["wsjtx"],
        "wsjt-x-2-3": ["wsjtx_2_3"],
        "wsjt-x-2-4": ["wsjtx_2_4"],
        "packet": ["direwolf"],
        "pocsag": ["digiham"],
        "js8call": ["js8", "js8py"],
        "drm": ["dream"],
    }

    def feature_availability(self):
        return {name: self.is_available(name) for name in FeatureDetector.features}

    def feature_report(self):
        def requirement_details(name):
            available = self.has_requirement(name)
            return {
                "available": available,
                # as of now, features are always enabled as soon as they are available. this may change in the future.
                "enabled": available,
                "description": self.get_requirement_description(name),
            }

        def feature_details(name):
            return {
                "available": self.is_available(name),
                "requirements": {name: requirement_details(name) for name in self.get_requirements(name)},
            }

        return {name: feature_details(name) for name in FeatureDetector.features}

    def is_available(self, feature):
        return self.has_requirements(self.get_requirements(feature))

    def get_failed_requirements(self, feature):
        return [req for req in self.get_requirements(feature) if not self.has_requirement(req)]

    def get_requirements(self, feature):
        try:
            return FeatureDetector.features[feature]
        except KeyError:
            raise UnknownFeatureException('Feature "{0}" is not known.'.format(feature))

    def has_requirements(self, requirements):
        passed = True
        for requirement in requirements:
            passed = passed and self.has_requirement(requirement)
        return passed

    def _get_requirement_method(self, requirement):
        methodname = "has_" + requirement
        if hasattr(self, methodname) and callable(getattr(self, methodname)):
            return getattr(self, methodname)
        return None

    def has_requirement(self, requirement):
        cache = FeatureCache.getSharedInstance()
        if cache.has(requirement):
            return cache.get(requirement)

        logger.debug("performing feature check for %s", requirement)
        method = self._get_requirement_method(requirement)
        result = False
        if method is not None:
            result = method()
        else:
            logger.error("detection of requirement {0} not implement. please fix in code!".format(requirement))
        logger.debug("feature check for %s complete. result: %s", requirement, result)

        cache.set(requirement, result)
        return result

    def get_requirement_description(self, requirement):
        return inspect.getdoc(self._get_requirement_method(requirement))

    def command_is_runnable(self, command, expected_result=None):
        tmp_dir = CoreConfig().get_temporary_directory()
        cmd = shlex.split(command)
        env = os.environ.copy()
        # prevent X11 programs from opening windows if called from a GUI shell
        env.pop("DISPLAY", None)
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=tmp_dir,
                env=env,
            )
            rc = process.wait()
            if expected_result is None:
                return rc != 32512
            else:
                return rc == expected_result
        except FileNotFoundError:
            return False

    def has_csdr(self):
        """
        OpenWebRX uses the demodulator and pipeline tools provided by the csdr project. Please check out [the project
        page on github](https://github.com/jketterl/csdr) for further details and installation instructions.

        In addition, the [pycsdr](https://github.com/jketterl/pycsdr) package must be installed to provide
        python bindings for the csdr library.
        """
        required_version = LooseVersion("0.18.0")

        try:
            from pycsdr.modules import csdr_version
            from pycsdr.modules import version as pycsdr_version

            return (
                LooseVersion(csdr_version) >= required_version and
                LooseVersion(pycsdr_version) >= required_version
            )
        except ImportError:
            return False

    def has_nmux(self):
        """
        Nmux is another tool provided by the csdr project. It is used for internal multiplexing of the IQ data streams.
        If you're missing nmux even though you have csdr installed, please update your csdr version.
        """
        return self.command_is_runnable("nmux --help")

    def has_perseustest(self):
        """
        To use a Microtelecom Perseus HF receiver, compile and
        install the libperseus-sdr:
        ```
         sudo apt install libusb-1.0-0-dev
         cd /tmp
         wget https://github.com/Microtelecom/libperseus-sdr/releases/download/v0.8.2/libperseus_sdr-0.8.2.tar.gz
         tar -zxvf libperseus_sdr-0.8.2.tar.gz
         cd libperseus_sdr-0.8.2/
         ./configure
         make
         sudo make install
         sudo ldconfig
         perseustest
        ```
        """
        return self.command_is_runnable("perseustest -h")

    def has_digiham(self):
        """
        To use digital voice modes, the digiham package is required. You can find the package and installation
        instructions [here](https://github.com/jketterl/digiham).

        In addition, the [pydigiham](https://github.com/jketterl/pydigiham) package must be installed to provide
        python bindings for the digiham library.

        Please note: there is close interaction between digiham and openwebrx, so older versions will probably not work.
        If you have an older verison of digiham installed, please update it along with openwebrx.
        As of now, we require version 0.6 of digiham.
        """
        required_version = LooseVersion("0.6")

        try:
            from digiham.modules import digiham_version as digiham_version
            from digiham.modules import version as pydigiham_version

            return (
                LooseVersion(digiham_version) >= required_version
                and LooseVersion(pydigiham_version) >= required_version
            )
        except ImportError:
            return False

    def _check_connector(self, command, required_version):
        owrx_connector_version_regex = re.compile("^{} version (.*)$".format(re.escape(command)))

        try:
            process = subprocess.Popen([command, "--version"], stdout=subprocess.PIPE)
            matches = owrx_connector_version_regex.match(process.stdout.readline().decode())
            if matches is None:
                return False
            version = LooseVersion(matches.group(1))
            process.wait(1)
            return version >= required_version
        except FileNotFoundError:
            return False

    def _check_owrx_connector(self, command):
        return self._check_connector(command, LooseVersion("0.5"))

    def has_rtl_connector(self):
        """
        The owrx_connector package offers direct interfacing between your hardware and openwebrx. It allows quicker
        frequency switching, uses less CPU and can even provide more stability in some cases.

        You can get it [here](https://github.com/jketterl/owrx_connector).
        """
        return self._check_owrx_connector("rtl_connector")

    def has_rtl_tcp_connector(self):
        """
        The owrx_connector package offers direct interfacing between your hardware and openwebrx. It allows quicker
        frequency switching, uses less CPU and can even provide more stability in some cases.

        You can get it [here](https://github.com/jketterl/owrx_connector).
        """
        return self._check_owrx_connector("rtl_tcp_connector")

    def has_soapy_connector(self):
        """
        The owrx_connector package offers direct interfacing between your hardware and openwebrx. It allows quicker
        frequency switching, uses less CPU and can even provide more stability in some cases.

        You can get it [here](https://github.com/jketterl/owrx_connector).
        """
        return self._check_owrx_connector("soapy_connector")

    def _has_soapy_driver(self, driver):
        try:
            process = subprocess.Popen(["SoapySDRUtil", "--info"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            factory_regex = re.compile("^Available factories\\.\\.\\. ?(.*)$")

            drivers = []
            for line in process.stdout:
                matches = factory_regex.match(line.decode())
                if matches:
                    drivers = [s.strip() for s in matches.group(1).split(", ")]

            return driver in drivers
        except FileNotFoundError:
            return False

    def has_soapy_rtl_sdr(self):
        """
        The SoapySDR module for rtl-sdr devices can be used as an alternative to the rtl_connector. It provides
        additional support for the direct sampling mod.

        You can get it [here](https://github.com/pothosware/SoapyRTLSDR/wiki).
        """
        return self._has_soapy_driver("rtlsdr")

    def has_soapy_sdrplay(self):
        """
        The SoapySDR module for sdrplay devices is required for interfacing with SDRPlay devices (RSP1*, RSP2*, RSPDuo)

        You can get it [here](https://github.com/SDRplay/SoapySDRPlay).
        """
        return self._has_soapy_driver("sdrplay")

    def has_soapy_airspy(self):
        """
        The SoapySDR module for airspy devices is required for interfacing with Airspy devices (Airspy R2, Airspy Mini).

        You can get it [here](https://github.com/pothosware/SoapyAirspy/wiki).
        """
        return self._has_soapy_driver("airspy")

    def has_soapy_airspyhf(self):
        """
        The SoapySDR module for airspyhf devices is required for interfacing with Airspy HF devices (Airspy HF+,
        Airspy HF discovery).

        You can get it [here](https://github.com/pothosware/SoapyAirspyHF/wiki).
        """
        return self._has_soapy_driver("airspyhf")

    def has_soapy_lime_sdr(self):
        """
        The Lime Suite installs - amongst others - a Soapy driver for the LimeSDR device series.

        You can get it [here](https://github.com/myriadrf/LimeSuite).
        """
        return self._has_soapy_driver("lime")

    def has_soapy_pluto_sdr(self):
        """
        The SoapySDR module for PlutoSDR devices is required for interfacing with PlutoSDR devices.

        You can get it [here](https://github.com/pothosware/SoapyPlutoSDR).
        """
        return self._has_soapy_driver("plutosdr")

    def has_soapy_remote(self):
        """
        The SoapyRemote allows the usage of remote SDR devices using the SoapySDRServer.

        You can get the code and find additional information [here](https://github.com/pothosware/SoapyRemote/wiki).
        """
        return self._has_soapy_driver("remote")

    def has_soapy_uhd(self):
        """
        The SoapyUHD module allows using UHD / USRP devices with SoapySDR.

        You can get it [here](https://github.com/pothosware/SoapyUHD/wiki).
        """
        return self._has_soapy_driver("uhd")

    def has_soapy_radioberry(self):
        """
        The Radioberry is a SDR hat for the Raspberry Pi.

        You can find more information, along with its SoapySDR module [here](https://github.com/pa3gsb/Radioberry-2.x).
        """
        return self._has_soapy_driver("radioberry")

    def has_soapy_hackrf(self):
        """
        The SoapyHackRF allows HackRF to be used with SoapySDR.

        You can get it [here](https://github.com/pothosware/SoapyHackRF/wiki).
        """
        return self._has_soapy_driver("hackrf")

    def has_soapy_fcdpp(self):
        """
        The SoapyFCDPP module allows the use of the Funcube Dongle Pro+.

        You can get it [here](https://github.com/pothosware/SoapyFCDPP).
        """
        return self._has_soapy_driver("fcdpp")

    def has_soapy_bladerf(self):
        """
        The SoapyBladeRF module allows the use of Blade RF devices.

        You can get it [here](https://github.com/pothosware/SoapyBladeRF).
        """
        return self._has_soapy_driver("bladerf")

    def has_m17_demod(self):
        """
        The `m17-demod` tool is used to demodulate M17 digital voice signals.

        You can find more information [here](https://github.com/mobilinkd/m17-cxx-demod)
        """
        return self.command_is_runnable("m17-demod")

    def has_direwolf(self):
        """
        OpenWebRX uses the [direwolf](https://github.com/wb2osz/direwolf) software modem to decode Packet Radio and
        report data back to APRS-IS. Direwolf is available from the package manager on many distributions, or you can
        compile it from source.
        """
        return self.command_is_runnable("direwolf --help")

    def has_airspy_rx(self):
        """
        In order to use an Airspy Receiver, you need to install the airspy_rx receiver software.
        """
        return self.command_is_runnable("airspy_rx --help")

    def has_wsjtx(self):
        """
        To decode FT8 and other digimodes, you need to install the WSJT-X software suite. Please check the
        [WSJT-X homepage](https://physics.princeton.edu/pulsar/k1jt/wsjtx.html) for ready-made packages or instructions
        on how to build from source.
        """
        return reduce(and_, map(self.command_is_runnable, ["jt9", "wsprd"]), True)

    def _has_wsjtx_version(self, required_version):
        wsjt_version_regex = re.compile("^WSJT-X (.*)$")

        try:
            process = subprocess.Popen(["wsjtx_app_version", "--version"], stdout=subprocess.PIPE)
            matches = wsjt_version_regex.match(process.stdout.readline().decode())
            if matches is None:
                return False
            version = LooseVersion(matches.group(1))
            process.wait(1)
            return version >= required_version
        except FileNotFoundError:
            return False

    def has_wsjtx_2_3(self):
        """
        Newer digital modes (e.g. FST4, FST4) require WSJT-X in at least version 2.3.
        """
        return self.has_wsjtx() and self._has_wsjtx_version(LooseVersion("2.3"))

    def has_wsjtx_2_4(self):
        """
        WSJT-X version 2.4 introduced the Q65 mode.
        """
        return self.has_wsjtx() and self._has_wsjtx_version(LooseVersion("2.4"))

    def has_js8(self):
        """
        To decode JS8, you will need to install [JS8Call](http://js8call.com/)

        Please note that the `js8` command line decoder is not made available on $PATH by some JS8Call package builds.
        You will need to manually make it available by either linking it to `/usr/bin` or by adding its location to
        $PATH.
        """
        return self.command_is_runnable("js8")

    def has_js8py(self):
        """
        The js8py library is used to decode binary JS8 messages into readable text. More information is available on
        [its github page](https://github.com/jketterl/js8py).
        """
        required_version = StrictVersion("0.1")
        try:
            from js8py.version import strictversion

            return strictversion >= required_version
        except ImportError:
            return False

    def has_alsa(self):
        """
        Some SDR receivers are identifying themselves as a soundcard. In order to read their data, OpenWebRX relies
        on the Alsa library. It is available as a package for most Linux distributions.
        """
        return self.command_is_runnable("arecord --help")

    def has_rockprog(self):
        """
        The "rockprog" executable is required to send commands to your FiFiSDR. It needs to be installed separately.

        You can find instructions and downloads [here](https://o28.sischa.net/fifisdr/trac/wiki/De%3Arockprog).
        """
        return self.command_is_runnable("rockprog")

    def has_freedv_rx(self):
        """
        The "freedv\_rx" executable is required to demodulate FreeDV digital transmissions. It comes together with the
        codec2 library, but it's only a supplemental part and not installed by default or contained in its packages.
        To install it, you will need to compile codec2 from source and manually install freedv\_rx.

        Detailed installation instructions are available on the
        [OpenWebRX wiki](https://github.com/jketterl/openwebrx/wiki/FreeDV-demodulator-notes).
        """
        return self.command_is_runnable("freedv_rx")

    def has_dream(self):
        """
        In order to be able to decode DRM broadcasts, OpenWebRX needs the "dream" DRM decoder.

        The version supplied by most distributions will not work properly on the command line, so compiling from source
        with a custom set of commands is recommended. Detailed installation instructions are available on the
        [OpenWebRX wiki](https://github.com/jketterl/openwebrx/wiki/DRM-demodulator-notes).
        """
        return self.command_is_runnable("dream --help", 0)

    def has_sddc_connector(self):
        """
        The sddc_connector allows connectivity with SDR devices powered by libsddc, e.g. RX666, RX888, HF103.

        You can find more information [here](https://github.com/jketterl/sddc_connector).
        """
        return self._check_connector("sddc_connector", LooseVersion("0.1"))

    def has_hpsdr_connector(self):
        """
        In order to use the HPSDR connector, you will need to install [hpsdrconnector]
        (https://github.com/jancona/hpsdrconnector).
        """
        return self.command_is_runnable("hpsdrconnector -h")

    def has_runds_connector(self):
        """
        To use radios supporting R&S radios via EB200 or Ammos, you need to install the runds_connector.

        You can find more information [here](https://github.com/jketterl/runds_connector).
        """
        return self._check_connector("runds_connector", LooseVersion("0.2"))

    def has_codecserver_ambe(self):
        """
        Codecserver is used to decode audio data from digital voice modes using the AMBE codec.

        You can find more information [here](https://github.com/jketterl/codecserver).
        """

        config = Config.get()
        server = ""
        if "digital_voice_codecserver" in config:
            server = config["digital_voice_codecserver"]
        try:
            from digiham.modules import MbeSynthesizer

            return MbeSynthesizer.hasAmbe(server)
        except ImportError:
            return False
        except ConnectionError:
            return False
