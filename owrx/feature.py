import os

import logging
logger = logging.getLogger(__name__)


class UnknownFeatureException(Exception):
    pass

class FeatureDetector(object):
    features = {
        "core": [ "csdr", "nmux" ],
        "rtl_sdr": [ "rtl_sdr" ],
        "sdrplay": [ "rx_tools" ],
        "hackrf": [ "hackrf_transfer" ]
    }

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
            methodname = "has_" + requirement
            if hasattr(self, methodname) and callable(getattr(self, methodname)):
                passed = passed and getattr(self, methodname)()
            else:
                logger.error("detection of requirement {0} not implement. please fix in code!".format(requirement))
        return passed

    def has_csdr(self):
        return os.system("csdr 2> /dev/null") != 32512

    def has_nmux(self):
        return os.system("nmux --help 2> /dev/null") != 32512

    def has_rtl_sdr(self):
        return os.system("rtl_sdr --help 2> /dev/null") != 32512

    def has_rx_tools(self):
        return os.system("rx_sdr --help 2> /dev/null") != 32512

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
    def has_hackrf_transfer(self):
        # TODO i don't have a hackrf, so somebody doublecheck this.
        # TODO also check if it has the stdout feature
        return os.system("hackrf_transfer --help 2> /dev/null") != 32512
