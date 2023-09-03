from csdr.chain import Chain
from pycsdr.modules import Shift, FirDecimate, Bandpass, Squelch, FractionalDecimator, Writer
from pycsdr.types import Format
from typing import Union
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
        if outputRate > self.inputRate:
            raise SelectorError(
                "cannot provide selected output rate {} since it is bigger than input rate {}".format(
                    outputRate,
                    self.inputRate
                )
            )
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
    def __init__(self, inputRate: int, outputRate: int, withSquelch: bool = True):
        self.inputRate = inputRate
        self.outputRate = outputRate
        self.frequencyOffset = 0

        self.shift = Shift(0.0)

        self.decimation = Decimator(inputRate, outputRate)

        self.bandpass = self._buildBandpass()
        self.bandpassCutoffs = [None, None]

        workers = [self.shift, self.decimation]

        if withSquelch:
            self.readings_per_second = 4
            # s-meter readings are available every 1024 samples
            # the reporting interval is measured in those 1024-sample blocks
            self.squelch = Squelch(5, int(outputRate / (self.readings_per_second * 1024)))
            workers += [self.squelch]

        super().__init__(workers)

    def _buildBandpass(self) -> Bandpass:
        bp_transition = 320.0 / self.outputRate
        return Bandpass(transition=bp_transition, use_fft=True)

    def setFrequencyOffset(self, offset: int) -> None:
        if offset == self.frequencyOffset:
            return
        self.frequencyOffset = offset
        self._updateShift()

    def _updateShift(self):
        shift = -self.frequencyOffset / self.inputRate
        self.shift.setRate(shift)

    def _convertToLinear(self, db: float) -> float:
        return float(math.pow(10, db / 10))

    def setSquelchLevel(self, level: float) -> None:
        self.squelch.setSquelchLevel(self._convertToLinear(level))

    def _enableBandpass(self):
        index = self.indexOf(lambda x: isinstance(x, Bandpass))
        if index < 0:
            self.insert(2, self.bandpass)

    def _disableBandpass(self):
        index = self.indexOf(lambda x: isinstance(x, Bandpass))
        if index >= 0:
            self.remove(index)

    def setBandpass(self, lowCut: float, highCut: float) -> None:
        self.bandpassCutoffs = [lowCut, highCut]
        if None in self.bandpassCutoffs:
            self._disableBandpass()
        else:
            self._enableBandpass()
            scaled = [x / self.outputRate for x in self.bandpassCutoffs]
            self.bandpass.setBandpass(*scaled)

    def setLowCut(self, lowCut: Union[float, None]) -> None:
        self.bandpassCutoffs[0] = lowCut
        self.setBandpass(*self.bandpassCutoffs)

    def setHighCut(self, highCut: Union[float, None]) -> None:
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
        index = self.indexOf(lambda x: isinstance(x, Bandpass))
        self.bandpass = self._buildBandpass()
        self.setBandpass(*self.bandpassCutoffs)
        if index >= 0:
            self.replace(index, self.bandpass)

    def setInputRate(self, inputRate: int) -> None:
        if inputRate == self.inputRate:
            return
        self.inputRate = inputRate
        self.decimation.setInputRate(inputRate)
        self._updateShift()


class SecondarySelector(Chain):
    def __init__(self, sampleRate: int, bandwidth: float):
        self.sampleRate = sampleRate
        self.frequencyOffset = 0
        self.shift = Shift(0.0)
        cutoffRate = bandwidth / sampleRate
        self.bandpass = Bandpass(-cutoffRate, cutoffRate, cutoffRate, use_fft=True)
        workers = [self.shift, self.bandpass]
        super().__init__(workers)

    def setFrequencyOffset(self, offset: int) -> None:
        if offset == self.frequencyOffset:
            return
        self.frequencyOffset = offset
        if self.frequencyOffset is None:
            return
        self.shift.setRate(-offset / self.sampleRate)


class SelectorError(Exception):
    pass
