from owrx.source.connector import ConnectorSource, ConnectorDeviceDescription
from owrx.command import Option, Flag
from owrx.form.error import ValidationError
from owrx.form.input import Input, NumberInput, TextInput, CheckboxInput
from owrx.form.input.validator import RangeValidator
from typing import List

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
#   --serverPort uint
#     	Server port for this radio (default 7300)
#
# If a remote IP address is not set, the connector will use the HPSDR discovery protocol
# to find radios on the local network and will connect to the first radio it discovers.
# If there is more than one HPSDR radio on the network, the IP address of the desired radio
# should always be specified.
# To use multiple HPSDR radios, each radio should have its IP address and a unique server port
# specfied. For example:
#   Radio 1: (Remote IP: 192.168.1.11, Server port: 7300)
#   Radio 2: (Remote IP: 192.168.1.22, Server port: 7301)

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
                    "server_port": Option("--serverPort"),
                    "debug": Flag("--debug"),
                }
            )
        )

class RemoteInput(TextInput):
    def __init__(self):
        super().__init__(
            "remote", 
            "Remote IP", 
            infotext=(
                "HPSDR radio IP address. If it is not set, the connector will connect to the first radio it discovers. "
                "If there is more than one HPSDR radio on the network, IP addresses of the desired radios should always be specified."
            )
        )

class HpsdrDeviceDescription(ConnectorDeviceDescription):
    def getName(self):
        return "HPSDR devices (Hermes / Hermes Lite 2 / Red Pitaya)"

    def getInputs(self) -> List[Input]:
        return super().getInputs() + [
            RemoteInput(), 
            NumberInput(
                "rf_gain", 
                "LNA Gain", 
                "LNA gain between 0 (-12dB) and 60 (48dB) (default 20)", 
                validator=RangeValidator(0, 60)
            ),
            CheckboxInput(
                "debug",
                "Show connector debugging messages in the log"
            ),
            NumberInput(
                "server_port", 
                "Server port", 
                ("Radio server port (default 7300). When using multiple radios, each must be on a separate port, "
                 "e.g. 7300 for the first, 7301 for the second.")
            ),
        ]

    def getDeviceOptionalKeys(self):
        return list(filter(lambda x : x not in ["rtltcp_compat", "iqswap"], super().getDeviceOptionalKeys())) + ["remote","debug","server_port"]

    def getProfileOptionalKeys(self):
        return list(filter(lambda x : x != "iqswap", super().getProfileOptionalKeys()))

