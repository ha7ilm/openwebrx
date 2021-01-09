import threading

import logging

logger = logging.getLogger(__name__)


class CpuUsageThread(threading.Thread):
    sharedInstance = None
    creationLock = threading.Lock()

    @staticmethod
    def getSharedInstance():
        with CpuUsageThread.creationLock:
            if CpuUsageThread.sharedInstance is None:
                CpuUsageThread.sharedInstance = CpuUsageThread()
        return CpuUsageThread.sharedInstance

    def __init__(self):
        self.clients = []
        self.doRun = True
        self.last_worktime = 0
        self.last_idletime = 0
        self.endEvent = threading.Event()
        super().__init__()

    def run(self):
        logger.debug("cpu usage thread starting up")
        while self.doRun:
            try:
                cpu_usage = self.get_cpu_usage()
            except:
                cpu_usage = 0
            for c in self.clients:
                c.write_cpu_usage(cpu_usage)
            self.endEvent.wait(timeout=3)
        logger.debug("cpu usage thread shut down")

    def get_cpu_usage(self):
        try:
            f = open("/proc/stat", "r")
        except:
            return 0  # Workaround, possibly we're on a Mac
        line = ""
        while not "cpu " in line:
            line = f.readline()
        f.close()
        spl = line.split(" ")
        worktime = int(spl[2]) + int(spl[3]) + int(spl[4])
        idletime = int(spl[5])
        dworktime = worktime - self.last_worktime
        didletime = idletime - self.last_idletime
        rate = float(dworktime) / (didletime + dworktime)
        self.last_worktime = worktime
        self.last_idletime = idletime
        if self.last_worktime == 0:
            return 0
        return rate

    def add_client(self, c):
        self.clients.append(c)
        if not self.is_alive():
            self.start()

    def remove_client(self, c):
        try:
            self.clients.remove(c)
        except ValueError:
            pass
        if not self.clients:
            self.shutdown()

    def shutdown(self):
        with CpuUsageThread.creationLock:
            CpuUsageThread.sharedInstance = None
        self.doRun = False
        self.endEvent.set()
