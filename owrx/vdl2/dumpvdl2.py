from pycsdr.modules import ExecModule
from pycsdr.types import Format


class DumpVDL2Module(ExecModule):
    def __init__(self):
        super().__init__(
            Format.COMPLEX_SHORT,
            Format.CHAR,
            [
                "dumpvdl2",
                "--iq-file", "-",
                "--oversample", "1",
                "--sample-format", "S16_LE",
                "--output", "decoded:json:file:path=-",
            ]
        )
