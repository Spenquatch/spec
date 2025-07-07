"""Database connection singleton."""

_connection = None

def get_connection():
    global _connection
    if _connection is None:
        _connection = DatabaseConnection()
    return _connection

class DatabaseConnection:
    def __init__(self):
        self.connected = True

    def query(self, sql):
        return "result"
