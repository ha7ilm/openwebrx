from datetime import datetime, timedelta
import threading, time
from owrx.config import PropertyManager

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

        def removeLoop():
            while True:
                try:
                    self.removeOldPositions()
                except Exception:
                    logger.exception("error while removing old map positions")
                time.sleep(60)

        threading.Thread(target=removeLoop, daemon=True).start()
        super().__init__()

    def broadcast(self, update):
        for c in self.clients:
            c.write_update(update)

    def addClient(self, client):
        self.clients.append(client)
        client.write_update([
            {
                "callsign": callsign,
                "location": record["location"].__dict__(),
                "lastseen": record["updated"].timestamp() * 1000,
                "mode"    : record["mode"]
            }
            for (callsign, record) in self.positions.items()
        ])

    def removeClient(self, client):
        try:
            self.clients.remove(client)
        except ValueError:
            pass

    def updateLocation(self, callsign, loc: Location, mode: str):
        ts = datetime.now()
        self.positions[callsign] = {"location": loc, "updated": ts, "mode": mode}
        self.broadcast([
            {
                "callsign": callsign,
                "location": loc.__dict__(),
                "lastseen": ts.timestamp() * 1000,
                "mode"    : mode
            }
        ])

    def removeLocation(self, callsign):
        self.positions.pop(callsign, None)
        # TODO broadcast removal to clients

    def removeOldPositions(self):
        pm = PropertyManager.getSharedInstance()
        retention = timedelta(seconds=pm["map_position_retention_time"])
        cutoff = datetime.now() - retention

        to_be_removed = [callsign for (callsign, pos) in self.positions.items() if pos["updated"] < cutoff]
        for callsign in to_be_removed:
            self.removeLocation(callsign)

class LatLngLocation(Location):
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

    def __dict__(self):
        return {
            "type":"latlon",
            "lat":self.lat,
            "lon":self.lon
        }


class LocatorLocation(Location):
    def __init__(self, locator: str):
        self.locator = locator

    def __dict__(self):
        return {
            "type":"locator",
            "locator":self.locator
        }
