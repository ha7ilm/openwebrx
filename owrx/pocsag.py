from csdr.module import PickleModule
from owrx.bands import Bandplan
from owrx.metrics import Metrics, CounterMetric
from owrx.reporting import ReportingEngine
import logging

logger = logging.getLogger(__name__)


class PocsagParser(PickleModule):
    def __init__(self):
        self.band = None
        super().__init__()

    def process(self, meta):
        try:
            if "address" in meta:
                meta["address"] = int(meta["address"])
            meta["mode"] = "Pocsag"
            self.pushDecode()
            ReportingEngine.getSharedInstance().spot(meta)
            return meta
        except Exception:
            logger.exception("Exception while parsing Pocsag message")

    def setDialFrequency(self, freq: int) -> None:
        self.band = Bandplan.getSharedInstance().findBand(freq)

    def pushDecode(self):
        band = "unknown"
        if self.band is not None:
            band = self.band.getName()
        name = "digiham.decodes.{band}.pocsag".format(band=band)
        metrics = Metrics.getSharedInstance()
        metric = metrics.getMetric(name)
        if metric is None:
            metric = CounterMetric()
            metrics.addMetric(name, metric)
        metric.inc()
