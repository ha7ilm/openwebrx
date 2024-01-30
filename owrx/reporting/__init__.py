import threading
from owrx.config import Config
from owrx.reporting.reporter import Reporter, FilteredReporter
from owrx.reporting.pskreporter import PskReporter
from owrx.reporting.wsprnet import WsprnetReporter
from owrx.feature import FeatureDetector
import logging

logger = logging.getLogger(__name__)


class ReportingEngine(object):
    creationLock = threading.Lock()
    sharedInstance = None

    # concrete classes if they can be imported without the risk of optional dependencies
    # tuples if the import needs to be detected by a feature check
    reporterClasses = {
        "pskreporter": PskReporter,
        "wsprnet": WsprnetReporter,
        "mqtt": ("owrx.reporting.mqtt", "MqttReporter")
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
        configKeys = ["{}_enabled".format(n) for n in self.reporterClasses.keys()]
        self.configSub = Config.get().filter(*configKeys).wire(self.setupReporters)
        self.setupReporters()

    def setupReporters(self, *args):
        config = Config.get()
        for typeStr, reporterClass in self.reporterClasses.items():
            configKey = "{}_enabled".format(typeStr)
            if isinstance(reporterClass, tuple):
                # feature check
                if FeatureDetector().is_available(typeStr):
                    package, className = reporterClass
                    module = __import__(package, fromlist=[className])
                    reporterClass = getattr(module, className)
                else:
                    continue
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
            if not isinstance(r, FilteredReporter) or spot["mode"] in r.getSupportedModes():
                try:
                    r.spot(spot)
                except Exception:
                    logger.exception("error sending spot to reporter")
