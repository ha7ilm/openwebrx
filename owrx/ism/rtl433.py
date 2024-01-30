from pycsdr.modules import ExecModule
from pycsdr.types import Format
from csdr.module import JsonParser
from owrx.reporting import ReportingEngine


class Rtl433Module(ExecModule):
    def __init__(self):
        super().__init__(
            Format.COMPLEX_FLOAT,
            Format.CHAR,
            ["rtl_433", "-r", "cf32:-", "-F", "json", "-M", "time:unix", "-C", "si", "-s", "1200000"]
        )


class IsmParser(JsonParser):
    def __init__(self):
        super().__init__("ISM")

    def process(self, line):
        data = super().process(line)
        ReportingEngine.getSharedInstance().spot(data)
        return data
