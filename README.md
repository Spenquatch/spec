# spec

A versioned documentation layer for AI-assisted development. `spec` maintains a separate Git repository of contextual documentation that helps AI agents understand your codebase without polluting your main Git history.

## Why spec?

- **AI-Optimized Context**: Structured documentation designed for LLM consumption
- **Version-Controlled Memory**: AI agents can learn from past attempts and decisions
- **Isolated Git History**: Documentation changes don't clutter your main repository
- **Scoped Context Windows**: Load only relevant documentation to fit within token limits

## Installation

```bash
pip install spec-cli
```

## Quick Start

```bash
# Initialize spec in your project
spec init

# Generate documentation for new files
spec gen src/models.py
spec gen .  # Generate for all untracked files

# Track documentation changes
spec add .
spec commit -m "Document authentication flow"

# View documentation
spec show src/models.py
spec status
```

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
- `spec regen <path>` - Regenerate documentation (preserves history)
- `spec show <path>` - Display documentation for a file

### Version Control
- `spec add <path>` - Stage documentation changes
- `spec commit -m "..."` - Commit documentation changes
- `spec status` - Show documentation status
- `spec log [path]` - Show documentation history
- `spec diff [path]` - Show uncommitted changes

### AI Agent Integration
- `spec agent-scope [options]` - Export scoped context for AI agents
  - `--dir <path>` - Scope to directory
  - `--depth <n>` - Include n levels of context
  - `--limit <tokens>` - Maximum token count

## Templates

Customize documentation format with `.spectemplate`:

```yaml
index:
  template: |
    # {{filename}}
    
    **Location**: {{filepath}}
    **Purpose**: {{ai:purpose}}
    **Responsibilities**: {{ai:responsibilities}}
    **Requirements**: {{ai:requirements}}
    **Example Usage**: {{ai:example}}
    **Notes**: {{ai:notes}}

history:
  template: |
    ## {{date}} - {{ai:summary}}
    
    **Changes**: {{ai:changes}}
    **Reason**: {{ai:reason}}
```

## Environment Variables

- `SPEC_DEBUG=1` - Enable debug output for troubleshooting

## Automation (Coming Soon)

```bash
# Watch for changes
spec watch              # Auto-generate for new files
spec watch --regen     # Also regenerate on changes

# Git hooks
spec hook install      # Auto-generate on git commit
spec config auto-gen on
```

## Use Cases

### For AI Development
- Provide rich context to AI coding assistants
- Track why certain approaches failed
- Maintain institutional knowledge across AI sessions

### For Teams
- Onboard new developers with comprehensive docs
- Document architectural decisions
- Track technical debt and TODOs

### For Code Review
- Understand the "why" behind implementations
- Review documentation changes alongside code
- Ensure specs stay synchronized

## Configuration

```bash
spec config set ai.provider openai
spec config set ai.model gpt-4
spec config set auto-gen.enabled true
spec config set auto-gen.paths "src/,lib/"
```

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

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.