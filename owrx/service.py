import threading
from owrx.source import SdrService
from owrx.bands import Bandplan
from csdr import dsp, output
from owrx.wsjt import WsjtParser

import logging

logger = logging.getLogger(__name__)


class ServiceOutput(output):
    def __init__(self, frequency):
        self.frequency = frequency

    def add_output(self, t, read_fn):
        logger.debug("got output of type {0}".format(t))

        def pump(read, write):
            def copy():
                run = True
                while run:
                    data = read()
                    if data is None or (isinstance(data, bytes) and len(data) == 0):
                        logger.warning("zero read on {0}".format(t))
                        run = False
                    else:
                        write(data)

            return copy

        if t == "wsjt_demod":
            parser = WsjtParser(WsjtHandler())
            parser.setDialFrequency(self.frequency)
            target = pump(read_fn, parser.parse)
        else:
            # dump everything else
            # TODO rewrite the output mechanism in a way that avoids producing unnecessary data
            target = pump(read_fn, lambda x: None)
        threading.Thread(target=target).start()


class ServiceHandler(object):
    def __init__(self, source):
        self.services = []
        self.source = source
        self.source.addClient(self)
        self.source.getProps().collect("center_freq", "samp_rate").wire(self.onFrequencyChange)
        self.onFrequencyChange("", "")

    def onSdrAvailable(self):
        logger.debug("sdr {0} is available".format(self.source.getName()))
        self.onFrequencyChange("", "")

    def onSdrUnavailable(self):
        logger.debug("sdr {0} is unavailable".format(self.source.getName()))
        self.stopServices()

    def isSupported(self, mode):
        return mode in ["ft8", "ft4", "wspr"]

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
        logger.debug("sdr {0} is changing frequency".format(self.source.getName()))
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
        for source in SdrService.getSources().values():
            ServiceHandler(source)


class Service(object):
    pass


class WsjtService(Service):
    pass
