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

import logging
logger = logging.getLogger(__name__)


class Ft8Chopper(threading.Thread):
    def __init__(self, source):
        self.source = source
        (self.wavefilename, self.wavefile) = self.getWaveFile()
        self.switchingLock = threading.Lock()
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.fileQueue = []
        (self.outputReader, self.outputWriter) = Pipe()
        self.doRun = True
        super().__init__()

    def getWaveFile(self):
        filename = "/tmp/openwebrx-ft8chopper-{id}-{timestamp}.wav".format(
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
        seconds = (int(t.second / 15) + 1) * 15
        if seconds >= 60:
            t = t + timedelta(minutes = 1)
            seconds = 0
        t = t.replace(second = seconds, microsecond = 0)
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

    def decode(self):
        def decode_and_unlink(file):
            #TODO expose decoding quality parameters through config
            decoder = subprocess.Popen(["jt9", "--ft8", "-d", "3", file], stdout=subprocess.PIPE)
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
        logger.debug("FT8 chopper starting up")
        self.startScheduler()
        while self.doRun:
            data = self.source.read(256)
            if data is None or (isinstance(data, bytes) and len(data) == 0):
                logger.warning("zero read on ft8 chopper")
                self.doRun = False
            else:
                self.switchingLock.acquire()
                self.wavefile.writeframes(data)
                self.switchingLock.release()

            self.decode()
        logger.debug("FT8 chopper shutting down")
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


class WsjtParser(object):
    def __init__(self, handler):
        self.handler = handler
        self.locator_pattern = re.compile(".*\s([A-Z0-9]+)\s([A-R]{2}[0-9]{2})$")

    modes = {
        "~": "FT8"
    }

    def parse(self, data):
        try:
            msg = data.decode().rstrip()
            # sample
            # '222100 -15 -0.0  508 ~  CQ EA7MJ IM66'
            # known debug messages we know to skip
            if msg.startswith("<DecodeFinished>"):
                return
            if msg.startswith(" EOF on input file"):
                return

            out = {}
            ts = datetime.strptime(msg[0:6], "%H%M%S")
            out["timestamp"] = int(datetime.combine(date.today(), ts.time(), datetime.now().tzinfo).timestamp() * 1000)
            out["db"] = float(msg[7:10])
            out["dt"] = float(msg[11:15])
            out["freq"] = int(msg[16:20])
            modeChar = msg[21:22]
            out["mode"] = mode = WsjtParser.modes[modeChar] if modeChar in WsjtParser.modes else "unknown"
            wsjt_msg = msg[24:60].strip()
            self.parseLocator(wsjt_msg, mode)
            out["msg"] = wsjt_msg

            self.handler.write_wsjt_message(out)
        except ValueError:
            logger.exception("error while parsing wsjt message")

    def parseLocator(self, msg, mode):
        m = self.locator_pattern.match(msg)
        if m is None:
            return
        # this is a valid locator in theory, but it's somewhere in the arctic ocean, near the north pole, so it's very
        # likely this just means roger roger goodbye.
        if m.group(2) == "RR73":
            return
        Map.getSharedInstance().updateLocation(m.group(1), LocatorLocation(m.group(2)), mode)
