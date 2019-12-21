from . import SdrSource


class FifiSdrSource(SdrSource):
    def getCommand(self):
        return "arecord -D hw:2,0 -f S16_LE -r {samp_rate} -c2 -"

    def getFormatConversion(self):
        return "csdr convert_s16_f | csdr gain_ff 30"
