from owrx.config.core import CoreConfig
from owrx.audio import AudioChopperProfile
from owrx.audio.queue import QueueJob, DecoderQueue
import threading
import wave
import os
from multiprocessing.connection import Pipe
from datetime import datetime, timedelta
from queue import Full
from typing import List

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class WaveFile(object):
    def __init__(self, filename):
        self.filename = filename
        self.waveFile = wave.open(filename, "wb")
        self.waveFile.setnchannels(1)
        self.waveFile.setsampwidth(2)
        self.waveFile.setframerate(12000)

    def close(self):
        self.waveFile.close()

    def getFileName(self):
        return self.filename

    def writeframes(self, data):
        return self.waveFile.writeframes(data)

    def unlink(self):
        os.unlink(self.filename)
        self.waveFile = None


class AudioWriter(object):
    def __init__(self, active_dsp, outputWriter, interval, profiles: List[AudioChopperProfile]):
        self.dsp = active_dsp
        self.outputWriter = outputWriter
        self.interval = interval
        self.profiles = profiles
        self.wavefile = None
        self.switchingLock = threading.Lock()
        self.timer = None

    def getWaveFile(self):
        tmp_dir = CoreConfig().get_temporary_directory()
        filename = "{tmp_dir}/openwebrx-audiochopper-master-{id}-{timestamp}.wav".format(
            tmp_dir=tmp_dir,
            id=id(self),
            timestamp=datetime.utcnow().strftime("%y%m%d_%H%M%S"),
        )
        return WaveFile(filename)

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
            self.timer = None

    def _scheduleNextSwitch(self):
        self.cancelTimer()
        delta = self.getNextDecodingTime() - datetime.utcnow()
        self.timer = threading.Timer(delta.total_seconds(), self.switchFiles)
        self.timer.start()

    def switchFiles(self):
        with self.switchingLock:
            file = self.wavefile
            self.wavefile = self.getWaveFile()

        file.close()
        for profile in self.profiles:
            tmp_dir = CoreConfig().get_temporary_directory()

            # create hardlinks for the individual profiles
            filename = "{tmp_dir}/openwebrx-audiochopper-{pid}-{timestamp}.wav".format(
                tmp_dir=tmp_dir,
                pid=id(profile),
                timestamp=datetime.utcnow().strftime(profile.getFileTimestampFormat()),
            )
            try:
                os.link(file.getFileName(), filename)
            except OSError:
                logger.warning("Error while linking job files")
                continue

            job = QueueJob(profile, self.outputWriter, filename, self.dsp.get_operating_freq())
            try:
                DecoderQueue.getSharedInstance().put(job)
            except Full:
                logger.warning("decoding queue overflow; dropping one file")
                job.unlink()

        # our master can be deleted now, the profiles will delete their hardlinked copies after processing
        file.unlink()

        self._scheduleNextSwitch()

    def start(self):
        self.wavefile = self.getWaveFile()
        self._scheduleNextSwitch()

    def write(self, data):
        with self.switchingLock:
            self.wavefile.writeframes(data)

    def stop(self):
        self.cancelTimer()
        try:
            self.wavefile.close()
        except Exception:
            logger.exception("error closing wave file")
        try:
            with self.switchingLock:
                self.wavefile.unlink()
        except Exception:
            logger.exception("error removing undecoded file")
        self.wavefile = None
