from datetime import datetime


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
        super().__init__()

    def broadcast(self, update):
        for c in self.clients:
            c.write_update(update)

    def addClient(self, client):
        self.clients.append(client)
        client.write_update([{"callsign": callsign, "location": record["loc"].__dict__()} for (callsign, record) in self.positions.items()])

    def removeClient(self, client):
        try:
            self.clients.remove(client)
        except ValueError:
            pass

    def updateLocation(self, callsign, loc: Location):
        self.positions[callsign] = {"loc": loc, "updated": datetime.now()}
        self.broadcast([{"callsign": callsign, "location": loc.__dict__()}])


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
