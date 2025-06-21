"""
Comprehensive test module for demonstrating improved AI documentation.

This module contains multiple classes and functions to test the AI's ability
to analyze larger codebases with the increased context window.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class UserProfile:
    """User profile data structure."""

    username: str
    email: str
    age: int
    preferences: dict[str, str]


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, connection_string: str):
        """Initialize database manager."""
        self.connection_string = connection_string
        self.connection = None
        self.is_connected = False

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            # Mock connection logic
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        self.is_connected = False
        self.connection = None

    def execute_query(self, query: str) -> list[dict]:
        """Execute SQL query and return results."""
        if not self.is_connected:
            raise ConnectionError("Database not connected")

        # Mock query execution
        return [{"result": "mock_data"}]


class UserService:
    """Service for managing user operations."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize user service."""
        self.db = db_manager
        self.cache = {}

    def create_user(self, profile: UserProfile) -> bool:
        """Create a new user in the system."""
        try:
            query = f"INSERT INTO users (username, email, age) VALUES ('{profile.username}', '{profile.email}', {profile.age})"
            self.db.execute_query(query)
            self.cache[profile.username] = profile
            return True
        except Exception as e:
            print(f"User creation failed: {e}")
            return False

    def get_user(self, username: str) -> UserProfile | None:
        """Retrieve user by username."""
        if username in self.cache:
            return self.cache[username]

        try:
            query = f"SELECT * FROM users WHERE username = '{username}'"
            results = self.db.execute_query(query)
            if results:
                # Mock user creation from DB result
                return UserProfile(
                    username=results[0].get("username", ""),
                    email=results[0].get("email", ""),
                    age=results[0].get("age", 0),
                    preferences={},
                )
        except Exception as e:
            print(f"User retrieval failed: {e}")

        return None

    def update_user_preferences(
        self, username: str, preferences: dict[str, str]
    ) -> bool:
        """Update user preferences."""
        user = self.get_user(username)
        if user:
            user.preferences.update(preferences)
            self.cache[username] = user
            return True
        return False


class FileProcessor:
    """Process various file types and formats."""

    SUPPORTED_EXTENSIONS = [".txt", ".csv", ".json", ".xml"]

    def __init__(self, base_path: str):
        """Initialize file processor."""
        self.base_path = Path(base_path)
        self.processed_files = []

    def validate_file(self, file_path: str | Path) -> bool:
        """Validate if file can be processed."""
        path = Path(file_path)

        if not path.exists():
            return False

        if path.suffix not in self.SUPPORTED_EXTENSIONS:
            return False

        if path.stat().st_size > 100 * 1024 * 1024:  # 100MB limit
            return False

        return True

    def process_file(self, file_path: str | Path) -> dict[str, str | int]:
        """Process a single file and return metadata."""
        if not self.validate_file(file_path):
            raise ValueError(f"Invalid file: {file_path}")

        path = Path(file_path)

        metadata = {
            "filename": path.name,
            "size": path.stat().st_size,
            "extension": path.suffix,
            "lines": 0,
            "processing_time": 0,
        }

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
                metadata["lines"] = len(content.splitlines())

            self.processed_files.append(path)

        except Exception as e:
            raise RuntimeError(f"Failed to process {path}: {e}")

        return metadata

    def batch_process(self, file_paths: list[str | Path]) -> list[dict]:
        """Process multiple files in batch."""
        results = []

        for file_path in file_paths:
            try:
                result = self.process_file(file_path)
                results.append(result)
            except Exception as e:
                results.append({"filename": str(file_path), "error": str(e)})

        return results


def calculate_statistics(data: list[int | float]) -> dict[str, float]:
    """Calculate basic statistics for a dataset."""
    if not data:
        return {}

    n = len(data)
    total = sum(data)
    mean = total / n

    # Calculate variance
    variance = sum((x - mean) ** 2 for x in data) / n
    std_dev = variance**0.5

    sorted_data = sorted(data)

    # Calculate median
    if n % 2 == 0:
        median = (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
    else:
        median = sorted_data[n // 2]

    return {
        "count": n,
        "sum": total,
        "mean": mean,
        "median": median,
        "variance": variance,
        "std_dev": std_dev,
        "min": min(data),
        "max": max(data),
    }


def main():
    """Main function demonstrating the system."""
    # Initialize database and services
    db = DatabaseManager("sqlite:///test.db")
    if not db.connect():
        print("Failed to connect to database")
        return

    user_service = UserService(db)

    # Create sample users
    users = [
        UserProfile("alice", "alice@example.com", 25, {"theme": "dark"}),
        UserProfile("bob", "bob@example.com", 30, {"theme": "light"}),
        UserProfile("charlie", "charlie@example.com", 35, {"theme": "auto"}),
    ]

    for user in users:
        success = user_service.create_user(user)
        print(f"Created user {user.username}: {success}")

    # Process files
    processor = FileProcessor("/tmp")
    sample_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    stats = calculate_statistics(sample_data)
    print(f"Statistics: {stats}")

    # Cleanup
    db.disconnect()
    print("System demonstration completed")


if __name__ == "__main__":
    main()
