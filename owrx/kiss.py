import socket
import time
from owrx.map import Map, LatLngLocation
import logging

logger = logging.getLogger(__name__)

FEND = 0xC0
FESC = 0xDB
TFEND = 0xDC
TFESC = 0XDD

def group(a, *ns):
    for n in ns:
        a = [a[i:i+n] for i in range(0, len(a), n)]
    return a

def join(a, *cs):
    return [cs[0].join(join(t, *cs[1:])) for t in a] if cs else a

def hexdump(data):
    toHex = lambda c: '{:02X}'.format(c)
    toChr = lambda c: chr(c) if 32 <= c < 127 else '.'
    make = lambda f, *cs: join(group(list(map(f, data)), 8, 2), *cs)
    hs = make(toHex, '  ', ' ')
    cs = make(toChr, ' ', '')
    for i, (h, c) in enumerate(zip(hs, cs)):
        print ('{:010X}: {:48}  {:16}'.format(i * 16, h, c))


class KissClient(object):
    def __init__(self, port):
        time.sleep(1)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("localhost", port))

    def read(self):
        buf = bytes()
        escaped = False
        while True:
            input = self.socket.recv(1)
            # EOF
            if len(input) == 0:
                return bytes()

            if input[0] == FESC:
                escaped = True
            elif escaped:
                if input[0] == TFEND:
                    buf += [FEND]
                elif input[0] == TFESC:
                    buf += [FESC]
                else:
                    logger.warning("invalid escape char: %s", str(input[0]))
                escaped = False
            elif input[0] == FEND:
                logger.debug("decoded frame: " + str(buf))
                if len(buf) > 0:
                    try:
                        return self.parseFrame(buf)
                    except Exception:
                        logger.exception("failed to decode packet data")
                        return {}
            else:
                buf += input

    def parseFrame(self, frame):
        # data frames start with 0x00
        if frame[0] != 0x00:
            return {}
        ax25frame = frame[1:]
        control_pid = ax25frame.find(bytes([0x03, 0xf0]))
        if control_pid % 7 > 0:
            logger.warning("aprs packet framing error: control/pid position not aligned with 7-octet callsign data")

        def chunks(l, n):
            """Yield successive n-sized chunks from l."""
            for i in range(0, len(l), n):
                yield l[i:i + n]

        information = ax25frame[control_pid+2:]

        data = {
            "destination": self.extractCallsign(ax25frame[0:7]),
            "source": self.extractCallsign(ax25frame[7:14]),
            "path": [self.extractCallsign(c) for c in chunks(ax25frame[14:control_pid], 7)]
        }
        # TODO how can we tell if this is an APRS frame at all?
        aprsData = self.parseAprsData(data["destination"], information)
        data.update(aprsData)

        logger.debug(data)
        if "lat" in data and "lon" in data:
            loc = LatLngLocation(data["lat"], data["lon"], data["comment"] if "comment" in data else None)
            Map.getSharedInstance().updateLocation(data["source"], loc, "APRS")
        return data

    def hasCompressedCoordinatesx(self, raw):
        return raw[0] == "/" or raw[0] == "\\"

    def parseUncompressedCoordinates(self, raw):
        # TODO parse N/S and E/W
        return {
            "lat": int(raw[0:2]) + float(raw[2:7]) / 60,
            "lon": int(raw[9:12]) + float(raw[12:17]) / 60,
            "symbol": raw[18]
        }

    def parseCompressedCoordinates(self, raw):
        # TODO parse compressed coordinate formats
        return {}

    def parseMicEFrame(self, destination, information):
        # TODO decode MIC-E Frame

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

    def parseAprsData(self, destination, information):
        if information[0] == 0x1c or information[0] == 0x60:
            return self.parseMicEFrame(destination, information)

        information = information.decode()
        logger.debug(information)

        if information[0] == "!" or information[0] == "=":
            # position without timestamp
            information = information[1:]
        elif information[0] == "/" or information[0] == "@":
            # position with timestamp
            # TODO parse timestamp
            information = information[8:]
        else:
            return {}

        if self.hasCompressedCoordinatesx(information):
            coords = self.parseCompressedCoordinates(information[0:9])
            coords["comment"] = information[9:]
        else:
            coords = self.parseUncompressedCoordinates(information[0:19])
            coords["comment"] = information[19:]
        return coords

    def extractCallsign(self, input):
        cs = bytes([b >> 1 for b in input[0:6]]).decode().strip()
        ssid = (input[6] & 0b00011110) >> 1
        if ssid > 0:
            return "{callsign}-{ssid}".format(callsign=cs, ssid=ssid)
        else:
            return cs
