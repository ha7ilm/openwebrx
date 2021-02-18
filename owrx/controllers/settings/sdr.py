from owrx.controllers.admin import AuthorizationMixin
from owrx.controllers.template import WebpageController
from owrx.config import Config
from urllib.parse import quote
import json


class SdrSettingsController(AuthorizationMixin, WebpageController):
    def header_variables(self):
        variables = super().header_variables()
        variables["assets_prefix"] = "../"
        return variables

    def template_variables(self):
        variables = super().template_variables()
        variables["sections"] = self.render_devices()
        variables["title"] = "SDR device settings"
        return variables

    def render_devices(self):
        return """
            <div class="col-12">
                {devices}
            </div>
        """.format(
            devices="".join(self.render_device(key, value) for key, value in Config.get()["sdrs"].items())
        )

    def render_device(self, device_id, config):
        return """
            <div class="card device bg-dark text-white">
                <div class="card-header">
                    {device_name}
                </div>
                <div class="card-body">
                    sdr detail goes here
                </div>
            </div>
        """.format(
            device_name=config["name"]
        )

    def indexAction(self):
        self.serve_template("settings/general.html", **self.template_variables())
