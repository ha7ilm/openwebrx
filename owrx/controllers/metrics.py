from . import Controller
from owrx.metrics import CounterMetric, DirectMetric, Metrics
import json
import re



class MetricsController(Controller):
    def indexAction(self):
        data = json.dumps(Metrics.getSharedInstance().getHierarchicalMetrics())
        self.send_response(data, content_type="application/json")

    def prometheusAction(self):
        metrics = Metrics.getSharedInstance().getFlatMetrics()

        def prometheusFormat(key, metric):
            value = metric.getValue()
            if isinstance(metric, CounterMetric):
                key += "_total"
                value = value["count"]
            elif isinstance(metric, DirectMetric):
                pass
            else:
                raise ValueError("Unexpected metric type for metric {}".format(repr(metric)))

            return "{key} {value}".format(key=re.sub('[^a-zA-Z0-9:_]', '_', key), value=value)

        data = ["# https://prometheus.io/docs/instrumenting/exposition_formats/"] + [
            prometheusFormat(k, v) for k, v in metrics.items()
        ]

        self.send_response("\n".join(data), content_type="text/plain; version=0.0.4")
