from abc import ABC, ABCMeta, abstractmethod
from owrx.config.core import CoreConfig
from owrx.config import Config
from owrx.metrics import Metrics, CounterMetric, DirectMetric
import threading
import wave
import subprocess
import os
from multiprocessing.connection import Pipe, wait
from datetime import datetime, timedelta
from queue import Queue, Full, Empty
from itertools import groupby

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class QueueJob(object):
    def __init__(self, profile, writer, file, freq):
        self.profile = profile
        self.writer = writer
        self.file = file
        self.freq = freq

    def run(self):
        logger.debug("processing file %s", self.file)
        tmp_dir = CoreConfig().get_temporary_directory()
        decoder = subprocess.Popen(
            ["nice", "-n", "10"] + self.profile.decoder_commandline(self.file),
            stdout=subprocess.PIPE,
            cwd=tmp_dir,
            close_fds=True,
            )
        try:
            for line in decoder.stdout:
                self.writer.send((self.profile, self.freq, line))
        except (OSError, AttributeError):
            decoder.stdout.flush()
            # TODO uncouple parsing from the output so that decodes can still go to the map and the spotters
            logger.debug("output has gone away while decoding job.")
        try:
            rc = decoder.wait(timeout=10)
            if rc != 0:
                raise RuntimeError("decoder return code: {0}".format(rc))
        except subprocess.TimeoutExpired:
            logger.warning("subprocess (pid=%i}) did not terminate correctly; sending kill signal.", decoder.pid)
            decoder.kill()
            raise

    def unlink(self):
        try:
            os.unlink(self.file)
        except FileNotFoundError:
            pass


PoisonPill = object()


class QueueWorker(threading.Thread):
    def __init__(self, queue):
        self.queue = queue
        self.doRun = True
        super().__init__()

    def run(self) -> None:
        while self.doRun:
            job = self.queue.get()
            if job is PoisonPill:
                self.stop()
            else:
                try:
                    job.run()
                except Exception:
                    logger.exception("failed to decode job")
                    self.queue.onError()
                finally:
                    job.unlink()

            self.queue.task_done()

    def stop(self):
        self.doRun = False


class DecoderQueue(Queue):
    sharedInstance = None
    creationLock = threading.Lock()

    @staticmethod
    def getSharedInstance():
        with DecoderQueue.creationLock:
            if DecoderQueue.sharedInstance is None:
                DecoderQueue.sharedInstance = DecoderQueue()
        return DecoderQueue.sharedInstance

    @staticmethod
    def stopAll():
        with DecoderQueue.creationLock:
            if DecoderQueue.sharedInstance is not None:
                DecoderQueue.sharedInstance.stop()
                DecoderQueue.sharedInstance = None

    def __init__(self):
        pm = Config.get()
        super().__init__(pm["decoding_queue_length"])
        self.workers = []
        self._setWorkers(pm["decoding_queue_workers"])
        self.subscriptions = [
            pm.wireProperty("decoding_queue_length", self._setMaxSize),
            pm.wireProperty("decoding_queue_workers", self._setWorkers),
        ]
        metrics = Metrics.getSharedInstance()
        metrics.addMetric("decoding.queue.length", DirectMetric(self.qsize))
        self.inCounter = CounterMetric()
        metrics.addMetric("decoding.queue.in", self.inCounter)
        self.outCounter = CounterMetric()
        metrics.addMetric("decoding.queue.out", self.outCounter)
        self.overflowCounter = CounterMetric()
        metrics.addMetric("decoding.queue.overflow", self.overflowCounter)
        self.errorCounter = CounterMetric()
        metrics.addMetric("decoding.queue.error", self.errorCounter)

    def _setMaxSize(self, size):
        if self.maxsize == size:
            return
        self.maxsize = size

    def _setWorkers(self, workers):
        while len(self.workers) > workers:
            logger.debug("stopping one worker")
            self.workers.pop().stop()
        while len(self.workers) < workers:
            logger.debug("starting one worker")
            self.workers.append(self.newWorker())

    def stop(self):
        logger.debug("shutting down the queue")
        while self.subscriptions:
            self.subscriptions.pop().cancel()
        try:
            # purge all remaining jobs
            while not self.empty():
                job = self.get()
                job.unlink()
                self.task_done()
        except Empty:
            pass
        # put() a PoisonPill for all active workers to shut them down
        for w in self.workers:
            if w.is_alive():
                self.put(PoisonPill)
        self.join()

    def put(self, item, **kwars):
        self.inCounter.inc()
        try:
            super(DecoderQueue, self).put(item, block=False)
        except Full:
            self.overflowCounter.inc()
            raise

    def get(self, **kwargs):
        # super.get() is blocking, so it would mess up the stats to inc() first
        out = super(DecoderQueue, self).get(**kwargs)
        self.outCounter.inc()
        return out

    def newWorker(self):
        worker = QueueWorker(self)
        worker.start()
        return worker

    def onError(self):
        self.errorCounter.inc()


class AudioChopperProfile(ABC):
    @abstractmethod
    def getInterval(self):
        pass

    @abstractmethod
    def getFileTimestampFormat(self):
        pass

    @abstractmethod
    def decoder_commandline(self, file):
        pass


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
    def __init__(self, active_dsp, interval, profiles: list[AudioChopperProfile]):
        self.dsp = active_dsp
        self.interval = interval
        self.profiles = profiles
        self.wavefile = None
        self.switchingLock = threading.Lock()
        self.timer = None
        (self.outputReader, self.outputWriter) = Pipe()

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
            os.link(file.getFileName(), filename)

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
        self.outputWriter.close()
        self.outputWriter = None

        # drain messages left in the queue so that the queue can be successfully closed
        # this is necessary since python keeps the file descriptors open otherwise
        try:
            while True:
                self.outputReader.recv()
        except EOFError:
            pass
        self.outputReader.close()
        self.outputReader = None

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


class AudioChopper(threading.Thread, metaclass=ABCMeta):
    def __init__(self, active_dsp, readfn: callable, *profiles: AudioChopperProfile):
        sorted_profiles = sorted(profiles, key=lambda p: p.getInterval())
        groups = {interval: list(group) for interval, group in groupby(sorted_profiles, key=lambda p: p.getInterval())}
        self.readfn = readfn
        self.writers = [AudioWriter(active_dsp, interval, profiles) for interval, profiles in groups.items()]
        self.doRun = True
        super().__init__()

    def run(self) -> None:
        logger.debug("Audio chopper starting up")
        for w in self.writers:
            w.start()
        while self.doRun:
            data = None
            try:
                data = self.readfn(256)
            except ValueError:
                pass
            if data is None or (isinstance(data, bytes) and len(data) == 0):
                self.doRun = False
            else:
                for w in self.writers:
                    w.write(data)

        logger.debug("Audio chopper shutting down")
        for w in self.writers:
            w.stop()

    def read(self):
        try:
            readers = wait([w.outputReader for w in self.writers])
            return [r.recv() for r in readers]
        except (EOFError, OSError):
            return None
