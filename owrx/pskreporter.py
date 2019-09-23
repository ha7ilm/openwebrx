import logging
import threading
import time
import random
from sched import scheduler

logger = logging.getLogger(__name__)


class PskReporter(object):
    sharedInstance = None
    creationLock = threading.Lock()
    interval = 300

    @staticmethod
    def getSharedInstance():
        with PskReporter.creationLock:
            if PskReporter.sharedInstance is None:
                PskReporter.sharedInstance = PskReporter()
        return PskReporter.sharedInstance

    def __init__(self):
        self.spots = []
        self.spotLock = threading.Lock()
        self.scheduler = scheduler(time.time, time.sleep)
        self.scheduleNextUpload()
        threading.Thread(target=self.scheduler.run).start()

    def scheduleNextUpload(self):
        delay = PskReporter.interval + random.uniform(-30, 30)
        logger.debug("scheduling next pskreporter upload in %f seconds", delay)
        self.scheduler.enter(delay, 1, self.upload)

    def spot(self, spot):
        with self.spotLock:
            self.spots.append(spot)

    def upload(self):
        with self.spotLock:
            spots = self.spots
            self.spots = []

        if spots:
            logger.debug("would now upload %i spots", len(spots))

        self.scheduleNextUpload()
