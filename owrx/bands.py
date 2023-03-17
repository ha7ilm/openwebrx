from owrx.modes import Modes, DigitalMode
from datetime import datetime, timezone
import json
import os

import logging

logger = logging.getLogger(__name__)


class Band(object):
    def __init__(self, b_dict):
        self.name = b_dict["name"]
        self.lower_bound = b_dict["lower_bound"]
        self.upper_bound = b_dict["upper_bound"]
        self.frequencies = []
        if "frequencies" in b_dict:
            availableModes = [mode.modulation for mode in Modes.getAvailableModes()]
            for (mode, freqs) in b_dict["frequencies"].items():
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
                    f_dict = {"frequency": f} if not isinstance(f, dict) else f
                    f_dict["mode"] = mode

                    if not self.inBand(f_dict["frequency"]):
                        logger.warning(
                            "Frequency for {mode} on {band} is not within band limits: {frequency}".format(
                                mode=mode, frequency=f_dict["frequency"], band=self.name
                            )
                        )
                        continue

                    if "underlying" in f_dict:
                        m = Modes.findByModulation(mode)
                        if not isinstance(m, DigitalMode):
                            logger.warning("%s is not a digital mode, cannot be used with \"underlying\" config", mode)
                            continue
                        if f_dict["underlying"] not in m.underlying:
                            logger.warning(
                                "%s is not a valid underlying mode for %s; skipping",
                                f_dict["underlying"],
                                mode
                            )

                    self.frequencies.append(f_dict)

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
        self.bands = []
        self.file_modified = None
        self.fileList = ["/etc/openwebrx/bands.json", "bands.json"]

    def _refresh(self):
        modified = self._getFileModifiedTimestamp()
        if self.file_modified is None or modified > self.file_modified:
            logger.debug("reloading bands from disk due to file modification")
            self.bands = self._loadBands()
            self.file_modified = modified

    def _getFileModifiedTimestamp(self):
        timestamp = 0
        for file in self.fileList:
            try:
                timestamp = os.path.getmtime(file)
                break
            except FileNotFoundError:
                pass
        return datetime.fromtimestamp(timestamp, timezone.utc)

    def _loadBands(self):
        for file in self.fileList:
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
        self._refresh()
        return [band for band in self.bands if band.inBand(freq)]

    def findBand(self, freq):
        bands = self.findBands(freq)
        if bands:
            return bands[0]
        else:
            return None

    def collectDialFrequencies(self, range):
        self._refresh()
        return [e for b in self.bands for e in b.getDialFrequencies(range)]
