from csdr.chain import Chain
from pycsdr.modules import AudioResampler, Convert, AdpcmEncoder
from pycsdr.types import Format


class ClientAudioChain(Chain):
    def __init__(self, inputRate: int, clientRate: int, compression: str):
        workers = []
        if inputRate != clientRate:
            workers += [AudioResampler(inputRate, clientRate)]
        workers += [Convert(Format.FLOAT, Format.SHORT)]
        if compression == "adpcm":
            workers += [AdpcmEncoder()]
        super().__init__(*workers)
