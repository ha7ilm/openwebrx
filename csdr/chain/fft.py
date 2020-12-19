from csdr.chain import Chain
from pycsdr import Fft, LogAveragePower, FftExchangeSides, CompressFftAdpcm


class FftChain(Chain):
    def __init__(self, fft_size, fft_block_size, fft_averages, fft_compression):
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
