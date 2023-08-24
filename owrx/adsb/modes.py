from csdr.module import PickleModule
from math import sqrt, atan2, pi, floor, acos, cos
from owrx.map import LatLngLocation, Map
import time

import logging

logger = logging.getLogger(__name__)


FEET_PER_METER = 3.28084

nz = 15
d_lat_even = 360 / (4 * nz)
d_lat_odd = 360 / (4 * nz - 1)


class AirplaneLocation(LatLngLocation):
    def __init__(self, message):
        super().__init__(message["lat"], message["lon"])


class CprCache:
    def __init__(self):
        self.aircraft = {}

    def getRecentData(self, icao: str):
        if icao not in self.aircraft:
            return []
        now = time.time()
        filtered = [r for r in self.aircraft[icao] if now - r["timestamp"] < 10]
        records = sorted(filtered, key=lambda r: r["timestamp"])
        self.aircraft[icao] = records
        return [r["data"] for r in records]

    def addRecord(self, icao: str, data: any):
        if icao not in self.aircraft:
            self.aircraft[icao] = []
        self.aircraft[icao].append({"timestamp": time.time(), "data": data})


class ModeSParser(PickleModule):
    def __init__(self):
        self.cprCache = CprCache()
        super().__init__()

    def process(self, input):
        format = (input[0] & 0b11111000) >> 3
        message = {
            "mode": "ADSB",
            "format": format
        }
        if format == 17:
            message["capability"] = input[0] & 0b111
            message["icao"] = icao = input[1:4].hex()
            type = (input[4] & 0b11111000) >> 3
            message["type"] = type

            if type in [1, 2, 3, 4]:
                # identification message
                id = [
                    (input[5] & 0b11111100) >> 2,
                    ((input[5] & 0b00000011) << 4) | ((input[6] & 0b11110000) >> 4),
                    ((input[6] & 0b00001111) << 2) | ((input[7] & 0b11000000) >> 6),
                    input[7] & 0b00111111,
                    (input[8] & 0b11111100) >> 2,
                    ((input[8] & 0b00000011) << 4) | ((input[9] & 0b11110000) >> 4),
                    ((input[9] & 0b00001111) << 2) | ((input[10] & 0b11000000) >> 6),
                    input[10] & 0b00111111
                ]

                message["identification"] = bytes(b + (0x40 if b < 27 else 0) for b in id).decode("ascii")

            elif type in [5, 6, 7, 8]:
                # surface position
                pass

            elif type in [9, 10, 11, 12, 13, 14, 15, 16, 17, 18]:
                # airborne position (w/ baro  altitude)

                cpr = self.__getCprData(icao, input)
                if cpr is not None:
                    lat, lon = cpr
                    message["lat"] = lat
                    message["lon"] = lon

                q = (input[5] & 0b1)
                altitude = ((input[5] & 0b11111110) << 3) | ((input[6] & 0b11110000) >> 4)
                if q:
                    message["altitude"] = altitude * 25 - 1000
                else:
                    # TODO: it's gray encoded
                    message["altitude"] = altitude * 100

            elif type == 19:
                # airborne velocity
                subtype = input[4] & 0b111
                if subtype in [1, 2]:
                    # velocity is reported in an east/west and a north/south component
                    # vew = velocity east / west
                    vew = ((input[5] & 0b00000011) << 8) | input[6]
                    # vns = velocity north / south
                    vns = ((input[7] & 0b01111111) << 3) | ((input[8] & 0b1110000000) >> 5)

                    # 0 means no data
                    if vew != 0 and vns != 0:
                        # dew = direction east/west (0 = to east, 1 = to west)
                        dew = (input[5] & 0b00000100) >> 2
                        # dns = direction north/south (0 = to north, 1 = to south)
                        dns = (input[7] & 0b10000000) >> 7

                        vx = vew - 1
                        if dew:
                            vx *= -1
                        vy = vns - 1
                        if dns:
                            vy *= -1
                        # supersonic
                        if subtype == 2:
                            vx *= 4
                            vy *= 4
                        message["groundspeed"] = sqrt(vx ** 2 + vy ** 2)
                        message["groundtrack"] = (atan2(vx, vy) * 360 / (2 * pi)) % 360

                    # vertical rate
                    vr = ((input[8] & 0b00000111) << 6) | ((input[9] & 0b11111100) >> 2)
                    if vr != 0:
                        # vertical speed sign (1 = negative)
                        svr = ((input[8] & 0b00001000) >> 3)
                        # vertical speed
                        vs = 64 * (vr - 1)
                        if svr:
                            vs *= -1
                        message["verticalspeed"] = vs

                elif subtype in [3, 4]:
                    sh = (input[5] & 0b00000100) >> 2
                    if sh:
                        hdg = ((input[5] & 0b00000011) << 8) | input[6]
                        message["heading"] = hdg * 360 / 1024
                        logger.debug("decoded from subtype 3: heading = %i", message["heading"])
                    airspeed = ((input[7] & 0b01111111) << 3) | ((input[8] & 0b11100000) >> 5)
                    if airspeed != 0:
                        airspeed -= 1
                        # supersonic
                        if subtype == 4:
                            airspeed *= 4
                        airspeed_type = (input[7] & 0b10000000) >> 7
                        if airspeed_type:
                            message["TAS"] = airspeed
                            logger.debug("decoded from subtype 3: TAS = %i", message["TAS"])
                        else:
                            message["IAS"] = airspeed
                            logger.debug("decoded from subtype 3: IAS = %i", message["IAS"])

            elif type in [20, 21, 22]:
                # airborne position (w/GNSS height)

                cpr = self.__getCprData(icao, input)
                if cpr is not None:
                    lat, lon = cpr
                    message["lat"] = lat
                    message["lon"] = lon

                altitude = (input[5] << 4) | ((input[6] & 0b1111) >> 4)
                message["altitude"] = altitude * FEET_PER_METER

            elif type == 28:
                # aircraft status
                pass

            elif type == 29:
                # target state and status information
                pass

            elif type == 31:
                # aircraft operation status
                pass

        elif format == 11:
            # Mode-S All-call reply
            message["icao"] = input[1:4].hex()

        if "lat" in message and "lon" in message:
            loc = AirplaneLocation(message)
            Map.getSharedInstance().updateLocation({"callsign": icao}, loc, "ADS-B", None)

        return message

    def __getCprData(self, icao: str, input):
        self.cprCache.addRecord(icao, {
            "cpr_format": (input[6] & 0b00000100) >> 2,
            "lat_cpr": ((input[6] & 0b00000011) << 15) | (input[7] << 7) | ((input[8] & 0b11111110) >> 1),
            "lon_cpr": ((input[8] & 0b00000001) << 16) | (input[9] << 8) | (input[10]),
        })

        records = self.cprCache.getRecentData(icao)

        try:
            # records are sorted by timestamp, last should be newest
            odd = next(r for r in reversed(records) if r["cpr_format"])
            even = next(r for r in reversed(records) if not r["cpr_format"])
            newest = next(reversed(records))

            lat_cpr_even = even["lat_cpr"] / 2 ** 17
            lat_cpr_odd = odd["lat_cpr"] / 2 ** 17

            # latitude zone index
            j = floor(59 * lat_cpr_even - 60 * lat_cpr_odd + .5)

            lat_even = d_lat_even * ((j % 60) + lat_cpr_even)
            lat_odd = d_lat_odd * ((j % 59) + lat_cpr_odd)

            if lat_even >= 270:
                lat_even -= 360
            if lat_odd >= 270:
                lat_odd -= 360

            def nl(lat):
                if lat == 0:
                    return 59
                elif lat == 87:
                    return 2
                elif lat == -87:
                    return 2
                elif lat > 87:
                    return 1
                elif lat < -87:
                    return 1
                else:
                    return floor((2 * pi) / acos(1 - (1 - cos(pi / (2 * nz))) / (cos((pi / 180) * abs(lat)) ** 2)))

            if nl(lat_even) != nl(lat_odd):
                logger.debug("latitude zone mismatch")
                return

            lat = lat_odd if newest["cpr_format"] else lat_even

            lon_cpr_even = even["lon_cpr"] / 2 ** 17
            lon_cpr_odd = odd["lon_cpr"] / 2 ** 17

            # longitude zone index
            nl_lat = nl(lat)
            m = floor(lon_cpr_even * (nl_lat - 1) - lon_cpr_odd * nl_lat + .5)

            n_even = max(nl_lat, 1)
            n_odd = max(nl_lat - 1, 1)

            d_lon_even = 360 / n_even
            d_lon_odd = 360 / n_odd

            lon_even = d_lon_even * (m % n_even + lon_cpr_even)
            lon_odd = d_lon_odd * (m % n_odd + lon_cpr_odd)

            lon = lon_odd if newest["cpr_format"] else lon_even
            if lon >= 180:
                lon -= 360

            return lat, lon

        except StopIteration:
            # we don't have both CPR records. better luck next time.
            pass
