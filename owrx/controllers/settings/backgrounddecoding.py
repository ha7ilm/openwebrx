from owrx.controllers.settings import SettingsFormController
from owrx.form.section import Section
from owrx.form.input import CheckboxInput, ServicesCheckboxInput
from owrx.breadcrumb import Breadcrumb, BreadcrumbItem
from owrx.controllers.settings import SettingsBreadcrumb


class BackgroundDecodingController(SettingsFormController):
    def getTitle(self):
        return "Background decoding"

    def get_breadcrumb(self) -> Breadcrumb:
        return SettingsBreadcrumb().append(BreadcrumbItem("Background decoding", "settings/backgrounddecoding"))

    def getSections(self):
        return [
            Section(
                "Background decoding",
                CheckboxInput(
                    "services_enabled",
                    "Enable background decoding services",
                ),
                ServicesCheckboxInput("services_decoders", "Enabled services"),
            ),
        ]
