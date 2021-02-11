from owrx.property import PropertyStack
from owrx.config.error import ConfigError
from owrx.config.defaults import defaultConfig
from owrx.config.dynamic import DynamicConfig
from owrx.config.classic import ClassicConfig


class Config(PropertyStack):
    sharedConfig = None

    def __init__(self):
        super().__init__()
        self.storableConfig = DynamicConfig()
        layers = [
            self.storableConfig,
            ClassicConfig(),
            defaultConfig,
        ]
        for i, l in enumerate(layers):
            self.addLayer(i, l)

    @staticmethod
    def get():
        if Config.sharedConfig is None:
            Config.sharedConfig = Config()
        return Config.sharedConfig

    def store(self):
        self.storableConfig.store()

    @staticmethod
    def validateConfig():
        # no config checks atm
        # just basic loading verification
        Config.get()

    def __setitem__(self, key, value):
        # in the config, all writes go to the json layer
        return self.storableConfig.__setitem__(key, value)
