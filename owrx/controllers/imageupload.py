from owrx.controllers.assets import AssetsController
from owrx.controllers.admin import AuthorizationMixin
from owrx.config.core import CoreConfig
import uuid
import json


class ImageUploadController(AuthorizationMixin, AssetsController):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        self.file = request.query["file"][0] if "file" in request.query else None

    def getFilePath(self, file=None):
        if self.file is None:
            raise FileNotFoundError("missing filename")
        return "{tmp}/{file}".format(
            tmp=CoreConfig().get_temporary_directory(),
            file=self.file
        )

    def indexAction(self):
        self.serve_file(None)

    def _is_png(self, contents):
        return contents[0:8] == bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])

    def _is_jpg(self, contents):
        return contents[0:3] == bytes([0xFF, 0xD8, 0xFF])

    def processImage(self):
        if "id" not in self.request.query:
            self.send_response("{}", content_type="application/json", code=400)
        # TODO: limit file size
        contents = self.get_body()
        filetype = None
        if self._is_png(contents):
            filetype = "png"
        if self._is_jpg(contents):
            filetype = "jpg"
        if filetype is None:
            self.send_response("{}", content_type="application/json", code=400)
        else:
            self.file = "{id}-{uuid}.{ext}".format(
                id=self.request.query["id"][0],
                uuid=uuid.uuid4().hex,
                ext=filetype,
            )
            with open(self.getFilePath(), "wb") as f:
                f.write(contents)
            self.send_response(json.dumps({"file": self.file}), content_type="application/json")
