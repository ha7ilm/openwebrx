from .direct import DirectSource
from owrx.command import Flag, Option


class HackrfSource(DirectSource):
    def __init__(self, id, props, port):
        super().__init__(id, props, port)
        self.getCommandMapper().setBase("hackrf_transfer").setMappings(
            {
                "samp_rate": Option("-s"),
                "tuner_freq": Option("-f"),
                "rf_gain": Option("-g"),
                "lna_gain": Option("-l"),
                "rf_amp": Option("-a"),
            }
        ).setStatic("-r-")

    def getEventNames(self):
        return super().getEventNames() + [
            "lna_gain",
            "rf_amp",
        ]

    def getFormatConversion(self):
        return ["csdr convert_s8_f"]
