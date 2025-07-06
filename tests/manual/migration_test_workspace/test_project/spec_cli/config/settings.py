"""Test settings module with singleton imports."""

class SettingsManager:
    def __init__(self):
        self.value = "test"

    def get_value(self):
        return self.value

def get_settings():
    return SettingsManager()
