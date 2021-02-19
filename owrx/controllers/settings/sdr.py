from owrx.controllers.admin import AuthorizationMixin
from owrx.controllers.template import WebpageController
from owrx.controllers.settings import SettingsFormController
from owrx.source import SdrDeviceDescription, SdrDeviceDescriptionMissing
from owrx.config import Config
from urllib.parse import quote, unquote

import logging

logger = logging.getLogger(__name__)


class SdrDeviceListController(AuthorizationMixin, WebpageController):
    def header_variables(self):
        variables = super().header_variables()
        variables["assets_prefix"] = "../"
        return variables

    def template_variables(self):
        variables = super().template_variables()
        variables["content"] = self.render_devices()
        variables["title"] = "SDR device settings"
        variables["assets_prefix"] = "../"
        return variables

    def render_devices(self):
        def render_device(device_id, config):
            return """
            <li class="list-group-item">
                <a href="{device_link}">
                    <h3>{device_name}</h3>
                </a>
                <div>
                    some more device info here
                </div>
            </li>
        """.format(
                device_name=config["name"],
                device_link="{}/{}".format(self.request.path, quote(device_id)),
            )

        return """
            <ul class="row list-group list-group-flush sdr-device-list">
                {devices}
            </ul>
        """.format(
            devices="".join(render_device(key, value) for key, value in Config.get()["sdrs"].items())
        )

    def indexAction(self):
        self.serve_template("settings/general.html", **self.template_variables())


class SdrDeviceController(SettingsFormController):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        self.device_id, self.device = self._get_device()

    def getData(self):
        return self.device

    def store(self):
        # need to overwrite the existing key in the config since the layering won't capture the changes otherwise
        config = Config.get()
        sdrs = config["sdrs"]
        sdrs[self.device_id] = self.getData()
        config["sdrs"] = sdrs
        super().store()

    def getSections(self):
        try:
            description = SdrDeviceDescription.getByType(self.device["type"])
            return [description.getSection()]
        except SdrDeviceDescriptionMissing:
            # TODO provide a generic interface that allows to switch the type
            return []

    def getTitle(self):
        return self.device["name"]

    def _get_device(self):
        device_id = unquote(self.request.matches.group(1))
        if device_id not in Config.get()["sdrs"]:
            return None
        return device_id, Config.get()["sdrs"][device_id]

    def header_variables(self):
        variables = super().header_variables()
        variables["assets_prefix"] = "../../"
        return variables

    def template_variables(self):
        variables = super().template_variables()
        variables["assets_prefix"] = "../../"
        return variables

    def indexAction(self):
        if self.device is None:
            self.send_response("device not found", code=404)
            return
        self.serve_template("settings/general.html", **self.template_variables())
