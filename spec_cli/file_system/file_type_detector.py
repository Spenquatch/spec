from pathlib import Path

from ..logging.debug import debug_logger


class FileTypeDetector:
    """Detects file types and determines processability for spec generation."""

    # Comprehensive file type mappings
    LANGUAGE_EXTENSIONS = {
        # Programming languages
        ".py": "python",
        ".pyx": "python",
        ".pyi": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".class": "java",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".hh": "cpp",
        ".hxx": "cpp",
        ".rs": "rust",
        ".go": "go",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".scala": "scala",
        ".cs": "csharp",
        ".vb": "visualbasic",
        # Web technologies
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "css",
        ".sass": "css",
        ".less": "css",
        ".xml": "xml",
        ".xsl": "xml",
        ".xsd": "xml",
        # Data formats
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".csv": "csv",
        ".sql": "sql",
        # Documentation
        ".md": "markdown",
        ".markdown": "markdown",
        ".rst": "restructuredtext",
        ".txt": "text",
        # Configuration
        ".conf": "config",
        ".config": "config",
        ".cfg": "config",
        ".ini": "config",
        ".env": "environment",
        # Build files
        ".mk": "build",
        ".make": "build",
    }

    SPECIAL_FILENAMES = {
        "makefile": "build",
        "dockerfile": "build",
        "vagrantfile": "build",
        "rakefile": "build",
        ".env": "environment",
        ".gitignore": "config",
        ".specignore": "config",
        "readme.md": "documentation",
        "changelog.md": "documentation",
    }

    BINARY_EXTENSIONS = {
        # Executables and libraries
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".a",
        ".lib",
        # Images
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".svg",
        ".ico",
        ".webp",
        # Documents
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        # Archives
        ".zip",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".7z",
        ".rar",
        # Media
        ".mp3",
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wav",
        ".flac",
        # Other binary formats
        ".bin",
        ".dat",
        ".db",
        ".sqlite",
        ".sqlite3",
    }

    # Maximum file size for processing (1MB)
    MAX_FILE_SIZE = 1_048_576

    def get_file_type(self, file_path: Path) -> str:
        """Determine the file type category based on file extension and name.

        Args:
            file_path: Path to the file to analyze

        Returns:
            String representing the file type category
        """
        extension = file_path.suffix.lower()
        filename = file_path.name.lower()

        debug_logger.log(
            "DEBUG",
            "Analyzing file type",
            file_path=str(file_path),
            extension=extension,
            filename=filename,
        )

        # Check special filenames first (higher priority)
        if filename in self.SPECIAL_FILENAMES:
            file_type = self.SPECIAL_FILENAMES[filename]
            debug_logger.log(
                "DEBUG", "File type detected by filename", file_type=file_type
            )
            return file_type

        # Check extensions
        if extension in self.LANGUAGE_EXTENSIONS:
            file_type = self.LANGUAGE_EXTENSIONS[extension]
            debug_logger.log(
                "DEBUG", "File type detected by extension", file_type=file_type
            )
            return file_type

        # No extension or unknown
        if not extension:
            debug_logger.log("DEBUG", "File has no extension")
            return "no_extension"

        debug_logger.log("DEBUG", "Unknown file type")
        return "unknown"

    def is_binary_file(self, file_path: Path) -> bool:
        """Check if file is binary based on extension.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file is likely binary, False otherwise
        """
        extension = file_path.suffix.lower()
        is_binary = extension in self.BINARY_EXTENSIONS

        debug_logger.log(
            "DEBUG",
            "Binary file check",
            file_path=str(file_path),
            extension=extension,
            is_binary=is_binary,
        )

        return is_binary

    def is_processable_file(self, file_path: Path) -> bool:
        """Check if file should be processed for spec generation.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file should be processed, False otherwise
        """
        # Check if binary
        if self.is_binary_file(file_path):
            debug_logger.log("DEBUG", "File skipped - binary", file_path=str(file_path))
            return False

        # Check file type
        file_type = self.get_file_type(file_path)
        if file_type == "unknown":
            debug_logger.log(
                "DEBUG", "File skipped - unknown type", file_path=str(file_path)
            )
            return False

        # Check file size (skip very large files)
        try:
            if file_path.exists() and file_path.stat().st_size > self.MAX_FILE_SIZE:
                debug_logger.log(
                    "DEBUG",
                    "File skipped - too large",
                    file_path=str(file_path),
                    size=file_path.stat().st_size,
                )
                return False
        except OSError as e:
            debug_logger.log(
                "WARNING",
                "Could not check file size",
                file_path=str(file_path),
                error=str(e),
            )
            return False

        debug_logger.log(
            "DEBUG",
            "File is processable",
            file_path=str(file_path),
            file_type=file_type,
        )
        return True

    def get_supported_extensions(self) -> set[str]:
        """Get all supported file extensions."""
        return set(self.LANGUAGE_EXTENSIONS.keys())

    def get_supported_filenames(self) -> set[str]:
        """Get all supported special filenames."""
        return set(self.SPECIAL_FILENAMES.keys())

    def get_file_category(self, file_path: Path) -> str | None:
        """Get the broader category for a file type.

        Args:
            file_path: Path to the file

        Returns:
            Category string or None if unknown
        """
        file_type = self.get_file_type(file_path)

        # Map specific types to broader categories
        category_mapping = {
            # Programming languages
            "python": "programming",
            "javascript": "programming",
            "typescript": "programming",
            "java": "programming",
            "c": "programming",
            "cpp": "programming",
            "rust": "programming",
            "go": "programming",
            "ruby": "programming",
            "php": "programming",
            "swift": "programming",
            "kotlin": "programming",
            "scala": "programming",
            "csharp": "programming",
            "visualbasic": "programming",
            # Web technologies
            "html": "web",
            "css": "web",
            "xml": "web",
            # Data and config
            "json": "data",
            "yaml": "data",
            "toml": "data",
            "csv": "data",
            "sql": "data",
            "config": "configuration",
            "environment": "configuration",
            # Documentation
            "markdown": "documentation",
            "restructuredtext": "documentation",
            "text": "documentation",
            "documentation": "documentation",
            # Build systems
            "build": "build",
        }

        return category_mapping.get(file_type)
