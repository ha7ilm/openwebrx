class ConfigNotFoundException(Exception):
    pass


class ConfigError(Exception):
    def __init__(self, key, message):
        super().__init__("Configuration Error (key: {0}): {1}".format(key, message))
