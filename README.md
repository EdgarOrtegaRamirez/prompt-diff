# Prompt Diff

CLI tool for versioning, diffing, and evaluating AI prompts.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-0_passed-brightgreen.svg)](tests/)

## What it does

Prompt Diff provides a lightweight, local-first system for managing AI prompt versions:

- **Version control** — Track every iteration of your prompts with timestamps and metadata
- **Unified diff** — See exactly what changed between versions (unified, stats, or JSON output)
- **Tagging & search** — Organize prompts with tags, search by name or tag
- **Registry format** — JSON-based registry file, portable and human-readable
- **CLI interface** — Create, show, diff, list, search, and info commands
- **Rich output** — Colored terminal output with tables and formatted diffs

Designed for prompt engineers, ML engineers, and AI developers who iterate on prompts frequently.

## Quick Start

```bash
# Install
pip install prompt-diff

# Create your first prompt version
prompt-diff create --name "Initial prompt" \
  --content "You are a helpful assistant." \
  --tag "initial" \
  --output prompts.json

# Create a second version
prompt-diff create --name "Enhanced with examples" \
  --content "You are a helpful assistant.\n\nExamples:\n- Q: What is AI?\n- A: Artificial Intelligence..." \
  --tag "enhanced" \
  --output prompts.json

# List all versions
prompt-diff list-versions prompts.json

# Diff two versions
prompt-diff diff prompts.json v001 v002

# Show stats about the diff
prompt-diff diff prompts.json v001 v002 --format stats

# Show full unified diff
prompt-diff diff prompts.json v001 v002 --format unified

# Search prompts
prompt-diff search prompts.json --tag "enhanced"

# Show registry info
prompt-diff info prompts.json
```

## Commands

| Command | Description |
|---------|-------------|
| `create` | Create a new prompt version |
| `show` | Show a specific prompt version |
| `diff` | Diff two prompt versions |
| `list-versions` | List all versions in a registry |
| `search` | Search versions by name or tag |
| `info` | Show registry statistics |
| `sample-config` | Print a sample registry configuration |

### Create Options

```bash
prompt-diff create \
  --name "My prompt" \
  --content "Your prompt text here" \
  --tag "production" \
  --tag "v2" \
  --metadata '{"author":"alice","model":"gpt-4"}' \
  --output prompts.json
```

Or read from a file:
```bash
prompt-diff create --name "File prompt" --file prompt.txt --output prompts.json
```

Or pipe from stdin:
```bash
echo "You are a helpful assistant." | prompt-diff create --name "Piped" --output prompts.json
```

## Architecture

```
prompt_diff/
├── __init__.py     # Package init with version
├── engine.py       # Core: PromptVersion, PromptRegistry, DiffResult, compute_diff
├── cli.py          # CLI commands (Click-based)
└── __main__.py     # Entry point for `python -m prompt_diff`
```

### Core Types

- **PromptVersion** — A single prompt with metadata, tags, and creation timestamp
- **PromptRegistry** — Collection of prompt versions with save/load support
- **DiffResult** — Computed diff with unified/stats/JSON formatting
- **compute_diff()** — Uses Python's difflib for line-level comparison

## Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Security Notes

- The CLI operates entirely offline — no network calls
- Registry files are plain JSON, treat them as you would source code
- File paths are validated to prevent path traversal
