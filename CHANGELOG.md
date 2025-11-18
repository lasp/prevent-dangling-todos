# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - Unreleased

### Breaking Changes

- **Renamed CLI arguments and environment variables for generic issue tracker support**
  - CLI: `-j/--jira-prefix` → `-t/--ticket-prefix` (old arguments still work with deprecation warnings)
  - Environment: `JIRA_PREFIX` → `TICKET_PREFIX` (old variable still works with deprecation warnings)
  - Python API: `TodoChecker(jira_prefixes=...)` → `TodoChecker(ticket_prefixes=...)`
  - This change makes the tool generic for any issue tracker (Jira, GitHub Issues, Linear, Asana, etc.)
  - **Migration**: Simply replace `-j` with `-t` in your `.pre-commit-config.yaml`. Old arguments continue to work.

- **Ticket prefix is now optional, with changed behavior when not provided**
  - In version 0.x, failing to provide a ticket prefix caused an error (exit code 2)
  - In version 1.0, when no ticket prefix is provided, ALL work comments (TODO, FIXME, etc.) are treated as violations, regardless of any references they may contain
  - This allows users to completely disallow work comments if desired
  - A warning message is displayed when no ticket prefix is specified to inform users of this behavior

- **Minimum Python version increased to 3.10**
  - Python 3.9 is no longer supported
  - This change allows usage of modern Python syntax features like PEP 604 union types

### Added

- **Line-by-line exclusions** via `# noqa` comments ([#ffc479c](https://github.com/lasp/prevent-dangling-todos/commit/ffc479c))
  - Follow Flake8's FIX001-FIX004 exclusion patterns
  - Use `# noqa`, `# noqa: FIX001`, or any FIX code to exclude specific lines
  - Allows bypassing the check for generated code or intentional technical debt documentation

- **Check unstaged files** with `-u/--check-unstaged` flag ([#2909f40](https://github.com/lasp/prevent-dangling-todos/commit/2909f40))
  - Checks all repository files for violations (as warnings)
  - Unstaged file violations shown with yellow ⚠️ warnings (non-blocking)
  - Staged file violations shown with red ❌ errors (blocking)
  - Uses `grep` for efficient batch processing of large codebases

- **Pre-commit config file filtering** ([#9821c44](https://github.com/lasp/prevent-dangling-todos/commit/9821c44))
  - Respects `.pre-commit-config.yaml` filtering configuration
  - Supports `files`, `exclude`, `types`, `types_or`, `exclude_types` filters
  - Applies to both staged and unstaged file checking
  - Uses `identify` library for file type detection

- **Branch-specific TODO tracking**
  - Automatically detects ticket IDs in branch names
  - Shows TODOs matching the current branch ticket as informational warnings (⚠️) instead of violations (❌)
  - Example: Branch `feature/PROJ-123-new-feature` shows `TODO PROJ-123` as yellow warnings

- **Multiple ticket prefix support**
  - Use comma-separated values for multiple issue trackers
  - Example: `-t JIRA,GITHUB,LINEAR`

- **Verbose mode enhancements**
  - Shows configuration at startup
  - Displays file-by-file status (✅ clean, ❌ violations)
  - Provides helpful examples when violations are found
  - Shows branch detection information

### Changed

- **Removed hard-coded file filtering** ([#85424be](https://github.com/lasp/prevent-dangling-todos/commit/85424be))
  - File filtering now exclusively uses `.pre-commit-config.yaml` configuration
  - Provides better flexibility and consistency with pre-commit behavior

- **Moved default comment prefixes to CLI** ([#85424be](https://github.com/lasp/prevent-dangling-todos/commit/85424be))
  - Default values now visible in `--help` output
  - Defaults: `TODO`, `FIXME`, `XXX`, `HACK`
  - Matches flake8-fixme plugin (FIX001-FIX004)

- **Updated all terminology** from "Jira" to "ticket/issue tracker"
  - Makes the tool's purpose clearer for non-Jira users
  - Documentation includes examples for Jira, GitHub Issues, Linear, etc.

- **Improved error messages and help text**
  - More descriptive deprecation warnings
  - Better configuration examples
  - Clearer troubleshooting guidance

### Removed

- **Removed import guards** for `yaml` and `identify` libraries ([#85424be](https://github.com/lasp/prevent-dangling-todos/commit/85424be))
  - These are explicit dependencies, no need for optional imports
  - Simplifies code and reduces unnecessary complexity

### Fixed

- Various test improvements and bug fixes
- Improved test coverage (94 tests passing)

### Documentation

- Comprehensive README update with new terminology
- Added migration guide for users upgrading from 0.x
- Added examples for multiple issue trackers (Jira, GitHub, Linear)
- Improved configuration examples
- Enhanced troubleshooting section

## [0.4.0] - 2024

Earlier versions not documented in this changelog. See git history for details.
