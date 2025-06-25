# Changelog

All notable changes to spec-cli will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Additional enterprise features and integrations (in development)
- Enhanced semantic search capabilities
- Performance optimizations for large codebases

## [0.1.63] - 2025-06-24

### Added
- **Core CLI Commands**: Complete Git workflow (`init`, `add`, `commit`, `status`, `log`, `diff`)
- **AI Documentation Generation**: Local AI models (Qwen3-Emb-0.6B) for intelligent content creation
- **Semantic Search**: 95% complete local AI search capabilities with JSON storage
- **Rich Terminal UI**: Beautiful interface with progress indicators, colors, and styling
- **Cross-Platform Support**: Robust Windows, macOS, and Linux compatibility
- **Template System**: Customizable documentation templates via `.spectemplate`
- **File Filtering**: Smart filtering with `.specignore` patterns
- **Batch Processing**: Generate documentation for entire directories efficiently
- **File Type Detection**: Support for 20+ programming languages and file types
- **Interactive Conflict Resolution**: Handle existing documentation gracefully
- **Debug Mode**: Comprehensive logging with `SPEC_DEBUG=1`
- **Enterprise Architecture**: Modular design with 2,426 tests and 85%+ coverage
- **Type Safety**: MyPy strict mode with 100% type coverage
- **Quality Automation**: Pre-commit hooks, automated formatting, and linting

### Changed
- **Architecture Refactoring**: Eliminated 121+ lines of duplicate code through systematic refactoring
- **Error Handling**: Structured error context with clear, actionable messages
- **Performance Optimization**: Optimized for large codebases and batch operations
- **Documentation Generation**: Enhanced with AI-powered content creation
- **Path Handling**: Robust cross-platform path normalization and validation

### Fixed
- **Cross-Platform Paths**: Fixed path separator issues across Windows/macOS/Linux
- **Git Isolation**: Resolved custom work tree configuration problems
- **Test Compatibility**: Fixed mock patching issues across Python versions
- **Memory Management**: Optimized memory usage for large file processing
- **Unicode Handling**: Improved handling of non-ASCII file names and content

### Security
- **Input Validation**: Comprehensive sanitization of file paths and user input
- **Secure Defaults**: Security-conscious default configuration
- **No Secret Logging**: Prevents accidental logging of sensitive information
- **Local Processing**: AI features work locally by default, no external API calls

## [0.1.5] - 2025-06-02

### Added
- **Initial Tagged Release**: First tagged version of spec-cli
- **Core Git Operations**: Complete workflow (`init`, `add`, `commit`, `status`, `log`, `diff`)
- **Basic AI Documentation**: Template-based documentation generation
- **Cross-Platform Support**: Windows, macOS, and Linux compatibility
- **Rich CLI Interface**: Terminal UI with basic styling and progress indicators

### Fixed
- Cross-platform path handling issues
- Git isolation with custom work tree configuration
- Basic error handling and user feedback

## [0.1.0] - 2025-05-30

### Added
- **Foundation Release**: Core spec-cli infrastructure
- **Git Integration**: Isolated Git repository management
- **Template System**: Basic documentation templates
- **File Operations**: Safe file handling and path validation
- **CLI Framework**: Command-line interface foundation

---

## Release Notes Format

Each release includes:
- **Added**: New features and capabilities
- **Changed**: Changes to existing functionality
- **Deprecated**: Features marked for removal in future versions
- **Removed**: Features removed in this version
- **Fixed**: Bug fixes and issue resolutions
- **Security**: Security improvements and vulnerability fixes

## Contributing to Changelog

When contributing to spec-cli:
1. Add your changes to the [Unreleased] section
2. Use the appropriate category (Added, Changed, Fixed, etc.)
3. Include issue references where applicable: `- Fixed memory leak in batch processing (#123)`
4. Keep entries concise but descriptive
5. Follow the established format and tone

## Version History

Detailed version history and release artifacts are available on the [GitHub Releases](https://github.com/yourusername/spec-cli/releases) page.
