from owrx.config.core import CoreConfig
from owrx.config.migration import Migrator
from owrx.property import PropertyLayer
from owrx.jsons import Encoder
import json


class DynamicConfig(PropertyLayer):
    _deleted = object()

    def __init__(self):
        super().__init__()
        try:
            with open(DynamicConfig._getSettingsFile(), "r") as f:
                for k, v in json.load(f).items():
                    if isinstance(v, dict):
                        self[k] = DynamicConfig._toLayer(v)
                    else:
                        self[k] = v
        except FileNotFoundError:
            pass
        Migrator.migrate(self)

    @staticmethod
    def _toLayer(dictionary: dict):
        layer = PropertyLayer()
        for k, v in dictionary.items():
            if isinstance(v, dict):
                layer[k] = DynamicConfig._toLayer(v)
            else:
                layer[k] = v
        return layer

    @staticmethod
    def _getSettingsFile():
        coreConfig = CoreConfig()
        return "{data_directory}/settings.json".format(data_directory=coreConfig.get_data_directory())

    def store(self):
        # don't write directly to file to avoid corruption on exceptions
        jsonContent = json.dumps(self.__dict__(), indent=4, cls=Encoder)
        with open(DynamicConfig._getSettingsFile(), "w") as file:
            file.write(jsonContent)

    def __delitem__(self, key):
        self.__setitem__(key, DynamicConfig._deleted)

    def __contains__(self, item):
        if not super().__contains__(item):
            return False
        if super().__getitem__(item) is DynamicConfig._deleted:
            return False
        return True

    def __getitem__(self, item):
        if self.__contains__(item):
            return super().__getitem__(item)
        raise KeyError('Key "{key}" does not exist'.format(key=item))

    def __dict__(self):
        return {k: v for k, v in super().__dict__().items() if v is not DynamicConfig._deleted}

    def keys(self):
        return [k for k in super().keys() if self.__contains__(k)]
