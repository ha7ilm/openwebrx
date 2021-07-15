from datetime import datetime, timezone, timedelta
from owrx.source import SdrSourceEventClient, SdrSourceState, SdrClientClass, SdrBusyState
from owrx.config import Config
import threading
import math
from abc import ABC, ABCMeta, abstractmethod

import logging

logger = logging.getLogger(__name__)


class ScheduleEntry(ABC):
    def __init__(self, startTime, endTime, profile):
        self.startTime = startTime
        self.endTime = endTime
        self.profile = profile

    def getProfile(self):
        return self.profile

    def __str__(self):
        return "{0} - {1}: {2}".format(self.startTime, self.endTime, self.profile)

    @abstractmethod
    def isCurrent(self, dt):
        pass

    @abstractmethod
    def getScheduledEnd(self):
        pass

    @abstractmethod
    def getNextActivation(self):
        pass


class TimeScheduleEntry(ScheduleEntry):
    def isCurrent(self, dt):
        time = dt.time()
        if self.startTime < self.endTime:
            return self.startTime <= time < self.endTime
        else:
            return self.startTime <= time or time < self.endTime

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


class DatetimeScheduleEntry(ScheduleEntry):
    def isCurrent(self, dt):
        return self.startTime <= dt < self.endTime

    def getScheduledEnd(self):
        return self.endTime

    def getNextActivation(self):
        return self.startTime


class Schedule(ABC):
    @staticmethod
    def parse(props):
        if "scheduler" in props:
            sc = props["scheduler"]
            t = sc["type"] if "type" in sc else "static"
            if t == "static":
                return StaticSchedule(sc["schedule"])
            elif t == "daylight":
                return DaylightSchedule(sc["schedule"])
            else:
                logger.warning("Invalid scheduler type: %s", t)
        # downwards compatibility
        elif "schedule" in props:
            return StaticSchedule(props["schedule"])

    @abstractmethod
    def getCurrentEntry(self):
        pass

    @abstractmethod
    def getNextEntry(self):
        pass


class TimerangeSchedule(Schedule, metaclass=ABCMeta):
    @abstractmethod
    def getEntries(self):
        pass

    def getCurrentEntry(self):
        current = [p for p in self.getEntries() if p.isCurrent(datetime.utcnow())]
        if current:
            return current[0]
        return None

    def getNextEntry(self):
        s = sorted(self.getEntries(), key=lambda e: e.getNextActivation())
        if s:
            return s[0]
        return None


class StaticSchedule(TimerangeSchedule):
    def __init__(self, scheduleDict):
        self.entries = []
        for time, profile in scheduleDict.items():
            if len(time) != 9:
                logger.warning("invalid schedule spec: %s", time)
                continue

            startTime = datetime.strptime(time[0:4], "%H%M").replace(tzinfo=timezone.utc).time()
            endTime = datetime.strptime(time[5:9], "%H%M").replace(tzinfo=timezone.utc).time()
            self.entries.append(TimeScheduleEntry(startTime, endTime, profile))

    def getEntries(self):
        return self.entries


class DaylightSchedule(TimerangeSchedule):
    greyLineTime = timedelta(hours=1)

    def __init__(self, scheduleDict):
        self.schedule = scheduleDict

    def getSunTimes(self, date):
        pm = Config.get()
        lat = pm["receiver_gps"]["lat"]
        lng = pm["receiver_gps"]["lon"]
        degtorad = math.pi / 180
        radtodeg = 180 / math.pi

        # Number of days since 01/01
        days = date.timetuple().tm_yday

        # Longitudinal correction
        longCorr = 4 * lng

        # calibrate for solstice
        b = 2 * math.pi * (days - 81) / 365

        # Equation of Time Correction
        eoTCorr = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)

        # Solar correction
        solarCorr = longCorr + eoTCorr

        # Solar declination
        declination = math.asin(math.sin(23.45 * degtorad) * math.sin(b))

        sunrise = 12 - math.acos(-math.tan(lat * degtorad) * math.tan(declination)) * radtodeg / 15 - solarCorr / 60
        sunset = 12 + math.acos(-math.tan(lat * degtorad) * math.tan(declination)) * radtodeg / 15 - solarCorr / 60

        midnight = datetime.combine(date, datetime.min.time())
        sunrise = midnight + timedelta(hours=sunrise)
        sunset = midnight + timedelta(hours=sunset)
        logger.debug("for {date} sunrise: {sunrise} sunset {sunset}".format(date=date, sunrise=sunrise, sunset=sunset))

        return sunrise, sunset

    def getEntries(self):
        now = datetime.utcnow()
        date = now.date()
        # greyline is optional, it its set it will shorten the other profiles
        useGreyline = "greyline" in self.schedule
        entries = []

        delta = DaylightSchedule.greyLineTime if useGreyline else timedelta()
        events = []
        # we need to start yesterday for longitudes close to the date line
        offset = -1
        while len(events) < 1:
            sunrise, sunset = self.getSunTimes(date + timedelta(days=offset))
            offset += 1
            events += [{"type": "sunrise", "time": sunrise}, {"type": "sunset", "time": sunset}]
            # keep only events in the future
            events = [v for v in events if v["time"] + delta > now]
        events.sort(key=lambda e: e["time"])

        previousEvent = None
        for event in events:
            # night profile _until_ sunrise, day profile _until_ sunset
            stype = "night" if event["type"] == "sunrise" else "day"
            if stype in self.schedule and (previousEvent is not None or event["time"] - delta > now):
                start = now if previousEvent is None else previousEvent
                entries.append(DatetimeScheduleEntry(start, event["time"] - delta, self.schedule[stype]))
            if useGreyline:
                entries.append(
                    DatetimeScheduleEntry(event["time"] - delta, event["time"] + delta, self.schedule["greyline"])
                )
            previousEvent = event["time"] + delta

        logger.debug([str(e) for e in entries])
        return entries


class ServiceScheduler(SdrSourceEventClient):
    def __init__(self, source):
        self.source = source
        self.selectionTimer = None
        self.currentEntry = None
        self.source.addClient(self)
        self.schedule = None
        props = self.source.getProps()
        self.subscriptions = []
        self.subscriptions.append(props.filter("center_freq", "samp_rate").wire(self.onFrequencyChange))
        self.subscriptions.append(props.wireProperty("scheduler", self.parseSchedule))
        # wireProperty calls parseSchedule with the initial value
        # self.parseSchedule()

    def parseSchedule(self, *args):
        props = self.source.getProps()
        self.schedule = Schedule.parse(props)
        self.scheduleSelection()

    def shutdown(self):
        while self.subscriptions:
            self.subscriptions.pop().cancel()
        self.cancelTimer()
        self.source.removeClient(self)

    def scheduleSelection(self, time=None):
        if not self.source.isEnabled() or self.source.isFailed():
            return
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

    def getClientClass(self) -> SdrClientClass:
        if self.currentEntry is None:
            return SdrClientClass.INACTIVE
        else:
            return SdrClientClass.BACKGROUND

    def onStateChange(self, state: SdrSourceState):
        if state is SdrSourceState.STOPPING:
            self.scheduleSelection()

    def onFail(self):
        self.shutdown()

    def onShutdown(self):
        self.shutdown()

    def onDisable(self):
        self.cancelTimer()

    def onEnable(self):
        self.scheduleSelection()

    def onBusyStateChange(self, state: SdrBusyState):
        if state is SdrBusyState.IDLE:
            self.scheduleSelection()

    def onFrequencyChange(self, changes):
        self.scheduleSelection()

    def _setCurrentEntry(self, entry):
        self.currentEntry = entry

        if entry is not None:
            logger.debug("selected profile %s until %s", entry.getProfile(), entry.getScheduledEnd())
            self.scheduleSelection(entry.getScheduledEnd())

            try:
                self.source.activateProfile(entry.getProfile())
                self.source.start()
            except KeyError:
                pass

        # tell the source to re-evaluate its current status
        # this should make it shut down if there's no other activity
        # TODO this is an improvised solution, should probably be integrated / improved in SdrSourceEventClient
        self.source.checkStatus()

    def selectProfile(self):
        if self.source.hasClients(SdrClientClass.USER):
            logger.debug("source has active users; not touching")
            return

        if self.schedule is None:
            self._setCurrentEntry(None)
            logger.debug("no active schedule, scheduler standing by for external events.")
            return

        logger.debug("source seems to be idle, selecting profile for background services")
        self._setCurrentEntry(self.schedule.getCurrentEntry())

        if self.currentEntry is None:
            logger.debug("schedule did not return a current profile. checking next (future) entry...")
            nextEntry = self.schedule.getNextEntry()
            if nextEntry is not None:
                self.scheduleSelection(nextEntry.getNextActivation())
            else:
                logger.debug("no next entry available, scheduler standing by for external events.")
            return
