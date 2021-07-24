from csdr.chain import Chain
from pycsdr.modules import Shift, FirDecimate, Bandpass, Squelch, FractionalDecimator
from pycsdr.types import Format


class DemodulatorChain(Chain):
    def __init__(self, samp_rate: int, audioRate: int, shiftRate: float, demodulator: Chain):
        self.shift = Shift(shiftRate)

        decimation, fraction = self._getDecimation(samp_rate, audioRate)
        if_samp_rate = samp_rate / decimation
        transition = 0.15 * (if_samp_rate / float(samp_rate))
        self.decimation = FirDecimate(decimation, transition)

        bp_transition = 320.0 / if_samp_rate
        self.bandpass = Bandpass(transition=bp_transition, use_fft=True)

        self.squelch = Squelch(5)

        workers = [self.shift, self.decimation]

        if fraction != 1.0:
            workers += [FractionalDecimator(Format.COMPLEX_FLOAT, fraction)]

        workers += [self.bandpass, self.squelch, demodulator]

        super().__init__(*workers)

    def setShiftRate(self, rate: float):
        self.shift.setRate(rate)

    def setSquelchLevel(self, level: float):
        self.squelch.setSquelchLevel(level)

    def setBandpass(self, low_cut: float, high_cut: float):
        self.bandpass.setBandpass(low_cut, high_cut)

    def _getDecimation(self, input_rate, output_rate):
        if output_rate <= 0:
            raise ValueError("invalid output rate: {rate}".format(rate=output_rate))
        decimation = 1
        target_rate = output_rate
        while input_rate / (decimation + 1) >= target_rate:
            decimation += 1
        fraction = float(input_rate / decimation) / output_rate
        return decimation, fraction
