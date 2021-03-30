from owrx.controllers.settings import Section, SettingsFormController
from owrx.config.core import CoreConfig
from owrx.form import (
    TextInput,
    NumberInput,
    FloatInput,
    LocationInput,
    TextAreaInput,
    DropdownInput,
    Option,
)
from owrx.form.converter import WaterfallColorsConverter, IntConverter
from owrx.form.receiverid import ReceiverKeysConverter
from owrx.form.gfx import AvatarInput, TopPhotoInput
from owrx.form.device import WaterfallLevelsInput, WaterfallAutoLevelsInput
from owrx.waterfall import WaterfallOptions
import shutil
import os
from glob import glob

import logging

logger = logging.getLogger(__name__)


class GeneralSettingsController(SettingsFormController):
    def getTitle(self):
        return "General Settings"

    def getSections(self):
        return [
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
                    + '<a href="https://www.receiverbook.de" target="_blank">Receiverbook</a>) here, one per line',
                ),
            ),
            Section(
                "Waterfall settings",
                DropdownInput(
                    "waterfall_scheme",
                    "Waterfall color scheme",
                    options=WaterfallOptions,
                ),
                TextAreaInput(
                    "waterfall_colors",
                    "Custom waterfall colors",
                    infotext="Please provide 6-digit hexadecimal RGB colors in HTML notation (#RRGGBB)"
                    + " or HEX notation (0xRRGGBB), one per line",
                    converter=WaterfallColorsConverter(),
                ),
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
                WaterfallLevelsInput("waterfall_levels", "Waterfall levels"),
                WaterfallAutoLevelsInput(
                    "waterfall_auto_levels",
                    "Automatic adjustment margins",
                    infotext="Specifies the upper and lower dynamic headroom that should be added when automatically "
                    + "adjusting waterfall colors",
                ),
                NumberInput(
                    "waterfall_auto_min_range",
                    "Automatic adjustment minimum range",
                    append="dB",
                    infotext="Minimum dynamic range the waterfall should cover after automatically adjusting "
                    + "waterfall colors",
                ),
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
                "Display settings",
                DropdownInput(
                    "tuning_precision",
                    "Tuning precision",
                    options=[Option(str(i), "{} Hz".format(10 ** i)) for i in range(0, 6)],
                    converter=IntConverter(),
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
        ]

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

    def processData(self, data):
        # Image handling
        for img in ["receiver_avatar", "receiver_top_photo"]:
            self.handle_image(data, img)
        # special handling for waterfall colors: custom colors only stay in config if custom color scheme is selected
        if "waterfall_scheme" in data:
            scheme = WaterfallOptions(data["waterfall_scheme"])
            if scheme is not WaterfallOptions.CUSTOM and "waterfall_colors" in data:
                data["waterfall_colors"] = None
        super().processData(data)
