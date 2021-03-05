from owrx.controllers.admin import AuthorizationMixin
from owrx.controllers.template import WebpageController
from owrx.controllers.settings import SettingsFormController
from owrx.source import SdrDeviceDescription, SdrDeviceDescriptionMissing, SdrClientClass
from owrx.config import Config
from owrx.connection import OpenWebRxReceiverClient
from owrx.controllers.settings import Section
from urllib.parse import quote, unquote
from owrx.sdr import SdrService
from owrx.form import TextInput, DropdownInput, Option
from owrx.property import PropertyLayer, PropertyStack
from abc import ABCMeta, abstractmethod


class SdrDeviceListController(AuthorizationMixin, WebpageController):
    def template_variables(self):
        variables = super().template_variables()
        variables["content"] = self.render_devices()
        variables["title"] = "SDR device settings"
        variables["modal"] = ""
        return variables

    def render_devices(self):
        def render_profile(device_id, profile_id, profile):
            return """
                <li class="list-group-item">
                    <a href="{profile_link}">{profile_name}</a>
                </li>
            """.format(
                profile_name=profile["name"],
                profile_link="{}settings/sdr/{}/profile/{}".format(
                    self.get_document_root(), quote(device_id), quote(profile_id)
                ),
            )

        def render_device(device_id, config):
            # TODO: this only returns non-failed sources...
            source = SdrService.getSource(device_id)

            additional_info = ""

            if source is not None:
                profiles = source.getProfiles()
                currentProfile = profiles[source.getProfileId()]
                clients = {c: len(source.getClients(c)) for c in SdrClientClass}
                clients = {c: v for c, v in clients.items() if v}
                connections = len([c for c in source.getClients() if isinstance(c, OpenWebRxReceiverClient)])
                additional_info = """
                    <div>Current profile: {current_profile}</div>
                    <div>Clients: {clients}</div>
                    <div>Connections: {connections}</div>
                """.format(
                    current_profile=currentProfile["name"],
                    clients=", ".join("{cls}: {count}".format(cls=c.name, count=v) for c, v in clients.items()),
                    connections=connections,
                )

            return """
                <li class="list-group-item">
                    <div class="row">
                        <div class="col-6">
                            <a href="{device_link}">
                                <h3>{device_name}</h3>
                            </a>
                            <div>State: {state}</div>
                            <div>{num_profiles} profile(s)</div>
                            {additional_info}
                        </div>
                        <div class="col-6">
                            <ul class="list-group list-group-flush sdr-profile-list">
                                {profiles}
                            </ul>
                            <a href="{newprofile_link}" class="btn btn-success">Add new profile...</a>
                        </div>
                    </div>
                </li>
            """.format(
                device_name=config["name"],
                device_link="{}/{}".format(self.request.path, quote(device_id)),
                state="Unknown" if source is None else source.getState(),
                num_profiles=len(config["profiles"]),
                additional_info=additional_info,
                profiles="".join(render_profile(device_id, p_id, p) for p_id, p in config["profiles"].items()),
                newprofile_link="{}settings/sdr/{}/newprofile".format(self.get_document_root(), quote(device_id)),
            )

        return """
            <ul class="list-group list-group-flush sdr-device-list">
                {devices}
            </ul>
            <div class="buttons container">
                <a class="btn btn-success" href="newsdr">Add new device...</a>
            </div>
        """.format(
            devices="".join(render_device(key, value) for key, value in Config.get()["sdrs"].items())
        )

    def indexAction(self):
        self.serve_template("settings/general.html", **self.template_variables())


class SdrFormController(SettingsFormController, metaclass=ABCMeta):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        self.device_id, self.device = self._get_device()

    def getTitle(self):
        return self.device["name"]

    def render_sections(self):
        return """
            {tabs}
            <div class="tab-body">
                {sections}
            </div>
        """.format(
            tabs=self.render_tabs(),
            sections=super().render_sections(),
        )

    def render_tabs(self):
        return """
            <ul class="nav nav-tabs">
                <li class="nav-item">
                    <a class="nav-link {device_active}" href="{device_link}">{device_name}</a>
                </li>
                {profile_tabs}
                <li class="nav-item">
                    <a href="{new_profile_link}" class="nav-link {new_profile_active}">New profile</a>
                </li>
            </ul>
        """.format(
            device_link="{}settings/sdr/{}".format(self.get_document_root(), quote(self.device_id)),
            device_name=self.device["name"],
            device_active="active" if self.isDeviceActive() else "",
            new_profile_active="active" if self.isNewProfileActive() else "",
            new_profile_link="{}settings/sdr/{}/newprofile".format(self.get_document_root(), quote(self.device_id)),
            profile_tabs="".join(
                """
                    <li class="nav-item">
                        <a class="nav-link {profile_active}" href="{profile_link}">{profile_name}</a>
                    </li>
                """.format(
                    profile_link="{}settings/sdr/{}/profile/{}".format(
                        self.get_document_root(), quote(self.device_id), quote(profile_id)
                    ),
                    profile_name=profile["name"],
                    profile_active="active" if self.isProfileActive(profile_id) else "",
                )
                for profile_id, profile in self.device["profiles"].items()
            ),
        )

    def isDeviceActive(self) -> bool:
        return False

    def isProfileActive(self, profile_id) -> bool:
        return False

    def isNewProfileActive(self) -> bool:
        return False

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
            return None, None
        return device_id, config["sdrs"][device_id]


class SdrFormControllerWithModal(SdrFormController, metaclass=ABCMeta):
    def buildModal(self):
        return """
            <div class="modal" id="deleteModal" tabindex="-1" role="dialog">
                <div class="modal-dialog" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5>Please confirm</h5>
                            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <p>Do you really want to delete this {object_type}?</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                            <a type="button" class="btn btn-danger" href="{confirm_url}">Delete</a>
                        </div>
                    </div>
                </div>
            </div>
        """.format(
            object_type=self.getModalObjectType(),
            confirm_url=self.getModalConfirmUrl(),
        )

    @abstractmethod
    def getModalObjectType(self):
        pass

    @abstractmethod
    def getModalConfirmUrl(self):
        pass


class SdrDeviceController(SdrFormControllerWithModal):
    def getData(self):
        return self.device

    def getSections(self):
        try:
            description = SdrDeviceDescription.getByType(self.device["type"])
            return [description.getDeviceSection()]
        except SdrDeviceDescriptionMissing:
            # TODO provide a generic interface that allows to switch the type
            return []

    def render_buttons(self):
        return (
            """
            <button type="button" class="btn btn-danger" data-toggle="modal" data-target="#deleteModal">Remove device...</button>
        """
            + super().render_buttons()
        )

    def isDeviceActive(self) -> bool:
        return True

    def indexAction(self):
        if self.device is None:
            self.send_response("device not found", code=404)
            return
        self.serve_template("settings/general.html", **self.template_variables())

    def processFormData(self):
        if self.device is None:
            self.send_response("device not found", code=404)
            return
        return super().processFormData()

    def getModalObjectType(self):
        return "SDR device"

    def getModalConfirmUrl(self):
        return "{}settings/deletesdr/{}".format(self.get_document_root(), quote(self.device_id))

    def deleteDevice(self):
        if self.device_id is None:
            return self.send_response("device not found", code=404)
        config = Config.get()
        sdrs = config["sdrs"]
        del sdrs[self.device_id]
        config.store()
        return self.send_redirect("{}settings/sdr".format(self.get_document_root()))


class NewSdrDeviceController(SettingsFormController):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        id_layer = PropertyLayer(id="")
        self.data_layer = PropertyLayer(name="", type="", profiles={})
        self.stack = PropertyStack()
        self.stack.addLayer(0, id_layer)
        self.stack.addLayer(1, self.data_layer)

    def getSections(self):
        return [
            Section(
                "New device settings",
                TextInput("name", "Device name"),
                DropdownInput("type", "Device type", [Option(name, name) for name in SdrDeviceDescription.getTypes()]),
                TextInput("id", "Device ID"),
            )
        ]

    def getTitle(self):
        return "New device"

    def getData(self):
        return self.stack

    def store(self):
        # need to overwrite the existing key in the config since the layering won't capture the changes otherwise
        config = Config.get()
        sdrs = config["sdrs"]
        if self.stack["id"] in sdrs:
            raise ValueError("device {} already exists!".format(self.stack["id"]))
        sdrs[self.stack["id"]] = self.data_layer
        config["sdrs"] = sdrs
        super().store()

    def getSuccessfulRedirect(self):
        return "{}settings/sdr/{}".format(self.get_document_root(), quote(self.stack["id"]))


class SdrProfileController(SdrFormControllerWithModal):
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

    def isProfileActive(self, profile_id) -> bool:
        return profile_id == self.profile_id

    def getSections(self):
        try:
            description = SdrDeviceDescription.getByType(self.device["type"])
            return [description.getProfileSection()]
        except SdrDeviceDescriptionMissing:
            # TODO provide a generic interface that allows to switch the type
            return []

    def indexAction(self):
        if self.profile is None:
            self.send_response("profile not found", code=404)
            return
        self.serve_template("settings/general.html", **self.template_variables())

    def processFormData(self):
        if self.profile is None:
            self.send_response("profile not found", code=404)
            return
        return super().processFormData()

    def render_buttons(self):
        return (
            """
                <button type="button" class="btn btn-danger" data-toggle="modal" data-target="#deleteModal">Remove profile...</button>
            """
            + super().render_buttons()
        )

    def getModalObjectType(self):
        return "profile"

    def getModalConfirmUrl(self):
        return "{}settings/sdr/{}/deleteprofile/{}".format(
            self.get_document_root(), quote(self.device_id), quote(self.profile_id)
        )

    def deleteProfile(self):
        if self.profile_id is None:
            return self.send_response("profile not found", code=404)
        config = Config.get()
        del self.device["profiles"][self.profile_id]
        config.store()
        return self.send_redirect("{}settings/sdr".format(self.get_document_root()))


class NewProfileController(SdrFormController):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        id_layer = PropertyLayer(id="")
        self.data_layer = PropertyLayer(name="")
        self.stack = PropertyStack()
        self.stack.addLayer(0, id_layer)
        self.stack.addLayer(1, self.data_layer)

    def getSections(self):
        return [
            Section(
                "New profile settings",
                TextInput("name", "Profile name"),
                TextInput("id", "Profile ID"),
            )
        ]

    def getTitle(self):
        return "New profile"

    def isNewProfileActive(self) -> bool:
        return True

    def store(self):
        if self.stack["id"] in self.device["profiles"]:
            raise ValueError("Profile {} already exists!".format(self.stack["id"]))
        self.device["profiles"][self.stack["id"]] = self.data_layer
        super().store()

    def getData(self):
        return self.stack

    def getSuccessfulRedirect(self):
        return "{}settings/sdr/{}/profile/{}".format(
            self.get_document_root(), quote(self.device_id), quote(self.stack["id"])
        )
