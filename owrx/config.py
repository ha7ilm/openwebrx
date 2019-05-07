import os

class Property(object):
    def __init__(self, value = None):
        self.value = value
        self.callbacks = []
    def getValue(self):
        return self.value
    def setValue(self, value):
        self.value = value
        for c in self.callbacks:
            c(self.value)
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

    def __init__(self):
        self.properties = {}

    def getProperty(self, name):
        if not name in self.properties:
            self.properties[name] = Property()
        return self.properties[name]

    def getPropertyValue(self, name):
        return self.getProperty(name).getValue()

class RequirementMissingException(Exception):
    pass

class FeatureDetector(object):
    features = {
        "core": [ "csdr", "nmux" ],
        "rtl_sdr": [ "rtl_sdr" ],
        "sdrplay": [ "rx_tools" ],
        "hackrf": [ "rx_tools" ]
    }

    def is_available(self, feature):
        return self.has_requirements(self.get_requirements(feature))

    def get_requirements(self, feature):
        return FeatureDetector.features[feature]

    def has_requirements(self, requirements):
        passed = True
        for requirement in requirements:
            methodname = "has_" + requirement
            if hasattr(self, methodname) and callable(getattr(self, methodname)):
                passed = passed and getattr(self, methodname)()
            else:
                print("detection of requirement {0} not implement. please fix in code!".format(requirement))
        return passed

    def has_csdr(self):
        return os.system("csdr 2> /dev/null") != 32512

    def has_nmux(self):
        return os.system("nmux --help 2> /dev/null") != 32512

    def has_rtl_sdr(self):
        return os.system("rtl_sdr --help 2> /dev/null") != 32512

    def has_rx_tools(self):
        return os.system("rx_sdr --help 2> /dev/null") != 32512
