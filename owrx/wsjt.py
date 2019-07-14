import threading
import wave
from datetime import datetime, timedelta, date
import time
import sched
import subprocess
import os
from multiprocessing.connection import Pipe
from owrx.map import Map, LocatorLocation
import re
from owrx.config import PropertyManager
from owrx.bands import Bandplan

import logging
logger = logging.getLogger(__name__)


class WsjtChopper(threading.Thread):
    def __init__(self, source):
        self.source = source
        self.tmp_dir = PropertyManager.getSharedInstance()["temporary_directory"]
        (self.wavefilename, self.wavefile) = self.getWaveFile()
        self.switchingLock = threading.Lock()
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.fileQueue = []
        (self.outputReader, self.outputWriter) = Pipe()
        self.doRun = True
        super().__init__()

    def getWaveFile(self):
        filename = "{tmp_dir}/openwebrx-wsjtchopper-{id}-{timestamp}.wav".format(
            tmp_dir = self.tmp_dir,
            id = id(self),
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
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
        t = zeroed + timedelta(seconds = seconds)
        logger.debug("scheduling: {0}".format(t))
        return t.timestamp()

    def startScheduler(self):
        self._scheduleNextSwitch()
        threading.Thread(target = self.scheduler.run).start()

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
        self.fileQueue.append(filename)
        self._scheduleNextSwitch()

    def decoder_commandline(self, file):
        '''
        must be overridden in child classes
        '''
        return []

    def decode(self):
        def decode_and_unlink(file):
            decoder = subprocess.Popen(self.decoder_commandline(file), stdout=subprocess.PIPE, cwd=self.tmp_dir)
            while True:
                line = decoder.stdout.readline()
                if line is None or (isinstance(line, bytes) and len(line) == 0):
                    break
                self.outputWriter.send(line)
            rc = decoder.wait()
            logger.debug("decoder return code: %i", rc)
            os.unlink(file)

            self.decoder = decoder

        if self.fileQueue:
            file = self.fileQueue.pop()
            logger.debug("processing file {0}".format(file))
            threading.Thread(target=decode_and_unlink, args=[file]).start()

    def run(self) -> None:
        logger.debug("WSJT chopper starting up")
        self.startScheduler()
        while self.doRun:
            data = self.source.read(256)
            if data is None or (isinstance(data, bytes) and len(data) == 0):
                logger.warning("zero read on WSJT chopper")
                self.doRun = False
            else:
                self.switchingLock.acquire()
                self.wavefile.writeframes(data)
                self.switchingLock.release()

            self.decode()
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


class Ft8Chopper(WsjtChopper):
    def __init__(self, source):
        self.interval = 15
        super().__init__(source)

    def decoder_commandline(self, file):
        #TODO expose decoding quality parameters through config
        return ["jt9", "--ft8", "-d", "3", file]


class WsprChopper(WsjtChopper):
    def __init__(self, source):
        self.interval = 120
        super().__init__(source)

    def decoder_commandline(self, file):
        #TODO expose decoding quality parameters through config
        return ["wsprd", "-d", file]


class Jt65Chopper(WsjtChopper):
    def __init__(self, source):
        self.interval = 60
        super().__init__(source)

    def decoder_commandline(self, file):
        #TODO expose decoding quality parameters through config
        return ["jt9", "--jt65", "-d", "3", file]


class Jt9Chopper(WsjtChopper):
    def __init__(self, source):
        self.interval = 60
        super().__init__(source)

    def decoder_commandline(self, file):
        #TODO expose decoding quality parameters through config
        return ["jt9", "--jt9", "-d", "3", file]


class WsjtParser(object):
    locator_pattern = re.compile(".*\\s([A-Z0-9]+)\\s([A-R]{2}[0-9]{2})$")
    jt9_pattern = re.compile("^([0-9]{6}|\\*{4}) .*")
    wspr_pattern = re.compile("^[0-9]{4} .*")
    wspr_splitter_pattern = re.compile("([A-Z0-9]*)\\s([A-R]{2}[0-9]{2})\\s([0-9]+)")

    def __init__(self, handler):
        self.handler = handler
        self.dial_freq = None
        self.band = None

    modes = {
        "~": "FT8",
        "#": "JT65",
        "@": "JT9"
    }

    def parse(self, data):
        try:
            msg = data.decode().rstrip()
            # known debug messages we know to skip
            if msg.startswith("<DecodeFinished>"):
                return
            if msg.startswith(" EOF on input file"):
                return

            out = {}
            if WsjtParser.jt9_pattern.match(msg):
                out = self.parse_from_jt9(msg)
            elif WsjtParser.wspr_pattern.match(msg):
                out = self.parse_from_wsprd(msg)

            self.handler.write_wsjt_message(out)
        except ValueError:
            logger.exception("error while parsing wsjt message")

    def parse_from_jt9(self, msg):
        # ft8 sample
        # '222100 -15 -0.0  508 ~  CQ EA7MJ IM66'
        # jt65 sample
        # '**** -10  0.4 1556 #  CQ RN6AM KN95'
        out = {}
        if msg.startswith("****"):
            out["timestamp"] = int(datetime.now().timestamp() * 1000)
            msg = msg[5:]
        else:
            ts = datetime.strptime(msg[0:6], "%H%M%S")
            out["timestamp"] = int(datetime.combine(date.today(), ts.time(), datetime.now().tzinfo).timestamp() * 1000)
            msg = msg[7:]
        out["db"] = float(msg[0:3])
        out["dt"] = float(msg[4:8])
        out["freq"] = int(msg[9:13])
        modeChar = msg[14:15]
        out["mode"] = mode = WsjtParser.modes[modeChar] if modeChar in WsjtParser.modes else "unknown"
        wsjt_msg = msg[17:53].strip()
        self.parseLocator(wsjt_msg, mode)
        out["msg"] = wsjt_msg
        return out

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
        out = {}
        now = datetime.now()
        ts = datetime.strptime(msg[0:4], "%M%S").replace(hour=now.hour)
        out["timestamp"] = int(datetime.combine(date.today(), ts.time(), now.tzinfo).timestamp() * 1000)
        out["db"] = float(msg[5:8])
        out["dt"] = float(msg[9:13])
        out["freq"] = float(msg[14:24])
        out["drift"] = int(msg[25:28])
        out["mode"] = "WSPR"
        wsjt_msg = msg[29:].strip()
        out["msg"] = wsjt_msg
        self.parseWsprMessage(wsjt_msg)
        return out

    def parseWsprMessage(self, msg):
        m = WsjtParser.wspr_splitter_pattern.match(msg)
        if m is None:
            return
        Map.getSharedInstance().updateLocation(m.group(1), LocatorLocation(m.group(2)), "WSPR", self.band)

    def setDialFrequency(self, freq):
        self.dial_freq = freq
        self.band = Bandplan.getSharedInstance().findBand(freq)
