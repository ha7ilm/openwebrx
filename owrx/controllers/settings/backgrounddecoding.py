from owrx.controllers.settings import SettingsFormController, Section
from owrx.form import CheckboxInput, ServicesCheckboxInput


class BackgroundDecodingController(SettingsFormController):
    def getTitle(self):
        return "Background decoding"

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
