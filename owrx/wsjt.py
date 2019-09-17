import threading
import wave
from datetime import datetime, timedelta, date, timezone
import time
import sched
import subprocess
import os
from multiprocessing.connection import Pipe
from owrx.map import Map, LocatorLocation
import re
from queue import Queue, Full
from owrx.config import PropertyManager
from owrx.bands import Bandplan
from owrx.metrics import Metrics, CounterMetric, DirectMetric

import logging

logger = logging.getLogger(__name__)


class WsjtQueueWorker(threading.Thread):
    def __init__(self, queue):
        self.queue = queue
        self.doRun = True
        super().__init__(daemon=True)

    def run(self) -> None:
        while self.doRun:
            (processor, file) = self.queue.get()
            try:
                logger.debug("processing file %s", file)
                processor.decode(file)
            except Exception:
                logger.exception("failed to decode job")
                self.queue.onError()
            self.queue.task_done()


class WsjtQueue(Queue):
    sharedInstance = None

    @staticmethod
    def getSharedInstance():
        if WsjtQueue.sharedInstance is None:
            pm = PropertyManager.getSharedInstance()
            WsjtQueue.sharedInstance = WsjtQueue(maxsize=pm["wsjt_queue_length"], workers=pm["wsjt_queue_workers"])
        return WsjtQueue.sharedInstance

    def __init__(self, maxsize, workers):
        super().__init__(maxsize)
        metrics = Metrics.getSharedInstance()
        metrics.addMetric("wsjt.queue.length", DirectMetric(self.qsize))
        self.inCounter = CounterMetric()
        metrics.addMetric("wsjt.queue.in", self.inCounter)
        self.outCounter = CounterMetric()
        metrics.addMetric("wsjt.queue.out", self.outCounter)
        self.overflowCounter = CounterMetric()
        metrics.addMetric("wsjt.queue.overflow", self.overflowCounter)
        self.errorCounter = CounterMetric()
        metrics.addMetric("wsjt.queue.error", self.errorCounter)
        self.workers = [self.newWorker() for _ in range(0, workers)]

    def put(self, item):
        self.inCounter.inc()
        try:
            super(WsjtQueue, self).put(item, block=False)
        except Full:
            self.overflowCounter.inc()
            raise

    def get(self, **kwargs):
        # super.get() is blocking, so it would mess up the stats to inc() first
        out = super(WsjtQueue, self).get(**kwargs)
        self.outCounter.inc()
        return out

    def newWorker(self):
        worker = WsjtQueueWorker(self)
        worker.start()
        return worker

    def onError(self):
        self.errorCounter.inc()


class WsjtChopper(threading.Thread):
    def __init__(self, source):
        self.source = source
        self.tmp_dir = PropertyManager.getSharedInstance()["temporary_directory"]
        (self.wavefilename, self.wavefile) = self.getWaveFile()
        self.switchingLock = threading.Lock()
        self.scheduler = sched.scheduler(time.time, time.sleep)
        (self.outputReader, self.outputWriter) = Pipe()
        self.doRun = True
        super().__init__()

    def getWaveFile(self):
        filename = "{tmp_dir}/openwebrx-wsjtchopper-{id}-{timestamp}.wav".format(
            tmp_dir=self.tmp_dir, id=id(self), timestamp=datetime.utcnow().strftime(self.fileTimestampFormat)
        )
        wavefile = wave.open(filename, "wb")
        wavefile.setnchannels(1)
        wavefile.setsampwidth(2)
        wavefile.setframerate(12000)
        return (filename, wavefile)

    def getNextDecodingTime(self):
        t = datetime.now()
        zeroed = t.replace(minute=0, second=0, microsecond=0)
        delta = t - zeroed
        seconds = (int(delta.total_seconds() / self.interval) + 1) * self.interval
        t = zeroed + timedelta(seconds=seconds)
        logger.debug("scheduling: {0}".format(t))
        return t.timestamp()

    def startScheduler(self):
        self._scheduleNextSwitch()
        threading.Thread(target=self.scheduler.run).start()

    def emptyScheduler(self):
        for event in self.scheduler.queue:
            self.scheduler.cancel(event)

    def _scheduleNextSwitch(self):
        self.scheduler.enterabs(self.getNextDecodingTime(), 1, self.switchFiles)

    def switchFiles(self):
        self.switchingLock.acquire()
        file = self.wavefile
        filename = self.wavefilename
        (self.wavefilename, self.wavefile) = self.getWaveFile()
        self.switchingLock.release()

        file.close()
        try:
            WsjtQueue.getSharedInstance().put((self, filename))
        except Full:
            logger.warning("wsjt decoding queue overflow; dropping one file")
            os.unlink(filename)
        self._scheduleNextSwitch()

    def decoder_commandline(self, file):
        """
        must be overridden in child classes
        """
        return []

    def decode(self, file):
        decoder = subprocess.Popen(
            self.decoder_commandline(file), stdout=subprocess.PIPE, cwd=self.tmp_dir, preexec_fn=lambda: os.nice(10)
        )
        while True:
            line = decoder.stdout.readline()
            if line is None or (isinstance(line, bytes) and len(line) == 0):
                break
            self.outputWriter.send(line)
        rc = decoder.wait()
        if rc != 0:
            logger.warning("decoder return code: %i", rc)
        os.unlink(file)

    def run(self) -> None:
        logger.debug("WSJT chopper starting up")
        self.startScheduler()
        while self.doRun:
            data = self.source.read(256)
            if data is None or (isinstance(data, bytes) and len(data) == 0):
                self.doRun = False
            else:
                self.switchingLock.acquire()
                self.wavefile.writeframes(data)
                self.switchingLock.release()

        logger.debug("WSJT chopper shutting down")
        self.outputReader.close()
        self.outputWriter.close()
        self.emptyScheduler()
        try:
            os.unlink(self.wavefilename)
        except Exception:
            logger.exception("error removing undecoded file")

    def read(self):
        try:
            return self.outputReader.recv()
        except EOFError:
            return None

    def decoding_depth(self, mode):
        pm = PropertyManager.getSharedInstance()
        # mode-specific setting?
        if "wsjt_decoding_depths" in pm and mode in pm["wsjt_decoding_depths"]:
                return pm["wsjt_decoding_depths"][mode]
        # return global default
        if "wsjt_decoding_depth" in pm:
            return pm["wsjt_decoding_depth"]
        # default when no setting is provided
        return 3


class Ft8Chopper(WsjtChopper):
    def __init__(self, source):
        self.interval = 15
        self.fileTimestampFormat = "%y%m%d_%H%M%S"
        super().__init__(source)

    def decoder_commandline(self, file):
        return ["jt9", "--ft8", "-d", str(self.decoding_depth("ft8")), file]


class WsprChopper(WsjtChopper):
    def __init__(self, source):
        self.interval = 120
        self.fileTimestampFormat = "%y%m%d_%H%M"
        super().__init__(source)

    def decoder_commandline(self, file):
        cmd = ["wsprd"]
        if self.decoding_depth("wspr") > 1:
            cmd += ["-d"]
        cmd += [file]
        return cmd


class Jt65Chopper(WsjtChopper):
    def __init__(self, source):
        self.interval = 60
        self.fileTimestampFormat = "%y%m%d_%H%M"
        super().__init__(source)

    def decoder_commandline(self, file):
        return ["jt9", "--jt65", "-d", str(self.decoding_depth("jt65")), file]


class Jt9Chopper(WsjtChopper):
    def __init__(self, source):
        self.interval = 60
        self.fileTimestampFormat = "%y%m%d_%H%M"
        super().__init__(source)

    def decoder_commandline(self, file):
        return ["jt9", "--jt9", "-d", str(self.decoding_depth("jt9")), file]


class Ft4Chopper(WsjtChopper):
    def __init__(self, source):
        self.interval = 7.5
        self.fileTimestampFormat = "%y%m%d_%H%M%S"
        super().__init__(source)

    def decoder_commandline(self, file):
        return ["jt9", "--ft4", "-d", str(self.decoding_depth("ft4")), file]


class WsjtParser(object):
    locator_pattern = re.compile(".*\\s([A-Z0-9]+)\\s([A-R]{2}[0-9]{2})$")
    wspr_splitter_pattern = re.compile("([A-Z0-9]*)\\s([A-R]{2}[0-9]{2})\\s([0-9]+)")

    def __init__(self, handler):
        self.handler = handler
        self.dial_freq = None
        self.band = None

    modes = {"~": "FT8", "#": "JT65", "@": "JT9", "+": "FT4"}

    def parse(self, data):
        try:
            msg = data.decode().rstrip()
            # known debug messages we know to skip
            if msg.startswith("<DecodeFinished>"):
                return
            if msg.startswith(" EOF on input file"):
                return

            modes = list(WsjtParser.modes.keys())
            if msg[21] in modes or msg[19] in modes:
                out = self.parse_from_jt9(msg)
            else:
                out = self.parse_from_wsprd(msg)

            self.handler.write_wsjt_message(out)
        except ValueError:
            logger.exception("error while parsing wsjt message")

    def parse_timestamp(self, instring, dateformat):
        ts = datetime.strptime(instring, dateformat)
        return int(datetime.combine(date.today(), ts.time()).replace(tzinfo=timezone.utc).timestamp() * 1000)

    def pushDecode(self, mode):
        metrics = Metrics.getSharedInstance()
        band = "unknown"
        if self.band is not None:
            band = self.band.getName()
        if band is None:
            band = "unknown"

        if mode is None:
            mode = "unknown"

        name = "wsjt.decodes.{band}.{mode}".format(band=band, mode=mode)
        metric = metrics.getMetric(name)
        if metric is None:
            metric = CounterMetric()
            metrics.addMetric(name, metric)

        metric.inc()

    def parse_from_jt9(self, msg):
        # ft8 sample
        # '222100 -15 -0.0  508 ~  CQ EA7MJ IM66'
        # jt65 sample
        # '2352  -7  0.4 1801 #  R0WAS R2ABM KO85'
        # '0003  -4  0.4 1762 #  CQ R2ABM KO85'
        modes = list(WsjtParser.modes.keys())
        if msg[19] in modes:
            dateformat = "%H%M"
        else:
            dateformat = "%H%M%S"
        timestamp = self.parse_timestamp(msg[0 : len(dateformat)], dateformat)
        msg = msg[len(dateformat) + 1 :]
        modeChar = msg[14:15]
        mode = WsjtParser.modes[modeChar] if modeChar in WsjtParser.modes else "unknown"
        wsjt_msg = msg[17:53].strip()
        self.parseLocator(wsjt_msg, mode)

        self.pushDecode(mode)
        return {
            "timestamp": timestamp,
            "db": float(msg[0:3]),
            "dt": float(msg[4:8]),
            "freq": int(msg[9:13]),
            "mode": mode,
            "msg": wsjt_msg,
        }

    def parseLocator(self, msg, mode):
        m = WsjtParser.locator_pattern.match(msg)
        if m is None:
            return
        # this is a valid locator in theory, but it's somewhere in the arctic ocean, near the north pole, so it's very
        # likely this just means roger roger goodbye.
        if m.group(2) == "RR73":
            return
        Map.getSharedInstance().updateLocation(m.group(1), LocatorLocation(m.group(2)), mode, self.band)

    def parse_from_wsprd(self, msg):
        # wspr sample
        # '2600 -24  0.4   0.001492 -1  G8AXA JO01 33'
        # '0052 -29  2.6   0.001486  0  G02CWT IO92 23'
        wsjt_msg = msg[29:].strip()
        self.parseWsprMessage(wsjt_msg)
        self.pushDecode("WSPR")
        return {
            "timestamp": self.parse_timestamp(msg[0:4], "%H%M"),
            "db": float(msg[5:8]),
            "dt": float(msg[9:13]),
            "freq": float(msg[14:24]),
            "drift": int(msg[25:28]),
            "mode": "WSPR",
            "msg": wsjt_msg,
        }

    def parseWsprMessage(self, msg):
        m = WsjtParser.wspr_splitter_pattern.match(msg)
        if m is None:
            return
        Map.getSharedInstance().updateLocation(m.group(1), LocatorLocation(m.group(2)), "WSPR", self.band)

    def setDialFrequency(self, freq):
        self.dial_freq = freq
        self.band = Bandplan.getSharedInstance().findBand(freq)
