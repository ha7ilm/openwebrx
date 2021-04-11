from owrx.modes import Modes, AudioChopperMode
from csdr.output import Output
from itertools import groupby
import threading
from owrx.audio import ProfileSourceSubscriber
from owrx.audio.wav import AudioWriter
from multiprocessing.connection import Pipe, wait

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
        self.writersChangedOut = None
        self.writersChangedIn = None
        super().__init__()

    def stop_writers(self):
        while self.writers:
            self.writers.pop().stop()

    def setup_writers(self):
        self.stop_writers()
        sorted_profiles = sorted(self.profile_source.getProfiles(), key=lambda p: p.getInterval())
        groups = {interval: list(group) for interval, group in groupby(sorted_profiles, key=lambda p: p.getInterval())}
        self.writers = [AudioWriter(self.dsp, interval, profiles) for interval, profiles in groups.items()]
        for w in self.writers:
            w.start()
        self.writersChangedOut.send(None)

    def supports_type(self, t):
        return t == "audio"

    def receive_output(self, t, read_fn):
        self.read_fn = read_fn
        self.start()

    def run(self) -> None:
        logger.debug("Audio chopper starting up")
        self.writersChangedOut, self.writersChangedIn = Pipe()
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
        self.writersChangedOut.close()
        self.writersChangedIn.close()

    def onProfilesChanged(self):
        logger.debug("profile change received, resetting writers...")
        self.setup_writers()

    def read(self):
        while True:
            try:
                readers = wait([w.outputReader for w in self.writers] + [self.writersChangedIn])
                received = [(r, r.recv()) for r in readers]
                data = [d for r, d in received if r is not self.writersChangedIn]
                if data:
                    return data
            except (EOFError, OSError):
                return None
