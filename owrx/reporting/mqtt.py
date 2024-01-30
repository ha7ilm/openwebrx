from paho.mqtt.client import Client
from owrx.reporting.reporter import Reporter
from owrx.config import Config
import json


class MqttReporter(Reporter):
    def __init__(self):
        pm = Config.get()
        self.client = Client()
        self.client.connect(host=pm["mqtt_host"])

    def stop(self):
        self.client.disconnect()

    def spot(self, spot):
        self.client.publish("openwebrx/spots", payload=json.dumps(spot))
