from owrx.modes import Modes, AudioChopperMode
from itertools import groupby
import threading
from owrx.audio import ProfileSourceSubscriber
from owrx.audio.wav import AudioWriter
from csdr.chain import Chain
import pickle

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AudioChopper(threading.Thread, Chain, ProfileSourceSubscriber):
    # TODO parser typing
    def __init__(self, mode_str: str, parser):
        self.parser = parser
        self.doRun = True
        self.writers = []
        mode = Modes.findByModulation(mode_str)
        if mode is None or not isinstance(mode, AudioChopperMode):
            raise ValueError("Mode {} is not an audio chopper mode".format(mode_str))
        self.profile_source = mode.get_profile_source()
        super().__init__()
        Chain.__init__(self, [])

    def stop_writers(self):
        while self.writers:
            self.writers.pop().stop()

    def setup_writers(self):
        self.stop_writers()
        sorted_profiles = sorted(self.profile_source.getProfiles(), key=lambda p: p.getInterval())
        groups = {interval: list(group) for interval, group in groupby(sorted_profiles, key=lambda p: p.getInterval())}
        writers = [
            AudioWriter(self, interval, profiles) for interval, profiles in groups.items()
        ]
        for w in writers:
            w.start()
        self.writers = writers

    def setReader(self, reader):
        super().setReader(reader)
        self.start()

    def stop(self):
        self.reader.stop()
        super().stop()

    def run(self) -> None:
        logger.debug("Audio chopper starting up")
        self.setup_writers()
        self.profile_source.subscribe(self)
        while self.doRun:
            data = None
            try:
                data = self.reader.read()
            except ValueError:
                pass
            if data is None:
                self.doRun = False
            else:
                for w in self.writers:
                    w.write(data.tobytes())

        logger.debug("Audio chopper shutting down")
        self.profile_source.unsubscribe(self)
        self.stop_writers()

    def onProfilesChanged(self):
        logger.debug("profile change received, resetting writers...")
        self.setup_writers()

    def send(self, profile, line):
        data = self.parser.parse(profile, line)
        if data is not None and self.writer is not None:
            self.writer.write(pickle.dumps(data))
