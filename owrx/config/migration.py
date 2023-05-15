from abc import ABC, abstractmethod
from owrx.property import PropertyLayer

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


class ConfigMigratorVersion4(ConfigMigrator):
    def _replaceWaterfallLevels(self, instance):
        if (
            "waterfall_min_level" in instance
            and "waterfall_max_level" in instance
            and not "waterfall_levels" in instance
        ):
            instance["waterfall_levels"] = {
                "min": instance["waterfall_min_level"],
                "max": instance["waterfall_max_level"],
            }
            del instance["waterfall_min_level"]
            del instance["waterfall_max_level"]

    def migrate(self, config):
        # migrate root level
        self._replaceWaterfallLevels(config)
        if "sdrs" in config:
            for device in config["sdrs"].__dict__().values():
                # migrate device level
                self._replaceWaterfallLevels(device)
                if "profiles" in device:
                    for profile in device["profiles"].__dict__().values():
                        # migrate profile level
                        self._replaceWaterfallLevels(profile)

        config["version"] = 5


class ConfigMigratorVersion5(ConfigMigrator):
    def migrate(self, config):
        if "frequency_display_precision" in config:
            # old config was always in relation to the display in MHz (1e6 Hz, hence the 6)
            config["tuning_precision"] = 6 - config["frequency_display_precision"]
            del config["frequency_display_precision"]
        config["version"] = 6


class ConfigMigratorVersion6(ConfigMigrator):
    def migrate(self, config):
        if "waterfall_auto_level_margin" in config:
            walm_config = config["waterfall_auto_level_margin"]
            if "min_range" in walm_config:
                config["waterfall_auto_min_range"] = walm_config["min_range"]
            wal = {k: v for k, v in walm_config.items() if k in ["min", "max"]}
            config["waterfall_auto_levels"] = PropertyLayer(**wal)
            del config["waterfall_auto_level_margin"]
        config["version"] = 7


class ConfigMigratorVersion7(ConfigMigrator):
    def migrate(self, config):
        if "callsign_url" in config:
            if "qrzcq.com" in config["callsign_url"]:
                config["callsign_service"] = "qrzcq"
            elif "qrz.com" in config["callsign_url"]:
                config["callsign_service"] = "qrz"
            else:
                logger.warning("unable to migrate callsign_url! please check settings!")
            del config["callsign_url"]
        config["version"] = 8


class Migrator(object):
    currentVersion = 8
    migrators = {
        1: ConfigMigratorVersion1(),
        2: ConfigMigratorVersion2(),
        3: ConfigMigratorVersion3(),
        4: ConfigMigratorVersion4(),
        5: ConfigMigratorVersion5(),
        6: ConfigMigratorVersion6(),
        7: ConfigMigratorVersion7(),
    }

    @staticmethod
    def migrate(config):
        version = config["version"] if "version" in config else 1
        if version == Migrator.currentVersion:
            return
        elif version > Migrator.currentVersion:
            raise ValueError(
                "Configuration version is too high (current: {}, found: {})".format(Migrator.currentVersion, version)
            )

        logger.debug("migrating config from version %i", version)
        migrators = [Migrator.migrators[i] for i in range(version, Migrator.currentVersion)]
        for migrator in migrators:
            migrator.migrate(config)
