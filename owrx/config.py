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
    def detectAllFeatures(self):
        print("Starting Feature detection")
        self.detect_csdr()
        self.detect_nmux()
        print("Feature detection completed.")

    def detect_csdr(self):
        if os.system("csdr 2> /dev/null") == 32512: #check for csdr
            raise RequirementMissingException("You need to install \"csdr\" to run OpenWebRX!")

    def detect_nmux(self):
        if os.system("nmux --help 2> /dev/null") == 32512: #check for nmux
            raise RequirementMissingException("You need to install an up-to-date version of \"csdr\" that contains the \"nmux\" tool to run OpenWebRX! Please upgrade \"csdr\"!")
