"""User service with singleton pattern."""

class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class UserService(metaclass=SingletonMeta):
    def get_user(self, user_id):
        return f"User {user_id}"
