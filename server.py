from http.server import HTTPServer
from owrx.http import RequestHandler
from owrx.config import PropertyManager, FeatureDetector, RequirementMissingException
from owrx.source import RtlNmuxSource
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
        pm.getProperty(name).setValue(value)

    try:
        FeatureDetector().detectAllFeatures()

    except RequirementMissingException as e:
        print("you are missing required dependencies to run openwebrx. "
              "please check the message and the readme for details:")
        print(e)
        return

    RtlNmuxSource()

    server = ThreadedHttpServer(('0.0.0.0', pm.getPropertyValue("web_port")), RequestHandler)
    server.serve_forever()


if __name__=="__main__":
    main()
