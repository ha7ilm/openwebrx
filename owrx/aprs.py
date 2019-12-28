from owrx.kiss import KissDeframer
from owrx.map import Map, LatLngLocation
from owrx.bands import Bandplan
from owrx.metrics import Metrics, CounterMetric
from datetime import datetime, timezone
import re
import logging

logger = logging.getLogger(__name__)


# speed is in knots... convert to metric (km/h)
knotsToKilometers = 1.852
feetToMeters = 0.3048
milesToKilometers = 1.609344
inchesToMilimeters = 25.4


def fahrenheitToCelsius(f):
    return (f - 32) * 5 / 9


# not sure what the correct encoding is. it seems TAPR has set utf-8 as a standard, but not everybody is following it.
encoding = "utf-8"

# regex for altitute in comment field
altitudeRegex = re.compile("(^.*)\\/A=([0-9]{6})(.*$)")

# regex for parsing third-party headers
thirdpartyeRegex = re.compile("^([a-zA-Z0-9-]+)>((([a-zA-Z0-9-]+\\*?,)*)([a-zA-Z0-9-]+\\*?)):(.*)$")

# regex for getting the message id out of message
messageIdRegex = re.compile("^(.*){([0-9]{1,5})$")


def decodeBase91(input):
    base = decodeBase91(input[:-1]) * 91 if len(input) > 1 else 0
    return base + (ord(input[-1]) - 33)


def getSymbolData(symbol, table):
    return {"symbol": symbol, "table": table, "index": ord(symbol) - 33, "tableindex": ord(table) - 33}


class Ax25Parser(object):
    def parse(self, ax25frame):
        control_pid = ax25frame.find(bytes([0x03, 0xF0]))
        if control_pid % 7 > 0:
            logger.warning("aprs packet framing error: control/pid position not aligned with 7-octet callsign data")

        def chunks(l, n):
            """Yield successive n-sized chunks from l."""
            for i in range(0, len(l), n):
                yield l[i : i + n]

        return {
            "destination": self.extractCallsign(ax25frame[0:7]),
            "source": self.extractCallsign(ax25frame[7:14]),
            "path": [self.extractCallsign(c) for c in chunks(ax25frame[14:control_pid], 7)],
            "data": ax25frame[control_pid + 2 :],
        }

    def extractCallsign(self, input):
        cs = bytes([b >> 1 for b in input[0:6]]).decode(encoding, "replace").strip()
        ssid = (input[6] & 0b00011110) >> 1
        if ssid > 0:
            return "{callsign}-{ssid}".format(callsign=cs, ssid=ssid)
        else:
            return cs


class WeatherMapping(object):
    def __init__(self, char, key, length, scale=None):
        self.char = char
        self.key = key
        self.length = length
        self.scale = scale

    def matches(self, input):
        return self.char == input[0] and len(input) > self.length

    def updateWeather(self, weather, input):
        def deepApply(obj, key, v):
            keys = key.split(".")
            if len(keys) > 1:
                if not keys[0] in obj:
                    obj[keys[0]] = {}
                deepApply(obj[keys[0]], ".".join(keys[1:]), v)
            else:
                obj[key] = v

        try:
            value = int(input[1 : 1 + self.length])
            if self.scale:
                value = self.scale(value)
            deepApply(weather, self.key, value)
        except ValueError:
            pass
        remain = input[1 + self.length :]
        return weather, remain


class WeatherParser(object):
    mappings = [
        WeatherMapping("c", "wind.direction", 3),
        WeatherMapping("s", "wind.speed", 3, lambda x: x * milesToKilometers),
        WeatherMapping("g", "wind.gust", 3, lambda x: x * milesToKilometers),
        WeatherMapping("t", "temperature", 3, fahrenheitToCelsius),
        WeatherMapping("r", "rain.hour", 3, lambda x: x / 100 * inchesToMilimeters),
        WeatherMapping("p", "rain.day", 3, lambda x: x / 100 * inchesToMilimeters),
        WeatherMapping("P", "rain.sincemidnight", 3, lambda x: x / 100 * inchesToMilimeters),
        WeatherMapping("h", "humidity", 2),
        WeatherMapping("b", "barometricpressure", 5, lambda x: x / 10),
        WeatherMapping("s", "snowfall", 3, lambda x: x * 25.4),
    ]

    def __init__(self, data, weather={}):
        self.data = data
        self.weather = weather

    def getWeather(self):
        doWork = True
        weather = self.weather
        while doWork:
            mapping = next((m for m in WeatherParser.mappings if m.matches(self.data)), None)
            if mapping:
                (weather, remain) = mapping.updateWeather(weather, self.data)
                self.data = remain
                doWork = len(self.data) > 0
            else:
                doWork = False
        return weather

    def getRemainder(self):
        return self.data


class AprsLocation(LatLngLocation):
    def __init__(self, data):
        super().__init__(data["lat"], data["lon"])
        self.data = data

    def __dict__(self):
        res = super(AprsLocation, self).__dict__()
        for key in ["comment", "symbol", "course", "speed"]:
            if key in self.data:
                res[key] = self.data[key]
        return res


class AprsParser(object):
    def __init__(self, handler):
        self.ax25parser = Ax25Parser()
        self.deframer = KissDeframer()
        self.dial_freq = None
        self.band = None
        self.handler = handler
        self.metric = self.getMetric()

    def setDialFrequency(self, freq):
        self.dial_freq = freq
        self.band = Bandplan.getSharedInstance().findBand(freq)
        self.metric = self.getMetric()

    def getMetric(self):
        band = "unknown"
        if self.band is not None:
            band = self.band.getName()
        name = "aprs.decodes.{band}.aprs".format(band=band)
        metrics = Metrics.getSharedInstance()
        metric = metrics.getMetric(name)
        if metric is None:
            metric = CounterMetric()
            metrics.addMetric(name, metric)
        return metric

    def parse(self, raw):
        for frame in self.deframer.parse(raw):
            try:
                data = self.ax25parser.parse(frame)

                # TODO how can we tell if this is an APRS frame at all?
                aprsData = self.parseAprsData(data)

                logger.debug("decoded APRS data: %s", aprsData)
                self.updateMap(aprsData)
                self.metric.inc()
                self.handler.write_aprs_data(aprsData)
            except Exception:
                logger.exception("exception while parsing aprs data")

    def updateMap(self, mapData):
        if "type" in mapData and mapData["type"] == "thirdparty" and "data" in mapData:
            mapData = mapData["data"]
        if "lat" in mapData and "lon" in mapData:
            loc = AprsLocation(mapData)
            source = mapData["source"]
            if "type" in mapData:
                if mapData["type"] == "item":
                    source = mapData["item"]
                elif mapData["type"] == "object":
                    source = mapData["object"]
            Map.getSharedInstance().updateLocation(source, loc, "APRS", self.band)

    def hasCompressedCoordinates(self, raw):
        return raw[0] == "/" or raw[0] == "\\"

    def parseUncompressedCoordinates(self, raw):
        lat = int(raw[0:2]) + float(raw[2:7]) / 60
        if raw[7] == "S":
            lat *= -1
        lon = int(raw[9:12]) + float(raw[12:17]) / 60
        if raw[17] == "W":
            lon *= -1
        return {"lat": lat, "lon": lon, "symbol": getSymbolData(raw[18], raw[8])}

    def parseCompressedCoordinates(self, raw):
        return {
            "lat": 90 - decodeBase91(raw[1:5]) / 380926,
            "lon": -180 + decodeBase91(raw[5:9]) / 190463,
            "symbol": getSymbolData(raw[9], raw[0]),
        }

    def parseTimestamp(self, raw):
        now = datetime.now()
        if raw[6] == "h":
            ts = datetime.strptime(raw[0:6], "%H%M%S")
            ts = ts.replace(year=now.year, month=now.month, day=now.month, tzinfo=timezone.utc)
        else:
            ts = datetime.strptime(raw[0:6], "%d%H%M")
            ts = ts.replace(year=now.year, month=now.month)
            if raw[6] == "z":
                ts = ts.replace(tzinfo=timezone.utc)
            elif raw[6] == "/":
                ts = ts.replace(tzinfo=now.tzinfo)
            else:
                logger.warning("invalid timezone info byte: %s", raw[6])
        return int(ts.timestamp() * 1000)

    def parseStatusUpate(self, raw):
        res = {"type": "status"}
        if raw[6] == "z":
            res["timestamp"] = self.parseTimestamp(raw[0:7])
            res["comment"] = raw[7:]
        else:
            res["comment"] = raw
        return res

    def parseAprsData(self, data):
        information = data["data"]

        # forward some of the ax25 data
        aprsData = {"source": data["source"], "destination": data["destination"], "path": data["path"]}

        if information[0] == 0x1C or information[0] == ord("`") or information[0] == ord("'"):
            aprsData.update(MicEParser().parse(data))
            return aprsData

        information = information.decode(encoding, "replace")

        # APRS data type identifier
        dti = information[0]

        if dti == "!" or dti == "=":
            # position without timestamp
            aprsData.update(self.parseRegularAprsData(information[1:]))
        elif dti == "/" or dti == "@":
            # position with timestamp
            aprsData["timestamp"] = self.parseTimestamp(information[1:8])
            aprsData.update(self.parseRegularAprsData(information[8:]))
        elif dti == ">":
            # status update
            aprsData.update(self.parseStatusUpate(information[1:]))
        elif dti == "}":
            # third party
            aprsData.update(self.parseThirdpartyAprsData(information[1:]))
        elif dti == ":":
            # message
            aprsData.update(self.parseMessage(information[1:]))
        elif dti == ";":
            # object
            aprsData.update(self.parseObject(information[1:]))
        elif dti == ")":
            # item
            aprsData.update(self.parseItem(information[1:]))

        return aprsData

    def parseObject(self, information):
        result = {"type": "object"}
        if len(information) > 16:
            result["object"] = information[0:9].strip()
            result["live"] = information[9] == "*"
            result["timestamp"] = self.parseTimestamp(information[10:17])
            result.update(self.parseRegularAprsData(information[17:]))
            # override type, losing information about compression
            result["type"] = "object"
        return result

    def parseItem(self, information):
        result = {"type": "item"}
        if len(information) > 3:
            indexes = [information[0:10].find(p) for p in ["!", "_"]]
            filtered = [i for i in indexes if i >= 3]
            filtered.sort()
            if len(filtered):
                index = filtered[0]
                result["item"] = information[0:index]
                result["live"] = information[index] == "!"
                result.update(self.parseRegularAprsData(information[index + 1 :]))
                # override type, losing information about compression
                result["type"] = "item"
        return result

    def parseMessage(self, information):
        result = {"type": "message"}
        if len(information) > 9 and information[9] == ":":
            result["adressee"] = information[0:9]
            message = information[10:]
            if len(message) > 3 and message[0:3] == "ack":
                result["type"] = "messageacknowledgement"
                result["messageid"] = int(message[3:8])
            elif len(message) > 3 and message[0:3] == "rej":
                result["type"] = "messagerejection"
                result["messageid"] = int(message[3:8])
            else:
                matches = messageIdRegex.match(message)
                if matches:
                    result["messageid"] = int(matches.group(2))
                    message = matches.group(1)
                result["message"] = message
        return result

    def parseThirdpartyAprsData(self, information):
        matches = thirdpartyeRegex.match(information)
        if matches:
            path = matches.group(2).split(",")
            destination = next((c.strip("*").upper() for c in path if c.endswith("*")), None)
            data = self.parseAprsData(
                {
                    "source": matches.group(1).upper(),
                    "destination": destination,
                    "path": path,
                    "data": matches.group(6).encode(encoding),
                }
            )
            return {"type": "thirdparty", "data": data}

        return {"type": "thirdparty"}

    def parseRegularAprsData(self, information):
        if self.hasCompressedCoordinates(information):
            aprsData = self.parseCompressedCoordinates(information[0:10])
            aprsData["type"] = "compressed"
            if information[10] != " ":
                if information[10] == "{":
                    # pre-calculated radio range
                    aprsData["range"] = 2 * 1.08 ** (ord(information[11]) - 33) * milesToKilometers
                else:
                    aprsData["course"] = (ord(information[10]) - 33) * 4
                    # speed is in knots... convert to metric (km/h)
                    aprsData["speed"] = (1.08 ** (ord(information[11]) - 33) - 1) * knotsToKilometers
                # compression type
                t = ord(information[12])
                aprsData["fix"] = (t & 0b00100000) > 0
                sources = ["other", "GLL", "GGA", "RMC"]
                aprsData["nmeasource"] = sources[(t & 0b00011000) >> 3]
                origins = [
                    "Compressed",
                    "TNC BText",
                    "Software",
                    "[tbd]",
                    "KPC3",
                    "Pico",
                    "Other tracker",
                    "Digipeater conversion",
                ]
                aprsData["compressionorigin"] = origins[t & 0b00000111]
            comment = information[13:]
        else:
            aprsData = self.parseUncompressedCoordinates(information[0:19])
            aprsData["type"] = "regular"
            comment = information[19:]

        def decodeHeightGainDirectivity(comment):
            res = {"height": 2 ** int(comment[4]) * 10 * feetToMeters, "gain": int(comment[5])}
            directivity = int(comment[6])
            if directivity == 0:
                res["directivity"] = "omni"
            elif 0 < directivity < 9:
                res["directivity"] = directivity * 45
            return res

        # aprs data extensions
        # yes, weather stations are officially identified by their symbols. go figure...
        if "symbol" in aprsData and aprsData["symbol"]["index"] == 62:
            # weather report
            weather = {}
            if len(comment) > 6 and comment[3] == "/":
                try:
                    weather["wind"] = {"direction": int(comment[0:3]), "speed": int(comment[4:7]) * milesToKilometers}
                except ValueError:
                    pass
                comment = comment[7:]

            parser = WeatherParser(comment, weather)
            aprsData["weather"] = parser.getWeather()
            comment = parser.getRemainder()
        elif len(comment) > 6:
            if comment[3] == "/":
                # course and speed
                # for a weather report, this would be wind direction and speed
                try:
                    aprsData["course"] = int(comment[0:3])
                    aprsData["speed"] = int(comment[4:7]) * knotsToKilometers
                except ValueError:
                    pass
                comment = comment[7:]
            elif comment[0:3] == "PHG":
                # station power and effective antenna height/gain/directivity
                try:
                    powerCodes = [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
                    aprsData["power"] = powerCodes[int(comment[3])]
                    aprsData.update(decodeHeightGainDirectivity(comment))
                except ValueError:
                    pass
                comment = comment[7:]
            elif comment[0:3] == "RNG":
                # pre-calculated radio range
                try:
                    aprsData["range"] = int(comment[3:7]) * milesToKilometers
                except ValueError:
                    pass
                comment = comment[7:]
            elif comment[0:3] == "DFS":
                # direction finding signal strength and antenna height/gain
                try:
                    aprsData["strength"] = int(comment[3])
                    aprsData.update(decodeHeightGainDirectivity(comment))
                except ValueError:
                    pass
                comment = comment[7:]

        matches = altitudeRegex.match(comment)
        if matches:
            aprsData["altitude"] = int(matches.group(2)) * feetToMeters
            comment = matches.group(1) + matches.group(3)

        aprsData["comment"] = comment

        return aprsData


class MicEParser(object):
    def extractNumber(self, input):
        n = ord(input)
        if n >= ord("P"):
            return n - ord("P")
        if n >= ord("A"):
            return n - ord("A")
        return n - ord("0")

    def listToNumber(self, input):
        base = self.listToNumber(input[:-1]) * 10 if len(input) > 1 else 0
        return base + input[-1]

    def extractAltitude(self, comment):
        if len(comment) < 4 or comment[3] != "}":
            return (comment, None)
        return comment[4:], decodeBase91(comment[:3]) - 10000

    def extractDevice(self, comment):
        if len(comment) > 0:
            if comment[0] == ">":
                if len(comment) > 1:
                    if comment[-1] == "=":
                        return comment[1:-1], {"manufacturer": "Kenwood", "device": "TH-D72"}
                    if comment[-1] == "^":
                        return comment[1:-1], {"manufacturer": "Kenwood", "device": "TH-D74"}
                return comment[1:], {"manufacturer": "Kenwood", "device": "TH-D7A"}
            if comment[0] == "]":
                if len(comment) > 1 and comment[-1] == "=":
                    return comment[1:-1], {"manufacturer": "Kenwood", "device": "TM-D710"}
                return comment[1:], {"manufacturer": "Kenwood", "device": "TM-D700"}
            if len(comment) > 2 and (comment[0] == "`" or comment[0] == "'"):
                if comment[-2] == "_":
                    devices = {
                        "b": "VX-8",
                        '"': "FTM-350",
                        "#": "VX-8G",
                        "$": "FT1D",
                        "%": "FTM-400DR",
                        ")": "FTM-100D",
                        "(": "FT2D",
                        "0": "FT3D",
                    }
                    return comment[1:-2], {"manufacturer": "Yaesu", "device": devices.get(comment[-1], "Unknown")}
                if comment[-2:] == " X":
                    return comment[1:-2], {"manufacturer": "SainSonic", "device": "AP510"}
                if comment[-2] == "(":
                    devices = {"5": "D578UV", "8": "D878UV"}
                    return comment[1:-2], {"manufacturer": "Anytone", "device": devices.get(comment[-1], "Unknown")}
                if comment[-2] == "|":
                    devices = {"3": "TinyTrack3", "4": "TinyTrack4"}
                    return comment[1:-2], {"manufacturer": "Byonics", "device": devices.get(comment[-1], "Unknown")}
                if comment[-2:] == "^v":
                    return comment[1:-2], {"manufacturer": "HinzTec", "device": "anyfrog"}
                if comment[-2] == ":":
                    devices = {"4": "P4dragon DR-7400 modem", "8": "P4dragon DR-7800 modem"}
                    return (
                        comment[1:-2],
                        {"manufacturer": "SCS GmbH & Co.", "device": devices.get(comment[-1], "Unknown")},
                    )
                if comment[-2:] == "~v":
                    return comment[1:-2], {"manufacturer": "Other", "device": "Other"}
                return comment[1:-2], None
        return comment, None

    def parse(self, data):
        information = data["data"]
        destination = data["destination"]

        rawLatitude = [self.extractNumber(c) for c in destination[0:6]]
        lat = self.listToNumber(rawLatitude[0:2]) + self.listToNumber(rawLatitude[2:6]) / 6000
        if ord(destination[3]) <= ord("9"):
            lat *= -1

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

        speed = (information[4] - 28) * 10
        dc28 = information[5] - 28
        speed += int(dc28 / 10)
        course = (dc28 % 10) * 100
        course += information[6] - 28
        if speed >= 800:
            speed -= 800
        if course >= 400:
            course -= 400
        # speed is in knots... convert to metric (km/h)
        speed *= knotsToKilometers

        comment = information[9:].decode(encoding, "replace").strip()
        (comment, altitude) = self.extractAltitude(comment)

        (comment, device) = self.extractDevice(comment)

        # altitude might be inside the device string, so repeat and choose one
        (comment, insideAltitude) = self.extractAltitude(comment)
        altitude = next((a for a in [altitude, insideAltitude] if a is not None), None)

        return {
            "fix": information[0] == ord("`") or information[0] == 0x1C,
            "lat": lat,
            "lon": lon,
            "comment": comment,
            "altitude": altitude,
            "speed": speed,
            "course": course,
            "device": device,
            "type": "Mic-E",
            "symbol": getSymbolData(chr(information[7]), chr(information[8])),
        }
