import threading
import wave
from datetime import datetime, timedelta, timezone
import subprocess
import os
from multiprocessing.connection import Pipe
from owrx.map import Map, LocatorLocation
import re
from queue import Queue, Full
from owrx.config import PropertyManager
from owrx.bands import Bandplan
from owrx.metrics import Metrics, CounterMetric, DirectMetric
from owrx.pskreporter import PskReporter

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    creationLock = threading.Lock()

    @staticmethod
    def getSharedInstance():
        with WsjtQueue.creationLock:
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
        self.timer = None
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
        return filename, wavefile

    def getNextDecodingTime(self):
        t = datetime.utcnow()
        zeroed = t.replace(minute=0, second=0, microsecond=0)
        delta = t - zeroed
        seconds = (int(delta.total_seconds() / self.interval) + 1) * self.interval
        t = zeroed + timedelta(seconds=seconds)
        logger.debug("scheduling: {0}".format(t))
        return t

    def cancelTimer(self):
        if self.timer:
            self.timer.cancel()

    def _scheduleNextSwitch(self):
        if self.doRun:
            delta = self.getNextDecodingTime() - datetime.utcnow()
            self.timer = threading.Timer(delta.total_seconds(), self.switchFiles)
            self.timer.start()

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
        for line in decoder.stdout:
            self.outputWriter.send(line)
        try:
            rc = decoder.wait(timeout=10)
            if rc != 0:
                logger.warning("decoder return code: %i", rc)
        except subprocess.TimeoutExpired:
            logger.warning("subprocess (pid=%i}) did not terminate correctly; sending kill signal.", decoder.pid)
            decoder.kill()
        os.unlink(file)

    def run(self) -> None:
        logger.debug("WSJT chopper starting up")
        self._scheduleNextSwitch()
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
        self.cancelTimer()
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
                decoder = Jt9Decoder()
            else:
                decoder = WsprDecoder()
            out = decoder.parse(msg, self.dial_freq)
            if "mode" in out:
                self.pushDecode(out["mode"])
                if "callsign" in out and "locator" in out:
                    Map.getSharedInstance().updateLocation(
                        out["callsign"], LocatorLocation(out["locator"]), out["mode"], self.band
                    )
                    PskReporter.getSharedInstance().spot(out)

            self.handler.write_wsjt_message(out)
        except ValueError:
            logger.exception("error while parsing wsjt message")

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

    def setDialFrequency(self, freq):
        self.dial_freq = freq
        self.band = Bandplan.getSharedInstance().findBand(freq)


class Decoder(object):
    def parse_timestamp(self, instring, dateformat):
        ts = datetime.strptime(instring, dateformat)
        return int(
            datetime.combine(datetime.utcnow().date(), ts.time()).replace(tzinfo=timezone.utc).timestamp() * 1000
        )


class Jt9Decoder(Decoder):
    locator_pattern = re.compile("[A-Z0-9]+\\s([A-Z0-9]+)\\s([A-R]{2}[0-9]{2})$")

    def parse(self, msg, dial_freq):
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

        result = {
            "timestamp": timestamp,
            "db": float(msg[0:3]),
            "dt": float(msg[4:8]),
            "freq": dial_freq + int(msg[9:13]),
            "mode": mode,
            "msg": wsjt_msg,
        }
        result.update(self.parseMessage(wsjt_msg))
        return result

    def parseMessage(self, msg):
        m = Jt9Decoder.locator_pattern.match(msg)
        if m is None:
            return {}
        # this is a valid locator in theory, but it's somewhere in the arctic ocean, near the north pole, so it's very
        # likely this just means roger roger goodbye.
        if m.group(2) == "RR73":
            return {"callsign": m.group(1)}
        return {"callsign": m.group(1), "locator": m.group(2)}


class WsprDecoder(Decoder):
    wspr_splitter_pattern = re.compile("([A-Z0-9]*)\\s([A-R]{2}[0-9]{2})\\s([0-9]+)")

    def parse(self, msg, dial_freq):
        # wspr sample
        # '2600 -24  0.4   0.001492 -1  G8AXA JO01 33'
        # '0052 -29  2.6   0.001486  0  G02CWT IO92 23'
        wsjt_msg = msg[29:].strip()
        result = {
            "timestamp": self.parse_timestamp(msg[0:4], "%H%M"),
            "db": float(msg[5:8]),
            "dt": float(msg[9:13]),
            "freq": dial_freq + int(float(msg[14:24]) * 1e6),
            "drift": int(msg[25:28]),
            "mode": "WSPR",
            "msg": wsjt_msg,
        }
        result.update(self.parseMessage(wsjt_msg))
        return result

    def parseMessage(self, msg):
        m = WsprDecoder.wspr_splitter_pattern.match(msg)
        if m is None:
            return {}
        return {"callsign": m.group(1), "locator": m.group(2)}
