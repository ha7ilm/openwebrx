from abc import ABC, abstractmethod
from owrx.bands import Bandplan


class Parser(ABC):
    def __init__(self, handler):
        self.handler = handler
        self.dial_freq = None
        self.band = None

    @abstractmethod
    def parse(self, raw):
        pass

    def setDialFrequency(self, freq):
        self.dial_freq = freq
        self.band = Bandplan.getSharedInstance().findBand(freq)

    def getBand(self):
        return self.band
