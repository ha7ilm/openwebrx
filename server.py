from http.server import HTTPServer
from owrx.http import RequestHandler
from owrx.config import PropertyManager, FeatureDetector, RequirementMissingException
from owrx.source import SdrService
from socketserver import ThreadingMixIn

class ThreadedHttpServer(ThreadingMixIn, HTTPServer):
    pass

def main():
    print()
    print("OpenWebRX - Open Source SDR Web App for Everyone!  | for license see LICENSE file in the package")
    print("_________________________________________________________________________________________________")
    print()
    print("Author contact info:    Andras Retzler, HA7ILM <randras@sdr.hu>")
    print()

    cfg=__import__("config_webrx")
    pm = PropertyManager.getSharedInstance()
    for name, value in cfg.__dict__.items():
        if (name.startswith("__")): continue
        pm[name] = value

    featureDetector = FeatureDetector()
    if not featureDetector.is_available("core"):
        print("you are missing required dependencies to run openwebrx. "
              "please check that the following core requirements are installed:")
        print(", ".join(featureDetector.get_requirements("core")))
        return

    server = ThreadedHttpServer(('0.0.0.0', pm.getPropertyValue("web_port")), RequestHandler)
    server.serve_forever()


if __name__=="__main__":
    main()
