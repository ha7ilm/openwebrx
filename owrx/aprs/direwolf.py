import random
from owrx.config import Config
from abc import ABC, abstractmethod
import socket

import logging

logger = logging.getLogger(__name__)

FEET_PER_METER = 3.28084


class DirewolfConfigSubscriber(ABC):
    @abstractmethod
    def onConfigChanged(self):
        pass


class DirewolfConfig(object):
    config_keys = [
        "aprs_callsign",
        "aprs_igate_enabled",
        "aprs_igate_server",
        "aprs_igate_password",
        "receiver_gps",
        "aprs_igate_symbol",
        "aprs_igate_beacon",
        "aprs_igate_gain",
        "aprs_igate_dir",
        "aprs_igate_comment",
        "aprs_igate_height",
    ]

    def __init__(self):
        self.subscribers = []
        self.configSub = None
        self.port = None

    def wire(self, subscriber: DirewolfConfigSubscriber):
        self.subscribers.append(subscriber)
        if self.configSub is None:
            pm = Config.get()
            self.configSub = pm.filter(*DirewolfConfig.config_keys).wire(self._fireChanged)

    def unwire(self, subscriber: DirewolfConfigSubscriber):
        self.subscribers.remove(subscriber)
        if not self.subscribers and self.configSub is not None:
            self.configSub.cancel()

    def _fireChanged(self, changes):
        for sub in self.subscribers:
            try:
                sub.onConfigChanged()
            except Exception:
                logger.exception("Error while notifying Direwolf subscribers")

    def getPort(self):
        # direwolf has some strange hardcoded port ranges
        while self.port is None:
            try:
                port = random.randrange(1024, 49151)
                # test if port is available for use
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(("localhost", port))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.close()
                self.port = port
            except OSError:
                pass
        return self.port

    def getConfig(self, is_service):
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
            port=self.getPort(), callsign=pm["aprs_callsign"]
        )

        if is_service and pm["aprs_igate_enabled"]:
            pbeacon = ""

            if pm["aprs_igate_beacon"]:
                # Format beacon lat/lon
                lat = pm["receiver_gps"]["lat"]
                lon = pm["receiver_gps"]["lon"]
                direction_ns = "N" if lat > 0 else "S"
                direction_we = "E" if lon > 0 else "W"
                lat = abs(lat)
                lon = abs(lon)
                lat = "{0:02d}^{1:05.2f}{2}".format(int(lat), (lat - int(lat)) * 60, direction_ns)
                lon = "{0:03d}^{1:05.2f}{2}".format(int(lon), (lon - int(lon)) * 60, direction_we)

                # Convert height from meters to feet if specified
                height = ""
                if "aprs_igate_height" in pm:
                    try:
                        height_m = float(pm["aprs_igate_height"])
                        height_ft = round(height_m * FEET_PER_METER)
                        height = "HEIGHT=" + str(height_ft)
                    except:
                        logger.error(
                            "Cannot parse 'aprs_igate_height', expected float: " + str(pm["aprs_igate_height"])
                        )

                pbeacon = 'PBEACON sendto=IG delay=0:30 every=60:00 symbol={symbol} lat={lat} long={lon} {height} {gain} {adir} comment="{comment}"'.format(
                    symbol=pm["aprs_igate_symbol"],
                    lat=lat,
                    lon=lon,
                    height=height,
                    gain="GAIN=" + str(pm["aprs_igate_gain"]) if "aprs_igate_gain" in pm else "",
                    adir="DIR=" + str(pm["aprs_igate_dir"]) if "aprs_igate_dir" in pm else "",
                    comment=pm["aprs_igate_comment"],
                )

                logger.info("APRS PBEACON String: " + pbeacon)

            config += """
IGSERVER {server}
IGLOGIN {callsign} {password}
{pbeacon}
            """.format(
                server=pm["aprs_igate_server"],
                callsign=pm["aprs_callsign"],
                password=pm["aprs_igate_password"],
                pbeacon=pbeacon,
            )

        return config
