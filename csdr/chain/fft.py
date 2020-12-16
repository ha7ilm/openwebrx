from csdr.chain import Chain
from pycsdr import SocketClient, Fft, LogAveragePower, FftExchangeSides, CompressFftAdpcm


class FftChain(Chain):
    def __init__(self, port, fft_size, fft_block_size, fft_averages, fft_compression):
        workers = [
            SocketClient(port=port),
            Fft(size=fft_size, every_n_samples=int(fft_block_size)),
            LogAveragePower(add_db=-70, fft_size=fft_size, avg_number=fft_averages),
            FftExchangeSides(fft_size=fft_size),
        ]
        if fft_compression == "adpcm":
            workers += [CompressFftAdpcm(fft_size=fft_size)]
        super().__init__(*workers)
