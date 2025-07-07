"""Configuration manager singleton."""

def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class ConfigManager:
    def __init__(self):
        self.config = {}
    
    def get_config(self, key):
        return self.config.get(key)
