from csdr.module import AutoStartModule
from pycsdr.types import Format
from pycsdr.modules import Writer, TcpSource
from subprocess import Popen, PIPE
from owrx.aprs.direwolf import DirewolfConfig, DirewolfConfigSubscriber
from owrx.config.core import CoreConfig
import threading
import time
import os

import logging

logger = logging.getLogger(__name__)


class DirewolfModule(AutoStartModule, DirewolfConfigSubscriber):
    def __init__(self, service: bool = False):
        self.process = None
        self.tcpSource = None
        self.service = service
        self.direwolfConfigPath = "{tmp_dir}/openwebrx_direwolf_{myid}.conf".format(
            tmp_dir=CoreConfig().get_temporary_directory(), myid=id(self)
        )
        self.direwolfConfig = None
        super().__init__()

    def setWriter(self, writer: Writer) -> None:
        super().setWriter(writer)
        if self.tcpSource is not None:
            self.tcpSource.setWriter(writer)

    def getInputFormat(self) -> Format:
        return Format.SHORT

    def getOutputFormat(self) -> Format:
        return Format.CHAR

    def start(self):
        self.direwolfConfig = DirewolfConfig()
        self.direwolfConfig.wire(self)
        file = open(self.direwolfConfigPath, "w")
        file.write(self.direwolfConfig.getConfig(self.service))
        file.close()

        # direwolf -c {direwolf_config} -r {audio_rate} -t 0 -q d -q h 1>&2
        self.process = Popen(
            ["direwolf", "-c", self.direwolfConfigPath, "-r", "48000", "-t", "0", "-q", "d", "-q", "h"],
            start_new_session=True,
            stdin=PIPE,
        )

        # resume in case the reader has been stop()ed before
        self.reader.resume()
        threading.Thread(target=self.pump(self.reader.read, self.process.stdin.write)).start()

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

    def stop(self):
        if self.process is not None:
            self.process.terminate()
            self.process.wait()
            self.process = None
        os.unlink(self.direwolfConfigPath)
        self.direwolfConfig.unwire(self)
        self.direwolfConfig = None
        self.reader.stop()

    def onConfigChanged(self):
        self.stop()
        self.start()
