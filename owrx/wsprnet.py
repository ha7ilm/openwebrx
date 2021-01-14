from owrx.reporting import Reporter
from owrx.version import openwebrx_version
from owrx.config import Config
from owrx.locator import Locator
from queue import Queue, Full
from urllib import request, parse
import threading
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class Worker(threading.Thread):
    def __init__(self, queue: Queue):
        self.queue = queue
        self.doRun = True
        # some constants that we don't expect to change
        config = Config.get()
        self.callsign = config["wsprnet_callsign"]
        self.locator = Locator.fromCoordinates(config["receiver_gps"])

        super().__init__(daemon=True)

    def run(self):
        while self.doRun:
            try:
                spot = self.queue.get()
                self.uploadSpot(spot)
                self.queue.task_done()
            except Exception:
                logger.exception("Exception while uploading WSPRNet spot")

    def uploadSpot(self, spot):
        # function=wspr&date=210114&time=1732&sig=-15&dt=0.5&drift=0&tqrg=7.040019&tcall=DF2UU&tgrid=JN48&dbm=37&version=2.3.0-rc3&rcall=DD5JFK&rgrid=JN58SC&rqrg=7.040047&mode=2
        # {'timestamp': 1610655960000, 'db': -23.0, 'dt': 0.3, 'freq': 7040048, 'drift': -1, 'msg': 'LA3JJ JO59 37', 'callsign': 'LA3JJ', 'locator': 'JO59', 'mode': 'WSPR'}
        date = datetime.fromtimestamp(spot["timestamp"] / 1000, tz=timezone.utc)
        data = parse.urlencode({
            "function": "wspr",
            "date": date.strftime("%y%m%d"),
            "time": date.strftime("%H%M"),
            "sig": spot["db"],
            "dt": spot["dt"],
            "drift": spot["drift"],
            "tqrg": spot["freq"] / 1E6,
            "tcall": spot["callsign"],
            "tgrid": spot["locator"],
            "dbm": spot["dbm"],
            "version": openwebrx_version,
            "rcall": self.callsign,
            "rgrid": self.locator,
            # mode 2 = WSPR 2 minutes
            # TODO implement FST4W mode codes
            "mode": 2
        }).encode()
        request.urlopen("http://wsprnet.org/post/", data)


class WsprnetReporter(Reporter):
    def __init__(self):
        # max 100 entries
        self.queue = Queue(100)
        # single worker
        Worker(self.queue).start()

    def stop(self):
        pass

    def spot(self, spot):
        try:
            self.queue.put(spot, block=False)
        except Full:
            logger.warning("WSPRNet Queue overflow, one spot lost")

    def getSupportedModes(self):
        return ["WSPR"]
