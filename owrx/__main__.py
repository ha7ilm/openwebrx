from http.server import HTTPServer
from owrx.http import RequestHandler
from owrx.config import PropertyManager
from owrx.feature import FeatureDetector
from owrx.sdr import SdrService
from socketserver import ThreadingMixIn
from owrx.sdrhu import SdrHuUpdater
from owrx.service import Services
from owrx.websocket import WebSocketConnection
from owrx.pskreporter import PskReporter

import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class ThreadedHttpServer(ThreadingMixIn, HTTPServer):
    pass


def main():
    print(
        """

OpenWebRX - Open Source SDR Web App for Everyone!  | for license see LICENSE file in the package
_________________________________________________________________________________________________

Author contact info:    Andras Retzler, HA7ILM <randras@sdr.hu>
Author contact info:    Jakob Ketterl, DD5JFK <dd5jfk@darc.de>

    """
    )

    pm = PropertyManager.getSharedInstance().loadConfig()

    featureDetector = FeatureDetector()
    if not featureDetector.is_available("core"):
        print(
            "you are missing required dependencies to run openwebrx. "
            "please check that the following core requirements are installed:"
        )
        print(", ".join(featureDetector.get_requirements("core")))
        return

    # Get error messages about unknown / unavailable features as soon as possible
    SdrService.loadProps()

    if "sdrhu_key" in pm and pm["sdrhu_public_listing"]:
        updater = SdrHuUpdater()
        updater.start()

    Services.start()

    try:
        server = ThreadedHttpServer(("0.0.0.0", pm.getPropertyValue("web_port")), RequestHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        WebSocketConnection.closeAll()
        Services.stop()
        PskReporter.stop()
