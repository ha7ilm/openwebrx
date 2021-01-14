from owrx.feature import FeatureDetector
from functools import reduce


class Bandpass(object):
    def __init__(self, low_cut, high_cut):
        self.low_cut = low_cut
        self.high_cut = high_cut


class Mode(object):
    def __init__(self, modulation, name, bandpass: Bandpass = None, requirements=None, service=False, squelch=True):
        self.modulation = modulation
        self.name = name
        self.requirements = requirements if requirements is not None else []
        self.service = service
        self.bandpass = bandpass
        self.squelch = squelch

    def is_available(self):
        fd = FeatureDetector()
        return reduce(lambda a, b: a and b, [fd.is_available(r) for r in self.requirements], True)

    def is_service(self):
        return self.service

    def get_bandpass(self):
        return self.bandpass

    def get_modulation(self):
        return self.modulation


class AnalogMode(Mode):
    pass


class DigitalMode(Mode):
    def __init__(
        self, modulation, name, underlying, bandpass: Bandpass = None, requirements=None, service=False, squelch=True
    ):
        super().__init__(modulation, name, bandpass, requirements, service, squelch)
        self.underlying = underlying

    def get_bandpass(self):
        if self.bandpass is not None:
            return self.bandpass
        return Modes.findByModulation(self.underlying[0]).get_bandpass()

    def get_modulation(self):
        return Modes.findByModulation(self.underlying[0]).get_modulation()


class Modes(object):
    mappings = [
        AnalogMode("nfm", "FM", bandpass=Bandpass(-4000, 4000)),
        AnalogMode("wfm", "WFM", bandpass=Bandpass(-75000, 75000)),
        AnalogMode("am", "AM", bandpass=Bandpass(-4000, 4000)),
        AnalogMode("lsb", "LSB", bandpass=Bandpass(-3000, -300)),
        AnalogMode("usb", "USB", bandpass=Bandpass(300, 3000)),
        AnalogMode("cw", "CW", bandpass=Bandpass(700, 900)),
        AnalogMode("dmr", "DMR", bandpass=Bandpass(-4000, 4000), requirements=["digital_voice_digiham"], squelch=False),
        AnalogMode("dstar", "D-Star", bandpass=Bandpass(-3250, 3250), requirements=["digital_voice_dsd"], squelch=False),
        AnalogMode("nxdn", "NXDN", bandpass=Bandpass(-3250, 3250), requirements=["digital_voice_dsd"], squelch=False),
        AnalogMode("ysf", "YSF", bandpass=Bandpass(-4000, 4000), requirements=["digital_voice_digiham"], squelch=False),
        AnalogMode("m17", "M17", bandpass=Bandpass(-4000, 4000), requirements=["digital_voice_m17"], squelch=False),
        AnalogMode("freedv", "FreeDV", bandpass=Bandpass(300, 3000), requirements=["digital_voice_freedv"], squelch=False),
        AnalogMode("drm", "DRM", bandpass=Bandpass(-5000, 5000), requirements=["drm"], squelch=False),
        DigitalMode("bpsk31", "BPSK31", underlying=["usb"]),
        DigitalMode("bpsk63", "BPSK63", underlying=["usb"]),
        DigitalMode("ft8", "FT8", underlying=["usb"], bandpass=Bandpass(0, 3000), requirements=["wsjt-x"], service=True),
        DigitalMode("ft4", "FT4", underlying=["usb"], bandpass=Bandpass(0, 3000), requirements=["wsjt-x"], service=True),
        DigitalMode("jt65", "JT65", underlying=["usb"], bandpass=Bandpass(0, 3000), requirements=["wsjt-x"], service=True),
        DigitalMode("jt9", "JT9", underlying=["usb"], bandpass=Bandpass(0, 3000), requirements=["wsjt-x"], service=True),
        DigitalMode(
            "wspr", "WSPR", underlying=["usb"], bandpass=Bandpass(1350, 1650), requirements=["wsjt-x"], service=True
        ),
        DigitalMode("fst4", "FST4", underlying=["usb"], bandpass=Bandpass(0, 3000), requirements=["wsjt-x-2-3"], service=True),
        DigitalMode("fst4w", "FST4W", underlying=["usb"], bandpass=Bandpass(1350, 1650), requirements=["wsjt-x-2-3"], service=True),
        DigitalMode("js8", "JS8Call", underlying=["usb"], bandpass=Bandpass(0, 3000), requirements=["js8call"], service=True),
        DigitalMode(
            "packet",
            "Packet",
            underlying=["nfm", "usb", "lsb"],
            bandpass=Bandpass(-6250, 6250),
            requirements=["packet"],
            service=True,
            squelch=False,
        ),
        DigitalMode(
            "pocsag",
            "Pocsag",
            underlying=["nfm"],
            bandpass=Bandpass(-6000, 6000),
            requirements=["pocsag"],
            squelch=False,
        ),
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

    @staticmethod
    def findByModulation(modulation):
        modes = [m for m in Modes.getAvailableModes() if m.modulation == modulation]
        if modes:
            return modes[0]
