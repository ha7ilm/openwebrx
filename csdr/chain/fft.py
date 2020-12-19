from csdr.chain import Chain
from pycsdr import Fft, LogAveragePower, FftExchangeSides, CompressFftAdpcm

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class FftChain(Chain):
    def __init__(self, fft_size, fft_block_size, fft_averages, fft_compression):
        logger.debug("new fft: fft_size={0}, fft_block_size={1}, fft_averages={2}, fft_compression={3}".format(fft_size, fft_block_size, fft_averages, fft_compression))
        self.fft = Fft(size=fft_size, every_n_samples=int(fft_block_size))
        self.logAveragePower = LogAveragePower(add_db=-70, fft_size=fft_size, avg_number=fft_averages)
        self.fftExchangeSides = FftExchangeSides(fft_size=fft_size)
        workers = [
            self.fft,
            self.logAveragePower,
            self.fftExchangeSides,
        ]
        self.compressFftAdpcm = None
        if fft_compression == "adpcm":
            self.compressFftAdpcm = CompressFftAdpcm(fft_size=fft_size)
            workers += [self.compressFftAdpcm]
        super().__init__(*workers)

    def setFftAverages(self, fft_averages):
        logger.debug("setting fft_averages={0}".format(fft_averages))
        self.logAveragePower.setFftAverages(avg_number=fft_averages)

    def setFftBlockSize(self, fft_block_size):
        logger.debug("setting fft_block_size={0}".format(fft_block_size))
        self.fft.setEveryNSamples(int(fft_block_size))
