import threading
import socket
from owrx.source import SdrService
from owrx.bands import Bandplan
from csdr import dsp, output
from owrx.wsjt import WsjtParser
from owrx.aprs import AprsParser
from owrx.config import PropertyManager
from owrx.source import Resampler

import logging

logger = logging.getLogger(__name__)


class ServiceOutput(output):
    def __init__(self, frequency):
        self.frequency = frequency

    def getParser(self):
        # abstract method; implement in subclasses
        pass

    def receive_output(self, t, read_fn):
        parser = self.getParser()
        parser.setDialFrequency(self.frequency)
        target = self.pump(read_fn, parser.parse)
        threading.Thread(target=target).start()


class WsjtServiceOutput(ServiceOutput):
    def getParser(self):
        return WsjtParser(WsjtHandler())

    def supports_type(self, t):
        return t == "wsjt_demod"


class AprsServiceOutput(ServiceOutput):
    def getParser(self):
        return AprsParser(AprsHandler())

    def supports_type(self, t):
        return t == "packet_demod"


class ServiceHandler(object):
    def __init__(self, source):
        self.services = []
        self.source = source
        self.startupTimer = None
        self.source.addClient(self)
        self.source.getProps().collect("center_freq", "samp_rate").wire(self.onFrequencyChange)
        self.scheduleServiceStartup()

    def onSdrAvailable(self):
        self.scheduleServiceStartup()

    def onSdrUnavailable(self):
        self.stopServices()

    def isSupported(self, mode):
        return mode in PropertyManager.getSharedInstance()["services_decoders"]

    def stopServices(self):
        for service in self.services:
            service.stop()
        self.services = []

    def startServices(self):
        for service in self.services:
            service.start()

    def onFrequencyChange(self, key, value):
        self.stopServices()
        if not self.source.isAvailable():
            return
        self.scheduleServiceStartup()

    def scheduleServiceStartup(self):
        if self.startupTimer:
            self.startupTimer.cancel()
        self.startupTimer = threading.Timer(10, self.updateServices)
        self.startupTimer.start()

    def getAvailablePort(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port

    def updateServices(self):
        logger.debug("re-scheduling services due to sdr changes")
        self.stopServices()
        cf = self.source.getProps()["center_freq"]
        sr = self.source.getProps()["samp_rate"]
        srh = sr / 2
        frequency_range = (cf - srh, cf + srh)

        dials = [
            dial
            for dial in Bandplan.getSharedInstance().collectDialFrequencies(frequency_range)
            if self.isSupported(dial["mode"])
        ]

        if not dials:
            logger.debug("no services available")
            return

        self.services = []

        for group in self.optimizeResampling(dials, sr):
            frequencies = sorted([f["frequency"] for f in group])
            min = frequencies[0]
            max = frequencies[-1]
            cf = (min + max) / 2
            bw = max - min
            logger.debug("group center frequency: {0}, bandwidth: {1}".format(cf, bw))
            resampler_props = PropertyManager()
            resampler_props["center_freq"] = cf
            # TODO the + 24000 is a temporary fix since the resampling optimizer does not account for required bandwidths
            resampler_props["samp_rate"] = bw + 24000
            resampler = Resampler(resampler_props, self.getAvailablePort(), self.source)
            resampler.start()
            self.services.append(resampler)

            for dial in group:
                self.services.append(self.setupService(dial["mode"], dial["frequency"], resampler))

    def optimizeResampling(self, freqs, bandwidth):
        freqs = sorted(freqs, key=lambda f: f["frequency"])
        distances = [
            {"frequency": freqs[i]["frequency"], "distance": freqs[i + 1]["frequency"] - freqs[i]["frequency"]}
            for i in range(0, len(freqs) - 1)
        ]

        distances = [d for d in distances if d["distance"] > 0]

        distances = sorted(distances, key=lambda f: f["distance"], reverse=True)

        def calculate_usage(num_splits):
            splits = sorted([f["frequency"] for f in distances[0:num_splits]])
            previous = 0
            groups = []
            for split in splits:
                groups.append([f for f in freqs if previous < f["frequency"] <= split])
                previous = split
            groups.append([f for f in freqs if previous < f["frequency"]])

            def get_bandwitdh(group):
                freqs = sorted([f["frequency"] for f in group])
                # the group will process the full BW once, plus the reduced BW once for each group member
                return bandwidth + len(group) * (freqs[-1] - freqs[0] + 24000)

            total_bandwidth = sum([get_bandwitdh(group) for group in groups])
            return {"num_splits": num_splits, "total_bandwidth": total_bandwidth, "groups": groups}

        usages = [calculate_usage(i) for i in range(0, len(freqs))]
        # this is simulating no resampling. i haven't seen this as the best result yet
        usages += [{"num_splits": None, "total_bandwidth": bandwidth * len(freqs), "groups": [freqs]}]
        results = sorted(usages, key=lambda f: f["total_bandwidth"])

        for r in results:
            logger.debug("splits: {0}, total: {1}".format(r["num_splits"], r["total_bandwidth"]))

        return results[0]["groups"]

    def setupService(self, mode, frequency, source):
        logger.debug("setting up service {0} on frequency {1}".format(mode, frequency))
        # TODO selecting outputs will need some more intelligence here
        if mode == "packet":
            output = AprsServiceOutput(frequency)
        else:
            output = WsjtServiceOutput(frequency)
        d = dsp(output)
        d.nc_port = source.getPort()
        d.set_offset_freq(frequency - source.getProps()["center_freq"])
        if mode == "packet":
            d.set_demodulator("nfm")
            d.set_bpf(-4000, 4000)
        elif mode == "wspr":
            d.set_demodulator("usb")
            # WSPR only samples between 1400 and 1600 Hz
            d.set_bpf(1350, 1650)
        else:
            d.set_demodulator("usb")
            d.set_bpf(0, 3000)
        d.set_secondary_demodulator(mode)
        d.set_audio_compression("none")
        d.set_samp_rate(source.getProps()["samp_rate"])
        d.set_service()
        d.start()
        return d


class WsjtHandler(object):
    def write_wsjt_message(self, msg):
        pass


class AprsHandler(object):
    def write_aprs_data(self, data):
        pass


class Services(object):
    @staticmethod
    def start():
        if not PropertyManager.getSharedInstance()["services_enabled"]:
            return
        for source in SdrService.getSources().values():
            ServiceHandler(source)


class Service(object):
    pass


class WsjtService(Service):
    pass
