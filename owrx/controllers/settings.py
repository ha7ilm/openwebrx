from owrx.controllers.template import WebpageController
from owrx.controllers.admin import AuthorizationMixin
from owrx.config.core import CoreConfig
from owrx.config import Config
from urllib.parse import parse_qs
from owrx.form import (
    TextInput,
    NumberInput,
    FloatInput,
    LocationInput,
    TextAreaInput,
    CheckboxInput,
    DropdownInput,
    Option,
    ServicesCheckboxInput,
    Js8ProfileCheckboxInput,
    MultiCheckboxInput,
)
from owrx.form.converter import OptionalConverter
from owrx.form.receiverid import ReceiverKeysConverter
from owrx.form.aprs import AprsBeaconSymbols, AprsAntennaDirections
from owrx.form.wfm import WfmTauValues
from owrx.form.wsjt import Q65ModeMatrix
from owrx.form.gfx import AvatarInput, TopPhotoInput
from urllib.parse import quote
from owrx.wsjt import Fst4Profile, Fst4wProfile
import json
import logging
import shutil
import os
from glob import glob

logger = logging.getLogger(__name__)


class Section(object):
    def __init__(self, title, *inputs):
        self.title = title
        self.inputs = inputs

    def render_inputs(self):
        config = Config.get()
        return "".join([i.render(config) for i in self.inputs])

    def render(self):
        return """
            <div class="col-12 settings-section">
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


class SettingsController(AuthorizationMixin, WebpageController):
    def indexAction(self):
        self.serve_template("settings.html", **self.template_variables())


class SdrSettingsController(AuthorizationMixin, WebpageController):
    def template_variables(self):
        variables = super().template_variables()
        variables["devices"] = self.render_devices()
        return variables

    def render_devices(self):
        return "".join(self.render_device(key, value) for key, value in Config.get()["sdrs"].items())

    def render_device(self, device_id, config):
        return """
            <div class="card device bg-dark text-white">
                <div class="card-header">
                    {device_name}
                </div>
                <div class="card-body">
                    {form}
                </div>
            </div>
        """.format(
            device_name=config["name"], form=self.render_form(device_id, config)
        )

    def render_form(self, device_id, config):
        return """
            <form class="sdrdevice" data-config="{formdata}"></form>
        """.format(
            device_id=device_id, formdata=quote(json.dumps(config))
        )

    def indexAction(self):
        self.serve_template("sdrsettings.html", **self.template_variables())


class GeneralSettingsController(AuthorizationMixin, WebpageController):
    sections = [
        Section(
            "Receiver information",
            TextInput("receiver_name", "Receiver name"),
            TextInput("receiver_location", "Receiver location"),
            NumberInput(
                "receiver_asl",
                "Receiver elevation",
                append="meters above mean sea level",
            ),
            TextInput("receiver_admin", "Receiver admin"),
            LocationInput("receiver_gps", "Receiver coordinates"),
            TextInput("photo_title", "Photo title"),
            TextAreaInput("photo_desc", "Photo description"),
        ),
        Section(
            "Receiver images",
            AvatarInput(
                "receiver_avatar",
                "Receiver Avatar",
                infotext="For performance reasons, images are cached. "
                + "It can take a few hours until they appear on the site.",
            ),
            TopPhotoInput(
                "receiver_top_photo",
                "Receiver Panorama",
                infotext="For performance reasons, images are cached. "
                + "It can take a few hours until they appear on the site.",
            ),
        ),
        Section(
            "Receiver limits",
            NumberInput(
                "max_clients",
                "Maximum number of clients",
            ),
        ),
        Section(
            "Receiver listings",
            TextAreaInput(
                "receiver_keys",
                "Receiver keys",
                converter=ReceiverKeysConverter(),
                infotext="Put the keys you receive on listing sites (e.g. "
                + '<a href="https://www.receiverbook.de">Receiverbook</a>) here, one per line',
            ),
        ),
        Section(
            "Waterfall settings",
            NumberInput(
                "fft_fps",
                "FFT speed",
                infotext="This setting specifies how many lines are being added to the waterfall per second. "
                + "Higher values will give you a faster waterfall, but will also use more CPU.",
                append="frames per second",
            ),
            NumberInput("fft_size", "FFT size", append="bins"),
            FloatInput(
                "fft_voverlap_factor",
                "FFT vertical overlap factor",
                infotext="If fft_voverlap_factor is above 0, multiple FFTs will be used for creating a line on the "
                + "diagram.",
            ),
            NumberInput("waterfall_min_level", "Lowest waterfall level", append="dBFS"),
            NumberInput("waterfall_max_level", "Highest waterfall level", append="dBFS"),
        ),
        Section(
            "Compression",
            DropdownInput(
                "audio_compression",
                "Audio compression",
                options=[
                    Option("adpcm", "ADPCM"),
                    Option("none", "None"),
                ],
            ),
            DropdownInput(
                "fft_compression",
                "Waterfall compression",
                options=[
                    Option("adpcm", "ADPCM"),
                    Option("none", "None"),
                ],
            ),
        ),
        Section(
            "Digimodes",
            CheckboxInput("digimodes_enable", "", checkboxText="Enable Digimodes"),
            NumberInput("digimodes_fft_size", "Digimodes FFT size", append="bins"),
        ),
        Section(
            "Demodulator settings",
            NumberInput(
                "squelch_auto_margin",
                "Auto-Squelch threshold",
                infotext="Offset to be added to the current signal level when using the auto-squelch",
                append="dB",
            ),
            DropdownInput(
                "wfm_deemphasis_tau",
                "Tau setting for WFM (broadcast FM) deemphasis",
                WfmTauValues,
                infotext='See <a href="https://en.wikipedia.org/wiki/FM_broadcasting#Pre-emphasis_and_de-emphasis">'
                + "this Wikipedia article</a> for more information",
            ),
        ),
        Section(
            "Display settings",
            NumberInput(
                "frequency_display_precision",
                "Frequency display precision",
                infotext="Number of decimal digits to show on the frequency display",
            ),
        ),
        Section(
            "Digital voice",
            NumberInput(
                "digital_voice_unvoiced_quality",
                "Quality of unvoiced sounds in synthesized voice",
                infotext="Determines the quality, and thus the cpu usage, for the ambe codec used by digital voice"
                + "modes.<br />If you're running on a Raspi (up to 3B+) you should leave this set at 1",
            ),
            CheckboxInput(
                "digital_voice_dmr_id_lookup",
                "DMR id lookup",
                checkboxText="Enable lookup of DMR ids in the radioid database to show callsigns and names",
            ),
        ),
        Section(
            "Map settings",
            TextInput(
                "google_maps_api_key",
                "Google Maps API key",
                infotext="Google Maps requires an API key, check out "
                + '<a href="https://developers.google.com/maps/documentation/embed/get-api-key" target="_blank">'
                + "their documentation</a> on how to obtain one.",
            ),
            NumberInput(
                "map_position_retention_time",
                "Map retention time",
                infotext="Specifies how log markers / grids will remain visible on the map",
                append="s",
            ),
        ),
        Section(
            "Decoding settings",
            NumberInput("decoding_queue_workers", "Number of decoding workers"),
            NumberInput("decoding_queue_length", "Maximum length of decoding job queue"),
            NumberInput(
                "wsjt_decoding_depth",
                "Default WSJT decoding depth",
                infotext="A higher decoding depth will allow more results, but will also consume more cpu",
            ),
            NumberInput(
                "js8_decoding_depth",
                "Js8Call decoding depth",
                infotext="A higher decoding depth will allow more results, but will also consume more cpu",
            ),
            Js8ProfileCheckboxInput("js8_enabled_profiles", "Js8Call enabled modes"),
            MultiCheckboxInput(
                "fst4_enabled_intervals",
                "Enabled FST4 intervals",
                [Option(v, "{}s".format(v)) for v in Fst4Profile.availableIntervals],
            ),
            MultiCheckboxInput(
                "fst4w_enabled_intervals",
                "Enabled FST4W intervals",
                [Option(v, "{}s".format(v)) for v in Fst4wProfile.availableIntervals],
            ),
            Q65ModeMatrix("q65_enabled_combinations", "Enabled Q65 Mode combinations"),
        ),
        Section(
            "Background decoding",
            CheckboxInput(
                "services_enabled",
                "Service",
                checkboxText="Enable background decoding services",
            ),
            ServicesCheckboxInput("services_decoders", "Enabled services"),
        ),
        Section(
            "APRS settings",
            TextInput(
                "aprs_callsign",
                "APRS callsign",
                infotext="This callsign will be used to send data to the APRS-IS network",
            ),
            CheckboxInput(
                "aprs_igate_enabled",
                "APRS I-Gate",
                checkboxText="Send received APRS data to APRS-IS",
            ),
            TextInput("aprs_igate_server", "APRS-IS server"),
            TextInput("aprs_igate_password", "APRS-IS network password"),
            CheckboxInput(
                "aprs_igate_beacon",
                "APRS beacon",
                checkboxText="Send the receiver position to the APRS-IS network",
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
                "Reporting",
                checkboxText="Enable sending spots to pskreporter.info",
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
                "Reporting",
                checkboxText="Enable sending spots to wsprnet.org",
            ),
            TextInput(
                "wsprnet_callsign",
                "wsprnet callsign",
                infotext="This callsign will be used to send spots to wsprnet.org",
            ),
        ),
    ]

    def render_sections(self):
        sections = "".join(section.render() for section in GeneralSettingsController.sections)
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
        self.serve_template("generalsettings.html", **self.template_variables())

    def template_variables(self):
        variables = super().template_variables()
        variables["sections"] = self.render_sections()
        return variables

    def handle_image(self, data, image_id):
        if image_id in data:
            config = CoreConfig()
            if data[image_id] == "restore":
                # remove all possible file extensions
                for ext in ["png", "jpg"]:
                    try:
                        os.unlink("{}/{}.{}".format(config.get_data_directory(), image_id, ext))
                    except FileNotFoundError:
                        pass
            elif data[image_id]:
                if not data[image_id].startswith(image_id):
                    logger.warning("invalid file name: %s", data[image_id])
                else:
                    # get file extension (luckily, all options are three characters long)
                    ext = data[image_id][-3:]
                    data_file = "{}/{}.{}".format(config.get_data_directory(), image_id, ext)
                    temporary_file = "{}/{}".format(config.get_temporary_directory(), data[image_id])
                    shutil.copy(temporary_file, data_file)
            del data[image_id]
            # remove any accumulated temporary files on save
            for file in glob("{}/{}*".format(config.get_temporary_directory(), image_id)):
                os.unlink(file)

    def processFormData(self):
        data = parse_qs(self.get_body().decode("utf-8"), keep_blank_values=True)
        data = {k: v for i in GeneralSettingsController.sections for k, v in i.parse(data).items()}
        # Image handling
        for img in ["receiver_avatar", "receiver_top_photo"]:
            self.handle_image(data, img)
        config = Config.get()
        for k, v in data.items():
            if v is None:
                if k in config:
                    del config[k]
            else:
                config[k] = v
        config.store()
        self.send_redirect("/generalsettings")
