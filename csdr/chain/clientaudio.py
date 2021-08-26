from csdr.chain import Chain
from pycsdr.modules import AudioResampler, Convert, AdpcmEncoder, Limit
from pycsdr.types import Format


class Converter(Chain):
    def __init__(self, format: Format, inputRate: int, clientRate: int):
        workers = []
        if inputRate != clientRate:
            # we only have an audio resampler for float ATM so if we need to resample, we need to convert
            if format != Format.FLOAT:
                workers += [Convert(format, Format.FLOAT)]
            workers += [AudioResampler(inputRate, clientRate), Limit(), Convert(Format.FLOAT, Format.SHORT)]
        elif format != Format.SHORT:
            workers += [Convert(format, Format.SHORT)]
        super().__init__(workers)


class ClientAudioChain(Chain):
    def __init__(self, format: Format, inputRate: int, clientRate: int, compression: str):
        self.format = format
        self.inputRate = inputRate
        self.clientRate = clientRate
        workers = [self._buildConverter()]
        if compression == "adpcm":
            workers += [AdpcmEncoder(sync=True)]
        super().__init__(workers)

    def _buildConverter(self):
        return Converter(self.format, self.inputRate, self.clientRate)

    def setFormat(self, format: Format) -> None:
        if format == self.format:
            return
        self.format = format
        self.replace(0, self._buildConverter())

    def setInputRate(self, inputRate: int) -> None:
        if inputRate == self.inputRate:
            return
        self.inputRate = inputRate
        self.replace(0, self._buildConverter())

    def setClientRate(self, clientRate: int) -> None:
        if clientRate == self.clientRate:
            return
        self.clientRate = clientRate
        self.replace(0, self._buildConverter())

    def setAudioCompression(self, compression: str) -> None:
        index = self.indexOf(lambda x: isinstance(x, AdpcmEncoder))
        if compression == "adpcm":
            if index < 0:
                self.append(AdpcmEncoder(sync=True))
        else:
            if index >= 0:
                self.remove(index)
