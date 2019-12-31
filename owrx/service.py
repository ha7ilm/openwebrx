import threading
from datetime import datetime, timezone, timedelta
from owrx.source import SdrSource
from owrx.sdr import SdrService
from owrx.bands import Bandplan
from csdr.csdr import dsp, output
from owrx.wsjt import WsjtParser
from owrx.aprs import AprsParser
from owrx.config import PropertyManager
from owrx.source.resampler import Resampler
from owrx.feature import FeatureDetector

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


class ScheduleEntry(object):
    def __init__(self, startTime, endTime, profile):
        self.startTime = startTime
        self.endTime = endTime
        self.profile = profile

    def isCurrent(self, time):
        if self.startTime < self.endTime:
            return self.startTime <= time < self.endTime
        else:
            return self.startTime <= time or time < self.endTime

    def getProfile(self):
        return self.profile

    def getScheduledEnd(self):
        now = datetime.utcnow()
        end = now.combine(date=now.date(), time=self.endTime)
        while end < now:
            end += timedelta(days=1)
        return end

    def getNextActivation(self):
        now = datetime.utcnow()
        start = now.combine(date=now.date(), time=self.startTime)
        while start < now:
            start += timedelta(days=1)
        return start


class Schedule(object):
    @staticmethod
    def parse(scheduleDict):
        entries = []
        for time, profile in scheduleDict.items():
            if len(time) != 9:
                logger.warning("invalid schedule spec: %s", time)
                continue

            startTime = datetime.strptime(time[0:4], "%H%M").replace(tzinfo=timezone.utc).time()
            endTime = datetime.strptime(time[5:9], "%H%M").replace(tzinfo=timezone.utc).time()
            entries.append(ScheduleEntry(startTime, endTime, profile))
        return Schedule(entries)

    def __init__(self, entries):
        self.entries = entries

    def getCurrentEntry(self):
        current = [p for p in self.entries if p.isCurrent(datetime.utcnow().time())]
        if current:
            return current[0]
        return None

    def getNextEntry(self):
        s = sorted(self.entries, key=lambda e: e.getNextActivation())
        if s:
            return s[0]
        return None


class ServiceScheduler(object):
    def __init__(self, source, schedule):
        self.source = source
        self.selectionTimer = None
        self.schedule = Schedule.parse(schedule)
        self.source.addClient(self)
        self.source.getProps().collect("center_freq", "samp_rate").wire(self.onFrequencyChange)
        self.scheduleSelection()

    def shutdown(self):
        self.cancelTimer()
        self.source.removeClient(self)

    def scheduleSelection(self, time=None):
        seconds = 10
        if time is not None:
            delta = time - datetime.utcnow()
            seconds = delta.total_seconds()
        self.cancelTimer()
        self.selectionTimer = threading.Timer(seconds, self.selectProfile)
        self.selectionTimer.start()

    def cancelTimer(self):
        if self.selectionTimer:
            self.selectionTimer.cancel()

    def getClientClass(self):
        return SdrSource.CLIENT_BACKGROUND

    def onStateChange(self, state):
        if state == SdrSource.STATE_STOPPING:
            self.scheduleSelection()
        elif state == SdrSource.STATE_FAILED:
            self.cancelTimer()

    def onBusyStateChange(self, state):
        if state == SdrSource.BUSYSTATE_IDLE:
            self.scheduleSelection()

    def onFrequencyChange(self, name, value):
        self.scheduleSelection()

    def selectProfile(self):
        if self.source.hasClients(SdrSource.CLIENT_USER):
            logger.debug("source has active users; not touching")
            return
        logger.debug("source seems to be idle, selecting profile for background services")
        entry = self.schedule.getCurrentEntry()

        if entry is None:
            logger.debug("schedule did not return a profile. checking next entry...")
            nextEntry = self.schedule.getNextEntry()
            if nextEntry is not None:
                self.scheduleSelection(nextEntry.getNextActivation())
            return

        logger.debug("scheduling end for current profile: %s", entry.getScheduledEnd())
        self.scheduleSelection(entry.getScheduledEnd())

        try:
            self.source.activateProfile(entry.getProfile())
            self.source.start()
        except KeyError:
            pass


class ServiceHandler(object):
    def __init__(self, source):
        self.lock = threading.Lock()
        self.services = []
        self.source = source
        self.startupTimer = None
        self.source.addClient(self)
        props = self.source.getProps()
        props.collect("center_freq", "samp_rate").wire(self.onFrequencyChange)
        if self.source.isAvailable():
            self.scheduleServiceStartup()
        self.scheduler = None
        if "schedule" in props:
            self.scheduler = ServiceScheduler(self.source, props["schedule"])

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

    def onBusyStateChange(self, state):
        pass

    def isSupported(self, mode):
        # TODO this should be in a more central place (the frontend also needs this)
        requirements = {
            "ft8": "wsjt-x",
            "ft4": "wsjt-x",
            "jt65": "wsjt-x",
            "jt9": "wsjt-x",
            "wspr": "wsjt-x",
            "packet": "packet",
        }
        fd = FeatureDetector()

        # this looks overly complicated... but i'd like modes with no requirements to be always available without
        # being listed in the hash above
        unavailable = [mode for mode, req in requirements.items() if not fd.is_available(req)]
        configured = PropertyManager.getSharedInstance()["services_decoders"]
        available = [mode for mode in configured if mode not in unavailable]

        return mode in available

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

    def updateServices(self):
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

        with self.lock:
            self.services = []

            groups = self.optimizeResampling(dials, sr)
            if groups is None:
                for dial in dials:
                    self.services.append(self.setupService(dial["mode"], dial["frequency"], self.source))
            else:
                for group in groups:
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
                    resampler = Resampler(resampler_props, self.source)
                    resampler.start()

                    for dial in group:
                        self.services.append(self.setupService(dial["mode"], dial["frequency"], resampler))

                    # resampler goes in after the services since it must not be shutdown as long as the services are still running
                    self.services.append(resampler)

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
        # another possible outcome might be that it's best not to resample at all. this is a special case.
        usages += [{"num_splits": None, "total_bandwidth": bandwidth * len(freqs), "groups": [freqs]}]
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
    handlers = []

    @staticmethod
    def start():
        if not PropertyManager.getSharedInstance()["services_enabled"]:
            return
        for source in SdrService.getSources().values():
            Services.handlers.append(ServiceHandler(source))

    @staticmethod
    def stop():
        for handler in Services.handlers:
            handler.shutdown()
        Services.handlers = []


class Service(object):
    pass


class WsjtService(Service):
    pass
