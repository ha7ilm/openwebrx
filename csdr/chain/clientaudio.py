from csdr.chain import Chain
from pycsdr.modules import AudioResampler, Convert, AdpcmEncoder
from pycsdr.types import Format


class ClientAudioChain(Chain):
    def __init__(self, format: Format, inputRate: int, clientRate: int, compression: str):
        workers = []
        if format != Format.FLOAT:
            workers += [Convert(format, Format.FLOAT)]
        if inputRate != clientRate:
            workers += [AudioResampler(inputRate, clientRate)]
        workers += [Convert(Format.FLOAT, Format.SHORT)]
        if compression == "adpcm":
            workers += [AdpcmEncoder(sync=True)]
        super().__init__(*workers)
