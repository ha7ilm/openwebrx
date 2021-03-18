from http.server import HTTPServer
from owrx.http import RequestHandler
from owrx.config.core import CoreConfig
from owrx.config import Config
from owrx.feature import FeatureDetector
from owrx.sdr import SdrService
from socketserver import ThreadingMixIn
from owrx.service import Services
from owrx.websocket import WebSocketConnection
from owrx.reporting import ReportingEngine
from owrx.version import openwebrx_version
from owrx.audio import DecoderQueue
import signal

import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ThreadedHttpServer(ThreadingMixIn, HTTPServer):
    pass


class SignalException(Exception):
    pass


def handleSignal(sig, frame):
    raise SignalException("Received Signal {sig}".format(sig=sig))


def main():
    print(
        """

OpenWebRX - Open Source SDR Web App for Everyone!  | for license see LICENSE file in the package
_________________________________________________________________________________________________

Author contact info:    Jakob Ketterl, DD5JFK <dd5jfk@darc.de>
Documentation:          https://github.com/jketterl/openwebrx/wiki
Support and info:       https://groups.io/g/openwebrx

    """
    )

    logger.info("OpenWebRX version {0} starting up...".format(openwebrx_version))

    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, handleSignal)

    # config warmup
    Config.validateConfig()
    coreConfig = CoreConfig()

    featureDetector = FeatureDetector()
    if not featureDetector.is_available("core"):
        logger.error(
            "you are missing required dependencies to run openwebrx. "
            "please check that the following core requirements are installed and up to date:"
        )
        logger.error(", ".join(featureDetector.get_requirements("core")))
        return

    # Get error messages about unknown / unavailable features as soon as possible
    # start up "always-on" sources right away
    SdrService.getAllSources()

    Services.start()

    try:
        server = ThreadedHttpServer(("0.0.0.0", coreConfig.get_web_port()), RequestHandler)
        server.serve_forever()
    except SignalException:
        WebSocketConnection.closeAll()
        Services.stop()
        ReportingEngine.stopAll()
        DecoderQueue.stopAll()
