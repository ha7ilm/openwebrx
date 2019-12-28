from datetime import datetime, timedelta
import threading, time
from owrx.config import PropertyManager
from owrx.bands import Band

import logging

logger = logging.getLogger(__name__)


class Location(object):
    def __dict__(self):
        return {}


class Map(object):
    sharedInstance = None

    @staticmethod
    def getSharedInstance():
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

        threading.Thread(target=removeLoop, daemon=True).start()
        super().__init__()

    def broadcast(self, update):
        for c in self.clients:
            c.write_update(update)

    def addClient(self, client):
        self.clients.append(client)
        client.write_update(
            [
                {
                    "callsign": callsign,
                    "location": record["location"].__dict__(),
                    "lastseen": record["updated"].timestamp() * 1000,
                    "mode": record["mode"],
                    "band": record["band"].getName() if record["band"] is not None else None,
                }
                for (callsign, record) in self.positions.items()
            ]
        )

    def removeClient(self, client):
        try:
            self.clients.remove(client)
        except ValueError:
            pass

    def updateLocation(self, callsign, loc: Location, mode: str, band: Band = None):
        ts = datetime.now()
        with self.positionsLock:
            self.positions[callsign] = {"location": loc, "updated": ts, "mode": mode, "band": band}
        self.broadcast(
            [
                {
                    "callsign": callsign,
                    "location": loc.__dict__(),
                    "lastseen": ts.timestamp() * 1000,
                    "mode": mode,
                    "band": band.getName() if band is not None else None,
                }
            ]
        )

    def touchLocation(self, callsign):
        # not implemented on the client side yet, so do not use!
        ts = datetime.now()
        with self.positionsLock:
            if callsign in self.positions:
                self.positions[callsign]["updated"] = ts
        self.broadcast([{"callsign": callsign, "lastseen": ts.timestamp() * 1000}])

    def removeLocation(self, callsign):
        with self.positionsLock:
            del self.positions[callsign]
            # TODO broadcast removal to clients

    def removeOldPositions(self):
        pm = PropertyManager.getSharedInstance()
        retention = timedelta(seconds=pm["map_position_retention_time"])
        cutoff = datetime.now() - retention

        to_be_removed = [callsign for (callsign, pos) in self.positions.items() if pos["updated"] < cutoff]
        for callsign in to_be_removed:
            self.removeLocation(callsign)

    def rebuildPositions(self):
        with self.positionsLock:
            p = {key: value for key, value in self.positions.items()}
            self.positions = p


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
