import json

import logging

logger = logging.getLogger(__name__)


class Band(object):
    def __init__(self, dict):
        self.name = dict["name"]
        self.lower_bound = dict["lower_bound"]
        self.upper_bound = dict["upper_bound"]
        self.frequencies = []
        if "frequencies" in dict:
            for (mode, freqs) in dict["frequencies"].items():
                if not isinstance(freqs, list):
                    freqs = [freqs]
                for f in freqs:
                    if not self.inBand(f):
                        logger.warning(
                            "Frequency for {mode} on {band} is not within band limits: {frequency}".format(
                                mode=mode, frequency=f, band=self.name
                            )
                        )
                    else:
                        self.frequencies.append({"mode": mode, "frequency": f})

    def inBand(self, freq):
        return self.lower_bound <= freq <= self.upper_bound

    def getName(self):
        return self.name

    def getDialFrequencies(self, range):
        (low, hi) = range
        return [e for e in self.frequencies if low <= e["frequency"] <= hi]


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

    def collectDialFrequencies(self, range):
        return [e for b in self.bands for e in b.getDialFrequencies(range)]
