from csdr.chain import Chain
from pycsdr.modules import Shift, FirDecimate, Bandpass, Squelch, FractionalDecimator, Writer
from pycsdr.types import Format


class DemodulatorChain(Chain):
    def __init__(self, samp_rate: int, audioRate: int, shiftRate: float, demodulator: Chain):
        self.demodulator = demodulator

        self.shift = Shift(shiftRate)

        decimation, fraction = self._getDecimation(samp_rate, audioRate)
        if_samp_rate = samp_rate / decimation
        transition = 0.15 * (if_samp_rate / float(samp_rate))
        # set the cutoff on the fist decimation stage lower so that the resulting output
        # is already prepared for the second (fractional) decimation stage.
        # this spares us a second filter.
        self.decimation = FirDecimate(decimation, transition, 0.5 * decimation / (samp_rate / audioRate))

        bp_transition = 320.0 / audioRate
        self.bandpass = Bandpass(transition=bp_transition, use_fft=True)

        readings_per_second = 4
        # s-meter readings are available every 1024 samples
        # the reporting interval is measured in those 1024-sample blocks
        self.squelch = Squelch(5, int(audioRate / (readings_per_second * 1024)))

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

    def setPowerWriter(self, writer: Writer):
        self.squelch.setPowerWriter(writer)

    def setMetaWriter(self, writer: Writer):
        self.demodulator.setMetaWriter(writer)

    def _getDecimation(self, input_rate, output_rate):
        if output_rate <= 0:
            raise ValueError("invalid output rate: {rate}".format(rate=output_rate))
        decimation = 1
        target_rate = output_rate
        while input_rate / (decimation + 1) >= target_rate:
            decimation += 1
        fraction = float(input_rate / decimation) / output_rate
        return decimation, fraction
