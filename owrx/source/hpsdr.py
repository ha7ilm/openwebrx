from .connector import ConnectorSource
from owrx.command import Flag, Option

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
