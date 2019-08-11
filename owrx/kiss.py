import socket
import time
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
                    return self.parseFrame(buf)
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
        self.parseAprsData(information)

        data = {
            "destination": self.extractCallsign(ax25frame[0:7]),
            "source": self.extractCallsign(ax25frame[7:14]),
            "path": [self.extractCallsign(c) for c in chunks(ax25frame[14:control_pid], 7)]
        }
        logger.debug(data)
        return data

    def parseAprsData(self, data):
        hexdump(data)
        return {}

    def extractCallsign(self, input):
        cs = bytes([b >> 1 for b in input[0:6]]).decode().strip()
        ssid = (input[6] & 0b00011110) >> 1
        if ssid > 0:
            return "{callsign}-{ssid}".format(callsign=cs, ssid=ssid)
        else:
            return cs
