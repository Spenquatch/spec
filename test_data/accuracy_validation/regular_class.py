"""Regular class that should not be detected as singleton."""

class RegularClass:
    def __init__(self, value):
        self.value = value

    def process(self):
        return self.value * 2
