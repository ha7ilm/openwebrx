from owrx.kiss import KissDeframer
from owrx.map import Map, LatLngLocation
from owrx.bands import Bandplan
import logging

logger = logging.getLogger(__name__)


class Ax25Parser(object):

    def parse(self, ax25frame):
        control_pid = ax25frame.find(bytes([0x03, 0xf0]))
        if control_pid % 7 > 0:
            logger.warning("aprs packet framing error: control/pid position not aligned with 7-octet callsign data")

        def chunks(l, n):
            """Yield successive n-sized chunks from l."""
            for i in range(0, len(l), n):
                yield l[i:i + n]

        return {
            "destination": self.extractCallsign(ax25frame[0:7]),
            "source": self.extractCallsign(ax25frame[7:14]),
            "path": [self.extractCallsign(c) for c in chunks(ax25frame[14:control_pid], 7)],
            "data": ax25frame[control_pid+2:]
        }

    def extractCallsign(self, input):
        cs = bytes([b >> 1 for b in input[0:6]]).decode().strip()
        ssid = (input[6] & 0b00011110) >> 1
        if ssid > 0:
            return "{callsign}-{ssid}".format(callsign=cs, ssid=ssid)
        else:
            return cs


class AprsParser(object):

    def __init__(self, handler):
        self.ax25parser = Ax25Parser()
        self.deframer = KissDeframer()
        self.dial_freq = None
        self.band = None
        self.handler = handler

    def setDialFrequency(self, freq):
        self.dial_freq = freq
        self.band = Bandplan.getSharedInstance().findBand(freq)

    def parse(self, raw):
        for frame in self.deframer.parse(raw):
            data = self.ax25parser.parse(frame)

            # TODO how can we tell if this is an APRS frame at all?
            aprsData = self.parseAprsData(data)

            logger.debug(aprsData)
            if "lat" in aprsData and "lon" in aprsData:
                loc = LatLngLocation(aprsData["lat"], aprsData["lon"], aprsData["comment"] if "comment" in data else None)
                Map.getSharedInstance().updateLocation(data["source"], loc, "APRS", self.band)

            self.handler.write_aprs_data(aprsData)

    def hasCompressedCoordinatesx(self, raw):
        return raw[0] == "/" or raw[0] == "\\"

    def parseUncompressedCoordinates(self, raw):
        lat = int(raw[0:2]) + float(raw[2:7]) / 60
        if raw[7] == "S":
            lat *= -1
        lon = int(raw[9:12]) + float(raw[12:17]) / 60
        if raw[17] == "W":
            lon *= -1
        return {
            "lat": lat,
            "lon": lon,
            "symbol": raw[18]
        }

    def parseCompressedCoordinates(self, raw):
        def decodeBase91(input):
            base = decodeBase91(input[:-1]) * 91 if len(input) > 1 else 0
            return base + (ord(input[-1]) - 33)
        return {
            "lat": 90 - decodeBase91(raw[1:5]) / 380926,
            "lon": -180 + decodeBase91(raw[5:9]) / 190463,
            "symbol": raw[9]
        }

    def parseMicEFrame(self, data):
        information = data["data"]
        destination = data["destination"]

        def extractNumber(input):
            n = ord(input)
            if n >= ord("P"):
                return n - ord("P")
            if n >= ord("A"):
                return n - ord("A")
            return n - ord("0")

        def listToNumber(input):
            base = listToNumber(input[:-1]) * 10 if len(input) > 1 else 0
            return base + input[-1]

        logger.debug(destination)
        rawLatitude = [extractNumber(c) for c in destination[0:6]]
        logger.debug(rawLatitude)
        lat = listToNumber(rawLatitude[0:2]) + listToNumber(rawLatitude[2:6]) / 6000
        if ord(destination[3]) <= ord("9"):
            lat *= -1

        logger.debug(lat)

        logger.debug(information)
        lon = information[1] - 28
        if ord(destination[4]) >= ord("P"):
            lon += 100
        if 180 <= lon <= 189:
            lon -= 80
        if 190 <= lon <= 199:
            lon -= 190

        minutes = information[2] - 28
        if minutes >= 60:
            minutes -= 60

        lon += minutes / 60 + (information[3] - 28) / 6000

        if ord(destination[5]) >= ord("P"):
            lon *= -1

        return {
            "lat": lat,
            "lon": lon,
            "comment": information[9:].decode()
        }

    def parseAprsData(self, data):
        information = data["data"]

        # forward some of the ax25 data
        aprsData = {
            "source": data["source"],
            "destination": data["destination"],
            "path": data["path"]
        }

        if information[0] == 0x1c or information[0] == 0x60:
            aprsData.update(self.parseMicEFrame(data))
            return aprsData

        information = information.decode()
        logger.debug(information)

        if information[0] == "!" or information[0] == "=":
            # position without timestamp
            aprsData.update(self.parseRegularAprsData(information[1:]))
        elif information[0] == "/" or information[0] == "@":
            # position with timestamp
            # TODO parse timestamp
            aprsData.update(self.parseRegularAprsData(information[8:]))

        return aprsData

    def parseRegularAprsData(self, information):
        if self.hasCompressedCoordinatesx(information):
            aprsData = self.parseCompressedCoordinates(information[0:10])
            aprsData["comment"] = information[10:]
        else:
            aprsData = self.parseUncompressedCoordinates(information[0:19])
            aprsData["comment"] = information[19:]
        return aprsData
