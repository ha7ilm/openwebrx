from pycsdr.modules import ExecModule
from pycsdr.types import Format


class Rtl433Module(ExecModule):
    def __init__(self):
        super().__init__(
            Format.COMPLEX_FLOAT,
            Format.CHAR,
            ["rtl_433", "-r", "cf32:-", "-F", "json", "-M", "time:unix", "-C", "si", "-s", "1200000"]
        )
