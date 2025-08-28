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

### Custom Comment Types

Check only specific comment types:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA', '-c', 'TODO,FIXME']
```

### Quiet Mode for CI

Suppress decorative output in CI environments:

```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA', '-q']
```

### Alert Without Blocking

Alert developers to dangling TODOs without blocking commits. When using `--succeed-always`, the hook will always return exit code 0 (success), but by default pre-commit hides output from successful hooks. To ensure TODO violations are still visible, you should configure verbose output:

**Recommended: Always show output (persistent configuration)**
```yaml
repos:
  - repo: https://github.com/lasp/prevent-dangling-todos
    hooks:
      - id: prevent-dangling-todos
        args: ['-j', 'MYJIRA', '--succeed-always']
        verbose: true  # Always show output, even when hook succeeds
```

**Alternative: Show output only when needed (runtime flag)**
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
- `-q, --quiet`: Suppress decorative output
- `--succeed-always`: Always exit with code 0, even when TODOs are found
- `--version`: Show version information

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

4. **False positives**
   - Use `-c/--comment-prefix` to check only specific comment types
   - Consider using `-q/--quiet` mode in automated environments

### Getting Help

Run with `--help` to see all available options:

```bash
prevent-dangling-todos --help
```