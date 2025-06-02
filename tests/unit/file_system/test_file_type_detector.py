from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from spec_cli.file_system.file_type_detector import FileTypeDetector


class TestFileTypeDetector:
    """Test suite for FileTypeDetector class."""

    @pytest.fixture
    def detector(self) -> FileTypeDetector:
        """Create a FileTypeDetector instance for testing."""
        return FileTypeDetector()

    def test_file_type_detector_identifies_programming_languages(
        self, detector: FileTypeDetector
    ) -> None:
        """Test detection of programming language file types."""
        test_cases = [
            (Path("test.py"), "python"),
            (Path("script.pyx"), "python"),
            (Path("types.pyi"), "python"),
            (Path("app.js"), "javascript"),
            (Path("component.jsx"), "javascript"),
            (Path("main.ts"), "typescript"),
            (Path("component.tsx"), "typescript"),
            (Path("App.java"), "java"),
            (Path("main.c"), "c"),
            (Path("header.h"), "c"),
            (Path("main.cpp"), "cpp"),
            (Path("header.hpp"), "cpp"),
            (Path("main.rs"), "rust"),
            (Path("main.go"), "go"),
            (Path("script.rb"), "ruby"),
            (Path("index.php"), "php"),
            (Path("App.swift"), "swift"),
            (Path("Main.kt"), "kotlin"),
            (Path("App.scala"), "scala"),
            (Path("Program.cs"), "csharp"),
            (Path("Module.vb"), "visualbasic"),
        ]

        for file_path, expected_type in test_cases:
            assert detector.get_file_type(file_path) == expected_type

    def test_file_type_detector_identifies_web_technologies(
        self, detector: FileTypeDetector
    ) -> None:
        """Test detection of web technology file types."""
        test_cases = [
            (Path("index.html"), "html"),
            (Path("page.htm"), "html"),
            (Path("styles.css"), "css"),
            (Path("styles.scss"), "css"),
            (Path("styles.sass"), "css"),
            (Path("styles.less"), "css"),
            (Path("config.xml"), "xml"),
            (Path("transform.xsl"), "xml"),
            (Path("schema.xsd"), "xml"),
        ]

        for file_path, expected_type in test_cases:
            assert detector.get_file_type(file_path) == expected_type

    def test_file_type_detector_identifies_data_formats(
        self, detector: FileTypeDetector
    ) -> None:
        """Test detection of data format file types."""
        test_cases = [
            (Path("config.json"), "json"),
            (Path("config.yaml"), "yaml"),
            (Path("config.yml"), "yaml"),
            (Path("pyproject.toml"), "toml"),
            (Path("data.csv"), "csv"),
            (Path("query.sql"), "sql"),
        ]

        for file_path, expected_type in test_cases:
            assert detector.get_file_type(file_path) == expected_type

    def test_file_type_detector_identifies_special_filenames(
        self, detector: FileTypeDetector
    ) -> None:
        """Test detection based on special filenames."""
        test_cases = [
            (Path("Makefile"), "build"),
            (Path("makefile"), "build"),
            (Path("Dockerfile"), "build"),
            (Path("dockerfile"), "build"),
            (Path("Vagrantfile"), "build"),
            (Path("vagrantfile"), "build"),
            (Path("Rakefile"), "build"),
            (Path("rakefile"), "build"),
            (Path(".env"), "environment"),
            (Path(".gitignore"), "config"),
            (Path(".specignore"), "config"),
            (Path("README.md"), "documentation"),
            (Path("readme.md"), "documentation"),
            (Path("CHANGELOG.md"), "documentation"),
            (Path("changelog.md"), "documentation"),
        ]

        for file_path, expected_type in test_cases:
            assert detector.get_file_type(file_path) == expected_type

    def test_file_type_detector_handles_case_insensitive_extensions(
        self, detector: FileTypeDetector
    ) -> None:
        """Test that extensions are handled case-insensitively."""
        test_cases = [
            (Path("TEST.PY"), "python"),
            (Path("APP.JS"), "javascript"),
            (Path("MAIN.CPP"), "cpp"),
            (Path("CONFIG.JSON"), "json"),
            (Path("STYLES.CSS"), "css"),
        ]

        for file_path, expected_type in test_cases:
            assert detector.get_file_type(file_path) == expected_type

    def test_file_type_detector_handles_files_without_extensions(
        self, detector: FileTypeDetector
    ) -> None:
        """Test handling of files without extensions."""
        test_cases = [
            Path("script"),
            Path("binary"),
            Path("noextension"),
        ]

        for file_path in test_cases:
            assert detector.get_file_type(file_path) == "no_extension"

    def test_is_binary_file_identifies_executables_and_libraries(
        self, detector: FileTypeDetector
    ) -> None:
        """Test binary detection for executables and libraries."""
        binary_files = [
            Path("app.exe"),
            Path("library.dll"),
            Path("lib.so"),
            Path("framework.dylib"),
            Path("archive.a"),
            Path("library.lib"),
        ]

        for file_path in binary_files:
            assert detector.is_binary_file(file_path) is True

    def test_is_binary_file_identifies_images_and_media(
        self, detector: FileTypeDetector
    ) -> None:
        """Test binary detection for images and media files."""
        binary_files = [
            Path("image.jpg"),
            Path("photo.jpeg"),
            Path("icon.png"),
            Path("animation.gif"),
            Path("bitmap.bmp"),
            Path("vector.svg"),
            Path("favicon.ico"),
            Path("image.webp"),
            Path("song.mp3"),
            Path("video.mp4"),
            Path("movie.avi"),
            Path("film.mkv"),
            Path("clip.mov"),
            Path("audio.wav"),
            Path("music.flac"),
        ]

        for file_path in binary_files:
            assert detector.is_binary_file(file_path) is True

    def test_is_binary_file_returns_false_for_text_files(
        self, detector: FileTypeDetector
    ) -> None:
        """Test that text files are not identified as binary."""
        text_files = [
            Path("script.py"),
            Path("config.json"),
            Path("styles.css"),
            Path("README.md"),
            Path("data.csv"),
            Path("Makefile"),
        ]

        for file_path in text_files:
            assert detector.is_binary_file(file_path) is False

    def test_is_processable_file_rejects_binary_files(
        self, detector: FileTypeDetector
    ) -> None:
        """Test that binary files are rejected for processing."""
        binary_files = [
            Path("app.exe"),
            Path("image.jpg"),
            Path("archive.zip"),
            Path("video.mp4"),
        ]

        for file_path in binary_files:
            assert detector.is_processable_file(file_path) is False

    def test_is_processable_file_rejects_unknown_types(
        self, detector: FileTypeDetector
    ) -> None:
        """Test that unknown file types are rejected for processing."""
        unknown_files = [
            Path("file.unknown"),
            Path("data.xyz"),
            Path("test.weird"),
        ]

        for file_path in unknown_files:
            assert detector.is_processable_file(file_path) is False

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_is_processable_file_rejects_oversized_files(
        self, mock_stat: Any, mock_exists: Any, detector: FileTypeDetector
    ) -> None:
        """Test that oversized files are rejected for processing."""
        # Mock a file that exists and is larger than MAX_FILE_SIZE
        mock_exists.return_value = True
        mock_stat_result = Mock()
        mock_stat_result.st_size = detector.MAX_FILE_SIZE + 1
        mock_stat.return_value = mock_stat_result

        large_file = Path("large_script.py")
        assert detector.is_processable_file(large_file) is False

    def test_get_supported_extensions(self, detector: FileTypeDetector) -> None:
        """Test getting supported extensions."""
        extensions = detector.get_supported_extensions()

        # Check that it returns a set
        assert isinstance(extensions, set)

        # Check that it contains expected extensions
        expected_extensions = {".py", ".js", ".cpp", ".json", ".html", ".md"}
        assert expected_extensions.issubset(extensions)

    def test_get_supported_filenames(self, detector: FileTypeDetector) -> None:
        """Test getting supported special filenames."""
        filenames = detector.get_supported_filenames()

        # Check that it returns a set
        assert isinstance(filenames, set)

        # Check that it contains expected filenames
        expected_filenames = {"makefile", "dockerfile", ".env", ".gitignore"}
        assert expected_filenames.issubset(filenames)

    def test_get_file_category(self, detector: FileTypeDetector) -> None:
        """Test getting file categories."""
        test_cases = [
            (Path("script.py"), "programming"),
            (Path("app.js"), "programming"),
            (Path("styles.css"), "web"),
            (Path("index.html"), "web"),
            (Path("config.json"), "data"),
            (Path("settings.yaml"), "data"),
            (Path("app.conf"), "configuration"),
            (Path(".env"), "configuration"),
            (Path("README.md"), "documentation"),
            (Path("notes.txt"), "documentation"),
            (Path("Makefile"), "build"),
            (Path("unknown.xyz"), None),
        ]

        for file_path, expected_category in test_cases:
            assert detector.get_file_category(file_path) == expected_category
