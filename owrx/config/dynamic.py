from owrx.config.core import CoreConfig
from owrx.config.migration import Migrator
from owrx.property import PropertyLayer
from owrx.jsons import Encoder
import json


class DynamicConfig(PropertyLayer):
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
