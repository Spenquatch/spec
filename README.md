# spec

A versioned documentation layer for AI-assisted development. `spec` maintains a separate Git repository of contextual documentation that helps AI agents understand your codebase without polluting your main Git history.

## Why spec?

- **AI-Optimized Context**: Structured documentation designed for LLM consumption
- **Version-Controlled Memory**: AI agents can learn from past attempts and decisions
- **Isolated Git History**: Documentation changes don't clutter your main repository
- **Scoped Context Windows**: Load only relevant documentation to fit within token limits
- **Pluggable AI Integration**: Support for multiple AI providers (OpenAI, Anthropic, local models)
- **Concurrent Generation**: Fast documentation generation with configurable concurrency

## Installation

```bash
pip install spec-cli
```

## Quick Start

```bash
# Initialize spec in your project
spec init

# Generate documentation for files
spec gen src/models.py        # Single file
spec gen src/                 # Directory
spec gen .                    # Current directory (all files)

# Track documentation changes
spec add .
spec commit -m "Document authentication flow"

# View documentation status
spec status
spec log
spec diff
```

## Current Status

### ✅ Implemented Features
- **Project Initialization**: `spec init` creates isolated Git repository structure
- **Documentation Generation**: `spec gen` creates structured documentation with templates
- **Version Control**: Full Git workflow (`add`, `commit`, `status`, `log`, `diff`)
- **Template System**: Customizable documentation templates via `.spectemplate`
- **File Filtering**: Smart filtering with `.specignore` patterns
- **Conflict Resolution**: Interactive handling of existing documentation
- **Debug Mode**: Comprehensive debugging with `SPEC_DEBUG=1`
- **Batch Processing**: Generate documentation for entire directories
- **File Type Detection**: Support for 20+ programming languages and file types

### 🚧 In Development
- **AI Documentation Generation**: Replace placeholder content with AI-generated documentation
- **Git Hook Integration**: Auto-generate documentation on code changes
- **Terminal Styling**: Enhanced user experience with colors and formatting
- **Error Handling**: User-friendly error messages and validation

## How It Works

`spec` creates two directories:
- `.spec/` - A bare Git repository (like `.git`)
- `.specs/` - Working tree containing documentation

Your documentation mirrors your project structure:

```
project/
├── .spec/              # Bare Git repo for versioning
├── .specs/             # Documentation working tree
│   ├── src/
│   │   └── models/
│   │       ├── index.md
│   │       └── history.md
│   └── api/
│       └── users/
│           ├── index.md
│           └── history.md
├── .spectemplate       # Customizable templates
├── .specignore         # Ignore patterns
├── src/
│   └── models.py
└── api/
    └── users.py
```

Each source file gets a documentation directory with:
- `index.md`: Current understanding and specifications
- `history.md`: Evolution, decisions, and lessons learned

## Core Commands

### Documentation Management
- `spec init` - Initialize spec in current directory
- `spec gen <path>` - Generate documentation for file(s)
- `spec add <path>` - Stage documentation changes
- `spec commit -m "..."` - Commit documentation changes

### Version Control
- `spec status` - Show documentation status
- `spec log [path]` - Show documentation history
- `spec diff [path]` - Show uncommitted changes

### Future Commands
- `spec regen <path>` - Regenerate documentation (preserves history)
- `spec show <path>` - Display documentation for a file
- `spec agent-scope [options]` - Export scoped context for AI agents
- `spec hook install` - Install Git hooks for auto-generation

## Templates

Customize documentation format with `.spectemplate`:

```yaml
index:
  template: |
    # {{filename}}
    
    **Location**: {{filepath}}
    **Purpose**: {{purpose}}
    **Responsibilities**: {{responsibilities}}
    **Requirements**: {{requirements}}
    **Example Usage**: {{example_usage}}
    **Notes**: {{notes}}

history:
  template: |
    ## {{date}} - Initial Creation
    
    **Purpose**: Created initial specification for {{filename}}
    **Context**: {{context}}
    **Decisions**: {{decisions}}
    **Lessons Learned**: {{lessons}}
```

## Environment Variables

- `SPEC_DEBUG=1` - Enable debug output for troubleshooting
- `SPEC_DEBUG_LEVEL=INFO|DEBUG|WARNING|ERROR` - Set debug level
- `SPEC_DEBUG_TIMING=1` - Enable operation timing

## Future Enhancements

### AI Documentation Generation
**Status**: In Development

Automatic generation of documentation content using AI providers:

**Features**:
- **Pluggable Provider System**: Support for OpenAI, Anthropic, Hugging Face, local models
- **Concurrent Generation**: Process multiple files simultaneously (configurable 3-5 max)
- **Progress Display**: Real-time progress like pytest/pre-commit
- **Smart Content**: AI analyzes source code to generate meaningful documentation
- **Template Integration**: AI fills template variables based on code analysis

**Configuration**:
```yaml
# pyproject.toml [tool.spec] or .specconfig.yaml
ai:
  provider: "openai"      # openai, anthropic, huggingface, local
  model: "gpt-4"
  max_concurrency: 5
  temperature: 0.3
  max_tokens: 4000
```

**Usage**:
```bash
spec gen src/ --ai              # Generate with AI
spec regen src/models.py --ai   # Regenerate with AI
```

### Git Hook Integration
**Status**: Planned

Automatic documentation generation triggered by Git commits:

**Features**:
- **Hook Installation**: `spec hook install` sets up Git hooks
- **Change Detection**: Automatically detect modified files in commits
- **Selective Processing**: Only process changed files
- **Configurable Behavior**: Auto-commit or manual commit options
- **Error Handling**: Non-blocking failures with warnings

**Configuration**:
```yaml
hooks:
  auto_commit: false          # Manual commit by default
  on_error: "warn"           # warn, ignore, or block
  file_patterns: ["*.py", "*.js", "*.ts"]
  concurrent: true
```

**Usage**:
```bash
spec hook install              # Install hooks
spec hook uninstall            # Remove hooks
spec config hooks.auto_commit true
```

## Known Issues & Maintenance Items

### Bug Fixes Needed

1. **Git Command Messages**: 
   - **Issue**: `spec status` shows "git add ." in output instead of "spec add ."
   - **Fix**: Replace Git command suggestions with spec equivalents
   - **Priority**: Medium

2. **Uninitialized Directory Error**:
   - **Issue**: Running spec commands in non-initialized directories shows cryptic Git errors
   - **Error**: `fatal: not a git repository: '/path/.spec'`
   - **Fix**: Add validation to check for `.spec/` directory and show friendly error
   - **Priority**: High

3. **Emoji Usage**:
   - **Issue**: Emojis throughout codebase may not render properly on all terminals
   - **Fix**: Remove all emojis and replace with text indicators
   - **Priority**: Medium

### User Experience Improvements

1. **Terminal Styling**:
   - **Need**: Add colors and formatting for better readability
   - **Options**: Rich, Colorama, Click styling, or ANSI codes
   - **Features**: Colors for success/error/warning, progress bars, formatted output
   - **Priority**: Medium

2. **Error Messages**:
   - **Need**: User-friendly error messages with helpful suggestions
   - **Examples**: File not found, invalid templates, Git errors
   - **Priority**: High

3. **Progress Indicators**:
   - **Need**: Better progress display for long operations
   - **Features**: Progress bars, file counters, estimated time remaining
   - **Priority**: Low

## Development Setup

This project uses Poetry for dependency management and uv for virtual environments:

```bash
# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows

# Install dependencies with poetry
poetry install

# Run tests with coverage (80% minimum required)
poetry run pytest tests/unit/ -v --cov=spec_cli --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/

# Run linting and formatting
poetry run ruff check --fix .
poetry run ruff format .

# Run all pre-commit hooks
poetry run pre-commit run --all-files
```

## Use Cases

### For AI Development
- Provide rich context to AI coding assistants
- Track why certain approaches failed
- Maintain institutional knowledge across AI sessions
- Export scoped documentation for specific tasks

### For Teams
- Onboard new developers with comprehensive docs
- Document architectural decisions and trade-offs
- Track technical debt and future improvements
- Maintain living documentation that evolves with code

### For Code Review
- Understand the "why" behind implementations
- Review documentation changes alongside code
- Ensure specs stay synchronized with reality
- Track decision history and lessons learned

## IDE Integration

The `.spec/` and `.specs/` directories are designed to be hidden in IDEs like VSCode. Add to your workspace settings:

```json
{
  "files.exclude": {
    ".spec": true,
    ".specs": true
  }
}
```

## Contributing

We follow a vertical slice development philosophy - implementing features completely through implementation, testing, and typing before moving on. See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.