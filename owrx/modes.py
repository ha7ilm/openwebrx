from owrx.feature import FeatureDetector
from functools import reduce


class Mode(object):
    def __init__(self, modulation, name, requirements=None, service=False, digimode=False):
        self.modulation = modulation
        self.name = name
        self.digimode = digimode
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
        Mode("nfm", "FM"),
        Mode("am", "AM"),
        Mode("lsb", "LSB"),
        Mode("usb", "USB"),
        Mode("cw", "CW"),
        Mode("dmr", "DMR", requirements=["digital_voice_digiham"]),
        Mode("dstar", "DStar", requirements=["digital_voice_dsd"]),
        Mode("nxdn", "NXDN", requirements=["digital_voice_dsd"]),
        Mode("ysf", "YSF", requirements=["digital_voice_digiham"]),
        Mode("bpsk31", "BPSK31", digimode=True),
        Mode("bpsk63", "BPSK63", digimode=True),
        Mode("ft8", "FT8", requirements=["wsjt-x"], service=True, digimode=True),
        Mode("ft4", "FT4", requirements=["wsjt-x"], service=True, digimode=True),
        Mode("jt65", "JT65", requirements=["wsjt-x"], service=True, digimode=True),
        Mode("jt9", "JT9", requirements=["wsjt-x"], service=True, digimode=True),
        Mode("wspr", "WSPR", requirements=["wsjt-x"], service=True, digimode=True),
        Mode("packet", "Packet", ["packet"], service=True, digimode=True),
        Mode("js8", "JS8Call", requirements=["js8call"], service=True, digimode=True),
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
