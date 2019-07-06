import threading
import wave
from datetime import datetime, timedelta
import time
import sched
import subprocess

import logging
logger = logging.getLogger(__name__)


class Ft8Chopper(threading.Thread):
    def __init__(self, source):
        self.source = source
        (self.wavefilename, self.wavefile) = self.getWaveFile()
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.queue = []
        self.doRun = True
        super().__init__()

    def getWaveFile(self):
        filename = "/tmp/openwebrx-ft8chopper-{0}.wav".format(datetime.now().strftime("%Y%m%d-%H%M%S"))
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
        file = self.wavefile
        filename = self.wavefilename
        (self.wavefilename, self.wavefile) = self.getWaveFile()

        file.close()
        self.queue.append(filename)
        self._scheduleNextSwitch()

    def decode(self):
        if self.queue:
            file = self.queue.pop()
            logger.debug("processing file {0}".format(file))
            #TODO expose decoding quality parameters through config
            self.decoder = subprocess.Popen(["jt9", "--ft8", "-d", "3", file])

    def run(self) -> None:
        logger.debug("FT8 chopper starting up")
        self.startScheduler()
        while self.doRun:
            data = self.source.read(256)
            if data is None or (isinstance(data, bytes) and len(data) == 0):
                logger.warning("zero read on ft8 chopper")
                self.doRun = False
            else:
                self.wavefile.writeframes(data)

            self.decode()
        logger.debug("FT8 chopper shutting down")
        self.emptyScheduler()
