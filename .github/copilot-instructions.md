# prevent-dangling-todos Project Context for GitHub Copilot

You are working on `prevent-dangling-todos`, a Python pre-commit hook tool that enforces ticket references in TODO/FIXME comments from any issue tracking system (Jira, GitHub Issues, Linear, Asana, etc.).

## Project Overview

This tool prevents developers from committing work comments (TODO, FIXME, XXX, HACK) that don't reference a ticket from your issue tracker. It's designed to maintain code quality by ensuring all work items are properly tracked.

## Key Features

- **Universal issue tracker support**: Works with Jira, GitHub, Linear, and any tracker using `PREFIX-NUMBER` format
- **Multiple comment types**: Checks TODO, FIXME, XXX, HACK (customizable)
- **Branch-aware**: Automatically tracks TODOs for the current branch's ticket
- **Fast**: Uses `grep` for efficient batch processing
- **Flexible output**: Standard, quiet, or verbose modes
- **Configurable**: Extensive filtering via `.pre-commit-config.yaml`
- **Line-by-line exclusions**: Use `# noqa` comments to skip specific lines
- **Warning mode**: Check unstaged files without blocking commits

## Repository Structure

```
prevent_dangling_todos/
   prevent_dangling_todos/
      __init__.py
      cli.py              # Command-line interface and argument parsing
      prevent_todos.py    # Core TodoChecker class and logic
   tests/
      conftest.py         # Test fixtures and configuration
      test_cli.py         # CLI functionality tests
      test_prevent_todos.py # Core logic tests
      test_data/          # Test files with various TODO patterns
   pyproject.toml          # Python project configuration
   requirements.txt        # Runtime dependencies
   requirements-dev.txt    # Development dependencies
   README.md               # Comprehensive usage documentation
   LICENSE                 # BSD-3 license
```

## Core Components

### TodoChecker Class (`prevent_todos.py`)
The main logic class with these key methods:
- `__init__()`: Initialize with ticket_prefixes, comment_prefixes, quiet, verbose, succeed_always
- `check_file()`: Scan single file for violations, returns list of (line_num, content) tuples
- `check_files()`: Process multiple files, handles output formatting and exit codes
- `_build_patterns()`: Compiles regex patterns for comment and ticket matching

### CLI Interface (`cli.py`)
- Argument parsing with comprehensive help text and examples
- Environment variable support with CLI override precedence
- Error handling for missing ticket prefixes
- Validation for mutually exclusive `--quiet` and `--verbose` options

## Development Standards

### Package Management
- **UV**: Fast, modern Python package manager
- Install dependencies: `uv pip install -r requirements-dev.txt`
- Install package in development mode: `uv pip install -e .`

### Code Style
- Type hints on all function parameters and returns
- Comprehensive docstrings in NumPy format
- Error handling with informative messages
- Regex patterns are compiled once and reused

### Testing
- **Test Framework**: pytest with extensive coverage
- **Test Structure**: Separate test files for CLI and core logic
- **Test Data**: Real example files in `tests/test_data/`
- **Coverage Areas**: Pattern matching, file processing, CLI parsing, environment variables

### Dependencies
- **Runtime**: identify (>=2.0.0), pyyaml (>=6.0)
- **Development**: pytest, pytest-cov, ruff (linting), mypy (type checking), pre-commit, types-pyyaml

## Development Commands

### Setup
```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements-dev.txt
uv pip install -e .

# Install pre-commit hooks
pre-commit install
pre-commit install-hooks
```

### Testing
```bash
# Run full test suite
pytest

# Run with coverage
pytest --cov=prevent_dangling_todos --cov-report=xml --cov-report=term-missing

# Run linting
ruff check .

# Run type checking
mypy prevent_dangling_todos/

# Run all checks (as in CI)
pytest --cov=prevent_dangling_todos && ruff check . && mypy prevent_dangling_todos/
```

### Usage Examples

#### Basic Usage
```bash
prevent-dangling-todos -t MYPROJECT file.py
```

#### Multiple Ticket Prefixes
```bash
prevent-dangling-todos -t MYPROJECT,GITHUB,LINEAR *.py
```

#### Environment Variables
```bash
TICKET_PREFIX=MYPROJECT,GITHUB prevent-dangling-todos file.py
```

#### Verbose Output
```bash
prevent-dangling-todos -t MYPROJECT --verbose file.py
```

## Valid vs Invalid Comments

### ✅ Valid (Will Pass)
```python
# TODO MYPROJECT-123: Implement user authentication
# FIXME GITHUB-456: Handle edge case for empty input
/* HACK LINEAR-789: Temporary workaround for API issue */
// XXX JIRA-100: This needs refactoring

# TODO: This is excluded  # noqa
```

### ❌ Invalid (Will Fail)
```python
# TODO: Missing ticket reference
# FIXME: Another comment without ticket
# XXX Refactor this code
```

## Important Implementation Notes

- **Case Insensitive**: Both comment prefixes and ticket references are case-insensitive
- **Regex Escaping**: Ticket prefixes are properly escaped in regex patterns
- **File Exclusions**: `.pre-commit-config.yaml` files are excluded by default
- **Exit Codes**: 0 = success, 1 = violations found, 2 = configuration errors
- **Succeed Always**: Internal tracking still records violations even when returning 0

## Recent Changes

- Migrated from Poetry to UV for faster dependency management
- Added universal issue tracker support (not just Jira)
- Added line-by-line exclusions with `# noqa` comments
- Added unstaged file checking with `--check-unstaged` flag
- Added branch-specific TODO tracking
- Enhanced verbose mode with configuration and file status display

When working on this project, focus on maintaining the clean architecture, comprehensive testing, and user-friendly CLI experience that makes this tool effective for development teams.
