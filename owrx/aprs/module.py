from pycsdr.types import Format
from pycsdr.modules import Writer, TcpSource, ExecModule, CallbackWriter
from owrx.aprs.direwolf import DirewolfConfig, DirewolfConfigSubscriber
from owrx.config.core import CoreConfig
import time
import os

import logging

logger = logging.getLogger(__name__)


class LogWriter(CallbackWriter):
    def __init__(self):
        self.retained = bytes()
        super().__init__(Format.CHAR)

    def write(self, data: bytes) -> None:
        self.retained += data
        lines = self.retained.split(b"\n")

        # keep the last line
        # this should either be empty if the last char was \n
        # or an incomplete line if the read returned early
        self.retained = lines[-1]

        # log all completed lines
        for line in lines[0:-1]:
            logger.info("{}: {}".format("STDOUT", line.strip(b'\n').decode()))


class DirewolfModule(ExecModule, DirewolfConfigSubscriber):
    def __init__(self, service: bool = False):
        self.tcpSource = None
        self.writer = None
        self.service = service
        self.direwolfConfigPath = "{tmp_dir}/openwebrx_direwolf_{myid}.conf".format(
            tmp_dir=CoreConfig().get_temporary_directory(), myid=id(self)
        )

        self.direwolfConfig = DirewolfConfig()
        self.direwolfConfig.wire(self)
        self.__writeConfig()

        super().__init__(Format.SHORT, Format.CHAR, ["direwolf", "-c", self.direwolfConfigPath, "-r", "48000", "-t", "0", "-q", "d", "-q", "h"])
        # direwolf supplies the data via a socket which we tap into in start()
        # the output on its STDOUT is informative, but we still want to log it
        super().setWriter(LogWriter())
        self.start()

    def __writeConfig(self):
        file = open(self.direwolfConfigPath, "w")
        file.write(self.direwolfConfig.getConfig(self.service))
        file.close()

    def setWriter(self, writer: Writer) -> None:
        self.writer = writer
        if self.tcpSource is not None:
            self.tcpSource.setWriter(writer)

    def start(self):
        delay = 0.5
        retries = 0
        while True:
            try:
                self.tcpSource = TcpSource(self.direwolfConfig.getPort(), Format.CHAR)
                if self.writer:
                    self.tcpSource.setWriter(self.writer)
                break
            except ConnectionError:
                if retries > 20:
                    logger.error("maximum number of connection attempts reached. did direwolf start up correctly?")
                    raise
                retries += 1
            time.sleep(delay)

    def restart(self):
        self.__writeConfig()
        super().restart()
        self.start()

    def onConfigChanged(self):
        self.restart()

    def stop(self) -> None:
        super().stop()
        os.unlink(self.direwolfConfigPath)
        self.direwolfConfig.unwire(self)
        self.direwolfConfig = None
