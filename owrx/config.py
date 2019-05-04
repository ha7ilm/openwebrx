class Property(object):
    def __init__(self, value = None):
        self.value = value
    def getValue(self):
        return self.value
    def setValue(self, value):
        self.value = value

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
