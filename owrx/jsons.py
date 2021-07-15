from owrx.property import PropertyManager
import json


class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, PropertyManager):
            return o.__dict__()
        return super().default(o)
