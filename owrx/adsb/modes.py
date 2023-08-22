from csdr.module import PickleModule
from math import sqrt, atan2, pi

import logging

logger = logging.getLogger(__name__)


FEET_PER_METER = 3.28084


class ModeSParser(PickleModule):
    def process(self, input):
        format = (input[0] & 0b11111000) >> 3
        message =  {
            "mode": "ADSB",
            "format": format
        }
        if format == 17:
            message["capability"] = input[0] & 0b111
            message["icao"] = input[1:4].hex()
            type = (input[4] & 0b11111000) >> 3
            message["type"] = type

            if type in range(1, 5):
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

            elif type in range(5, 9):
                # surface position
                pass

            elif type in range(9, 19):
                # airborne position (w/ baro  altitude)
                q = (input[5] & 0b1)
                altitude = ((input[5] & 0b11111110) << 3) | ((input[6] & 0b1111) >> 4)
                if q:
                    message["altitude"] = altitude * 25 - 1000
                else:
                    # TODO: it's gray encoded
                    message["altitude"] = altitude * 100

            elif type == 19:
                # airborne velocity
                subtype = input[4] & 0b111
                if subtype in range(1, 3):
                    dew = (input[5] & 0b00000100) >> 2
                    vew = ((input[5] & 0b00000011) << 8) | input[6]
                    dns = (input[7] & 0b10000000) >> 7
                    vns = ((input[7] & 0b01111111) << 3) | ((input[8] & 0b1110000000) >> 5)
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
                else:
                    logger.debug("subtype: %i", subtype)

            elif type in range(20, 23):
                # airborne position (w/GNSS height)
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

        return message
