from . import SdrSource


class HackrfSource(SdrSource):
    def getCommand(self):
        return "hackrf_transfer -s {samp_rate} -f {tuner_freq} -g {rf_gain} -l{lna_gain} -a{rf_amp} -r-"

    def getFormatConversion(self):
        return "csdr convert_s8_f"
