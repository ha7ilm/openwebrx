from owrx.source.connector import ConnectorSource, ConnectorDeviceDescription
from owrx.command import Option
from owrx.form.error import ValidationError
from owrx.form.input import Input, NumberInput, TextInput
from owrx.form.input.validator import RangeValidator
from typing import List

# In order to use an HPSDR radio, you must install hpsdrconnector from https://github.com/jancona/hpsdrconnector
# These are the command line options available:
#  --frequency uint
#    	Tune to specified frequency in Hz (default 7100000)
#  --gain uint
#    	LNA gain between 0 (-12dB) and 60 (48dB) (default 20)
#   --radio string
#     	IP address of radio (default use first radio discovered)
#   --samplerate uint
#     	Use the specified samplerate: one of 48000, 96000, 192000, 384000 (default 96000)
#   --debug
#       Emit debug log messages on stdout
#
# If you omit `remote` from config_webrx.py, hpsdrconnector will use the HPSDR discovery protocol
# to find radios on your local network and will connect to the first radio it discovered.


class HpsdrSource(ConnectorSource):
    def getCommandMapper(self):
        return (
            super()
            .getCommandMapper()
            .setBase("hpsdrconnector")
            .setMappings(
                {
                    "tuner_freq": Option("--frequency"),
                    "samp_rate": Option("--samplerate"),
                    "remote": Option("--radio"),
                    "rf_gain": Option("--gain"),
                }
            )
        )

class RemoteInput(TextInput):
    def __init__(self):
        super().__init__(
            "remote", "Remote IP", infotext="Remote IP address to connect to."
        )

class HpsdrDeviceDescription(ConnectorDeviceDescription):
    def getName(self):
        return "HPSDR devices (Hermes / Hermes Lite 2 / Red Pitaya)"

    def getInputs(self) -> List[Input]:
        return super().getInputs() + [
            RemoteInput(), 
            NumberInput("rf_gain", "LNA Gain", "LNA gain between 0 (-12dB) and 60 (48dB)", validator=RangeValidator(0, 60)),
            ]

    def getDeviceOptionalKeys(self):
        return list(filter(lambda x : x not in ["rtltcp_compat", "iqswap"], super().getDeviceOptionalKeys())) + ["remote"]

    def getProfileOptionalKeys(self):
        return list(filter(lambda x : x != "iqswap", super().getProfileOptionalKeys()))

