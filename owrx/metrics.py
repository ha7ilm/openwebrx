class Metrics(object):
    sharedInstance = None

    @staticmethod
    def getSharedInstance():
        if Metrics.sharedInstance is None:
            Metrics.sharedInstance = Metrics()
        return Metrics.sharedInstance

    def __init__(self):
        self.metrics = {}

    def pushDecodes(self, band, mode, count=1):
        if band is None:
            band = "unknown"
        else:
            band = band.getName()

        if mode is None:
            mode = "unknown"

        if not band in self.metrics:
            self.metrics[band] = {}
        if not mode in self.metrics[band]:
            self.metrics[band][mode] = {"count": 0}

        self.metrics[band][mode]["count"] += count

    def getMetrics(self):
        return self.metrics
