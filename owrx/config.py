from owrx.property import PropertyLayer
import importlib.util
import os
import logging
import json
from glob import glob
from abc import ABC, abstractmethod
from configparser import ConfigParser

logger = logging.getLogger(__name__)


class ConfigNotFoundException(Exception):
    pass


class ConfigError(Exception):
    def __init__(self, key, message):
        super().__init__("Configuration Error (key: {0}): {1}".format(key, message))


class ConfigMigrator(ABC):
    @abstractmethod
    def migrate(self, config):
        pass

    def renameKey(self, config, old, new):
        if old in config and new not in config:
            config[new] = config[old]
            del config[old]


class ConfigMigratorVersion1(ConfigMigrator):
    def migrate(self, config):
        if "receiver_gps" in config:
            gps = config["receiver_gps"]
            config["receiver_gps"] = {"lat": gps[0], "lon": gps[1]}

        if "waterfall_auto_level_margin" in config:
            levels = config["waterfall_auto_level_margin"]
            config["waterfall_auto_level_margin"] = {"min": levels[0], "max": levels[1]}

        self.renameKey(config, "wsjt_queue_workers", "decoding_queue_workers")
        self.renameKey(config, "wsjt_queue_length", "decoding_queue_length")

        config["version"] = 2
        return config


class ConfigMigratorVersion2(ConfigMigrator):
    def migrate(self, config):
        if "waterfall_colors" in config and any(v > 0xFFFFFF for v in config["waterfall_colors"]):
            config["waterfall_colors"] = [v >> 8 for v in config["waterfall_colors"]]
        return config


class CoreConfig(object):
    defaults = {
        "core": {
            "data_directory": "/var/lib/openwebrx",
            "temporary_directory": "/tmp",
        },
        "web": {
            "port": 8073,
        },
        "aprs": {
            "symbols_path": "/usr/share/aprs-symbols/png"
        }
    }

    def __init__(self):
        config = ConfigParser()
        # set up config defaults
        config.read_dict(CoreConfig.defaults)
        # check for overrides
        overrides_dir = "/etc/openwebrx/openwebrx.conf.d"
        if os.path.exists(overrides_dir) and os.path.isdir(overrides_dir):
            overrides = glob(overrides_dir + "/*.conf")
        else:
            overrides = []
        # sequence things together
        config.read(["./openwebrx.conf", "/etc/openwebrx/openwebrx.conf"] + overrides)
        self.data_directory = config.get("core", "data_directory")
        CoreConfig.checkDirectory(self.data_directory, "data_directory")
        self.temporary_directory = config.get("core", "temporary_directory")
        CoreConfig.checkDirectory(self.temporary_directory, "temporary_directory")
        self.web_port = config.getint("web", "port")
        self.aprs_symbols_path = config.get("aprs", "symbols_path")

    @staticmethod
    def checkDirectory(dir, key):
        if not os.path.exists(dir):
            raise ConfigError(key, "{dir} doesn't exist".format(dir=dir))
        if not os.path.isdir(dir):
            raise ConfigError(key, "{dir} is not a directory".format(dir=dir))
        if not os.access(dir, os.W_OK):
            raise ConfigError(key, "{dir} is not writable".format(dir=dir))

    def get_web_port(self):
        return self.web_port

    def get_data_directory(self):
        return self.data_directory

    def get_temporary_directory(self):
        return self.temporary_directory

    def get_aprs_symbols_path(self):
        return self.aprs_symbols_path


class Config:
    sharedConfig = None
    currentVersion = 3
    migrators = {
        1: ConfigMigratorVersion1(),
        2: ConfigMigratorVersion2(),
    }

    @staticmethod
    def _loadPythonFile(file):
        spec = importlib.util.spec_from_file_location("config_webrx", file)
        cfg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cfg)
        pm = PropertyLayer()
        for name, value in cfg.__dict__.items():
            if name.startswith("__"):
                continue
            pm[name] = value
        return pm

    @staticmethod
    def _loadJsonFile(file):
        with open(file, "r") as f:
            pm = PropertyLayer()
            for k, v in json.load(f).items():
                pm[k] = v
            return pm

    @staticmethod
    def _getSettingsFile():
        coreConfig = CoreConfig()
        return "{data_directory}/settings.json".format(data_directory=coreConfig.get_data_directory())

    @staticmethod
    def _loadConfig():
        for file in [Config._getSettingsFile(), "/etc/openwebrx/config_webrx.py", "./config_webrx.py"]:
            try:
                if file.endswith(".py"):
                    return Config._loadPythonFile(file)
                elif file.endswith(".json"):
                    return Config._loadJsonFile(file)
                else:
                    logger.warning("unsupported file type: %s", file)
            except FileNotFoundError:
                pass
        raise ConfigNotFoundException("no usable config found! please make sure you have a valid configuration file!")

    @staticmethod
    def get():
        if Config.sharedConfig is None:
            Config.sharedConfig = Config._migrate(Config._loadConfig())
        return Config.sharedConfig

    @staticmethod
    def store():
        with open(Config._getSettingsFile(), "w") as file:
            json.dump(Config.get().__dict__(), file, indent=4)

    @staticmethod
    def validateConfig():
        # no config checks atm
        # just basic loading verification
        Config.get()

    @staticmethod
    def _migrate(config):
        version = config["version"] if "version" in config else 1
        if version == Config.currentVersion:
            return config

        logger.debug("migrating config from version %i", version)
        migrators = [Config.migrators[i] for i in range(version, Config.currentVersion)]
        for migrator in migrators:
            config = migrator.migrate(config)
        return config
