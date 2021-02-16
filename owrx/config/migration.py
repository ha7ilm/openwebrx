from abc import ABC, abstractmethod

import logging

logger = logging.getLogger(__name__)


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


class ConfigMigratorVersion2(ConfigMigrator):
    def migrate(self, config):
        if "waterfall_colors" in config and any(v > 0xFFFFFF for v in config["waterfall_colors"]):
            config["waterfall_colors"] = [v >> 8 for v in config["waterfall_colors"]]

        config["version"] = 3


class ConfigMigratorVersion3(ConfigMigrator):

    def migrate(self, config):
        # inline import due to circular dependencies
        from owrx.waterfall import WaterfallOptions

        if "waterfall_scheme" in config:
            scheme = WaterfallOptions(config["waterfall_scheme"])
            if scheme is not WaterfallOptions.CUSTOM and "waterfall_colors" in config:
                del config["waterfall_colors"]
        elif "waterfall_colors" in config:
            scheme = WaterfallOptions.findByColors(config["waterfall_colors"])
            if scheme is not WaterfallOptions.CUSTOM:
                logger.debug("detected waterfall option: %s", scheme.value)
                if "waterfall_colors" in config:
                    del config["waterfall_colors"]
            config["waterfall_scheme"] = scheme.value

        config["version"] = 4


class Migrator(object):
    currentVersion = 4
    migrators = {
        1: ConfigMigratorVersion1(),
        2: ConfigMigratorVersion2(),
        3: ConfigMigratorVersion3(),
    }

    @staticmethod
    def migrate(config):
        version = config["version"] if "version" in config else 1
        if version == Migrator.currentVersion:
            return config

        logger.debug("migrating config from version %i", version)
        migrators = [Migrator.migrators[i] for i in range(version, Migrator.currentVersion)]
        for migrator in migrators:
            migrator.migrate(config)
