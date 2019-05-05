from http.server import HTTPServer
from owrx.http import RequestHandler
from owrx.config import PropertyManager
from owrx.source import RtlNmuxSource, SpectrumThread
from socketserver import ThreadingMixIn

class ThreadedHttpServer(ThreadingMixIn, HTTPServer):
    pass

def main():
    cfg=__import__("config_webrx")
    pm = PropertyManager.getSharedInstance()
    for name, value in cfg.__dict__.items():
        if (name.startswith("__")): continue
        pm.getProperty(name).setValue(value)

    RtlNmuxSource()

    server = ThreadedHttpServer(('0.0.0.0', pm.getPropertyValue("web_port")), RequestHandler)
    server.serve_forever()

if __name__=="__main__":
    main()
