from pycsdr.modules import ExecModule, Writer, TcpSource
from pycsdr.types import Format
from csdr.module import LogWriter, ThreadModule
from owrx.socket import getAvailablePort
import time
import pickle

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


class RawDeframer(ThreadModule):
    def __init__(self):
        self.retained = bytes()
        super().__init__()

    def getInputFormat(self) -> Format:
        return Format.CHAR

    def getOutputFormat(self) -> Format:
        return Format.CHAR

    def run(self):
        while self.doRun:
            data = self.reader.read()
            if data is None:
                self.doRun = False
            else:
                self.retained += data
                lines = self.retained.split(b"\n")

                # keep the last line
                # this should either be empty if the last char was \n
                # or an incomplete line if the read returned early
                self.retained = lines[-1]

                # log all completed lines
                for line in lines[0:-1]:
                    self.writer.write(pickle.dumps(self.parse(line)))

    def parse(self, line):
        if line.startswith(b'*') and line.endswith(b';') and len(line) in [16, 30]:
            return bytes.fromhex(line[1:-1].decode())
        else:
            logger.warning("invalid raw message: %s", line)
