from .direct import DirectSource
from owrx.command import Flag, Option


class HackrfSource(DirectSource):
    def getCommandMapper(self):
        return super().getCommandMapper().setBase("hackrf_transfer").setMappings(
            {
                "samp_rate": Option("-s"),
                "tuner_freq": Option("-f"),
                "rf_gain": Option("-g"),
                "lna_gain": Option("-l"),
                "rf_amp": Option("-a"),
            }
        ).setStatic("-r-")

    def getFormatConversion(self):
        return ["csdr convert_s8_f"]
