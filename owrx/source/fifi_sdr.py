from owrx.command import Option
from .direct import DirectSource


class FifiSdrSource(DirectSource):
    def __init__(self, id, props, port):
        super().__init__(id, props, port)
        self.getCommandMapper().setBase("arecord").setMappings(
            {"device": Option("-D"), "samp_rate": Option("-r")}
        ).setStatic("-f S16_LE -c2 -")

    def getEventNames(self):
        return super().getEventNames() + ["device"]

    def getFormatConversion(self):
        return ["csdr convert_s16_f", "csdr gain_ff 30"]