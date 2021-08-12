from csdr.chain import Chain
from pycsdr.modules import AudioResampler, Convert, AdpcmEncoder, Limit
from pycsdr.types import Format


class ClientAudioChain(Chain):
    def __init__(self, format: Format, inputRate: int, clientRate: int, compression: str):
        workers = []
        if inputRate != clientRate:
            # we only have an audio resampler for float ATM so if we need to resample, we need to convert
            if format != Format.FLOAT:
                workers += [Convert(format, Format.FLOAT)]
            workers += [AudioResampler(inputRate, clientRate), Limit(), Convert(Format.FLOAT, Format.SHORT)]
        elif format != Format.SHORT:
            workers += [Convert(format, Format.SHORT)]
        if compression == "adpcm":
            workers += [AdpcmEncoder(sync=True)]
        super().__init__(*workers)
