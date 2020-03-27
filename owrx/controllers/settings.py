from abc import ABC, abstractmethod
from .admin import AdminController
from owrx.config import Config
from urllib.parse import parse_qs
import logging

logger = logging.getLogger(__name__)


class Input(ABC):
    def __init__(self, id, label, infotext=None):
        self.id = id
        self.label = label
        self.infotext = infotext

    def bootstrap_decorate(self, input):
        infotext = "<small>{text}</small>".format(text=self.infotext) if self.infotext else ""
        return """
            <div class="form-group row">
                <label class="col-form-label col-form-label-sm col-3" for="{id}">{label}</label>
                <div class="col-9 p-0">
                    {input}
                    {infotext}
                </div>
            </div>
        """.format(
            id=self.id, label=self.label, input=input, infotext=infotext
        )

    def input_classes(self):
        return " ".join(["form-control", "form-control-sm"])

    @abstractmethod
    def render_input(self, value):
        pass

    def render(self, config):
        return self.bootstrap_decorate(self.render_input(config[self.id]))

    def parse(self, data):
        return {self.id: data[self.id][0]} if self.id in data else {}


class TextInput(Input):
    def render_input(self, value):
        return """
            <input type="text" class="{classes}" id="{id}" name="{id}" placeholder="{label}" value="{value}">
        """.format(
            id=self.id, label=self.label, classes=self.input_classes(), value=value
        )


class NumberInput(Input):
    def render_input(self, value):
        return """
            <input type="number" class="{classes}" id="{id}" name="{id}" placeholder="{label}" value="{value}">
        """.format(
            id=self.id, label=self.label, classes=self.input_classes(), value=value
        )

    def convert_value(self, v):
        return int(v)

    def parse(self, data):
        return {k: self.convert_value(v) for k, v in super().parse(data).items()}


class FloatInput(NumberInput):
    def convert_value(self, v):
        return float(v)


class LocationInput(Input):
    def render_input(self, value):
        # TODO make this work and pretty
        return "Placeholder for a map widget to select receiver location"


class TextAreaInput(Input):
    def render_input(self, value):
        return """
            <textarea class="{classes}" id="{id}" name="{id}" style="height:200px;">{value}</textarea>
        """.format(
            id=self.id, classes=self.input_classes(), value=value
        )


class CheckboxInput(Input):
    def __init__(self, id, label, checkboxText, infotext=None):
        super().__init__(id, label, infotext=infotext)
        self.checkboxText = checkboxText

    def render_input(self, value):
        return """
          <div class="{classes}">
            <input class="form-check-input" type="checkbox" id="{id}" name="{id}" {checked}>
            <label class="form-check-label" for="{id}">
              {checkboxText}
            </label>
          </div>
        """.format(
            id=self.id, classes=self.input_classes(), checked="checked" if value else "", checkboxText=self.checkboxText
        )

    def input_classes(self):
        return " ".join(["form-check", "form-control-sm"])

    def parse(self, data):
        return {self.id: self.id in data and data[self.id][0] == "on"}


class DropdownOption(object):
    def __init__(self, value, text):
        self.value = value
        self.text = text


class DropdownInput(Input):
    def __init__(self, id, label, options, infotext = None):
        super().__init__(id, label, infotext=infotext)
        self.options = options

    def render_input(self, value):
        return """
            <select class="{classes}" id="{id}" name="{id}">{options}</select>
        """.format(classes=self.input_classes(), id=self.id, options=self.render_options(value))

    def render_options(self, value):
        options = [
            """
                <option value="{value}" {selected}>{text}</option>
            """.format(
                text=o.text, value=o.value, selected="selected" if o.value == value else ""
            ) for o in self.options
        ]
        return "".join(options)


class Section(object):
    def __init__(self, title, *inputs):
        self.title = title
        self.inputs = inputs

    def render_inputs(self):
        config = Config.get()
        return "".join([i.render(config) for i in self.inputs])

    def render(self):
        return """
            <div class="col-12 settings-category">
                <h3 class="settings-header">
                    {title}
                </h3>
                {inputs}
            </div>
        """.format(
            title=self.title, inputs=self.render_inputs()
        )

    def parse(self, data):
        return {k: v for i in self.inputs for k, v in i.parse(data).items()}


class SettingsController(AdminController):
    sections = [
        Section(
            "General settings",
            TextInput("receiver_name", "Receiver name"),
            TextInput("receiver_location", "Receiver location"),
            NumberInput("receiver_asl", "Receiver elevation", infotext="Elevation in meters above mean see level"),
            TextInput("receiver_admin", "Receiver admin"),
            LocationInput("receiver_gps", "Receiver coordinates"),
            TextInput("photo_title", "Photo title"),
            TextAreaInput("photo_desc", "Photo description"),
        ),
        Section(
            "Waterfall settings",
            NumberInput(
                "fft_fps",
                "FFT frames per second",
                infotext="This setting specifies how many lines are being added to the waterfall per second. "
                + "Higher values will give you a faster waterfall, but will also use more CPU.",
            ),
            NumberInput("fft_size", "FFT size"),
            FloatInput(
                "fft_voverlap_factor",
                "FFT vertical overlap factor",
                infotext="If fft_voverlap_factor is above 0, multiple FFTs will be used for creating a line on the "
                + "diagram.",
            ),
            NumberInput("waterfall_min_level", "Lowest waterfall level"),
            NumberInput("waterfall_max_level", "Highest waterfall level"),
        ),
        Section(
            "Compression",
            DropdownInput("audio_compression", "Audio compression", options=[
                DropdownOption("adpcm", "ADPCM"),
                DropdownOption("none", "None"),
            ]),
            DropdownInput("fft_compression", "Waterfall compression", options=[
                DropdownOption("adpcm", "ADPCM"),
                DropdownOption("none", "None"),
            ]),
        ),
        Section(
            "Digimodes",
            CheckboxInput("digimodes_enable", "", checkboxText="Enable Digimodes"),
            NumberInput("digimodes_fft_size", "Digimodes FFT size"),
        ),
        Section(
            "Digital voice",
            NumberInput(
                "digital_voice_unvoiced_quality",
                "Quality of unvoiced sounds in synthesized voice",
                infotext="Determines the quality, and thus the cpu usage, for the ambe codec used by digital voice"
                + "modes.<br />If you're running on a Raspi (up to 3B+) you should leave this set at 1"
            ),
            CheckboxInput(
                "digital_voice_dmr_id_lookup",
                "DMR id lookup",
                checkboxText="Enable lookup of DMR ids in the radioid database to show callsigns and names"
            ),
        ),
        Section(
            "Experimental pipe settings",
            CheckboxInput(
                "csdr_dynamic_bufsize",
                "",
                checkboxText="Enable dynamic buffer sizes",
                infotext="This allows you to change the buffering mode of csdr."
            ),
            CheckboxInput(
                "csdr_print_bufsizes",
                "",
                checkboxText="Print buffer sizez",
                infotext="This prints the buffer sizes used for csdr processes."
            ),
            CheckboxInput(
                "csdr_through",
                "",
                checkboxText="Print throughput",
                infotext="Enabling this will print out how much data is going into the DSP chains."
            ),
        ),
        Section(
            "Map settings",
            TextInput(
                "google_maps_api_key",
                "Google Maps API key",
                infotext="Google Maps requires an API key, check out "
                + '<a href="https://developers.google.com/maps/documentation/embed/get-api-key" target="_blank">'
                + "their documentation</a> on how to obtain one."
            ),
            NumberInput(
                "map_position_retention_time",
                "Map retention time",
                infotext="Unit is seconds<br/>Specifies how log markers / grids will remain visible on the map"
            ),
        ),
        Section(
            "WSJT-X settings",
            NumberInput("wsjt_queue_workers", "Number of WSJT decoding workers"),
            NumberInput("wsjt_queue_length", "Maximum length of WSJT job queue"),
            NumberInput(
                "wsjt_decoding_depth",
                "WSJT decoding depth",
                infotext="A higher decoding depth will allow more results, but will also consume more cpu"
            )
        ),
        Section(
            "Background decoding",
            CheckboxInput("services_enabled", "Service", checkboxText="Enable background decoding services"),
        ),
        Section(
            "APRS settings",
            TextInput(
                "aprs_callsign",
                "APRS callsign",
                infotext="This callsign will be used to send data to the APRS-IS network"
            ),
            CheckboxInput(
                "aprs_igate_enabled",
                "APRS I-Gate",
                checkboxText="Enable APRS receive-only I-Gate"
            ),
            TextInput("aprs_igate_server", "APRS-IS server"),
            TextInput("aprs_igate_password", "APRS-IS network password"),
            CheckboxInput(
                "aprs_igate_beacon",
                "APRS beacon",
                checkboxText="Send the receiver position to the APRS-IS network",
                infotext="Please check that your receiver location is setup correctly"
            ),
        ),
        Section(
            "pskreporter settings",
            CheckboxInput("pskreporter_enabled", "Reporting", checkboxText="Enable sending spots to pskreporter.info"),
            TextInput(
                "pskreporter_callsign",
                "pskreporter callsign",
                infotext="This callsign will be used to send spots to pskreporter.info"
            ),
        ),
        Section(
            "sdr.hu",
            TextInput(
                "sdrhu_key",
                "sdr.hu key",
                infotext='Please obtain your personal key on <a href="https://sdr.hu" target="_blank">sdr.hu</a>',
            ),
            CheckboxInput("sdrhu_public_listing", "List on sdr.hu", "List my receiver on sdr.hu"),
            TextInput("server_hostname", "Hostname"),
        ),
    ]

    def render_sections(self):
        sections = "".join(section.render() for section in SettingsController.sections)
        return """
            <form class="settings-body" method="POST">
                {sections}
                <div class="buttons">
                    <button type="submit" class="btn btn-primary">Apply</button>
                </div>
            </form>
        """.format(
            sections=sections
        )

    def indexAction(self):
        self.serve_template("admin.html", **self.template_variables())

    def template_variables(self):
        variables = super().template_variables()
        variables["sections"] = self.render_sections()
        return variables

    def processFormData(self):
        data = parse_qs(self.get_body().decode("utf-8"))
        data = {k: v for i in SettingsController.sections for k, v in i.parse(data).items()}
        config = Config.get()
        for k, v in data.items():
            config[k] = v
        Config.store()
        self.send_redirect("/admin")
