# GitHub Copilot Instructions for prevent-dangling-todos

## Project Overview

**prevent-dangling-todos** is a Python pre-commit hook that enforces ticket/issue references from any tracking system (Jira, GitHub Issues, Linear, Asana, etc.) in TODO/FIXME comments. It ensures all work items in code are properly tracked.

**Supported Platforms**: macOS and Linux only (Windows unsupported - no `grep` available)

## Architecture

### Core Components

1. **`cli.py`** - Command-line interface
   - Argument parsing with deprecated arg migration (-j → -t)
   - Environment variable support (TICKET_PREFIX, COMMENT_PREFIX)
   - Branch detection and ticket ID extraction
   - Configuration validation

2. **`prevent_todos.py`** - TodoChecker class
   - Line-by-line file scanning for staged files
   - Grep-based batch processing for unstaged files
   - Regex pattern matching with noqa exclusion support
   - File filtering based on .pre-commit-config.yaml

3. **Test Suite** (94 tests)
   - `test_cli.py` - CLI argument parsing and branch detection (35 tests)
   - `test_prevent_todos.py` - Core logic and edge cases (52 tests)
   - `test_end_to_end.py` - Integration tests (7 tests)

## Key Features to Remember

### Universal Issue Tracker Support
- Works with ANY tracker using PREFIX-NUMBER format (not just Jira)
- Use terminology: "ticket" or "issue" (not "Jira ticket")
- Multiple prefixes supported: `-t JIRA,GITHUB,LINEAR`

### Branch-Aware TODO Tracking
- Extracts ticket IDs from branch names automatically
- Example: `feature/PROJ-123-description` → detects `PROJ-123`
- TODOs for current branch ticket show as warnings (⚠️), not violations (❌)

### File Checking Modes
- **Default**: Only check staged files (passed as arguments)
- **With `--check-unstaged`**: Check entire repository
  - Staged files: violations (❌) - blocks commit
  - Unstaged files: warnings (⚠️) - informational only
  - Uses `grep` for performance

### Line-Level Exclusions
Supports `# noqa` comments (flake8-fixme FIX001-FIX004 pattern):
```python
# TODO: This fails without noqa
# TODO: This is excluded  # noqa
# FIXME: Also excluded  # noqa: FIX001
```

### Output Modes
- **Standard**: Show violations only
- **Quiet** (`-q`): Silent, exit codes only
- **Verbose** (`-v`): Config, violations, file status, help text

## Code Style Requirements

### Type Hints (Required)
```python
def function_name(param: str, optional: Optional[int] = None) -> List[str]:
    """Docstring in NumPy format."""
    pass
```

### Docstrings (NumPy Format)
```python
def check_file(self, filepath: str) -> List[Tuple[int, str]]:
    """
    Check a single file for work comments without ticket references.

    Parameters
    ----------
    filepath : str
        Path to the file to check

    Returns
    -------
    list of tuple
        List of (line_number, line_content) for violations found
    """
```

### Error Handling
Always provide informative error messages for users:
```python
if not ticket_prefixes:
    print("Error: No ticket prefix specified.", file=sys.stderr)
    sys.exit(2)
```

## Testing Guidelines

### Running Tests
```bash
pytest -v                                    # All tests
pytest tests/test_cli.py -v                  # Specific file
pytest tests/test_cli.py::TestCLI::test_name # Specific test
pytest --cov=prevent_dangling_todos          # With coverage
```

### Test Structure
- Use fixtures from `conftest.py`
- Mock subprocess calls for git operations
- Use `test_data/` files for realistic test scenarios
- Test both success and failure cases
- Test edge cases (empty files, special characters, etc.)

### Adding Tests
1. Write failing test first (TDD approach)
2. Implement feature
3. Verify test passes
4. Add additional edge case tests
5. Maintain >90% coverage

## Linting and Type Checking

### Before Committing
```bash
ruff check . --fix     # Auto-fix linting issues
ruff format .          # Format code
mypy prevent_dangling_todos  # Type checking
pytest -v              # Run all tests
```

### Pre-commit Hook
The repo uses its own tool plus standard hooks:
- prevent-dangling-todos (self-dogfooding!)
- trailing-whitespace, end-of-file-fixer
- ruff (linting + formatting)
- mypy (type checking)

## Common Tasks

### Adding CLI Argument
1. Add to `create_parser()` in `cli.py`
2. Handle in `main()` function
3. Pass to TodoChecker if needed
4. Add tests in `test_cli.py`
5. Update help text and examples
6. Update README.md

### Adding Feature
1. Implement in TodoChecker class (`prevent_todos.py`)
2. Add comprehensive unit tests
3. Add CLI support if user-facing
4. Add end-to-end test
5. Update README with examples
6. Update CHANGELOG.md

### Fixing Bug
1. Add failing test demonstrating bug
2. Fix the bug
3. Verify test passes
4. Add regression tests
5. Update CHANGELOG.md

## Important Implementation Details

### Regex Pattern Building
```python
# Patterns are built once at initialization for performance
def _build_patterns(self) -> None:
    # Escape all user inputs to prevent injection
    escaped_prefixes = [re.escape(p) for p in self.comment_prefixes]
    comment_regex = "|".join(escaped_prefixes)
    self.comment_pattern = re.compile(
        rf'^\s*[#/*\s]*\s*({comment_regex})\b',
        re.IGNORECASE
    )
```

### Security Considerations
- Use `grep -F` (fixed strings) to prevent command injection
- Escape all regex special characters with `re.escape()`
- Validate user inputs
- Set timeouts on subprocess calls

### Performance Optimizations
- Compile regex patterns once at initialization
- Use `grep` for batch processing (much faster than Python for large repos)
- Use generators where possible
- Read files efficiently with context managers

### Exit Codes
- `0` - Success (or `--succeed-always` mode)
- `1` - Violations found
- `2` - Configuration errors

## Terminology to Use Consistently

✅ **Use:**
- Ticket / Issue (not "Jira ticket")
- Ticket prefix (not "Jira prefix")
- Issue tracker / Project tracker (not "Jira")
- Work comments (for TODO, FIXME, etc.)
- Staged files (passed to hook)
- Unstaged files (all other tracked files)
- Violations (red ❌)
- Warnings (yellow ⚠️)
- Branch-specific TODOs

❌ **Avoid:**
- "Jira ticket" (too specific)
- "Jira prefix" (outdated terminology)
- "Comments" alone (be specific: "work comments")

## Dependencies

### Runtime (Minimal)
- Python 3.10+
- `identify>=2.0.0` - File type detection  
- `pyyaml>=6.0` - Config parsing

### Development
- pytest, pytest-cov - Testing
- ruff - Linting and formatting
- mypy - Type checking
- pre-commit - Git hooks

### External Tools Required
- `grep` - For batch processing (NOT available on Windows)
- `git` - For repository operations

## Examples for Code Completion

### Valid TODO Comments
```python
# TODO PROJ-123: Implement feature
# FIXME GITHUB-456: Handle edge case
# XXX LINEAR-789: Needs refactoring
# HACK JIRA-100: Temporary workaround
# TODO: Excluded comment  # noqa
```

### Invalid TODO Comments (Will Fail)
```python
# TODO: No ticket reference
# FIXME: Another violation
# XXX: Needs work
```

### CLI Usage Patterns
```bash
# Basic usage
prevent-dangling-todos -t MYPROJECT file.py

# Multiple prefixes
prevent-dangling-todos -t JIRA,GITHUB,LINEAR *.py

# Check entire repo
prevent-dangling-todos -t PROJ --check-unstaged

# Verbose output
prevent-dangling-todos -t PROJ -v file.py

# Non-blocking mode
prevent-dangling-todos -t PROJ --succeed-always file.py

# Custom comment types
prevent-dangling-todos -t PROJ -c TODO,FIXME file.py
```

### Pre-commit Configuration
```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    rev: v1.0.0
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'MYPROJECT']
        # Optional file filtering
        files: '^src/.*\.py$'
        exclude: '^tests/'
        types: [python]
```

## CI/CD Pipeline

### Test Matrix
- **OS**: Ubuntu, macOS (Windows excluded - no grep)
- **Python**: 3.11, 3.12, 3.13
- **Steps**: Install deps → Run tests with coverage → Lint → Type check → Codecov

### Local CI Simulation
```bash
# Run full CI checks locally
pytest --cov=prevent_dangling_todos --cov-report=term-missing
ruff check .
mypy prevent_dangling_todos
```

## Migration Notes (v0.x → v1.0)

### Deprecated (Still Working)
- `-j/--jira-prefix` → Use `-t/--ticket-prefix`
- `JIRA_PREFIX` env var → Use `TICKET_PREFIX`
- Python API: `jira_prefixes` param → `ticket_prefixes`

### Breaking Changes
- Default comment prefixes: 8 types → 4 types (TODO, FIXME, XXX, HACK)
- `.pre-commit-config.yaml` now excluded by default

## Debugging Tips

### Enable Verbose Mode
```bash
prevent-dangling-todos -t PREFIX -v file.py
```
Shows: configuration, files checked, violations, warnings, help text

### Test Specific Scenarios
```bash
# Test with specific files
prevent-dangling-todos -t PROJ tests/test_data/todos_invalid.py

# Test branch detection
git rev-parse --abbrev-ref HEAD
prevent-dangling-todos -t PROJ -v file.py  # Shows branch info

# Test grep functionality
prevent-dangling-todos -t PROJ --check-unstaged -v
```

## Version Information

**Current Version**: 1.0.0 (defined in `cli.py` and `pyproject.toml`)

When suggesting code changes, always:
1. Maintain backward compatibility where possible
2. Add deprecation warnings before removing features
3. Update version in both locations
4. Document breaking changes in CHANGELOG.md
5. Update README.md with new features/changes

## Quick Reference

| Task | Command |
|------|---------|
| Run tests | `pytest -v` |
| Run with coverage | `pytest --cov=prevent_dangling_todos` |
| Lint code | `ruff check . --fix` |
| Format code | `ruff format .` |
| Type check | `mypy prevent_dangling_todos` |
| Install dev deps | `uv pip install -e ".[dev]"` |
| Run tool locally | `prevent-dangling-todos -t PREFIX file.py` |

---

**Remember**: This tool helps teams across ALL issue trackers, not just Jira. Always use inclusive terminology and maintain universal compatibility. Test thoroughly on both macOS and Linux. Keep documentation in sync with code changes.
