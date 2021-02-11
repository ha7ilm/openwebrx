from owrx.config.core import CoreConfig
from owrx.config.migration import Migrator
from owrx.property import PropertyLayer
import json


class DynamicConfig(PropertyLayer):
    def __init__(self):
        super().__init__()
        try:
            with open(DynamicConfig._getSettingsFile(), "r") as f:
                for k, v in json.load(f).items():
                    self[k] = v
        except FileNotFoundError:
            pass
        Migrator.migrate(self)

    @staticmethod
    def _getSettingsFile():
        coreConfig = CoreConfig()
        return "{data_directory}/settings.json".format(data_directory=coreConfig.get_data_directory())

    def store(self):
        with open(DynamicConfig._getSettingsFile(), "w") as file:
            json.dump(self.__dict__(), file, indent=4)
