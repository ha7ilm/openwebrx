from . import Controller
from owrx.config import Config
from datetime import datetime
import mimetypes
import os
import pkg_resources


class AssetsController(Controller):
    def getModified(self, file):
        return None

    def openFile(self, file):
        pass

    def serve_file(self, file, content_type=None):
        try:
            modified = self.getModified(file)

            if modified is not None and "If-Modified-Since" in self.handler.headers:
                client_modified = datetime.strptime(
                    self.handler.headers["If-Modified-Since"], "%a, %d %b %Y %H:%M:%S %Z"
                )
                if modified <= client_modified:
                    self.send_response("", code=304)
                    return

            f = self.openFile(file)
            data = f.read()
            f.close()

            if content_type is None:
                (content_type, encoding) = mimetypes.MimeTypes().guess_type(file)
            self.send_response(data, content_type=content_type, last_modified=modified, max_age=3600)
        except FileNotFoundError:
            self.send_response("file not found", code=404)

    def indexAction(self):
        filename = self.request.matches.group(1)
        self.serve_file(filename)


class OwrxAssetsController(AssetsController):
    def openFile(self, file):
        return pkg_resources.resource_stream("htdocs", file)


class AprsSymbolsController(AssetsController):
    def __init__(self, handler, request, options):
        pm = Config.get()
        path = pm["aprs_symbols_path"]
        if not path.endswith("/"):
            path += "/"
        self.path = path
        super().__init__(handler, request, options)

    def getFilePath(self, file):
        return self.path + file

    def getModified(self, file):
        return datetime.fromtimestamp(os.path.getmtime(self.getFilePath(file)))

    def openFile(self, file):
        return open(self.getFilePath(file), "rb")
