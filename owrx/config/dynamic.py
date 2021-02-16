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
        # don't write directly to file to avoid corruption on exceptions
        jsonContent = json.dumps(self.__dict__(), indent=4)
        with open(DynamicConfig._getSettingsFile(), "w") as file:
            file.write(jsonContent)
