import os

import logging
logger = logging.getLogger(__name__)

class Property(object):
    def __init__(self, value = None):
        self.value = value
        self.callbacks = []
    def getValue(self):
        return self.value
    def setValue(self, value):
        if (self.value == value):
            return self
        self.value = value
        for c in self.callbacks:
            try:
                c(self.value)
            except Exception as e:
                logger.exception(e)
        return self
    def wire(self, callback):
        self.callbacks.append(callback)
        if not self.value is None: callback(self.value)
        return self

class PropertyManager(object):
    sharedInstance = None
    @staticmethod
    def getSharedInstance():
        if PropertyManager.sharedInstance is None:
            PropertyManager.sharedInstance = PropertyManager()
        return PropertyManager.sharedInstance

    def collect(self, *props):
        return PropertyManager(dict((name, self.getProperty(name) if self.hasProperty(name) else Property()) for name in props))

    def __init__(self, properties = None):
        self.properties = {}
        self.callbacks = []
        if properties is not None:
            for (name, prop) in properties.items():
                self.add(name, prop)

    def add(self, name, prop):
        self.properties[name] = prop
        def fireCallbacks(value):
            for c in self.callbacks:
                try:
                    c(name, value)
                except Exception as e:
                    logger.exception(e)
        prop.wire(fireCallbacks)
        return self

    def __getitem__(self, name):
        return self.getPropertyValue(name)

    def __setitem__(self, name, value):
        if not self.hasProperty(name):
            self.add(name, Property())
        self.getProperty(name).setValue(value)

    def hasProperty(self, name):
        return name in self.properties

    def getProperty(self, name):
        if not self.hasProperty(name):
            self.add(name, Property())
        return self.properties[name]

    def getPropertyValue(self, name):
        return self.getProperty(name).getValue()

    def wire(self, callback):
        self.callbacks.append(callback)
        return self

    def unwire(self, callback):
        self.callbacks.remove(callback)
        return self

    def defaults(self, other_pm):
        for (key, p) in self.properties.items():
            if p.getValue() is None:
                p.setValue(other_pm[key])
        return self

class UnknownFeatureException(Exception):
    pass

class RequirementMissingException(Exception):
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
