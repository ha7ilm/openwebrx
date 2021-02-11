from owrx.property import PropertyReadOnly, PropertyLayer
from owrx.config.migration import Migrator
import importlib.util


class ClassicConfig(PropertyReadOnly):
    def __init__(self):
        pm = ClassicConfig._loadConfig()
        Migrator.migrate(pm)
        super().__init__(pm)

    @staticmethod
    def _loadConfig():
        for file in ["/etc/openwebrx/config_webrx.py", "./config_webrx.py"]:
            try:
                return ClassicConfig._loadPythonFile(file)
            except FileNotFoundError:
                pass

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
