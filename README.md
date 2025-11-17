# prevent-dangling-todos

A pre-commit hook that prevents TODO, FIXME, and other work comments without ticket references from any issue tracking system.

This tool helps maintain code quality by ensuring all work comments are properly linked to issues in your project tracker (Jira, GitHub Issues, Linear, Asana, etc.).

## Features

- ✅ **Universal issue tracker support**: Works with Jira, GitHub, Linear, and any tracker using `PREFIX-NUMBER` format
- 🔍 **Multiple comment types**: Checks TODO, FIXME, XXX, HACK (customizable)
- 🎯 **Branch-aware**: Automatically tracks TODOs for the current branch's ticket
- ⚡ **Fast**: Uses `grep` for efficient batch processing
- 🎨 **Flexible output**: Standard, quiet, or verbose modes
- 🔧 **Configurable**: Extensive filtering via `.pre-commit-config.yaml`
- 📝 **Line-by-line exclusions**: Use `# noqa` comments to skip specific lines
- ⚠️  **Warning mode**: Check unstaged files without blocking commits

## Quick Start

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    rev: v1.0.0  # Use the latest release
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'MYPROJECT']  # Replace with your ticket prefix
```

That's it! Now commits will be blocked if they contain TODOs without `MYPROJECT-123` style references.

## Installation

### As a pre-commit hook (recommended)

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    rev: v1.0.0
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'MYPROJECT']
```

### Standalone installation

```bash
pip install git+https://github.com/lasp/prevent-dangling-todos.git
```

## Usage Examples

### Basic Usage

```yaml
# For Jira
args: ['-t', 'JIRA']

# For GitHub Issues
args: ['-t', 'GITHUB']

# For Linear
args: ['-t', 'LINEAR']

# Multiple trackers
args: ['-t', 'JIRA,GITHUB,LINEAR']
```

### Recommended: Maximum Visibility

Get violations AND branch-specific TODOs, check all files:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'MYPROJECT', '-v', '--check-unstaged']
        verbose: true      # Always show output
```

**This configuration:**
- Shows violations in staged files (❌ blocking errors)
- Shows TODOs in unstaged files (⚠️ warnings only)
- Tracks branch-specific TODOs (⚠️ informational)
- Always displays output even on success

### Non-Blocking Alerts

Alert about violations without blocking commits:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'MYPROJECT', '--succeed-always', '-v']
        verbose: true
```

Perfect for:
- Gradual migration to enforced TODO references
- Large codebases with existing TODOs
- Raising awareness without strict enforcement

## Configuration Options

### Command-Line Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--ticket-prefix` | `-t` | Ticket prefix(es) from your issue tracker (comma-separated) |
| `--comment-prefix` | `-c` | Comment types to check (default: `TODO,FIXME,XXX,HACK`) |
| `--check-unstaged` | `-u` | Also check unstaged files (as warnings) |
| `--verbose` | `-v` | Show configuration, file status, and help text |
| `--quiet` | `-q` | Silent mode - no output, only exit codes |
| `--succeed-always` | | Always exit 0, even with violations |
| `--version` | | Show version information |

**Deprecated (but still working):**
- `-j/--jira-prefix` → Use `-t/--ticket-prefix` instead
- `JIRA_PREFIX` env var → Use `TICKET_PREFIX` instead

### Environment Variables

Set in your shell instead of using command-line arguments:

```bash
export TICKET_PREFIX=MYPROJECT,GITHUB
export COMMENT_PREFIX=TODO,FIXME
```

Command-line arguments take precedence over environment variables.

### Default Comment Types

By default, these comment types are checked:
- `TODO` - General tasks
- `FIXME` - Known issues needing fixes
- `XXX` - Warning/attention markers
- `HACK` - Temporary workarounds

Customize with `-c` or `--comment-prefix`.

## Advanced Features

### Line-by-Line Exclusions

Exclude specific TODO comments using `# noqa`:

```python
# TODO: This will fail - no ticket reference

# TODO: This is excluded  # noqa
# FIXME: Also excluded  # noqa: FIX002
# XXX: Excluded with any FIX code  # noqa: FIX001,FIX003
```

The tool follows Flake8's FIX001-FIX004 exclusion patterns, allowing you to:
- Exclude generated code
- Document intentional technical debt
- Skip specific TODO comments that don't need tracking

### Checking Unstaged Files

By default, only staged files are checked. Use `--check-unstaged` to check all repository files:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'MYPROJECT', '--check-unstaged']
```

**Behavior:**
- **Staged file violations** → ❌ Block commit (red errors)
- **Unstaged file violations** → ⚠️ Warning only (yellow warnings)
- Unstaged violations don't affect exit code
- Uses `grep` for efficient batch processing

**Use cases:**
- Get visibility into ALL TODOs in your codebase
- Track technical debt across the entire repository
- Monitor TODO status without blocking development

### File Filtering

The tool respects your `.pre-commit-config.yaml` filtering configuration:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'MYPROJECT']

        # Regex pattern for files to include
        files: '^src/.*\.py$'

        # Regex pattern for files to exclude
        exclude: '^(tests/|docs/)'

        # File types (uses `identify` library)
        types: [python]                     # Only Python files
        types_or: [python, javascript]      # Python OR JavaScript
        exclude_types: [markdown, json]     # Exclude markdown and JSON
```

**Available filters:**
- `files`: Regex pattern - only check matching files
- `exclude`: Regex pattern - exclude matching files
- `types`: All specified types must match
- `types_or`: At least one specified type must match
- `exclude_types`: Exclude all specified types

These filters apply to **both** staged and unstaged file checking when using `--check-unstaged`.

File types are detected using the [`identify`](https://github.com/pre-commit/identify) library.

### Branch-Specific TODO Tracking

The tool automatically detects your current git branch and extracts ticket IDs matching your configured prefixes. TODOs referencing the current branch's ticket are shown as informational warnings (⚠️) instead of violations (❌).

**Example:**
- Branch: `feature/PROJ-123-new-feature`
- Detected ticket: `PROJ-123`
- `TODO PROJ-123: Complete implementation` → ⚠️ Warning (not a violation)
- `TODO PROJ-456: Different ticket` → Valid (different ticket)
- `TODO: No reference` → ❌ Violation

**Configuration:**
```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'PROJ', '-v']
```

**Note:** Branch detection messages are shown in verbose mode.

## Output Modes

### Standard Mode (Default)

Shows only violations with red ❌ marks, no success messages:

```
❌ file.py:15: # TODO: Missing ticket reference
❌ file.py:23: # FIXME: Another violation
```

### Quiet Mode (`-q/--quiet`)

Completely silent - no output, only exit codes:

```yaml
args: ['-t', 'MYPROJECT', '-q']
```

Perfect for:
- CI/CD pipelines
- Automated checks where output isn't needed
- Integration with other tools

### Verbose Mode (`-v/--verbose`)

Shows configuration, violations, file status, and help text:

```
🔍 Checking work comments for ticket references to projects MYPROJECT...
Checking for: TODO, FIXME, XXX, HACK

❌ file.py:15: # TODO: Missing ticket reference

⚠️  Unresolved TODOs for current branch ticket MYPROJECT-123:
⚠️  auth.py:10: # TODO MYPROJECT-123: Complete OAuth implementation

✅ clean_file.py
❌ file.py

💡 Please add ticket/issue references to work comments like:
   // TODO MYPROJECT-123: Implement user authentication
   # FIXME MYPROJECT-124: Handle edge case for empty input
```

## Valid vs Invalid Comments

### ✅ Valid Comments

```python
# TODO MYPROJECT-123: Implement user authentication
# FIXME GITHUB-456: Handle edge case for empty input
/* HACK LINEAR-789: Temporary workaround for API issue */
// XXX JIRA-100: This needs refactoring

# TODO: This is excluded  # noqa
```

### ❌ Invalid Comments (Will Cause Failure)

```python
# TODO: Missing ticket reference
# FIXME: Another comment without ticket
# XXX Refactor this code
```

## Migration from 0.x to 1.0

### Breaking Changes

**1. Command-line arguments:**
```yaml
# Before (0.x)
args: ['-j', 'MYPROJECT']

# After (1.0)
args: ['-t', 'MYPROJECT']  # Recommended

# Still works (with deprecation warning)
args: ['-j', 'MYPROJECT']  # Will show warning
```

**2. Environment variables:**
```bash
# Before (0.x)
export JIRA_PREFIX=MYPROJECT

# After (1.0)
export TICKET_PREFIX=MYPROJECT  # Recommended

# Still works (with deprecation warning)
export JIRA_PREFIX=MYPROJECT  # Will show warning
```

**3. Python API (if using programmatically):**
```python
# Before (0.x)
from prevent_dangling_todos.prevent_todos import TodoChecker
checker = TodoChecker(jira_prefixes=['PROJ'])

# After (1.0)
from prevent_dangling_todos.prevent_todos import TodoChecker
checker = TodoChecker(ticket_prefixes=['PROJ'])
```

### Migration Steps

1. **Update `.pre-commit-config.yaml`:**
   - Replace `-j` with `-t`
   - No other changes needed

2. **Update environment variables (if used):**
   - Replace `JIRA_PREFIX` with `TICKET_PREFIX`

3. **No immediate action required:**
   - Old arguments continue to work
   - Deprecation warnings will guide you
   - Plan to migrate before version 2.0

## Troubleshooting

### Common Issues

**1. "No ticket prefix specified" message**
- Ensure you provide `-t/--ticket-prefix` argument or `TICKET_PREFIX` environment variable
- If intentional (to disallow ALL TODOs), this is expected behavior

**2. Violations not showing when using `--succeed-always`**
- By default, pre-commit hides output from successful hooks
- **Solution**: Add `verbose: true` to your hook configuration

**3. Comments not being detected**
- Check format: `# TODO PROJ-123: Description`
- Ensure ticket prefix matches your configuration
- Verify comment type is in your `--comment-prefix` list

**4. Branch-specific TODOs not appearing**
- Use `verbose: true` in your config to see branch detection
- Check that branch name contains a valid ticket ID (e.g., `feature/PROJ-123-description`)
- Ensure branch detection isn't failing (check verbose output)

**5. Unstaged files not being checked**
- Add `--check-unstaged` / `-u` flag to your args
- Ensure you don't have conflicting `files` or `exclude` patterns

**6. File filtering not working as expected**
- Check your `.pre-commit-config.yaml` filters (`files`, `exclude`, `types`, etc.)
- Use `--verbose` to see which files are being checked
- Remember: filters apply to both staged and unstaged files

**7. False positives in generated code**
- Use `# noqa` comments to exclude specific lines
- Add file/directory exclusions in `.pre-commit-config.yaml`
- Adjust `--comment-prefix` to check only specific comment types

**8. Want to see all TODOs across codebase**
- Use `--check-unstaged` flag
- Add `verbose: true` to see detailed output
- Consider `--succeed-always` to avoid blocking while gaining visibility

### Getting Help

```bash
# Show all available options
prevent-dangling-todos --help

# Check version
prevent-dangling-todos --version
```

For issues or feature requests, please visit: https://github.com/lasp/prevent-dangling-todos/issues

## Examples by Use Case

### For GitHub Issues

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'GITHUB']
```

### For Linear

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'LINEAR']
```

### For Multiple Projects

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'FRONTEND,BACKEND,INFRA']
```

### Python Files Only

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'MYPROJECT']
        types: [python]
```

### Excluding Tests and Docs

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'MYPROJECT']
        exclude: '^(tests/|docs/|examples/)'
```

### Check Only TODOs (Ignore FIXME, XXX, etc.)

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'MYPROJECT', '-c', 'TODO']
```

### Monitor All TODOs Without Blocking

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-t', 'MYPROJECT', '--succeed-always', '--check-unstaged', '-v']
        verbose: true
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

BSD-3 License - See LICENSE file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed release notes.
