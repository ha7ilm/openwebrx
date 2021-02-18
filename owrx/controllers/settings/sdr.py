from owrx.controllers.admin import AuthorizationMixin
from owrx.controllers.template import WebpageController
from owrx.config import Config


class SdrSettingsController(AuthorizationMixin, WebpageController):
    def header_variables(self):
        variables = super().header_variables()
        variables["assets_prefix"] = "../"
        return variables

    def template_variables(self):
        variables = super().template_variables()
        variables["content"] = self.render_devices()
        variables["title"] = "SDR device settings"
        return variables

    def render_devices(self):
        def render_device(device_id, config):
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

        return """
            <div class="col-12">
                {devices}
            </div>
        """.format(
            devices="".join(render_device(key, value) for key, value in Config.get()["sdrs"].items())
        )

    def indexAction(self):
        self.serve_template("settings/general.html", **self.template_variables())
