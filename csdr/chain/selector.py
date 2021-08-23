from csdr.chain import Chain
from pycsdr.modules import Shift, FirDecimate, Bandpass, Squelch, FractionalDecimator, Writer
from pycsdr.types import Format
import math


class Decimator(Chain):
    def __init__(self, inputRate: int, outputRate: int):
        if outputRate > inputRate:
            raise ValueError("impossible decimation: cannot upsample {} to {}".format(inputRate, outputRate))
        self.inputRate = inputRate
        self.outputRate = outputRate

        decimation, fraction = self._getDecimation(outputRate)
        transition = 0.15 * (outputRate / float(self.inputRate))
        # set the cutoff on the fist decimation stage lower so that the resulting output
        # is already prepared for the second (fractional) decimation stage.
        # this spares us a second filter.
        cutoff = 0.5 * decimation / (self.inputRate / outputRate)

        workers = [
            FirDecimate(decimation, transition, cutoff),
        ]

        if fraction != 1.0:
            workers += [FractionalDecimator(Format.COMPLEX_FLOAT, fraction)]

        super().__init__(workers)

    def _getDecimation(self, outputRate: int) -> (int, float):
        d = self.inputRate / outputRate
        dInt = int(d)
        dFloat = float(self.inputRate / dInt) / outputRate
        return dInt, dFloat

    def _reconfigure(self):
        decimation, fraction = self._getDecimation(self.outputRate)
        transition = 0.15 * (self.outputRate / float(self.inputRate))
        cutoff = 0.5 * decimation / (self.inputRate / self.outputRate)
        self.replace(0, FirDecimate(decimation, transition, cutoff))
        index = self.indexOf(lambda x: isinstance(x, FractionalDecimator))
        if fraction != 1.0:
            decimator = FractionalDecimator(Format.COMPLEX_FLOAT, fraction)
            if index >= 0:
                self.replace(index, decimator)
            else:
                self.append(decimator)
        elif index >= 0:
            self.remove(index)

    def setOutputRate(self, outputRate: int) -> None:
        if outputRate == self.outputRate:
            return
        self.outputRate = outputRate
        self._reconfigure()

    def setInputRate(self, inputRate: int) -> None:
        if inputRate == self.inputRate:
            return
        self.inputRate = inputRate
        self._reconfigure()


class Selector(Chain):
    def __init__(self, inputRate: int, outputRate: int, shiftRate: float):
        self.outputRate = outputRate

        self.shift = Shift(shiftRate)

        self.decimation = Decimator(inputRate, outputRate)

        self.bandpass = self._buildBandpass()
        self.bandpassCutoffs = None
        self.setBandpass(-4000, 4000)

        self.readings_per_second = 4
        # s-meter readings are available every 1024 samples
        # the reporting interval is measured in those 1024-sample blocks
        self.squelch = Squelch(5, int(outputRate / (self.readings_per_second * 1024)))

        workers = [self.shift, self.decimation, self.bandpass, self.squelch]

        super().__init__(workers)

    def _buildBandpass(self) -> Bandpass:
        bp_transition = 320.0 / self.outputRate
        return Bandpass(transition=bp_transition, use_fft=True)

    def setShiftRate(self, rate: float) -> None:
        self.shift.setRate(rate)

    def _convertToLinear(self, db: float) -> float:
        return float(math.pow(10, db / 10))

    def setSquelchLevel(self, level: float) -> None:
        self.squelch.setSquelchLevel(self._convertToLinear(level))

    def setBandpass(self, lowCut: float, highCut: float) -> None:
        self.bandpassCutoffs = [lowCut, highCut]
        scaled = [x / self.outputRate for x in self.bandpassCutoffs]
        self.bandpass.setBandpass(*scaled)

    def setLowCut(self, lowCut: float) -> None:
        self.bandpassCutoffs[0] = lowCut
        self.setBandpass(*self.bandpassCutoffs)

    def setHighCut(self, highCut: float) -> None:
        self.bandpassCutoffs[1] = highCut
        self.setBandpass(*self.bandpassCutoffs)

    def setPowerWriter(self, writer: Writer) -> None:
        self.squelch.setPowerWriter(writer)

    def setOutputRate(self, outputRate: int) -> None:
        if outputRate == self.outputRate:
            return
        self.outputRate = outputRate

        self.decimation.setOutputRate(outputRate)
        self.squelch.setReportInterval(int(outputRate / (self.readings_per_second * 1024)))
        self.bandpass = self._buildBandpass()
        self.setBandpass(*self.bandpassCutoffs)
        self.replace(2, self.bandpass)

    def setInputRate(self, inputRate: int) -> None:
        self.decimation.setInputRate(inputRate)
