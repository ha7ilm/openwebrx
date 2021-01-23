import threading
from owrx.source import SdrSource, SdrSourceEventClient
from owrx.sdr import SdrService
from owrx.bands import Bandplan
from csdr.csdr import dsp, output
from owrx.wsjt import WsjtParser
from owrx.aprs import AprsParser
from owrx.js8 import Js8Parser
from owrx.config import Config
from owrx.source.resampler import Resampler
from owrx.property import PropertyLayer
from js8py import Js8Frame
from abc import ABCMeta, abstractmethod
from .schedule import ServiceScheduler
from owrx.modes import Modes

import logging

logger = logging.getLogger(__name__)


class ServiceOutput(output, metaclass=ABCMeta):
    def __init__(self, frequency):
        self.frequency = frequency

    @abstractmethod
    def getParser(self):
        # abstract method; implement in subclasses
        pass

    def receive_output(self, t, read_fn):
        parser = self.getParser()
        parser.setDialFrequency(self.frequency)
        target = self.pump(read_fn, parser.parse)
        threading.Thread(target=target, name="service_output_receive").start()


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


class Js8ServiceOutput(ServiceOutput):
    def getParser(self):
        return Js8Parser(Js8Handler())

    def supports_type(self, t):
        return t == "js8_demod"


class ServiceHandler(SdrSourceEventClient):
    def __init__(self, source):
        self.lock = threading.RLock()
        self.services = []
        self.source = source
        self.startupTimer = None
        self.scheduler = None
        self.source.addClient(self)
        props = self.source.getProps()
        props.filter("center_freq", "samp_rate").wire(self.onFrequencyChange)
        if self.source.isAvailable():
            self.scheduleServiceStartup()
        if "schedule" in props or "scheduler" in props:
            self.scheduler = ServiceScheduler(self.source)

    def getClientClass(self):
        return SdrSource.CLIENT_INACTIVE

    def onStateChange(self, state):
        if state == SdrSource.STATE_RUNNING:
            self.scheduleServiceStartup()
        elif state == SdrSource.STATE_STOPPING:
            logger.debug("sdr source becoming unavailable; stopping services.")
            self.stopServices()
        elif state == SdrSource.STATE_FAILED:
            logger.debug("sdr source failed; stopping services.")
            self.stopServices()
            if self.scheduler:
                self.scheduler.shutdown()

    def onBusyStateChange(self, state):
        pass

    def isSupported(self, mode):
        configured = Config.get()["services_decoders"]
        available = [m.modulation for m in Modes.getAvailableServices()]
        return mode in configured and mode in available

    def shutdown(self):
        self.stopServices()
        self.source.removeClient(self)
        if self.scheduler:
            self.scheduler.shutdown()

    def stopServices(self):
        with self.lock:
            services = self.services
            self.services = []

        for service in services:
            service.stop()

    def onFrequencyChange(self, changes):
        self.stopServices()
        if not self.source.isAvailable():
            return
        self.scheduleServiceStartup()

    def scheduleServiceStartup(self):
        if self.startupTimer:
            self.startupTimer.cancel()
        self.startupTimer = threading.Timer(10, self.updateServices)
        self.startupTimer.start()

    def updateServices(self):
        with self.lock:
            logger.debug("re-scheduling services due to sdr changes")
            self.stopServices()
            if not self.source.isAvailable():
                logger.debug("sdr source is unavailable")
                return
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

            groups = self.optimizeResampling(dials, sr)
            if groups is None:
                for dial in dials:
                    self.services.append(self.setupService(dial["mode"], dial["frequency"], self.source))
            else:
                for group in groups:
                    cf = self.get_center_frequency(group)
                    bw = self.get_bandwidth(group)
                    logger.debug("group center frequency: {0}, bandwidth: {1}".format(cf, bw))
                    resampler_props = PropertyLayer()
                    resampler_props["center_freq"] = cf
                    resampler_props["samp_rate"] = bw
                    resampler = Resampler(resampler_props, self.source)
                    resampler.start()

                    for dial in group:
                        self.services.append(self.setupService(dial["mode"], dial["frequency"], resampler))

                    # resampler goes in after the services since it must not be shutdown as long as the services are still running
                    self.services.append(resampler)

    def get_min_max(self, group):
        frequencies = sorted(group, key=lambda f: f["frequency"])
        lowest = frequencies[0]
        min = lowest["frequency"] + Modes.findByModulation(lowest["mode"]).get_bandpass().low_cut
        highest = frequencies[-1]
        max = highest["frequency"] + Modes.findByModulation(highest["mode"]).get_bandpass().high_cut
        return min, max

    def get_center_frequency(self, group):
        min, max = self.get_min_max(group)
        return (min + max) / 2

    def get_bandwidth(self, group):
        minFreq, maxFreq = self.get_min_max(group)
        # minimum bandwidth for a resampler: 25kHz
        return max(maxFreq - minFreq, 25000)

    def optimizeResampling(self, freqs, bandwidth):
        freqs = sorted(freqs, key=lambda f: f["frequency"])
        distances = [
            {
                "frequency": freqs[i]["frequency"],
                "distance": freqs[i + 1]["frequency"] - freqs[i]["frequency"],
            }
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

            def get_total_bandwidth(group):
                return bandwidth + len(group) * self.get_bandwidth(group)

            total_bandwidth = sum([get_total_bandwidth(group) for group in groups])
            return {
                "num_splits": num_splits,
                "total_bandwidth": total_bandwidth,
                "groups": groups,
            }

        usages = [calculate_usage(i) for i in range(0, len(freqs))]
        # another possible outcome might be that it's best not to resample at all. this is a special case.
        usages += [
            {
                "num_splits": None,
                "total_bandwidth": bandwidth * len(freqs),
                "groups": [freqs],
            }
        ]
        results = sorted(usages, key=lambda f: f["total_bandwidth"])

        for r in results:
            logger.debug("splits: {0}, total: {1}".format(r["num_splits"], r["total_bandwidth"]))

        best = results[0]
        if best["num_splits"] is None:
            return None
        return best["groups"]

    def setupService(self, mode, frequency, source):
        logger.debug("setting up service {0} on frequency {1}".format(mode, frequency))
        # TODO selecting outputs will need some more intelligence here
        if mode == "packet":
            output = AprsServiceOutput(frequency)
        elif mode == "js8":
            output = Js8ServiceOutput(frequency)
        else:
            output = WsjtServiceOutput(frequency)
        d = dsp(output)
        d.nc_port = source.getPort()
        center_freq = source.getProps()["center_freq"]
        d.set_offset_freq(frequency - center_freq)
        d.set_center_freq(center_freq)
        modeObject = Modes.findByModulation(mode)
        d.set_demodulator(modeObject.get_modulation())
        d.set_bandpass(modeObject.get_bandpass())
        d.set_secondary_demodulator(mode)
        d.set_audio_compression("none")
        d.set_samp_rate(source.getProps()["samp_rate"])
        d.set_temporary_directory(Config.get()["temporary_directory"])
        d.set_service()
        d.start()
        return d


class WsjtHandler(object):
    def write_wsjt_message(self, msg):
        pass


class AprsHandler(object):
    def write_aprs_data(self, data):
        pass


class Js8Handler(object):
    def write_js8_message(self, frame: Js8Frame, freq: int):
        pass


class Services(object):
    handlers = []

    @staticmethod
    def start():
        if not Config.get()["services_enabled"]:
            return
        for source in SdrService.getSources().values():
            props = source.getProps()
            if "services" not in props or props["services"] is not False:
                Services.handlers.append(ServiceHandler(source))

    @staticmethod
    def stop():
        for handler in Services.handlers:
            handler.shutdown()
        Services.handlers = []
