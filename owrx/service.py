import threading
from owrx.source import SdrService
from owrx.bands import Bandplan
from csdr import dsp, output
from owrx.wsjt import WsjtParser
from owrx.config import PropertyManager

import logging

logger = logging.getLogger(__name__)


class ServiceOutput(output):
    def __init__(self, frequency):
        self.frequency = frequency

    def add_output(self, t, read_fn):
        if t == "wsjt_demod":
            parser = WsjtParser(WsjtHandler())
            parser.setDialFrequency(self.frequency)
            target = self.pump(read_fn, parser.parse)
        else:
            # dump everything else
            # TODO rewrite the output mechanism in a way that avoids producing unnecessary data
            target = self.pump(read_fn, lambda x: None)
        threading.Thread(target=target).start()


class ServiceHandler(object):
    def __init__(self, source):
        self.services = []
        self.source = source
        self.source.addClient(self)
        self.source.getProps().collect("center_freq", "samp_rate").wire(self.onFrequencyChange)
        self.updateServices()

    def onSdrAvailable(self):
        self.updateServices()

    def onSdrUnavailable(self):
        self.stopServices()

    def isSupported(self, mode):
        # TODO make configurable
        return mode in PropertyManager.getSharedInstance()["services_decoders"]

    def stopServices(self):
        for service in self.services:
            service.stop()
        self.services = []

    def startServices(self):
        for service in self.services:
            service.start()

    def onFrequencyChange(self, key, value):
        if not self.source.isAvailable():
            return
        self.updateServices()

    def updateServices(self):
        logger.debug("re-scheduling services due to sdr changes")
        self.stopServices()
        cf = self.source.getProps()["center_freq"]
        srh = self.source.getProps()["samp_rate"] / 2
        frequency_range = (cf - srh, cf + srh)
        self.services = [self.setupService(dial["mode"], dial["frequency"]) for dial in Bandplan.getSharedInstance().collectDialFrequencies(frequency_range) if self.isSupported(dial["mode"])]

    def setupService(self, mode, frequency):
        logger.debug("setting up service {0} on frequency {1}".format(mode, frequency))
        d = dsp(ServiceOutput(frequency))
        d.nc_port = self.source.getPort()
        d.set_offset_freq(frequency - self.source.getProps()["center_freq"])
        d.set_demodulator("usb")
        d.set_bpf(0, 3000)
        d.set_secondary_demodulator(mode)
        d.set_audio_compression("none")
        d.set_samp_rate(self.source.getProps()["samp_rate"])
        d.start()
        return d


class WsjtHandler(object):
    def write_wsjt_message(self, msg):
        pass


class ServiceManager(object):
    sharedInstance = None
    @staticmethod
    def getSharedInstance():
        if ServiceManager.sharedInstance is None:
            ServiceManager.sharedInstance = ServiceManager()
        return ServiceManager.sharedInstance

    def start(self):
        if not PropertyManager.getSharedInstance()["services_enabled"]:
            return
        for source in SdrService.getSources().values():
            ServiceHandler(source)


class Service(object):
    pass


class WsjtService(Service):
    pass
