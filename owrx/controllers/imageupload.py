from owrx.controllers.assets import AssetsController
from owrx.config import CoreConfig
import uuid
import json


# TODO: implement authorization
class ImageUploadController(AssetsController):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        self.uuid = request.query["uuid"][0] if "uuid" in request.query else None
        self.id = request.query["id"][0] if "id" in request.query else None

    def getFilePath(self, file=None):
        if self.uuid is None:
            raise FileNotFoundError("missing uuid")
        if self.id is None:
            raise FileNotFoundError("missing id")
        return "{tmp}/{file}-{uuid}".format(
            tmp=CoreConfig().get_temporary_directory(),
            file=self.id,
            uuid=self.uuid,
        )

    def indexAction(self):
        self.serve_file(None)

    def processImage(self):
        self.uuid = uuid.uuid4().hex
        # TODO: limit file size
        # TODO: check image mime type, if possible
        contents = self.get_body()
        # TODO: clean up files after timeout or on shutdown
        with open(self.getFilePath(), 'wb') as f:
            f.write(contents)
        self.send_response(json.dumps({"uuid": self.uuid}), content_type="application/json")
