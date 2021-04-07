from owrx.controllers.settings import SettingsFormController, Section
from owrx.form.converter import OptionalConverter
from owrx.form.aprs import AprsBeaconSymbols, AprsAntennaDirections
from owrx.form import TextInput, CheckboxInput, DropdownInput, NumberInput


class ReportingController(SettingsFormController):
    def getTitle(self):
        return "Spotting and Reporting"

    def getSections(self):
        return [
            Section(
                "APRS-IS reporting",
                CheckboxInput(
                    "aprs_igate_enabled",
                    "Send received APRS data to APRS-IS",
                    infotext="Due to limits of the APRS-IS network, reporting will only work for background decoders"
                ),
                TextInput(
                    "aprs_callsign",
                    "APRS callsign",
                    infotext="This callsign will be used to send data to the APRS-IS network",
                ),
                TextInput("aprs_igate_server", "APRS-IS server"),
                TextInput("aprs_igate_password", "APRS-IS network password"),
                CheckboxInput(
                    "aprs_igate_beacon",
                    "Send the receiver position to the APRS-IS network",
                    infotext="Please check that your receiver location is setup correctly before enabling the beacon",
                ),
                DropdownInput(
                    "aprs_igate_symbol",
                    "APRS beacon symbol",
                    AprsBeaconSymbols,
                ),
                TextInput(
                    "aprs_igate_comment",
                    "APRS beacon text",
                    infotext="This text will be sent as APRS comment along with your beacon",
                    converter=OptionalConverter(),
                ),
                NumberInput(
                    "aprs_igate_height",
                    "Antenna height",
                    infotext="Antenna height above average terrain (HAAT)",
                    append="m",
                    converter=OptionalConverter(),
                ),
                NumberInput(
                    "aprs_igate_gain",
                    "Antenna gain",
                    append="dBi",
                    converter=OptionalConverter(),
                ),
                DropdownInput("aprs_igate_dir", "Antenna direction", AprsAntennaDirections),
            ),
            Section(
                "pskreporter settings",
                CheckboxInput(
                    "pskreporter_enabled",
                    "Enable sending spots to pskreporter.info",
                ),
                TextInput(
                    "pskreporter_callsign",
                    "pskreporter callsign",
                    infotext="This callsign will be used to send spots to pskreporter.info",
                ),
                TextInput(
                    "pskreporter_antenna_information",
                    "Antenna information",
                    infotext="Antenna description to be sent along with spots to pskreporter",
                    converter=OptionalConverter(),
                ),
            ),
            Section(
                "WSPRnet settings",
                CheckboxInput(
                    "wsprnet_enabled",
                    "Enable sending spots to wsprnet.org",
                ),
                TextInput(
                    "wsprnet_callsign",
                    "wsprnet callsign",
                    infotext="This callsign will be used to send spots to wsprnet.org",
                ),
            ),
        ]
