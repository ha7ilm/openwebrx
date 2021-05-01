from owrx.modes import Modes, AudioChopperMode
from csdr.output import Output
from itertools import groupby
import threading
from owrx.audio import ProfileSourceSubscriber
from owrx.audio.wav import AudioWriter
from multiprocessing.connection import Pipe

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AudioChopper(threading.Thread, Output, ProfileSourceSubscriber):
    def __init__(self, active_dsp, mode_str: str):
        self.read_fn = None
        self.doRun = True
        self.dsp = active_dsp
        self.writers = []
        mode = Modes.findByModulation(mode_str)
        if mode is None or not isinstance(mode, AudioChopperMode):
            raise ValueError("Mode {} is not an audio chopper mode".format(mode_str))
        self.profile_source = mode.get_profile_source()
        (self.outputReader, self.outputWriter) = Pipe()
        super().__init__()

    def stop_writers(self):
        while self.writers:
            self.writers.pop().stop()

    def setup_writers(self):
        self.stop_writers()
        sorted_profiles = sorted(self.profile_source.getProfiles(), key=lambda p: p.getInterval())
        groups = {interval: list(group) for interval, group in groupby(sorted_profiles, key=lambda p: p.getInterval())}
        writers = [
            AudioWriter(self.dsp, self.outputWriter, interval, profiles) for interval, profiles in groups.items()
        ]
        for w in writers:
            w.start()
        self.writers = writers

    def supports_type(self, t):
        return t == "audio"

    def receive_output(self, t, read_fn):
        self.read_fn = read_fn
        self.start()

    def run(self) -> None:
        logger.debug("Audio chopper starting up")
        self.setup_writers()
        self.profile_source.subscribe(self)
        while self.doRun:
            data = None
            try:
                data = self.read_fn(256)
            except ValueError:
                pass
            if data is None or (isinstance(data, bytes) and len(data) == 0):
                self.doRun = False
            else:
                for w in self.writers:
                    w.write(data)

        logger.debug("Audio chopper shutting down")
        self.profile_source.unsubscribe(self)
        self.stop_writers()
        self.outputWriter.close()
        self.outputWriter = None

        # drain messages left in the queue so that the queue can be successfully closed
        # this is necessary since python keeps the file descriptors open otherwise
        try:
            while True:
                self.outputReader.recv()
        except EOFError:
            pass
        self.outputReader.close()
        self.outputReader = None

    def onProfilesChanged(self):
        logger.debug("profile change received, resetting writers...")
        self.setup_writers()

    def read(self):
        try:
            return self.outputReader.recv()
        except (EOFError, OSError):
            return None
