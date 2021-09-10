from csdr.module import PickleModule
import logging

logger = logging.getLogger(__name__)


class PocsagParser(PickleModule):
    def process(self, meta):
        try:
            if "address" in meta:
                meta["address"] = int(meta["address"])
            meta["mode"] = "Pocsag"
            return meta
        except Exception:
            logger.exception("Exception while parsing Pocsag message")
