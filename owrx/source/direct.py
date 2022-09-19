from abc import ABCMeta
from owrx.source import SdrSource, SdrDeviceDescription
from csdr.chain import Chain
from typing import Optional
from pycsdr.modules import Buffer
from pycsdr.types import Format

import logging

logger = logging.getLogger(__name__)


class DirectSource(SdrSource, metaclass=ABCMeta):
    def __init__(self, id, props):
        self._conversion = None
        super().__init__(id, props)

    def onPropertyChange(self, changes):
        logger.debug("restarting sdr source due to property changes: {0}".format(changes))
        self.stop()
        self.sleepOnRestart()
        self.start()

    def nmux_memory(self):
        # in megabytes. This sets the approximate size of the circular buffer used by nmux.
        return 50

    def getNmuxCommand(self):
        props = self.sdrProps

        nmux_bufcnt = nmux_bufsize = 0
        while nmux_bufsize < props["samp_rate"] / 4:
            nmux_bufsize += 4096
        while nmux_bufsize * nmux_bufcnt < self.nmux_memory() * 1e6:
            nmux_bufcnt += 1
        if nmux_bufcnt == 0 or nmux_bufsize == 0:
            raise ValueError("Error: unable to calculate nmux buffer parameters.")

        return [
            "nmux --bufsize %d --bufcnt %d --port %d --address 127.0.0.1"
            % (
                nmux_bufsize,
                nmux_bufcnt,
                self.port,
            )
        ]

    def getCommand(self):
        return super().getCommand() + self.getNmuxCommand()

    # override this in subclasses, if necessary
    def getFormatConversion(self) -> Optional[Chain]:
        return None

    def _getTcpSourceFormat(self):
        conversion = self.getFormatConversion()
        return Format.COMPLEX_FLOAT if conversion is None else conversion.getInputFormat()

    # override this in subclasses, if necessary
    def sleepOnRestart(self):
        pass

    def getBuffer(self):
        if self.buffer is None:
            source = self._getTcpSource()
            buffer = Buffer(source.getOutputFormat())
            source.setWriter(buffer)
            self._conversion = self.getFormatConversion()
            if self._conversion is not None:
                self._conversion.setReader(buffer.getReader())
                # this one must be COMPLEX_FLOAT
                buffer = Buffer(Format.COMPLEX_FLOAT)
                self._conversion.setWriter(buffer)
            self.buffer = buffer
        return self.buffer


class DirectSourceDeviceDescription(SdrDeviceDescription):
    pass
