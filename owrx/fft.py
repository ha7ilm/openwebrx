from owrx.config import Config
from csdr.chain.fft import FftChain
from owrx.source import SdrSourceEventClient, SdrSourceState, SdrClientClass
from owrx.property import PropertyStack
from pycsdr.modules import Buffer
import threading

import logging

logger = logging.getLogger(__name__)


class SpectrumThread(SdrSourceEventClient):
    def __init__(self, sdrSource):
        self.sdrSource = sdrSource
        super().__init__()

        stack = PropertyStack()
        stack.addLayer(0, self.sdrSource.props)
        stack.addLayer(1, Config.get())
        self.props = stack.filter(
            "samp_rate",
            "fft_size",
            "fft_fps",
            "fft_voverlap_factor",
            "fft_compression",
        )

        self.dsp = None
        self.reader = None

        self.subscriptions = []

        logger.debug("Spectrum thread initialized successfully.")

    def start(self):
        if self.dsp is not None:
            return

        self.dsp = FftChain(
            self.props['samp_rate'],
            self.props['fft_size'],
            self.props['fft_voverlap_factor'],
            self.props['fft_fps'],
            self.props['fft_compression']
        )
        self.sdrSource.addClient(self)

        self.subscriptions += [
            self.props.filter("fft_size").wire(self.restart),
            # these props can be set on the fly
            self.props.wireProperty("samp_rate", self.dsp.setSampleRate),
            self.props.wireProperty("fft_fps", self.dsp.setFps),
            self.props.wireProperty("fft_voverlap_factor", self.dsp.setVOverlapFactor),
            self.props.wireProperty("fft_compression", self.dsp.setCompression),
        ]

        buffer = Buffer(self.dsp.getOutputFormat())
        self.dsp.setWriter(buffer)
        self.reader = buffer.getReader()
        threading.Thread(target=self.dsp.pump(self.reader.read, self.sdrSource.writeSpectrumData)).start()

        if self.sdrSource.isAvailable():
            self.dsp.setReader(self.sdrSource.getBuffer().getReader())

    def stop(self):
        if self.dsp is None:
            return
        self.dsp.stop()
        self.dsp = None
        self.reader.stop()
        self.reader = None
        self.sdrSource.removeClient(self)
        while self.subscriptions:
            self.subscriptions.pop().cancel()

    def restart(self, *args, **kwargs):
        self.stop()
        self.start()

    def getClientClass(self) -> SdrClientClass:
        return SdrClientClass.USER

    def onStateChange(self, state: SdrSourceState):
        if state is SdrSourceState.STOPPING:
            self.dsp.stop()
        elif state == SdrSourceState.RUNNING:
            if self.dsp is None:
                self.start()
            else:
                self.dsp.setReader(self.sdrSource.getBuffer().getReader())

    def onFail(self):
        if self.dsp is None:
            return
        self.dsp.stop()

    def onShutdown(self):
        if self.dsp is None:
            return
        self.dsp.stop()
