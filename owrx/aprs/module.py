from csdr.module import AutoStartModule
from pycsdr.types import Format
from pycsdr.modules import Reader, Writer, TcpSource
from subprocess import Popen, PIPE
from owrx.aprs.direwolf import DirewolfConfig
from owrx.config.core import CoreConfig
import threading
import time

import logging

logger = logging.getLogger(__name__)


class DirewolfModule(AutoStartModule):
    def __init__(self, service: bool = False):
        self.process = None
        self.inputReader = None
        self.tcpSource = None
        self.service = service
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
        temporary_directory = CoreConfig().get_temporary_directory()
        direwolf_config_path = "{tmp_dir}/openwebrx_direwolf_{myid}.conf".format(
            tmp_dir=temporary_directory, myid=id(self)
        )
        direwolf_config = DirewolfConfig()
        # TODO
        # direwolf_config.wire(self)

        file = open(direwolf_config_path, "w")
        file.write(direwolf_config.getConfig(self.service))
        file.close()

        # direwolf -c {direwolf_config} -r {audio_rate} -t 0 -q d -q h 1>&2
        self.process = Popen(
            ["direwolf", "-c", direwolf_config_path, "-r", "48000", "-t", "0", "-q", "d", "-q", "h"],
            start_new_session=True,
            stdin=PIPE,
        )

        threading.Thread(target=self.pump(self.reader.read, self.process.stdin.write)).start()

        delay = 0.5
        retries = 0
        while True:
            try:
                self.tcpSource = TcpSource(direwolf_config.getPort(), Format.CHAR)
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
        self.reader.stop()

    def pump(self, read, write):
        def copy():
            while True:
                data = None
                try:
                    data = read()
                except ValueError:
                    pass
                if data is None or isinstance(data, bytes) and len(data) == 0:
                    break
                write(data)

        return copy
