"""Test console module with singleton imports."""

from rich.console import Console

class ConsoleManager:
    def __init__(self):
        self.console = Console()

    def print(self, text):
        self.console.print(text)
