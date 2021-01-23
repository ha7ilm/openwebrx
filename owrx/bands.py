from owrx.modes import Modes
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
            availableModes = [mode.modulation for mode in Modes.getAvailableModes()]
            for (mode, freqs) in dict["frequencies"].items():
                if mode not in availableModes:
                    logger.info(
                        'Modulation "{mode}" is not available, bandplan bookmark will not be displayed'.format(
                            mode=mode
                        )
                    )
                    continue
                if not isinstance(freqs, list):
                    freqs = [freqs]
                for f in freqs:
                    if not self.inBand(f):
                        logger.warning(
                            "Frequency for {mode} on {band} is not within band limits: {frequency}".format(
                                mode=mode, frequency=f, band=self.name
                            )
                        )
                        continue
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
        self.bands = self.loadBands()

    def loadBands(self):
        for file in ["/etc/openwebrx/bands.json", "bands.json"]:
            try:
                f = open(file, "r")
                bands_json = json.load(f)
                f.close()
                return [Band(d) for d in bands_json]
            except FileNotFoundError:
                pass
            except json.JSONDecodeError:
                logger.exception("error while parsing bandplan file %s", file)
                return []
            except Exception:
                logger.exception("error while processing bandplan from %s", file)
                return []
        return []

    def findBands(self, freq):
        return [band for band in self.bands if band.inBand(freq)]

    def findBand(self, freq):
        bands = self.findBands(freq)
        if bands:
            return bands[0]
        else:
            return None

    def collectDialFrequencies(self, range):
        return [e for b in self.bands for e in b.getDialFrequencies(range)]
