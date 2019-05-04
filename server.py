from http.server import HTTPServer
from owrx.http import RequestHandler
from owrx.config import PropertyManager

cfg=__import__("config_webrx")
pm = PropertyManager.getSharedInstance()
for name, value in cfg.__dict__.items():
    if (name.startswith("__")): continue
    pm.getProperty(name).setValue(value)

server = HTTPServer(('0.0.0.0', 3000), RequestHandler)
server.serve_forever()

