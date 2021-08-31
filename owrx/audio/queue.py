from owrx.config import Config
from owrx.config.core import CoreConfig
from owrx.metrics import Metrics, CounterMetric, DirectMetric
from queue import Queue, Full, Empty
import subprocess
import os
import threading

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class QueueJobResult:
    def __init__(self, profile, frequency, lines):
        self.profile = profile
        self.frequency = frequency
        self.lines = lines


class QueueJob(object):
    def __init__(self, profile, frequency, writer, file):
        self.profile = profile
        self.frequency = frequency
        self.writer = writer
        self.file = file

    def run(self):
        logger.debug("processing file %s", self.file)
        tmp_dir = CoreConfig().get_temporary_directory()
        decoder = subprocess.Popen(
            ["nice", "-n", "10"] + self.profile.decoder_commandline(self.file),
            stdout=subprocess.PIPE,
            cwd=tmp_dir,
            close_fds=True,
            )
        lines = None
        try:
            lines = [l for l in decoder.stdout]
        except OSError:
            decoder.stdout.flush()
            # TODO uncouple parsing from the output so that decodes can still go to the map and the spotters
            logger.debug("output has gone away while decoding job.")

        # keep this out of the try/except
        if lines is not None:
            self.writer.sendResult(QueueJobResult(self.profile, self.frequency, lines))

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

    def put(self, item, **kwargs):
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
