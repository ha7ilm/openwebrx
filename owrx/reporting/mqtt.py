from paho.mqtt.client import Client
from owrx.reporting.reporter import Reporter
from owrx.config import Config
from owrx.property import PropertyDeleted
import json
import threading
import time

import logging

logger = logging.getLogger(__name__)


class MqttReporter(Reporter):
    DEFAULT_TOPIC = "openwebrx/decodes"

    def __init__(self):
        pm = Config.get()
        self.client = Client()
        self.topic = self.DEFAULT_TOPIC
        self.subscriptions = [
            pm.wireProperty("mqtt_host", self._setHost),
            pm.wireProperty("mqtt_topic", self._setTopic),
        ]
        self.run = True
        threading.Thread(target=self._loop).start()

    def _loop(self):
        # basic keepalive loop
        while self.run:
            self.client.loop()
            time.sleep(5)

    def _setHost(self, host):
        logger.debug("setting host to %s", host)
        self.client.disconnect()
        parts = host.split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 1883
        self.client.connect(host=host, port=port)

    def _setTopic(self, topic):
        if topic is PropertyDeleted:
            self.topic = self.DEFAULT_TOPIC
        else:
            self.topic = topic

    def stop(self):
        self.run = False
        self.client.disconnect()
        while self.subscriptions:
            self.subscriptions.pop().cancel()

    def spot(self, spot):
        self.client.publish(self.topic, payload=json.dumps(spot))
