from . import Controller
from owrx.feature import FeatureDetector
import json


class ApiController(Controller):
    def indexAction(self):
        data = json.dumps(FeatureDetector().feature_report())
        self.send_response(data, content_type="application/json")
