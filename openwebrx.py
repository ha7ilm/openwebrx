from http.server import HTTPServer
from owrx.http import RequestHandler
from owrx.config import PropertyManager, FeatureDetector
from owrx.source import SdrService
from socketserver import ThreadingMixIn
from owrx.sdrhu import SdrHuUpdater

import logging
logging.basicConfig(level = logging.DEBUG, format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class ThreadedHttpServer(ThreadingMixIn, HTTPServer):
    pass


def main():
    print("""

OpenWebRX - Open Source SDR Web App for Everyone!  | for license see LICENSE file in the package
_________________________________________________________________________________________________

Author contact info:    Andras Retzler, HA7ILM <randras@sdr.hu>

    """)

    pm = PropertyManager.getSharedInstance().loadConfig("config_webrx")

    featureDetector = FeatureDetector()
    if not featureDetector.is_available("core"):
        print("you are missing required dependencies to run openwebrx. "
              "please check that the following core requirements are installed:")
        print(", ".join(featureDetector.get_requirements("core")))
        return

    # Get error messages about unknown / unavailable features as soon as possible
    SdrService.loadProps()

    if "sdrhu_key" in pm and pm["sdrhu_public_listing"]:
        updater = SdrHuUpdater()
        updater.start()

    server = ThreadedHttpServer(('0.0.0.0', pm.getPropertyValue("web_port")), RequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
