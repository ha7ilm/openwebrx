import threading
from owrx.config import Config
from owrx.reporting.reporter import Reporter
from owrx.reporting.pskreporter import PskReporter
from owrx.reporting.wsprnet import WsprnetReporter
import logging

logger = logging.getLogger(__name__)


class ReportingEngine(object):
    creationLock = threading.Lock()
    sharedInstance = None

    reporterClasses = {
        "pskreporter_enabled": PskReporter,
        "wsprnet_enabled": WsprnetReporter,
    }

    @staticmethod
    def getSharedInstance():
        with ReportingEngine.creationLock:
            if ReportingEngine.sharedInstance is None:
                ReportingEngine.sharedInstance = ReportingEngine()
            return ReportingEngine.sharedInstance

    @staticmethod
    def stopAll():
        with ReportingEngine.creationLock:
            if ReportingEngine.sharedInstance is not None:
                ReportingEngine.sharedInstance.stop()

    def __init__(self):
        self.reporters = []
        self.configSub = Config.get().filter(*ReportingEngine.reporterClasses.keys()).wire(self.setupReporters)
        self.setupReporters()

    def setupReporters(self, *args):
        config = Config.get()
        for configKey, reporterClass in ReportingEngine.reporterClasses.items():
            if configKey in config and config[configKey]:
                if not any(isinstance(r, reporterClass) for r in self.reporters):
                    self.reporters += [reporterClass()]
            else:
                for reporter in [r for r in self.reporters if isinstance(r, reporterClass)]:
                    reporter.stop()
                    self.reporters.remove(reporter)

    def stop(self):
        for r in self.reporters:
            r.stop()
        self.configSub.cancel()

    def spot(self, spot):
        for r in self.reporters:
            if spot["mode"] in r.getSupportedModes():
                r.spot(spot)
