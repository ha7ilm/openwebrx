import socket
import time
import logging
import random
from owrx.config import Config

logger = logging.getLogger(__name__)

FEND = 0xC0
FESC = 0xDB
TFEND = 0xDC
TFESC = 0xDD


class DirewolfConfig(object):
    def getConfig(self, port, is_service):
        pm = Config.get()

        config = """
ACHANNELS 1
ADEVICE stdin null

CHANNEL 0
MYCALL {callsign}
MODEM 1200

KISSPORT {port}
AGWPORT off
        """.format(
            port=port, callsign=pm["aprs_callsign"]
        )

        if is_service and pm["aprs_igate_enabled"]:
            config += """
IGSERVER {server}
IGLOGIN {callsign} {password}
            """.format(
                server=pm["aprs_igate_server"], callsign=pm["aprs_callsign"], password=pm["aprs_igate_password"]
            )

            if pm["aprs_igate_beacon"]:
                #Format beacon lat/lon
                lat = pm["receiver_gps"]["lat"]
                lon = pm["receiver_gps"]["lon"]
                direction_ns = "N" if lat > 0 else "S"
                direction_we = "E" if lon > 0 else "W"
                lat = abs(lat)
                lon = abs(lon)
                lat = "{0:02d}^{1:05.2f}{2}".format(int(lat), (lat - int(lat)) * 60, direction_ns)
                lon = "{0:03d}^{1:05.2f}{2}".format(int(lon), (lon - int(lon)) * 60, direction_we)

                #Format beacon details
                symbol  = str(pm["aprs_igate_symbol"])             if "aprs_igate_symbol"  in pm else "R&"
                power   = str(pm["aprs_igate_power"])              if "aprs_igate_power"   in pm else "0"
                height  = "HEIGHT=" + str(pm["aprs_igate_height"]) if "aprs_igate_height"  in pm else ""
                gain    = "GAIN=" + str(pm["aprs_igate_gain"])     if "aprs_igate_gain"    in pm else ""
                adir    = "DIR=" + str(pm["aprs_igate_dir"])       if "aprs_igate_dir"     in pm else ""
                freq    = "FREQ=" + str(pm["aprs_igate_freq"])     if "aprs_igate_freq"    in pm else ""
                tone    = "TONE=" + str(pm["aprs_igate_tone"])     if "aprs_igate_tone"    in pm else ""
                offset  = "OFFSET=" + str(pm["aprs_igate_offset"]) if "aprs_igate_offset"  in pm else ""
                comment = str(pm["aprs_igate_comment"])            if "aprs_igate_comment" in pm else "\"OpenWebRX APRS gateway\""

                logger.info(str(len(comment)))
                if((len(comment) > 0) and ((comment[0] != '"') or (comment[len(comment)-1] != '"'))):
                    logger.info(comment)
                    comment = "\"" + comment + "\""
                    logger.info(comment)

                pbeacon= "PBEACON sendto=IG delay=0:30 every=60:00 symbol={symbol} lat={lat} long={lon} POWER={power} {height} {gain} {adir} {freq} {tone} {offset} comment={comment}".format(
                    symbol=symbol, lat=lat, lon=lon, power=power, height=height, gain=gain, adir=adir, freq=freq, tone=tone, offset=offset, comment=comment )

                logger.info("APRS PBEACON String: " + pbeacon)
                
                config += """
                          {pbeacon}
                          """.format(pbeacon=pbeacon)

        return config


class KissClient(object):
    @staticmethod
    def getFreePort():
        # direwolf has some strange hardcoded port ranges
        while True:
            try:
                port = random.randrange(1024, 49151)
                # test if port is available for use
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(("localhost", port))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.close()
                return port
            except OSError:
                pass

    def __init__(self, port):
        delay = .5
        retries = 0
        while True:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect(("localhost", port))
                break
            except ConnectionError:
                if retries > 20:
                    logger.error("maximum number of connection attempts reached. did direwolf start up correctly?")
                    raise
                retries += 1
            time.sleep(delay)

    def read(self):
        return self.socket.recv(1)


class KissDeframer(object):
    def __init__(self):
        self.escaped = False
        self.buf = bytearray()

    def parse(self, input):
        frames = []
        for b in input:
            if b == FESC:
                self.escaped = True
            elif self.escaped:
                if b == TFEND:
                    self.buf.append(FEND)
                elif b == TFESC:
                    self.buf.append(FESC)
                else:
                    logger.warning("invalid escape char: %s", str(input[0]))
                self.escaped = False
            elif input[0] == FEND:
                # data frames start with 0x00
                if len(self.buf) > 1 and self.buf[0] == 0x00:
                    frames += [self.buf[1:]]
                self.buf = bytearray()
            else:
                self.buf.append(b)
        return frames
