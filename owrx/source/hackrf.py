from .soapy import SoapyConnectorSource
from owrx.command import Option
import time


class HackrfSource(SoapyConnectorSource):
    def getDriver(self):
        return "hackrf"