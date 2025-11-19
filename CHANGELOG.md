# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.0

### Breaking Changes

- **Renamed CLI arguments and environment variables for generic issue tracker support**
  - CLI: `-j/--jira-prefix` → `-t/--ticket-prefix` (old arguments still work with deprecation warnings)
  - Environment: `JIRA_PREFIX` → `TICKET_PREFIX` (old variable still works with deprecation warnings)
  - **Migration**: Simply replace `-j` with `-t` in your `.pre-commit-config.yaml`. Old arguments continue to work for now.

- **Ticket prefix is now optional, with changed behavior when not provided**
  - In version 0.x, failing to provide a ticket prefix caused an error (exit code 2)
  - In version 1.0, when no ticket prefix is provided, ALL work comments (TODO, FIXME, etc.) are treated as violations, regardless of any references they may contain

- **Minimum Python version increased to 3.10**
  - Python 3.9 is no longer supported

### Added

- **Line-by-line exclusions** via `# noqa` comments
  - Follow Flake8's FIX001-FIX004 exclusion patterns, which match the default work items (TODO, FIXME, XXX, HACK)
  - Use `# noqa`, `# noqa: FIX001`, or any FIX code to exclude specific lines entirely (the number is ignored)

- **Check unstaged files** with `-u/--check-unstaged` flag
  - Checks all repository files for violations (as warnings)
  - Unstaged file violations shown with yellow ⚠️ warnings (non-blocking commits)
  - Staged file violations shown with red ❌ errors (blocking commits)
  - Uses `grep` for efficient batch processing of large codebases

- **Pre-commit config file filtering** for all files (staged and unstaged)
  - Respects `.pre-commit-config.yaml` filtering configuration
  - Supports `files`, `exclude`, `types`, `types_or`, `exclude_types` filters
  - Applies to both staged and unstaged file checking

- **Branch-specific TODO tracking**
  - Automatically detects ticket IDs in branch names
  - Shows TODOs matching the current branch ticket as informational warnings (⚠️) instead of violations (❌)
  - Example: Branch `feature/PROJ-123-new-feature` shows `TODO PROJ-123` as yellow warnings

- **Multiple ticket prefix support**
  - Use comma-separated values for multiple issue trackers
  - Example: `-t JIRA,GITHUB,LINEAR`

### Changed

- **Changed default comment prefixes**
  - Default values now visible in `--help` output
  - Defaults: `TODO`, `FIXME`, `XXX`, `HACK`
  - Matches flake8-fixme plugin (FIX001-FIX004)

- **Moved to UV for python project management**
  - Switched from Poetry to uv
  - Includes updates to devcontainer configuration
  - No impacts to users

### Removed

- NA

### Fixed

- **Git operations with no staged files no longer fail**
  - Previously the CLI would fail if no files were passed
  - With the addition of unstaged file checking and making the files arguments optional, this bug is fixed

### Documentation

- Comprehensive README update with new terminology
- Added migration guide for users upgrading from 0.x
- Added examples for multiple issue trackers (Jira, GitHub, Linear)
- Improved configuration examples
- Enhanced troubleshooting section



*Earlier versions not documented in this changelog. See git history for details.*
