# AGENTS.md — Prompt Diff

## For AI Agents

### Project Overview
Prompt Diff is a Python CLI tool for versioning, diffing, and evaluating AI prompts.
It uses a JSON-based registry to track prompt iterations with metadata and tags.

### Quick Commands
```bash
# Create a prompt version
prompt-diff create --name "test" --content "prompt text" --output prompts.json

# List versions
prompt-diff list-versions prompts.json

# Diff versions
prompt-diff diff prompts.json v001 v002 --format stats

# Search
prompt-diff search prompts.json --tag "production"
```

### Architecture
- `engine.py` — Core data models (PromptVersion, PromptRegistry, DiffResult) and diff computation
- `cli.py` — Click-based CLI with 7 commands (create, show, diff, list-versions, search, info, sample-config)
- `__main__.py` — Module entry point

### Key Classes
- `PromptVersion` — Single prompt with id, name, content, metadata, tags, timestamp
- `PromptRegistry` — Collection of versions with save/load, search by tag, get latest
- `DiffResult` — Diff output with unified/stats/JSON formatting
- `compute_diff()` — Line-level diff using difflib.SequenceMatcher

### Testing
```bash
pytest tests/ -v
```
Two test files: `test_engine.py` (unit tests for engine) and `test_cli.py` (integration tests for CLI).

### Adding Features
1. New engine logic → add to `engine.py`, add tests to `test_engine.py`
2. New CLI command → add to `cli.py`, add integration test to `test_cli.py`
3. Always update README.md for new commands
