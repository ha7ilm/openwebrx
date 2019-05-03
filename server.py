from http.server import HTTPServer
from owrx.http import RequestHandler

server = HTTPServer(('0.0.0.0', 3000), RequestHandler)
server.serve_forever()

