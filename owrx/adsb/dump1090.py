from pycsdr.modules import ExecModule, Writer, TcpSource
from pycsdr.types import Format
from csdr.module import LogWriter, LineBasedModule
from owrx.socket import getAvailablePort
import time

import logging

logger = logging.getLogger(__name__)


class Dump1090Module(ExecModule):
    def __init__(self):
        self.tcpSource = None
        self.writer = None
        self.port = getAvailablePort()

        super().__init__(
            Format.COMPLEX_SHORT,
            Format.CHAR,
            ["dump1090", "--ifile", "-", "--iformat", "SC16", "--quiet", "--net-ro-port", str(self.port)],
            # send some data on decoder shutdown since the dump1090 internal reader locks up otherwise
            # dump1090 reads chunks of 100ms, which equals to 240k samples at 2.4MS/s
            # some extra should not hurt
            flushSize=300000
        )
        super().setWriter(LogWriter(__name__))

        self.start()

    def start(self):
        delay = 0.5
        retries = 0
        while True:
            try:
                self.tcpSource = TcpSource(self.port, Format.CHAR)
                if self.writer:
                    self.tcpSource.setWriter(self.writer)
                break
            except ConnectionError:
                if retries > 20:
                    logger.error("maximum number of connection attempts reached. did dump1090 start up correctly?")
                    raise
                retries += 1
            time.sleep(delay)

    def setWriter(self, writer: Writer) -> None:
        self.writer = writer
        if self.tcpSource is not None:
            self.tcpSource.setWriter(writer)


class RawDeframer(LineBasedModule):
    def process(self, line: bytes):
        if line.startswith(b'*') and line.endswith(b';') and len(line) in [16, 30]:
            return bytes.fromhex(line[1:-1].decode())
        elif line == b"*0000;":
            # heartbeat message. not a valid message, but known. do not log.
            return
        else:
            logger.warning("invalid raw message: %s", line)
