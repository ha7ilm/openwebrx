from owrx.controllers.admin import AuthorizationMixin
from owrx.controllers.template import WebpageController
from owrx.controllers.settings import SettingsFormController
from owrx.controllers.settings.devices import SdrDeviceType
from owrx.config import Config
from urllib.parse import quote, unquote


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
        self.device = self._get_device()

    def getSections(self):
        device_type = SdrDeviceType.getByType(self.device["type"])
        if device_type is None:
            # TODO provide a generic interface that allows to switch the type
            return []
        return [device_type.getSection()]

    def getTitle(self):
        return self.device["name"]

    def _get_device(self):
        device_id = unquote(self.request.matches.group(1))
        if device_id not in Config.get()["sdrs"]:
            return None
        return Config.get()["sdrs"][device_id]

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
