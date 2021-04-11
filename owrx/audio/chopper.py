from owrx.modes import Modes, AudioChopperMode
from csdr.output import Output
from itertools import groupby
from abc import ABCMeta
import threading
from owrx.audio.wav import AudioWriter
from multiprocessing.connection import wait

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AudioChopper(threading.Thread, Output, metaclass=ABCMeta):
    def __init__(self, active_dsp, mode_str: str):
        mode = Modes.findByModulation(mode_str)
        if mode is None or not isinstance(mode, AudioChopperMode):
            raise ValueError("Mode {} is not an audio chopper mode".format(mode_str))
        sorted_profiles = sorted(mode.getProfiles(), key=lambda p: p.getInterval())
        groups = {interval: list(group) for interval, group in groupby(sorted_profiles, key=lambda p: p.getInterval())}
        self.read_fn = None
        self.writers = [AudioWriter(active_dsp, interval, profiles) for interval, profiles in groups.items()]
        self.doRun = True
        super().__init__()

    def receive_output(self, t, read_fn):
        self.read_fn = read_fn
        self.start()

    def run(self) -> None:
        logger.debug("Audio chopper starting up")
        for w in self.writers:
            w.start()
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
        for w in self.writers:
            w.stop()

    def read(self):
        try:
            readers = wait([w.outputReader for w in self.writers])
            return [r.recv() for r in readers]
        except (EOFError, OSError):
            return None
