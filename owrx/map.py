from datetime import datetime, timedelta
from owrx.config import Config
from owrx.bands import Band
from abc import abstractmethod, ABCMeta
import threading
import time
import sys

import logging

logger = logging.getLogger(__name__)


class Location(object):
    def __dict__(self):
        return {}


class Map(object):
    sharedInstance = None
    creationLock = threading.Lock()

    @staticmethod
    def getSharedInstance():
        with Map.creationLock:
            if Map.sharedInstance is None:
                Map.sharedInstance = Map()
        return Map.sharedInstance

    def __init__(self):
        self.clients = []
        self.positions = {}
        self.positionsLock = threading.Lock()

        def removeLoop():
            loops = 0
            while True:
                try:
                    self.removeOldPositions()
                except Exception:
                    logger.exception("error while removing old map positions")
                loops += 1
                # rebuild the positions dictionary every once in a while, it consumes lots of memory otherwise
                if loops == 60:
                    try:
                        self.rebuildPositions()
                    except Exception:
                        logger.exception("error while rebuilding positions")
                    loops = 0
                time.sleep(60)

        threading.Thread(target=removeLoop, daemon=True, name="map_removeloop").start()
        super().__init__()

    def broadcast(self, update):
        for c in self.clients:
            c.write_update(update)

    def addClient(self, client):
        self.clients.append(client)
        client.write_update(
            [
                {
                    "source": record["source"],
                    "location": record["location"].__dict__(),
                    "lastseen": record["updated"].timestamp() * 1000,
                    "mode": record["mode"],
                    "band": record["band"].getName() if record["band"] is not None else None,
                }
                for record in self.positions.values()
            ]
        )

    def removeClient(self, client):
        try:
            self.clients.remove(client)
        except ValueError:
            pass

    def _sourceToKey(self, source):
        if "ssid" in source:
            return "{callsign}-{ssid}".format(**source)
        elif "icao" in source:
            return source["icao"]
        elif "flight" in source:
            return source["flight"]
        return source["callsign"]

    def updateLocation(self, source, loc: Location, mode: str, band: Band = None):
        ts = datetime.now()
        key = self._sourceToKey(source)
        with self.positionsLock:
            if isinstance(loc, IncrementalUpdate) and key in self.positions:
                loc.update(self.positions[key]["location"])
            self.positions[key] = {"source": source, "location": loc, "updated": ts, "mode": mode, "band": band}
        self.broadcast(
            [
                {
                    "source": source,
                    "location": loc.__dict__(),
                    "lastseen": ts.timestamp() * 1000,
                    "mode": mode,
                    "band": band.getName() if band is not None else None,
                }
            ]
        )

    def touchLocation(self, source):
        # not implemented on the client side yet, so do not use!
        ts = datetime.now()
        key = self._sourceToKey(source)
        with self.positionsLock:
            if key in self.positions:
                self.positions[key]["updated"] = ts
        self.broadcast([{"source": source, "lastseen": ts.timestamp() * 1000}])

    def removeLocation(self, key):
        with self.positionsLock:
            del self.positions[key]
            # TODO broadcast removal to clients

    def removeOldPositions(self):
        pm = Config.get()
        retention = timedelta(seconds=pm["map_position_retention_time"])
        now = datetime.now()
        cutoff = now - retention

        def isExpired(pos):
            if pos["updated"] < cutoff:
                return True
            if isinstance(pos["location"], TTLUpdate):
                if now - pos["location"].getTTL() > pos["updated"]:
                    return True
            return False

        with self.positionsLock:
            to_be_removed = [key for (key, pos) in self.positions.items() if isExpired(pos)]
        for key in to_be_removed:
            self.removeLocation(key)

    def rebuildPositions(self):
        logger.debug("rebuilding map storage; size before: %i", sys.getsizeof(self.positions))
        with self.positionsLock:
            p = {key: value for key, value in self.positions.items()}
            self.positions = p
        logger.debug("rebuild complete; size after: %i", sys.getsizeof(self.positions))


class LatLngLocation(Location):
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

    def __dict__(self):
        res = {"type": "latlon", "lat": self.lat, "lon": self.lon}
        return res


class LocatorLocation(Location):
    def __init__(self, locator: str):
        self.locator = locator

    def __dict__(self):
        return {"type": "locator", "locator": self.locator}


class IncrementalUpdate(Location, metaclass=ABCMeta):
    @abstractmethod
    def update(self, previousLocation: Location):
        pass


class TTLUpdate(Location, metaclass=ABCMeta):
    @abstractmethod
    def getTTL(self) -> timedelta:
        pass

    def __dict__(self):
        res = super().__dict__()
        res["ttl"] = self.getTTL().total_seconds() * 1000
        return res
