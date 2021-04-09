from owrx.modes import Modes, AudioChopperMode
from csdr.output import Output
from owrx.audio import AudioChopper


class AudioHandler(Output):
    def __init__(self, active_dsp: "csdr.csdr.Dsp", mode: str):
        self.dsp = active_dsp
        self.mode = Modes.findByModulation(mode)
        if mode is None or not isinstance(self.mode, AudioChopperMode):
            raise ValueError("Mode {} is not an audio chopper mode".format(mode))
        self.chopper = None

    def supports_type(self, t):
        return t == "audio"

    def receive_output(self, t, read_fn):
        self.chopper = AudioChopper(self.dsp, read_fn, *self.mode.getProfiles())
        self.chopper.start()

    def read(self, *args, **kwargs):
        return self.chopper.read(*args, **kwargs)
