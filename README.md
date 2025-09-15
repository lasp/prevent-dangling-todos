# prevent-dangling-todos

A pre-commit hook that prevents TODO, FIXME, and other work comments that don't reference a Jira ticket.

This tool helps maintain code quality by ensuring all work comments (TODO, FIXME, XXX, HACK, BUG, REVIEW, OPTIMIZE, REFACTOR) are properly linked to tracking issues.

## Usage

### Basic Usage

Add to your `.pre-commit-config.yaml` file:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA']
```

### Multiple Jira Prefixes

Use comma-separated values for multiple prefixes:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA,PROJECT,TEAM']
```

### Recommended Configurations

#### For Maximum TODO Visibility (Recommended)
Get both violations AND branch-specific TODOs, check all files:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA', '-v']
        always_run: true  # Check all files for branch-specific TODOs
        verbose: true     # Always show output
```

#### For Non-Blocking Alerts with Branch Tracking
Alert about TODOs without blocking commits:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA', '--succeed-always', '-v']
        always_run: true  # Check all files for branch-specific TODOs
        verbose: true     # Always show output even when hook succeeds
```

### Custom Comment Types

Check only specific comment types:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA', '-c', 'TODO,FIXME']
```

### Output Modes

The tool supports three output modes:

**Standard Mode (default)**: Shows only violations with red X marks, no success messages
```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA']
```

**Quiet Mode**: Completely silent - no output, only exit codes
```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA', '-q']
```

**Verbose Mode**: Shows configuration, violations, file status summary, help text, and branch-specific TODOs
```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA', '-v']
```

### Branch-Specific TODO Tracking

The tool automatically detects your current git branch and extracts ticket IDs that match your configured Jira prefixes. When TODOs reference the current branch's ticket, they are displayed separately as informational warnings (yellow ⚠️) rather than violations (red ❌).

#### Checking All Files (Including Untouched)

By default, pre-commit only runs on modified files. To catch branch-specific TODOs in files that haven't been changed, configure the hook to **always run**:

#### Complete Branch Tracking Configuration

For full branch-specific TODO tracking, use both verbose and always_run:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA', '-v']
        always_run: true
        verbose: true  # Ensure output is always shown
```

**Example branch detection:**
- Branch: `feature/MYJIRA-123-user-auth`
- Detected ticket: `MYJIRA-123`
- TODOs with `MYJIRA-123` will be shown as warnings, not violations

**Note:** Branch detection messages are only shown in verbose mode or when there are issues detecting the branch.

### Alert Without Blocking

Alert developers to dangling TODOs without blocking commits. When using `--succeed-always`, the hook will always return exit code 0 (success), but by default pre-commit hides output from successful hooks. To ensure TODO violations are still visible, you should configure verbose output:

**Recommended: Always show output with branch tracking**
```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA', '--succeed-always', '-v']
        always_run: true  # Check all files for branch-specific TODOs
        verbose: true  # Always show output, even when hook succeeds
```

**Alternative: Basic alert without branch tracking**
```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA', '--succeed-always']
        verbose: true  # Always show output, even when hook succeeds
```

**Runtime flag approach (minimal configuration)**
```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA', '--succeed-always']
```
Then run with: `pre-commit run --verbose` or `git commit` (if you want to see violations occasionally)

**When to use `--succeed-always`:**
- You want to raise awareness about TODOs without blocking commits
- You're implementing a gradual migration to enforced TODO references
- You have a large codebase with existing TODOs and want visibility before enforcing

**When to use normal mode (without `--succeed-always`):**
- You want to strictly enforce TODO references (blocks commits until fixed)
- You have a clean codebase or are starting fresh
- You want to prevent any new dangling TODOs from being committed

## Configuration Options

### Command Line Arguments

- `-j, --jira-prefix PREFIXES`: Jira project prefixes (comma-separated)
- `-c, --comment-prefix PREFIXES`: Comment types to check (comma-separated)
- `-q, --quiet`: Silent mode - no output, just exit codes
- `-v, --verbose`: Verbose mode - show configuration, violations, file status, and help text
- `--succeed-always`: Always exit with code 0, even when TODOs are found
- `--version`: Show version information

**Note**: `--quiet` and `--verbose` are mutually exclusive options.

### File Exclusions

By default, `.pre-commit-config.yaml` files are excluded from checking since they typically contain configuration comments that don't need Jira references.

To override this behavior or add additional exclusions:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA']
        exclude: '^(\.pre-commit-config\.yaml|docs/.*\.md)$'  # Custom exclusions
```

### Environment Variables

You can set `JIRA_PREFIX` and `COMMENT_PREFIX` environment variables in your shell instead of using CLI arguments. Command line arguments take precedence over environment variables.

### Default Comment Types

By default, the following comment types are checked:
TODO, FIXME, XXX, HACK, BUG, REVIEW, OPTIMIZE, REFACTOR

## Examples

### Valid Comments

```python
# TODO MYJIRA-123: Implement user authentication
# FIXME PROJECT-456: Handle edge case for empty input
/* HACK TEAM-789: Temporary workaround for API issue */
```

### Invalid Comments (Will Cause Failure)

```python
# TODO: Missing Jira reference
# FIXME: Another comment without ticket
```

### Output Examples

**Standard Mode** (violations only):
```
❌ file.py:15: # TODO: Missing Jira reference
❌ file.py:23: # FIXME: Another comment without ticket


⚠️  Unresolved TODOs for current branch ticket MYJIRA-123:
⚠️  auth.py:10: # TODO MYJIRA-123: Complete OAuth implementation
⚠️  auth.py:25: # FIXME MYJIRA-123: Handle token refresh edge case
```

**Quiet Mode**: No output (silent)

**Verbose Mode**:
```
🔍 Checking work comments for Jira references to projects MYJIRA... Checking for: TODO, FIXME, XXX, HACK, BUG, REVIEW, OPTIMIZE, REFACTOR

❌ file.py:15: # TODO: Missing Jira reference
❌ file.py:23: # FIXME: Another comment without ticket

⚠️  Unresolved TODOs for current branch ticket MYJIRA-123:
⚠️  auth.py:10: # TODO MYJIRA-123: Complete OAuth implementation
⚠️  auth.py:25: # FIXME MYJIRA-123: Handle token refresh edge case

✅ clean_file.py
❌ file.py

💡 Please add Jira issue references to work comments like:
   // TODO MYJIRA-123: Implement user authentication
   # FIXME MYJIRA-124: Handle edge case for empty input

Note: No ticket ID detected in current branch 'main'
```

## Troubleshooting

### Common Issues

1. **"Jira project prefix(es) must be specified"**
   - Ensure you provide either `-j/--jira-prefix` argument or `JIRA_PREFIX` environment variable

2. **TODO violations not showing when using `--succeed-always`**
   - By default, pre-commit hides output from successful hooks
   - **Solution**: Add `verbose: true` to your hook configuration, or use `pre-commit run --verbose`
   - See the "Alert Without Blocking" section for examples

3. **Comments not being detected**
   - Check that your comment format matches: `# TODO JIRA-123: Description`
   - Ensure the Jira prefix matches your configuration

4. **Branch-specific TODOs not appearing**
   - **Solution**: Use `verbose: true` in your config
   - Use `always_run: true` to check all files, not just modified ones
   - Ensure your branch name contains a valid ticket ID (e.g., `feature/MYJIRA-123-description`)

5. **Branch detection not working**
   - Ensure you're in a git repository with a valid branch
   - Check that your branch name includes a ticket ID matching your Jira prefixes
   - Branch detection messages appear in verbose mode or when there are detection issues

6. **False positives**
   - Use `-c/--comment-prefix` to check only specific comment types
   - Consider using `-q/--quiet` mode for silent operation in CI/CD pipelines
   - Use `-v/--verbose` mode when you need detailed information about what files are being checked

### Getting Help

Run with `--help` to see all available options:

```bash
prevent-dangling-todos --help
```