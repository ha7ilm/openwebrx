from pycsdr.modules import ExecModule
from pycsdr.types import Format
from csdr.module import LineBasedModule
import json

import logging

logger = logging.getLogger(__name__)


class Rtl433Module(ExecModule):
    def __init__(self):
        super().__init__(
            Format.COMPLEX_FLOAT,
            Format.CHAR,
            ["rtl_433", "-r", "cf32:-", "-F", "json", "-M", "time:unix", "-C", "si"]
        )


class JsonParser(LineBasedModule):
    def process(self, line):
        try:
            msg = json.loads(line.decode())
            msg["mode"] = "ISM"
            logger.debug(msg)
            return msg
        except json.JSONDecodeError:
            logger.exception("error parsing rtl433 json")
