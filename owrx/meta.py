from owrx.config import Config
from urllib import request
import json
from datetime import datetime, timedelta
import logging
import threading
from owrx.map import Map, LatLngLocation
from owrx.parser import Parser
from owrx.aprs import AprsParser, AprsLocation
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Enricher(ABC):
    def __init__(self, parser):
        self.parser = parser

    @abstractmethod
    def enrich(self, meta):
        pass


class DmrCache(object):
    sharedInstance = None

    @staticmethod
    def getSharedInstance():
        if DmrCache.sharedInstance is None:
            DmrCache.sharedInstance = DmrCache()
        return DmrCache.sharedInstance

    def __init__(self):
        self.cache = {}
        self.cacheTimeout = timedelta(seconds=86400)

    def isValid(self, key):
        if key not in self.cache:
            return False
        entry = self.cache[key]
        return entry["timestamp"] + self.cacheTimeout > datetime.now()

    def put(self, key, value):
        self.cache[key] = {"timestamp": datetime.now(), "data": value}

    def get(self, key):
        if not self.isValid(key):
            return None
        return self.cache[key]["data"]


class DmrMetaEnricher(Enricher):
    def __init__(self, parser):
        super().__init__(parser)
        self.threads = {}

    def downloadRadioIdData(self, id):
        cache = DmrCache.getSharedInstance()
        try:
            logger.debug("requesting DMR metadata for id=%s", id)
            res = request.urlopen("https://www.radioid.net/api/dmr/user/?id={0}".format(id), timeout=30).read()
            data = json.loads(res.decode("utf-8"))
            cache.put(id, data)
        except json.JSONDecodeError:
            cache.put(id, None)
        del self.threads[id]

    def enrich(self, meta):
        if not Config.get()["digital_voice_dmr_id_lookup"]:
            return meta
        if "source" not in meta:
            return meta
        id = meta["source"]
        cache = DmrCache.getSharedInstance()
        if not cache.isValid(id):
            if id not in self.threads:
                self.threads[id] = threading.Thread(target=self.downloadRadioIdData, args=[id], daemon=True)
                self.threads[id].start()
            return meta
        data = cache.get(id)
        if data is not None and "count" in data and data["count"] > 0 and "results" in data:
            meta["additional"] = data["results"][0]
        return meta


class YsfMetaEnricher(Enricher):
    def enrich(self, meta):
        for key in ["source", "up", "down", "target"]:
            if key in meta:
                meta[key] = meta[key].strip()
        for key in ["lat", "lon"]:
            if key in meta:
                meta[key] = float(meta[key])
        if "source" in meta and "lat" in meta and "lon" in meta:
            # TODO parsing the float values should probably happen earlier
            loc = LatLngLocation(meta["lat"], meta["lon"])
            Map.getSharedInstance().updateLocation(meta["source"], loc, "YSF", self.parser.getBand())
        return meta


class DStarEnricher(Enricher):
    def enrich(self, meta):
        if "dpmr" in meta:
            # we can send the DPMR stuff through our APRS parser to extract the information
            # TODO: only thrid-party parsing accepts this format right now
            # TODO: we also need to pass a handler, which is not needed
            parser = AprsParser(None)
            dprsData = parser.parseThirdpartyAprsData(meta["dpmr"])
            logger.debug("decoded APRS data: %s", dprsData)
            if "data" in dprsData:
                data = dprsData["data"]
                if "lat" in data and "lon" in data:
                    # TODO: we could actually get the symbols from the parsed APRS data and show that
                    meta["lat"] = data["lat"]
                    meta["lon"] = data["lon"]

                    if "ourcall" in meta:
                        # send location info to map as well
                        loc = AprsLocation(data)
                        Map.getSharedInstance().updateLocation(meta["ourcall"], loc, "APRS", self.parser.getBand())

        return meta


class MetaParser(Parser):
    def __init__(self, handler):
        super().__init__(handler)
        self.enrichers = {"DMR": DmrMetaEnricher(self), "YSF": YsfMetaEnricher(self), "DSTAR": DStarEnricher(self)}

    def parse(self, meta):
        fields = meta.split(";")
        meta = {v[0]: "".join(v[1:]) for v in map(lambda x: x.split(":"), fields) if v[0] != ""}

        if "protocol" in meta:
            protocol = meta["protocol"]
            if protocol in self.enrichers:
                meta = self.enrichers[protocol].enrich(meta)
        self.handler.write_metadata(meta)
