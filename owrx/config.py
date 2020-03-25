from owrx.property import PropertyManager, PropertyLayer
import importlib.util
import os
import logging

logger = logging.getLogger(__name__)


class ConfigNotFoundException(Exception):
    pass


class ConfigError(object):
    def __init__(self, key, message):
        self.key = key
        self.message = message

    def __str__(self):
        return "Configuration Error (key: {0}): {1}".format(self.key, self.message)


class Config:
    sharedConfig = None

    @staticmethod
    def _loadConfig():
        pm = PropertyLayer()
        for file in ["/etc/openwebrx/config_webrx.py", "./config_webrx.py"]:
            try:
                spec = importlib.util.spec_from_file_location("config_webrx", file)
                cfg = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(cfg)
                for name, value in cfg.__dict__.items():
                    if name.startswith("__"):
                        continue
                    pm[name] = value
                return pm
            except FileNotFoundError:
                pass
        raise ConfigNotFoundException("no usable config found! please make sure you have a valid configuration file!")

    @staticmethod
    def get():
        if Config.sharedConfig is None:
            Config.sharedConfig = Config._loadConfig()
        return Config.sharedConfig

    @staticmethod
    def validateConfig():
        pm = Config.get()
        errors = [
            Config.checkTempDirectory(pm)
        ]

        return [e for e in errors if e is not None]

    @staticmethod
    def checkTempDirectory(pm: PropertyManager):
        key = "temporary_directory"
        if key not in pm or pm[key] is None:
            return ConfigError(key, "temporary directory is not set")
        if not os.path.exists(pm[key]):
            return ConfigError(key, "temporary directory doesn't exist")
        if not os.path.isdir(pm[key]):
            return ConfigError(key, "temporary directory path is not a directory")
        if not os.access(pm[key], os.W_OK):
            return ConfigError(key, "temporary directory is not writable")
        return None
