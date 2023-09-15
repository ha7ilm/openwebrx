from pycsdr.modules import ExecModule
from pycsdr.types import Format
from csdr.module import LineBasedModule

import logging

logger = logging.getLogger(__name__)


class Dump1090Module(ExecModule):
    def __init__(self):
        super().__init__(
            Format.COMPLEX_SHORT,
            Format.CHAR,
            ["dump1090", "--ifile", "-", "--iformat", "SC16", "--raw"],
            # send some data on decoder shutdown since the dump1090 internal reader locks up otherwise
            # dump1090 reads chunks of 100ms, which equals to 240k samples at 2.4MS/s
            # some extra should not hurt
            flushSize=300000
        )


class RawDeframer(LineBasedModule):
    def process(self, line: bytes):
        if line.startswith(b'*') and line.endswith(b';') and len(line) in [16, 30]:
            return bytes.fromhex(line[1:-1].decode())
        elif line == b"*0000;":
            # heartbeat message. not a valid message, but known. do not log.
            return
        else:
            logger.warning("invalid raw message: %s", line)
