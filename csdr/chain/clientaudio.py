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
        workers = []
        converter = self._buildConverter()
        if not converter.empty():
            workers += [converter]
        if compression == "adpcm":
            workers += [AdpcmEncoder(sync=True)]
        super().__init__(workers)

    def _buildConverter(self):
        return Converter(self.format, self.inputRate, self.clientRate)

    def _updateConverter(self):
        converter = self._buildConverter()
        index = self.indexOf(lambda x: isinstance(x, Converter))
        if converter.empty():
            if index >= 0:
                self.remove(index)
        else:
            if index >= 0:
                self.replace(index, converter)
            else:
                self.insert(0, converter)

    def setFormat(self, format: Format) -> None:
        if format == self.format:
            return
        self.format = format
        self._updateConverter()

    def setInputRate(self, inputRate: int) -> None:
        if inputRate == self.inputRate:
            return
        self.inputRate = inputRate
        self._updateConverter()

    def setClientRate(self, clientRate: int) -> None:
        if clientRate == self.clientRate:
            return
        self.clientRate = clientRate
        self._updateConverter()

    def setAudioCompression(self, compression: str) -> None:
        index = self.indexOf(lambda x: isinstance(x, AdpcmEncoder))
        if compression == "adpcm":
            if index < 0:
                self.append(AdpcmEncoder(sync=True))
        else:
            if index >= 0:
                self.remove(index)
