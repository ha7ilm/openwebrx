from pycsdr.modules import ExecModule, Writer, TcpSource
from pycsdr.types import Format
from csdr.module import LogWriter
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
            ["dump1090", "--ifile", "-", "--iformat", "SC16", "--quiet", "--net-ro-port", str(self.port)]
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
