"""Database connection singleton."""

from singleton import SingletonMeta

class DatabaseConnection(metaclass=SingletonMeta):
    def __init__(self):
        self.connected = True
    
    def query(self, sql):
        return "result"
        
def get_connection():
    return DatabaseConnection()
