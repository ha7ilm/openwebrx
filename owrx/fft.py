from owrx.config import Config
from csdr.chain.fft import FftChain
import threading
from owrx.source import SdrSource, SdrSourceEventClient
from owrx.property import PropertyStack

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
            "csdr_dynamic_bufsize",
            "csdr_print_bufsizes",
            "csdr_through",
        )

        self.dsp = None

        self.subscriptions = []
        self.subscriptions += [
            # these props require a restart
            self.props.wireProperty("fft_size", self.restart),
            self.props.wireProperty("fft_compression", self.restart),
        ]

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
            # these props can be set on the fly
            self.props.wireProperty("samp_rate", self.dsp.setSampleRate),
            self.props.wireProperty("fft_fps", self.dsp.setFps),
            self.props.wireProperty("fft_voverlap_factor", self.dsp.setVOverlapFactor),
        ]

        threading.Thread(target=self.dsp.pump(self.sdrSource.writeSpectrumData)).start()

        if self.sdrSource.isAvailable():
            self.dsp.setInput(self.sdrSource.getBuffer())

    def stop(self):
        if self.dsp is None:
            return
        self.dsp.stop()
        self.dsp = None
        self.sdrSource.removeClient(self)
        while self.subscriptions:
            self.subscriptions.pop().cancel()

    def restart(self, *args, **kwargs):
        self.stop()
        self.start()

    def getClientClass(self):
        return SdrSource.CLIENT_USER

    def onStateChange(self, state):
        if state in [SdrSource.STATE_STOPPING, SdrSource.STATE_FAILED]:
            self.dsp.stop()
        elif state == SdrSource.STATE_RUNNING:
            if self.dsp is None:
                self.start()
            else:
                self.dsp.setInput(self.sdrSource.getBuffer())

    def onBusyStateChange(self, state):
        pass
