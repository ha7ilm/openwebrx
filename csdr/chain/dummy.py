from pycsdr.types import Format
from csdr.chain import Module


class DummyDemodulator(Module):
    def __init__(self, outputFormat: Format):
        self.outputFormat = outputFormat
        super().__init__()

    def getInputFormat(self) -> Format:
        return Format.COMPLEX_FLOAT

    def getOutputFormat(self) -> Format:
        return self.outputFormat
