from pycsdr.modules import ExecModule
from pycsdr.types import Format


class RedseaModule(ExecModule):
    def __init__(self, sampleRate: int, rbds: bool):
        args = ["redsea", "--samplerate", str(sampleRate)]
        if rbds:
            args += ["--rbds"]
        super().__init__(
            Format.SHORT,
            Format.CHAR,
            args
        )
