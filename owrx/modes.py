from owrx.feature import FeatureDetector
from functools import reduce


class Mode(object):
    def __init__(self, modulation, name, requirements=None, service=False):
        self.modulation = modulation
        self.name = name
        self.requirements = requirements if requirements is not None else []
        self.service = service

    def is_available(self):
        fd = FeatureDetector()
        return reduce(
            lambda a, b: a and b, [fd.is_available(r) for r in self.requirements], True
        )

    def is_service(self):
        return self.service


class Modes(object):
    mappings = [
        Mode("ft8", "FT8", ["wsjt-x"], True),
        Mode("ft4", "FT4", ["wsjt-x"], True),
        Mode("jt65", "JT65", ["wsjt-x"], True),
        Mode("jt9", "JT9", ["wsjt-x"], True),
        Mode("wspr", "WSPR", ["wsjt-x"], True),
        Mode("packet", "Packet", ["packet"], True),
        Mode("js8", "JS8Call", ["js8call"], True),
    ]

    @staticmethod
    def getModes():
        return Modes.mappings

    @staticmethod
    def getAvailableModes():
        return [m for m in Modes.getModes() if m.is_available()]

    @staticmethod
    def getAvailableServices():
        return [m for m in Modes.getAvailableModes() if m.is_service()]
