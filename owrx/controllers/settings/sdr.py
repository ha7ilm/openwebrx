from owrx.controllers.admin import AuthorizationMixin
from owrx.controllers.template import WebpageController
from owrx.controllers.settings import SettingsFormController
from owrx.source import SdrDeviceDescription, SdrDeviceDescriptionMissing, SdrClientClass
from owrx.config import Config
from owrx.connection import OpenWebRxReceiverClient
from owrx.controllers.settings import SettingsBreadcrumb
from owrx.form.section import Section
from urllib.parse import quote, unquote
from owrx.sdr import SdrService
from owrx.form.input import TextInput, DropdownInput, Option
from owrx.form.input.validator import RequiredValidator
from owrx.property import PropertyLayer
from owrx.breadcrumb import BreadcrumbMixin, Breadcrumb, BreadcrumbItem
from owrx.log import HistoryHandler
from abc import ABCMeta, abstractmethod
from uuid import uuid4


class SdrDeviceBreadcrumb(SettingsBreadcrumb):
    def __init__(self):
        super().__init__()
        self.append(BreadcrumbItem("SDR device settings", "settings/sdr"))


class SdrDeviceListController(AuthorizationMixin, BreadcrumbMixin, WebpageController):
    def template_variables(self):
        variables = super().template_variables()
        variables["content"] = self.render_devices()
        variables["title"] = "SDR device settings"
        variables["modal"] = ""
        variables["error"] = ""
        return variables

    def get_breadcrumb(self):
        return SdrDeviceBreadcrumb()

    def render_devices(self):
        def render_device(device_id, config):
            sources = SdrService.getAllSources()
            source = sources[device_id] if device_id in sources else None

            additional_info = ""
            state_info = "Unknown"

            if source is not None:
                profiles = source.getProfiles()
                currentProfile = profiles[source.getProfileId()]
                clients = {c: len(source.getClients(c)) for c in SdrClientClass}
                clients = {c: v for c, v in clients.items() if v}
                connections = len([c for c in source.getClients() if isinstance(c, OpenWebRxReceiverClient)])
                additional_info = """
                    <div>{num_profiles} profile(s)</div>
                    <div>Current profile: {current_profile}</div>
                    <div>Clients: {clients}</div>
                    <div>Connections: {connections}</div>
                """.format(
                    num_profiles=len(config["profiles"]),
                    current_profile=currentProfile["name"],
                    clients=", ".join("{cls}: {count}".format(cls=c.name, count=v) for c, v in clients.items()),
                    connections=connections,
                )

                state_info = ", ".join(
                    s
                    for s in [
                        str(source.getState()),
                        None if source.isEnabled() else "Disabled",
                        "Failed" if source.isFailed() else None,
                    ]
                    if s is not None
                )

            return """
                <li class="list-group-item">
                    <div class="row">
                        <div class="col-6">
                            <a href="{device_link}">
                                <h3>{device_name}</h3>
                            </a>
                            <div>State: {state}</div>
                        </div>
                        <div class="col-6">
                            {additional_info}
                        </div>
                    </div>
                </li>
            """.format(
                device_name=config["name"] if config["name"] else "[Unnamed device]",
                device_link="{}settings/sdr/{}".format(self.get_document_root(), quote(device_id)),
                state=state_info,
                additional_info=additional_info,
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
            device_name=self.device["name"] if self.device["name"] else "[Unnamed device]",
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
                    profile_name=profile["name"] if profile["name"] else "[Unnamed profile]",
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
    def render_remove_button(self):
        return ""

    def render_buttons(self):
        return self.render_remove_button() + super().render_buttons()

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
    def get_breadcrumb(self) -> Breadcrumb:
        return SdrDeviceBreadcrumb().append(
            BreadcrumbItem(self.device["name"], "settings/sdr/{}".format(self.device_id))
        )

    def getData(self):
        return self.device

    def getSections(self):
        try:
            description = SdrDeviceDescription.getByType(self.device["type"])
            return [description.getDeviceSection()]
        except SdrDeviceDescriptionMissing:
            # TODO provide a generic interface that allows to switch the type
            return []

    def render_remove_button(self):
        return """
            <button type="button" class="btn btn-danger" data-toggle="modal" data-target="#deleteModal">Remove device...</button>
        """

    def isDeviceActive(self) -> bool:
        return True

    def indexAction(self):
        if self.device is None:
            self.send_response("device not found", code=404)
            return
        super().indexAction()

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
        # need to overwrite the existing key in the config since the layering won't capture the changes otherwise
        config["sdrs"] = sdrs
        config.store()
        return self.send_redirect("{}settings/sdr".format(self.get_document_root()))

    def render_sections(self):
        handler = HistoryHandler.getHandler("owrx.source.{id}".format(id=self.device_id))
        return """
            {sections}
            <div class="card mt-2">
                <div class="card-header">Recent device log messages</div>
                <div class="card-body">
                    <pre class="card-text device-log-messages">{messages}</pre>
                </div>
            </div>
        """.format(
            sections=super().render_sections(),
            messages=handler.getFormattedHistory(),
        )


class NewSdrDeviceController(SettingsFormController):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        self.data_layer = PropertyLayer(name="", type="", profiles=PropertyLayer())
        self.device_id = str(uuid4())

    def get_breadcrumb(self) -> Breadcrumb:
        return SdrDeviceBreadcrumb().append(BreadcrumbItem("New device", "settings/sdr/newsdr"))

    def getSections(self):
        return [
            Section(
                "New device settings",
                TextInput("name", "Device name", validator=RequiredValidator()),
                DropdownInput(
                    "type",
                    "Device type",
                    [Option(sdr_type, name) for sdr_type, name in SdrDeviceDescription.getTypes().items()],
                    infotext="Note: Switching the type will not be possible after creation since the set of available "
                    + "options is different for each type.<br />Note: This dropdown only shows device types that have "
                    + "their requirements met. If a type is missing from the list, please check the feature report.",
                ),
            )
        ]

    def getTitle(self):
        return "New device"

    def getData(self):
        return self.data_layer

    def store(self):
        # need to overwrite the existing key in the config since the layering won't capture the changes otherwise
        config = Config.get()
        sdrs = config["sdrs"]
        # a uuid should be unique, so i'm not sure if there's a point in this check
        if self.device_id in sdrs:
            raise ValueError("device {} already exists!".format(self.device_id))
        sdrs[self.device_id] = self.data_layer
        config["sdrs"] = sdrs
        super().store()

    def getSuccessfulRedirect(self):
        return "{}settings/sdr/{}".format(self.get_document_root(), quote(self.device_id))


class SdrProfileController(SdrFormControllerWithModal):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        self.profile_id, self.profile = self._get_profile()

    def get_breadcrumb(self) -> Breadcrumb:
        return (
            SdrDeviceBreadcrumb()
            .append(BreadcrumbItem(self.device["name"], "settings/sdr/{}".format(self.device_id)))
            .append(
                BreadcrumbItem(
                    self.profile["name"], "settings/sdr/{}/profile/{}".format(self.device_id, self.profile_id)
                )
            )
        )

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
        super().indexAction()

    def processFormData(self):
        if self.profile is None:
            self.send_response("profile not found", code=404)
            return
        return super().processFormData()

    def render_remove_button(self):
        return """
            <button type="button" class="btn btn-danger" data-toggle="modal" data-target="#deleteModal">Remove profile...</button>
        """

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
        return self.send_redirect("{}settings/sdr/{}".format(self.get_document_root(), quote(self.device_id)))


class NewProfileController(SdrProfileController):
    def __init__(self, handler, request, options):
        self.data_layer = PropertyLayer(name="")
        super().__init__(handler, request, options)

    def get_breadcrumb(self) -> Breadcrumb:
        return (
            SdrDeviceBreadcrumb()
            .append(BreadcrumbItem(self.device["name"], "settings/sdr/{}".format(self.device_id)))
            .append(BreadcrumbItem("New profile", "settings/sdr/{}/newprofile".format(self.device_id)))
        )

    def _get_profile(self):
        return str(uuid4()), self.data_layer

    def isNewProfileActive(self) -> bool:
        return True

    def store(self):
        # a uuid should be unique, so i'm not sure if there's a point in this check
        if self.profile_id in self.device["profiles"]:
            raise ValueError("Profile {} already exists!".format(self.profile_id))
        self.device["profiles"][self.profile_id] = self.data_layer
        super().store()

    def getSuccessfulRedirect(self):
        return "{}settings/sdr/{}/profile/{}".format(
            self.get_document_root(), quote(self.device_id), quote(self.profile_id)
        )

    def render_remove_button(self):
        # new profile doesn't have a remove button
        return ""
