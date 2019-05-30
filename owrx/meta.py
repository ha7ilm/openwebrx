from owrx.config import PropertyManager
from urllib import request
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DmrMetaEnricher(object):
    def __init__(self):
        self.cache = {}
        self.cacheTimeout = timedelta(seconds = 86400)
    def cacheEntryValid(self, id):
        if not id in self.cache: return False
        entry = self.cache[id]
        return entry["timestamp"] + self.cacheTimeout > datetime.now()
    def enrich(self, meta):
        if not PropertyManager.getSharedInstance()["digital_voice_dmr_id_lookup"]: return None
        if not "source" in meta: return None
        source = meta["source"]
        if not self.cacheEntryValid(source):
            try:
                logger.debug("requesting DMR metadata for id=%s", source)
                res = request.urlopen("https://www.radioid.net/api/dmr/user/?id={0}".format(source), timeout=5).read()
                data = json.loads(res.decode("utf-8"))
                self.cache[source] = {
                    "timestamp": datetime.now(),
                    "data": data
                }
            except json.JSONDecodeError:
                self.cache[source] = {
                    "timestamp": datetime.now(),
                    "data": None
                }
        data = self.cache[source]["data"]
        if "count" in data and data["count"] > 0 and "results" in data:
            return data["results"][0]
        return None


class MetaParser(object):
    enrichers = {
        "DMR": DmrMetaEnricher()
    }
    def __init__(self, handler):
        self.handler = handler
    def parse(self, meta):
        fields = meta.split(";")
        meta = {v[0] : "".join(v[1:]) for v in map(lambda x: x.split(":"), fields)}

        if "protocol" in meta:
            protocol = meta["protocol"]
            if protocol in MetaParser.enrichers:
                additional_data = MetaParser.enrichers[protocol].enrich(meta)
                if additional_data is not None: meta["additional"] = additional_data
        self.handler.write_metadata(meta)

