from owrx.form import DropdownEnum


class AprsBeaconSymbols(DropdownEnum):
    BEACON_RECEIVE_ONLY = ("R&", "Receive only IGate")
    BEACON_HF_GATEWAY = ("/&", "HF Gateway")
    BEACON_IGATE_GENERIC = ("I&", "Igate Generic (please use more specific overlay)")
    BEACON_PSKMAIL = ("P&", "PSKmail node")
    BEACON_TX_1 = ("T&", "TX IGate with path set to 1 hop")
    BEACON_WIRES_X = ("W&", "Wires-X")
    BEACON_TX_2 = ("2&", "TX IGate with path set to 2 hops")

    def __new__(cls, *args, **kwargs):
        value, description = args
        obj = object.__new__(cls)
        obj._value_ = value
        obj.description = description
        return obj

    def __str__(self):
        return "{description} ({symbol})".format(description=self.description, symbol=self.value)


class AprsAntennaDirections(DropdownEnum):
    DIRECTION_OMNI = None
    DIRECTION_N = "N"
    DIRECTION_NE = "NE"
    DIRECTION_E = "E"
    DIRECTION_SE = "SE"
    DIRECTION_S = "S"
    DIRECTION_SW = "SW"
    DIRECTION_W = "W"
    DIRECTION_NW = "NW"

    def __str__(self):
        return "omnidirectional" if self.value is None else self.value
