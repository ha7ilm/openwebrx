from . import Controller
from owrx.feature import FeatureDetector
from owrx.config import Config
import json


class ApiController(Controller):
    def indexAction(self):
        data = json.dumps(FeatureDetector().feature_report())
        self.send_response(data, content_type="application/json")

    def receiverDetails(self):
        receiver_details = Config.get().filter(
            "receiver_name",
            "receiver_location",
            "receiver_asl",
            "receiver_gps",
            "photo_title",
            "photo_desc",
        )
        data = json.dumps(receiver_details.__dict__())
        self.send_response(data, content_type="application/json")
