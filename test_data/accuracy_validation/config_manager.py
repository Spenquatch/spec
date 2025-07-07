"""Configuration manager singleton."""

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config = {}
        return cls._instance

    def get_config(self, key):
        return self.config.get(key)
