import os
import subprocess
from functools import reduce
from operator import and_
import re
from distutils.version import LooseVersion
import inspect

import logging
logger = logging.getLogger(__name__)


class UnknownFeatureException(Exception):
    pass


class FeatureDetector(object):
    features = {
        "core": [ "csdr", "nmux", "nc" ],
        "rtl_sdr": [ "rtl_sdr" ],
        "sdrplay": [ "rx_tools" ],
        "hackrf": [ "hackrf_transfer" ],
        "airspy": [ "airspy_rx" ],
        "digital_voice_digiham": [ "digiham", "sox" ],
        "digital_voice_dsd": [ "dsd", "sox", "digiham" ],
        "wsjt-x": [ "wsjtx" ]
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
                "description": self.get_requirement_description(name)
            }

        def feature_details(name):
            return {
                "description": "",
                "available": self.is_available(name),
                "requirements": {name: requirement_details(name) for name in self.get_requirements(name)}
            }

        return {name: feature_details(name) for name in FeatureDetector.features}

    def is_available(self, feature):
        return self.has_requirements(self.get_requirements(feature))

    def get_requirements(self, feature):
        try:
            return FeatureDetector.features[feature]
        except KeyError:
            raise UnknownFeatureException("Feature \"{0}\" is not known.".format(feature))

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
        method = self._get_requirement_method(requirement)
        if method is not None:
            return method()
        else:
            logger.error("detection of requirement {0} not implement. please fix in code!".format(requirement))
        return False

    def get_requirement_description(self, requirement):
        return inspect.getdoc(self._get_requirement_method(requirement))

    def command_is_runnable(self, command):
        return os.system("{0} 2>/dev/null >/dev/null".format(command)) != 32512

    def has_csdr(self):
        """
        OpenWebRX uses the demodulator and pipeline tools provided by the csdr project. Please check out [the project
        page on github](https://github.com/simonyiszk/csdr) for further details and installation instructions.
        """
        return self.command_is_runnable("csdr")

    def has_nmux(self):
        """
        Nmux is another tool provided by the csdr project. It is used for internal multiplexing of the IQ data streams.
        If you're missing nmux even though you have csdr installed, please update your csdr version.
        """
        return self.command_is_runnable("nmux --help")

    def has_nc(self):
        """
        Nc is the client used to connect to the nmux multiplexer. It is provided by either the BSD netcat (recommended
        for better performance) or GNU netcat packages. Please check your distribution package manager for options.
        """
        return self.command_is_runnable('nc --help')

    def has_rtl_sdr(self):
        """
        The rtl-sdr command is required to read I/Q data from an RTL SDR USB-Stick. It is available in most
        distribution package managers.
        """
        return self.command_is_runnable("rtl_sdr --help")

    def has_rx_tools(self):
        """
        The rx_tools package can be used to interface with SDR devices compatible with SoapySDR. It is currently used
        to connect to SDRPlay devices. Please check the following pages for more details:

        * [rx_tools GitHub page](https://github.com/rxseger/rx_tools)
        * [SoapySDR Project wiki](https://github.com/pothosware/SoapySDR/wiki)
        * [SDRPlay homepage](https://www.sdrplay.com/)
        """
        return self.command_is_runnable("rx_sdr --help")

    def has_hackrf_transfer(self):
        """
        To use a HackRF, compile the HackRF host tools from its "stdout" branch:
        ```
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
        ```
        """
        # TODO i don't have a hackrf, so somebody doublecheck this.
        # TODO also check if it has the stdout feature
        return self.command_is_runnable("hackrf_transfer --help")

    def command_exists(self, command):
        return os.system("which {0}".format(command)) == 0

    def has_digiham(self):
        """
        To use digital voice modes, the digiham package is required. You can find the package and installation
        instructions [here](https://github.com/jketterl/digiham).

        Please note: there is close interaction between digiham and openwebrx, so older versions will probably not work.
        If you have an older verison of digiham installed, please update it along with openwebrx.
        As of now, we require version 0.2 of digiham.
        """
        required_version = LooseVersion("0.2")

        digiham_version_regex = re.compile('^digiham version (.*)$')
        def check_digiham_version(command):
            try:
                process = subprocess.Popen([command, "--version"], stdout=subprocess.PIPE)
                version = LooseVersion(digiham_version_regex.match(process.stdout.readline().decode()).group(1))
                process.wait(1)
                return version >= required_version
            except FileNotFoundError:
                return False
        return reduce(and_,
                      map(
                          check_digiham_version,
                          ["rrc_filter", "ysf_decoder", "dmr_decoder", "mbe_synthesizer", "gfsk_demodulator",
                           "digitalvoice_filter"]
                      ),
                      True)

    def has_dsd(self):
        """
        The digital voice modes NXDN and D-Star can be decoded by the dsd project. Please note that you need the version
        modified by F4EXB that provides stdin/stdout support. You can find it [here](https://github.com/f4exb/dsd).
        """
        return self.command_is_runnable("dsd")

    def has_sox(self):
        """
        The sox audio library is used to convert between the typical 8 kHz audio sampling rate used by digital modes and
        the audio sampling rate requested by the client.

        It is available for most distributions through the respective package manager.
        """
        return self.command_is_runnable("sox")

    def has_airspy_rx(self):
        """
        In order to use an Airspy Receiver, you need to install the airspy_rx receiver software.
        """
        return self.command_is_runnable("airspy_rx --help 2> /dev/null")

    def has_wsjtx(self):
        """
        To decode FT8 and other digimodes, you need to install the WSJT-X software suite. Please check the
        [WSJT-X homepage](https://physics.princeton.edu/pulsar/k1jt/wsjtx.html) for ready-made packages or instructions
        on how to build from source.
        """
        return self.command_is_runnable("jt9")
