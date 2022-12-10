from owrx.source import SdrSource
from pycsdr.modules import Buffer, FirDecimate, Shift
from pycsdr.types import Format
from csdr.chain import Chain


class Resampler(SdrSource):
    def onPropertyChange(self, changes):
        self.logger.warning("Resampler is unable to handle property changes: {0}".format(changes))

    def __init__(self, props, sdr):
        sdrProps = sdr.getProps()
        shift = (sdrProps["center_freq"] - props["center_freq"]) / sdrProps["samp_rate"]
        decimation = int(float(sdrProps["samp_rate"]) / props["samp_rate"])
        if_samp_rate = sdrProps["samp_rate"] / decimation
        transition_bw = 0.15 * (if_samp_rate / float(sdrProps["samp_rate"]))
        props["samp_rate"] = if_samp_rate

        self.chain = Chain([
            Shift(shift),
            FirDecimate(decimation, transition_bw)
        ])

        self.chain.setReader(sdr.getBuffer().getReader())

        super().__init__(None, props)

    def getBuffer(self):
        if self.buffer is None:
            self.buffer = Buffer(Format.COMPLEX_FLOAT)
            self.chain.setWriter(self.buffer)
        return self.buffer

    def stop(self):
        self.chain.stop()
        self.chain = None
        super().stop()

    def activateProfile(self, profile_id=None):
        self.logger.warning("Resampler does not support setting profiles")
        pass

    def validateProfiles(self):
        # resampler does not support profiles
        pass
