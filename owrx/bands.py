import json


class Band(object):
    def __init__(self, dict):
        self.name = dict["name"]
        self.lower_bound = dict["lower_bound"]
        self.upper_bound = dict["upper_bound"]

    def inBand(self, freq):
        return self.lower_bound <= freq <= self.upper_bound

    def getName(self):
        return self.name


class Bandplan(object):
    sharedInstance = None
    @staticmethod
    def getSharedInstance():
        if Bandplan.sharedInstance is None:
            Bandplan.sharedInstance = Bandplan()
        return Bandplan.sharedInstance

    def __init__(self):
        f = open("bands.json", "r")
        bands_json = json.load(f)
        f.close()
        self.bands = [Band(d) for d in bands_json]

    def findBand(self, freq):
        return next(band for band in self.bands if band.inBand(freq))
