# prevent-dangling-todos Project Context for Claude

You are working on `prevent-dangling-todos`, a Python pre-commit hook tool that enforces ticket references from **any** issue tracking system (Jira, GitHub Issues, Linear, Asana, etc.) in TODO/FIXME comments.

## Project Overview

This tool prevents developers from committing work comments (TODO, FIXME, XXX, HACK) that don't reference a ticket from their issue tracking system. It's designed to maintain code quality by ensuring all work items are properly tracked across any project management platform.

**Important**: Windows platforms are not currently supported due to the lack of `grep`. Mac and Linux work fine.

## Key Features

- **Universal Issue Tracker Support**: Works with any tracker using PREFIX-NUMBER format (Jira, GitHub, Linear, etc.)
- **Comment Detection**: Scans for 4 types of work comments by default (TODO, FIXME, XXX, HACK)
- **Multiple Prefixes**: Supports multiple ticket prefixes (comma-separated: e.g., JIRA,GITHUB,LINEAR)
- **Branch-Aware**: Automatically detects ticket IDs in branch names and tracks branch-specific TODOs
- **Unstaged File Checking**: Can check entire repository with `--check-unstaged` flag (warnings only for unstaged)
- **Grep-Based Processing**: Uses `grep` for efficient batch processing of unstaged files
- **Line-Level Exclusions**: Supports `# noqa` comments to exclude specific lines (follows flake8-fixme FIX001-FIX004 pattern)
- **Flexible Modes**: Standard blocking mode or `--succeed-always` for alerts without blocking
- **Output Modes**: Three distinct modes - standard (violations only), quiet (silent), and verbose (detailed)
- **File Filtering**: Respects `.pre-commit-config.yaml` filters (files, exclude, types, exclude_types)
- **Environment Variables**: Supports `TICKET_PREFIX` and `COMMENT_PREFIX` env vars (deprecated: `JIRA_PREFIX`)

## Repository Structure

```
prevent_dangling_todos/
   prevent_dangling_todos/
      __init__.py
      cli.py              # Command-line interface and argument parsing
      prevent_todos.py    # Core TodoChecker class with grep integration
   tests/
      conftest.py         # Test fixtures and configuration
      test_cli.py         # CLI functionality tests (35 tests)
      test_prevent_todos.py # Core logic tests (52 tests)
      test_end_to_end.py  # End-to-end integration tests (7 tests)
      test_data/          # Test files with various TODO patterns
   .devcontainer/
      CLAUDE.md           # Claude AI instructions (this file)
      Dockerfile          # Development container configuration
      devcontainer.json   # VS Code dev container settings
   .github/
      workflows/          # CI/CD workflows
         ci.yml           # Test matrix: Ubuntu/macOS, Python 3.11/3.12/3.13
         release.yml      # Release automation
      copilot-instructions.md  # GitHub Copilot instructions
   pyproject.toml          # Python project configuration (PEP 621 standard)
   .pre-commit-config.yaml # Pre-commit hook configuration for this repo
   .pre-commit-hooks.yaml  # Hook definition for consumers
   README.md               # Comprehensive usage documentation (506 lines)
   CHANGELOG.md            # Detailed release notes
   LICENSE                 # BSD-3 license
```

## Core Components

### TodoChecker Class (`prevent_todos.py`)

The main logic class with these key responsibilities:

**Initialization** (`__init__`):
- Takes ticket_prefixes (can be empty list to disallow ALL work comments)
- Takes comment_prefixes (default: TODO, FIXME, XXX, HACK)
- Configures modes: quiet, verbose, succeed_always, check_unstaged
- Accepts current_ticket_id for branch-aware tracking
- Builds regex patterns once for efficiency

**Core Methods**:
- `check_file(filepath)`: Scans single file for violations, returns list of (line_num, content) tuples
- `check_files(files)`: Main entry point - processes files, handles output, returns exit code
- `_build_patterns()`: Compiles regex patterns for comment and ticket matching
- `_find_todos_with_grep()`: Uses grep for efficient batch processing of unstaged files
- `_get_all_repo_files()`: Gets all tracked files from git
- `_parse_precommit_config()`: Reads .pre-commit-config.yaml for file filtering
- `_filter_files()`: Applies files/exclude/types/exclude_types filters
- `_has_noqa()`: Checks if line has `# noqa` exclusion comment

**Exit Codes**:
- 0 = success (or succeed_always mode)
- 1 = violations found
- 2 = configuration errors

### CLI Interface (`cli.py`)

**Argument Parsing**:
- `-t/--ticket-prefix`: Ticket prefixes (replaces deprecated `-j/--jira-prefix`)
- `-c/--comment-prefix`: Comment types to check
- `-q/--quiet`: Silent mode
- `-v/--verbose`: Detailed output
- `-u/--check-unstaged`: Check all repo files (not just staged)
- `--succeed-always`: Never fail (exit 0)
- `--version`: Show version (currently 1.0.0)

**Environment Variables** (lower precedence than CLI):
- `TICKET_PREFIX` (replaces deprecated `JIRA_PREFIX`)
- `COMMENT_PREFIX`

**Branch Detection**:
- `_get_current_git_branch()`: Gets current branch name
- `_extract_ticket_id()`: Extracts ticket ID from branch name (e.g., feature/PROJ-123-description → PROJ-123)
- Passes current_ticket_id to TodoChecker for special handling

## Development Standards

### Code Style
- **Type Hints**: All function parameters and returns must have type hints
- **Docstrings**: NumPy format for all public functions and classes
- **Error Handling**: Informative messages for users
- **Performance**: Regex patterns compiled once and reused
- **Security**: Fixed-string matching (grep -F) to prevent command injection

### Testing (94 tests total, all passing)

**Test Framework**: pytest with extensive coverage
- `test_cli.py`: CLI parsing, environment variables, branch detection, flags
- `test_prevent_todos.py`: Core logic, pattern matching, file processing, grep integration, noqa exclusions
- `test_end_to_end.py`: Integration tests for branch-aware TODOs

**Test Data**: Real example files in `tests/test_data/` with various TODO patterns

**Running Tests**:
```bash
# Full test suite
pytest -v

# With coverage
pytest --cov=prevent_dangling_todos --cov-report=term-missing

# Specific test file
pytest tests/test_cli.py -v
```

### Dependencies

**Runtime** (minimal dependencies):
- Python 3.10+
- `identify>=2.0.0` - File type detection
- `pyyaml>=6.0` - Config parsing

**Development**:
- pytest, pytest-cov - Testing
- ruff - Linting and formatting
- mypy - Type checking
- pre-commit - Git hooks

**External Tools**:
- `grep` - Required for batch processing (not available on Windows)
- `git` - Required for repository operations

### Linting and Type Checking

```bash
# Run linting (auto-fix)
ruff check . --fix

# Run formatting
ruff format .

# Run type checking
mypy prevent_dangling_todos
```

## Usage Examples

### Basic Usage
```bash
# Single ticket prefix
prevent-dangling-todos -t MYPROJECT file.py

# Multiple ticket prefixes
prevent-dangling-todos -t JIRA,GITHUB,LINEAR *.py

# Environment variables
TICKET_PREFIX=MYPROJECT prevent-dangling-todos file.py
```

### Advanced Usage
```bash
# Check entire repository (staged + unstaged)
prevent-dangling-todos -t MYPROJECT --check-unstaged

# Verbose output with configuration details
prevent-dangling-todos -t MYPROJECT -v file.py

# Alert without blocking (always exit 0)
prevent-dangling-todos -t MYPROJECT --succeed-always file.py

# Custom comment types
prevent-dangling-todos -t MYPROJECT -c TODO,FIXME file.py

# No files argument = check all tracked files
prevent-dangling-todos -t MYPROJECT
```

### Pre-commit Hook Configuration
```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    rev: v1.0.0
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'MYPROJECT']
        
        # Optional: file filtering
        files: '^src/.*\.py$'
        exclude: '^(tests/|docs/)'
        types: [python]
        exclude_types: [markdown]
```

## Valid vs Invalid Comments

### ✅ Valid Comments (Will Pass)
```python
# TODO MYPROJECT-123: Implement user authentication
# FIXME GITHUB-456: Handle edge case for empty input
/* HACK LINEAR-789: Temporary workaround for API issue */
// XXX JIRA-100: This needs refactoring

# TODO: This is excluded  # noqa
# FIXME: Also excluded  # noqa: FIX001
```

### ❌ Invalid Comments (Will Fail)
```python
# TODO: Missing ticket reference
# FIXME: Another comment without ticket
# XXX Refactor this code
# HACK: Quick fix needed
```

## Important Implementation Notes

### Case Sensitivity
- Both comment prefixes and ticket references are **case-insensitive**
- Pattern matching uses `re.IGNORECASE` flag

### Regex Escaping
- Ticket prefixes are properly escaped with `re.escape()` in patterns
- Comment prefixes are also escaped for safety

### Branch Detection
- Extracts ticket IDs from branch names automatically
- TODOs matching current branch ticket are shown as warnings (⚠️), not violations (❌)
- Does not affect exit code
- Example: `feature/PROJ-123-description` → detects `PROJ-123`

### Noqa Exclusions
- Follows flake8-fixme pattern: `# noqa`, `# noqa: FIX001`, etc.
- Must be at end of line (whitespace after is OK)
- Case-insensitive
- Works with any FIX code (FIX001, FIX002, FIX003, FIX004)

### File Processing
- **Staged files** (passed as arguments): Checked line-by-line in Python
- **Unstaged files** (with `--check-unstaged`): Batch processed with `grep` for performance
- Respects `.pre-commit-config.yaml` filters for both staged and unstaged

### Security Considerations
- Uses `grep -F` (fixed strings) to prevent command injection
- Validates and escapes all user inputs in regex patterns
- No arbitrary command execution

## Recent Major Changes (v1.0.0)

### Terminology Changes
- `jira_prefix` → `ticket_prefix` (supports any issue tracker)
- `-j/--jira-prefix` → `-t/--ticket-prefix` (old still works with deprecation warning)
- `JIRA_PREFIX` → `TICKET_PREFIX` env var (old still works with deprecation warning)

### New Features
- Universal issue tracker support (was Jira-only)
- Branch-aware TODO tracking
- `--check-unstaged` flag for repository-wide checking
- Grep-based batch processing for performance
- `# noqa` exclusion support
- File filtering via `.pre-commit-config.yaml`
- `identify` library for file type detection
- No files argument = check all tracked files

### Breaking Changes from 0.x to 1.0
- Python API: `jira_prefixes` parameter → `ticket_prefixes`
- Default comment prefixes reduced from 8 to 4 (TODO, FIXME, XXX, HACK only)
- `.pre-commit-config.yaml` is now excluded by default

## Working with This Project as Claude

### When Making Changes

1. **Run tests frequently**: `pytest -v` after any code change
2. **Check types**: `mypy prevent_dangling_todos` before committing
3. **Lint code**: `ruff check . --fix` to auto-fix issues
4. **Update tests**: Add tests for new features or bug fixes
5. **Update README**: Keep documentation in sync with code changes
6. **Update CHANGELOG**: Document changes following Keep a Changelog format

### Common Tasks

**Adding a new command-line argument**:
1. Add to `create_parser()` in `cli.py`
2. Update `main()` to handle the argument
3. Pass to `TodoChecker` if needed
4. Add tests in `test_cli.py`
5. Update README with examples
6. Update help text and epilog examples

**Adding a new feature**:
1. Implement in `prevent_todos.py` (TodoChecker class)
2. Add comprehensive tests in `test_prevent_todos.py`
3. Add CLI support in `cli.py` if needed
4. Add end-to-end test in `test_end_to_end.py`
5. Update README with usage examples
6. Update CHANGELOG

**Fixing a bug**:
1. Add a failing test that demonstrates the bug
2. Fix the bug
3. Verify test now passes
4. Add regression test if needed
5. Update CHANGELOG

### Testing Strategies

**Unit Tests**: Test individual functions in isolation
- Mock subprocess calls for git operations
- Use test_data files for file processing
- Test edge cases and error handling

**Integration Tests**: Test end-to-end workflows
- Use real git operations where possible
- Test CLI argument combinations
- Test with various file types and patterns

**Coverage Goals**: Maintain high coverage (>90%)
- Focus on critical paths
- Test error conditions
- Test all CLI argument combinations

### Performance Considerations

- Grep is used for batch processing of unstaged files (much faster than Python)
- Regex patterns are compiled once at initialization
- File reading is done efficiently with context managers
- Subprocess calls have timeouts to prevent hangs

### Debugging Tips

**Enable verbose mode**: `prevent-dangling-todos -t PREFIX -v file.py`
- Shows configuration
- Shows which files are being checked
- Shows detailed violation information

**Run specific tests**: `pytest tests/test_cli.py::TestCLI::test_specific_test -v`

**Check git operations**: Test branch detection and file listing manually:
```bash
git rev-parse --abbrev-ref HEAD  # Get current branch
git ls-files  # List tracked files
```

## Terminology Reference

Use this terminology consistently:

- **Ticket** or **Issue** (not "Jira ticket")
- **Ticket prefix** (not "Jira prefix")
- **Issue tracker** or **Project tracker** (not "Jira")
- **Work comments** (for TODO, FIXME, etc.)
- **Staged files** (files passed to hook)
- **Unstaged files** (all other tracked files)
- **Violations** (red ❌) vs **Warnings** (yellow ⚠️)
- **Branch-specific TODOs** (TODOs for current branch ticket)

## CI/CD

**CI Workflow** (`.github/workflows/ci.yml`):
- Runs on: Ubuntu and macOS (Windows excluded)
- Python versions: 3.11, 3.12, 3.13
- Steps: Install deps, run tests with coverage, lint, type check
- Codecov integration for coverage reporting

**Release Workflow** (`.github/workflows/release.yml`):
- Triggered manually or on tags
- Builds and publishes to PyPI

When working on this project, always maintain the high code quality standards, comprehensive testing, and user-friendly experience that makes this tool valuable for development teams across different issue tracking platforms.
