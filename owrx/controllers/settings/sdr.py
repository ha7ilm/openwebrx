from owrx.controllers.admin import AuthorizationMixin
from owrx.controllers.template import WebpageController
from owrx.controllers.settings import SettingsFormController
from owrx.source import SdrDeviceDescription, SdrDeviceDescriptionMissing
from owrx.config import Config
from urllib.parse import quote, unquote
from owrx.sdr import SdrService
from abc import ABCMeta


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
            # TODO: this only returns non-failed sources...
            source = SdrService.getSource(device_id)

            return """
                <li class="list-group-item">
                    <a href="{device_link}">
                        <h3>{device_name}</h3>
                    </a>
                    <div>State: {state}</div>
                    <div>{num_profiles} profile(s)</div>
                </li>
            """.format(
                device_name=config["name"],
                device_link="{}/{}".format(self.request.path, quote(device_id)),
                state="Unknown" if source is None else source.getState(),
                num_profiles=len(config["profiles"]),
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


class SdrFormController(SettingsFormController, metaclass=ABCMeta):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        self.device_id, self.device = self._get_device()

    def store(self):
        # need to overwrite the existing key in the config since the layering won't capture the changes otherwise
        config = Config.get()
        sdrs = config["sdrs"]
        sdrs[self.device_id] = self.device
        config["sdrs"] = sdrs
        super().store()

    def _get_device(self):
        config = Config.get()
        device_id = unquote(self.request.matches.group(1))
        if device_id not in config["sdrs"]:
            return None
        return device_id, config["sdrs"][device_id]


class SdrDeviceController(SdrFormController):
    def getData(self):
        return self.device

    def getSections(self):
        try:
            description = SdrDeviceDescription.getByType(self.device["type"])
            return [description.getDeviceSection()]
        except SdrDeviceDescriptionMissing:
            # TODO provide a generic interface that allows to switch the type
            return []

    def getTitle(self):
        return self.device["name"]

    def header_variables(self):
        variables = super().header_variables()
        variables["assets_prefix"] = "../../"
        return variables

    def template_variables(self):
        variables = super().template_variables()
        variables["assets_prefix"] = "../../"
        return variables

    def render_sections(self):
        return super().render_sections() + self.render_profile_list(self.device["profiles"])

    def render_profile_list(self, profiles):
        def render_profile(profile_id, profile):
            return """
                <li class="list-group-item">
                    <a href="{profile_link}">{profile_name}</a>
                </li>
            """.format(
                profile_name=profile["name"],
                profile_link="{}/{}".format(self.request.path, quote(profile_id)),
            )

        return """
            <h3 class="settings-header">Profiles</h3>
            <ul class="row list-group list-group-flush sdr-profile-list">
                {profiles}
            </ul>
        """.format(
            profiles="".join(render_profile(p_id, p) for p_id, p in profiles.items())
        )

    def indexAction(self):
        if self.device is None:
            self.send_response("device not found", code=404)
            return
        self.serve_template("settings/general.html", **self.template_variables())


class SdrProfileController(SdrFormController):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        self.profile_id, self.profile = self._get_profile()

    def getData(self):
        return self.profile

    def _get_profile(self):
        if self.device is None:
            return None
        profile_id = unquote(self.request.matches.group(2))
        if profile_id not in self.device["profiles"]:
            return None
        return profile_id, self.device["profiles"][profile_id]

    def getSections(self):
        try:
            description = SdrDeviceDescription.getByType(self.device["type"])
            return [description.getProfileSection()]
        except SdrDeviceDescriptionMissing:
            # TODO provide a generic interface that allows to switch the type
            return []

    def getTitle(self):
        return self.profile["name"]

    def header_variables(self):
        variables = super().header_variables()
        variables["assets_prefix"] = "../../../"
        return variables

    def template_variables(self):
        variables = super().template_variables()
        variables["assets_prefix"] = "../../../"
        return variables

    def indexAction(self):
        if self.profile is None:
            self.send_response("profile not found", code=404)
            return
        self.serve_template("settings/general.html", **self.template_variables())
