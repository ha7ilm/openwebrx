from csdr.chain import Chain
from pycsdr import Fft, LogAveragePower, FftExchangeSides, CompressFftAdpcm

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class FftChain(Chain):
    def __init__(self, samp_rate, fft_size, fft_v_overlap_factor, fft_fps, fft_compression):
        self.sampleRate = samp_rate
        self.vOverlapFactor = fft_v_overlap_factor
        self.fps = fft_fps
        self.size = fft_size

        self.blockSize = 0
        self.fftAverages = 0

        self.fft = Fft(size=self.size, every_n_samples=self.blockSize)
        self.logAveragePower = LogAveragePower(add_db=-70, fft_size=self.size, avg_number=self.fftAverages)
        self.fftExchangeSides = FftExchangeSides(fft_size=self.size)
        workers = [
            self.fft,
            self.logAveragePower,
            self.fftExchangeSides,
        ]
        self.compressFftAdpcm = None
        if fft_compression == "adpcm":
            self.compressFftAdpcm = CompressFftAdpcm(fft_size=self.size)
            workers += [self.compressFftAdpcm]

        self._updateParameters()

        super().__init__(*workers)

    def _setFftAverages(self, fft_averages):
        if self.fftAverages == fft_averages:
            return
        self.fftAverages = fft_averages
        self.logAveragePower.setFftAverages(avg_number=self.fftAverages)

    def _setBlockSize(self, fft_block_size):
        if self.blockSize == int(fft_block_size):
            return
        self.blockSize = int(fft_block_size)
        self.fft.setEveryNSamples(self.blockSize)

    def setVOverlapFactor(self, fft_v_overlap_factor):
        if self.vOverlapFactor == fft_v_overlap_factor:
            return
        self.vOverlapFactor = fft_v_overlap_factor
        self._updateParameters()

    def setFps(self, fft_fps):
        if self.fps == fft_fps:
            return
        self.fps = fft_fps
        self._updateParameters()

    def setSampleRate(self, samp_rate):
        if self.sampleRate == samp_rate:
            return
        self.sampleRate = samp_rate
        self._updateParameters()

    def _updateParameters(self):
        if self.vOverlapFactor > 0:
            self._setFftAverages(
                int(round(1.0 * self.sampleRate / self.size / self.fps / (1.0 - self.vOverlapFactor)))
            )
        else:
            self._setFftAverages(0)

        if self.fftAverages == 0:
            self._setBlockSize(self.sampleRate / self.fps)
        else:
            self._setBlockSize(self.sampleRate / self.fps / self.fftAverages)
