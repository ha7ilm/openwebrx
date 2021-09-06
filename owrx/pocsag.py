from csdr.module import ThreadModule
from pycsdr.types import Format
import pickle

import logging

logger = logging.getLogger(__name__)


class PocsagParser(ThreadModule):
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
                for frame in self.parse(data.tobytes()):
                    self.writer.write(pickle.dumps(frame))

    def parse(self, raw):
        for line in raw.split(b"\n"):
            if not len(line):
                continue
            try:
                fields = line.decode("ascii", "replace").split(";")
                meta = {v[0]: "".join(v[1:]) for v in map(lambda x: x.split(":"), fields) if v[0] != ""}
                if "address" in meta:
                    meta["address"] = int(meta["address"])
                meta["mode"] = "Pocsag"
                yield meta
            except Exception:
                logger.exception("Exception while parsing Pocsag message")
