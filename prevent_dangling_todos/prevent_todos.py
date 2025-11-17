#!/usr/bin/env python3
"""
Pre-commit hook to check that TODO, FIXME, and other work comments include Jira issue references.  # noqa: FIX001

Usage: python prevent_todos.py file1.py file2.js ...
"""

import sys
import re
import os
import subprocess
from typing import List, Optional, Tuple, Union, Dict, Any

try:
    import yaml
    from identify import identify

    HAS_YAML = True
    HAS_IDENTIFY = True
except ImportError:
    HAS_YAML = False
    HAS_IDENTIFY = False


class TodoChecker:
    """
    Check files for work comments that lack Jira issue references.

    This class provides functionality to scan source code files for TODO, FIXME,  # noqa: FIX001
    and other work comments, ensuring they include proper Jira issue references.

    Attributes
    ----------
    jira_prefixes : list of str
        List of valid Jira project prefixes
    comment_prefixes : list of str
        List of comment prefixes to check (e.g., TODO, FIXME)  # noqa: FIX001
    quiet : bool
        Whether to suppress all output (silent mode)
    verbose : bool
        Whether to show detailed output including config, violations, file status, and help
    succeed_always : bool
        Whether to always exit with code 0 even when violations are found
    check_unstaged : bool
        Whether to also check unstaged files (as warnings)
    exit_code : int
        Track exit code for violations (0 = success, 1 = violations found)
    comment_pattern : re.Pattern
        Compiled regex for matching work comments
    jira_pattern : re.Pattern
        Compiled regex for matching Jira references
    """

    def __init__(
        self,
        jira_prefixes: Union[str, List[str]],
        comment_prefixes: Optional[List[str]] = None,
        quiet: bool = False,
        verbose: bool = False,
        succeed_always: bool = False,
        current_ticket_id: Optional[str] = None,
        check_unstaged: bool = False,
    ):
        """
        Initialize the TodoChecker.

        Parameters
        ----------
        jira_prefixes : str or list of str
            The Jira project prefix(es) to look for (e.g., "MYJIRA" or ["MYJIRA", "PROJECT"])
        comment_prefixes : list of str, optional
            Comment prefixes to check (e.g., ["TODO", "FIXME"]). If None, uses default list.  # noqa: FIX001
        quiet : bool, optional
            If True, suppress all output and only return exit codes. Default is False.
        verbose : bool, optional
            If True, show detailed output including config, violations, file status, and help. Default is False.
        succeed_always : bool, optional
            If True, always exit with code 0 even when violations are found. Default is False.
        current_ticket_id : str, optional
            The ticket ID for the current branch (e.g., "LIBSDC-123"). If provided, TODOs
            matching this ticket will be tracked separately for informational output.
        check_unstaged : bool, optional
            If True, also check unstaged files for violations (as warnings). Default is False.
        """
        # Always store as list internally
        if isinstance(jira_prefixes, str):
            self.jira_prefixes = [jira_prefixes]
        else:
            self.jira_prefixes = jira_prefixes

        self.quiet = quiet
        self.verbose = verbose
        self.succeed_always = succeed_always
        self.check_unstaged = check_unstaged
        self.exit_code = 0
        self.current_ticket_id = current_ticket_id
        self.ticket_todos: list[tuple] = []  # Track TODOs for the current ticket

        # Comment prefixes that should require Jira references
        if comment_prefixes is None:
            # Default list matches flake8-fixme plugin (FIX001-FIX004)
            self.comment_prefixes = [
                "TODO",  # noqa: FIX001
                "FIXME",  # noqa: FIX002
                "XXX",  # noqa: FIX003
                "HACK",  # noqa: FIX004
            ]
        else:
            self.comment_prefixes = comment_prefixes

        # Build regex patterns
        self._build_patterns()

    def _build_patterns(self) -> None:
        """
        Build regex patterns for matching comments and Jira references.

        Notes
        -----
        This method creates two compiled regex patterns:
        - comment_pattern: Matches work comment prefixes
        - jira_pattern: Matches Jira issue references (or None if no prefixes)
        - noqa_pattern: Matches noqa exclusion comments
        """
        # Pattern to find work comments
        prefixes_pattern = "|".join(self.comment_prefixes)
        self.comment_pattern = re.compile(rf"\b({prefixes_pattern})\b")

        # Pattern to find Jira references - match any of the allowed prefixes
        # If no jira prefixes are provided, jira_pattern will be None
        # meaning ALL work comments are violations
        if self.jira_prefixes:
            jira_prefixes_pattern = "|".join(
                re.escape(prefix) for prefix in self.jira_prefixes
            )
            self.jira_pattern: Optional[re.Pattern] = re.compile(
                rf"({jira_prefixes_pattern})-\d+"
            )
        else:
            self.jira_pattern = None

        # Pattern to find noqa exclusion comments
        # Matches: noqa at end of line OR noqa with flake8 FIX codes (FIX001-FIX004)
        self.noqa_pattern = re.compile(
            r"noqa\s*$|noqa.*(?:FIX001|FIX002|FIX003|FIX004)", re.IGNORECASE
        )

    def find_todos_with_grep(
        self, file_paths: List[str]
    ) -> Dict[str, List[Tuple[int, str]]]:
        """
        Use grep for efficient TODO detection across multiple files.  # noqa: FIX001

        Parameters
        ----------
        file_paths : list of str
            List of file paths to search

        Returns
        -------
        dict
            Dictionary mapping file paths to lists of (line_number, line_content) tuples
        """
        if not file_paths:
            return {}

        # Build grep pattern from comment prefixes
        pattern = "\\|".join(self.comment_prefixes)

        # Build the grep command
        # Use -H for filename, -n for line numbers, -I to skip binary files
        cmd = ["grep", "-Hn", "-I", f"\\b\\({pattern}\\)\\b"] + file_paths

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Parse grep output (format: filename:line_number:line_content)
            todos_by_file: Dict[str, List[Tuple[int, str]]] = {}

            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue

                    # Split only on the first two colons to handle colons in the content
                    parts = line.split(":", 2)
                    if len(parts) >= 3:
                        file_path = parts[0]
                        try:
                            line_num = int(parts[1])
                            content = parts[2]

                            # Check if this line has a Jira reference
                            # If jira_pattern is None, ALL work comments are violations
                            if (
                                self.jira_pattern is None
                                or not self.jira_pattern.search(content)
                            ):
                                # Skip if line has noqa exclusion
                                if not self.noqa_pattern.search(content):
                                    if file_path not in todos_by_file:
                                        todos_by_file[file_path] = []
                                    todos_by_file[file_path].append(
                                        (line_num, content.rstrip())
                                    )

                            # Track current ticket TODOs (only if we have jira patterns)
                            elif (
                                self.jira_pattern is not None
                                and self.current_ticket_id
                                and self.current_ticket_id in content
                            ):
                                self.ticket_todos.append(
                                    (file_path, line_num, content.rstrip())
                                )
                        except ValueError:
                            # Skip malformed lines
                            continue

            return todos_by_file

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            # Fallback to file-by-file checking
            return {}

    def get_all_repo_files(self) -> List[str]:
        """
        Get all tracked files in the repository using git ls-files.

        Returns
        -------
        list of str
            List of file paths tracked by git
        """
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                files = result.stdout.strip().split("\n")
                # Filter out empty strings, non-text files, and documentation/config files
                filtered_files = []
                for f in files:
                    if not f:
                        continue
                    # Skip binary and image files
                    if f.endswith(
                        (
                            ".png",
                            ".jpg",
                            ".jpeg",
                            ".gif",
                            ".pdf",
                            ".ico",
                            ".svg",
                            ".lock",
                            ".pyc",
                        )
                    ):
                        continue
                    # Skip documentation and config files that shouldn't have code TODOs
                    if f.endswith(
                        (
                            "README.md",
                            "CHANGELOG.md",
                            "LICENSE",
                            ".pre-commit-config.yaml",
                            ".pre-commit-hooks.yaml",
                        )
                    ):
                        continue
                    # Skip various directories
                    if f.startswith((".devcontainer/", "docs/", ".github/")):
                        continue
                    # Skip test files (they contain intentional violations for testing)
                    if (
                        f.startswith("tests/")
                        or "/test_data/" in f
                        or f.endswith("_test.py")
                        or f.endswith("test_.py")
                    ):
                        continue
                    # Skip package metadata files
                    if f in [
                        "pyproject.toml",
                        "setup.py",
                        "setup.cfg",
                        "requirements.txt",
                    ]:
                        continue
                    filtered_files.append(f)
                return filtered_files

            return []
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            if not self.quiet:
                print(
                    "⚠️  Warning: Unable to list repository files. Checking only provided files.",
                    file=sys.stderr,
                )
            return []

    def parse_precommit_config(
        self, hook_id: str = "prevent-dangling-todos"
    ) -> Dict[str, Any]:
        """
        Parse .pre-commit-config.yaml to extract file filtering configuration.

        Parameters
        ----------
        hook_id : str, optional
            The hook ID to look for in the config. Default is "prevent-dangling-todos".

        Returns
        -------
        dict
            Dictionary containing filtering fields:
            - files: regex pattern for included files
            - exclude: regex pattern for excluded files
            - types: list of file types to include
            - types_or: list of file types to include (OR logic)
            - exclude_types: list of file types to exclude
        """
        if not HAS_YAML:
            return {}

        config_path = ".pre-commit-config.yaml"
        if not os.path.isfile(config_path):
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config or "repos" not in config:
                return {}

            # Search for our hook in the repos
            for repo in config.get("repos", []):
                for hook in repo.get("hooks", []):
                    if hook.get("id") == hook_id:
                        # Extract filtering fields
                        result = {}
                        if "files" in hook:
                            result["files"] = hook["files"]
                        if "exclude" in hook:
                            result["exclude"] = hook["exclude"]
                        if "types" in hook:
                            result["types"] = hook["types"]
                        if "types_or" in hook:
                            result["types_or"] = hook["types_or"]
                        if "exclude_types" in hook:
                            result["exclude_types"] = hook["exclude_types"]
                        return result

            return {}
        except Exception as e:
            if not self.quiet:
                print(
                    f"⚠️  Warning: Could not parse .pre-commit-config.yaml: {e}",
                    file=sys.stderr,
                )
            return {}

    def filter_files_by_precommit_config(
        self, file_paths: List[str], config: Dict[str, Any]
    ) -> List[str]:
        """
        Filter files based on pre-commit configuration.

        Parameters
        ----------
        file_paths : list of str
            List of file paths to filter
        config : dict
            Configuration dictionary from parse_precommit_config()

        Returns
        -------
        list of str
            Filtered list of file paths
        """
        if not config:
            return file_paths

        filtered = file_paths

        # Apply 'files' regex filter (include pattern)
        if "files" in config:
            try:
                files_pattern = re.compile(config["files"])
                filtered = [f for f in filtered if files_pattern.search(f)]
            except re.error:
                pass  # Invalid regex, skip filtering

        # Apply 'exclude' regex filter
        if "exclude" in config:
            try:
                exclude_pattern = re.compile(config["exclude"])
                filtered = [f for f in filtered if not exclude_pattern.search(f)]
            except re.error:
                pass  # Invalid regex, skip filtering

        # Apply type filters using identify library
        if HAS_IDENTIFY and (
            "types" in config or "types_or" in config or "exclude_types" in config
        ):
            type_filtered = []
            for f in filtered:
                if not os.path.isfile(f):
                    continue

                try:
                    file_types = set(identify.tags_from_path(f))

                    # Check 'types' (all must match)
                    if "types" in config:
                        required_types = set(config["types"])
                        if not required_types.issubset(file_types):
                            continue

                    # Check 'types_or' (at least one must match)
                    if "types_or" in config:
                        or_types = set(config["types_or"])
                        if not or_types.intersection(file_types):
                            continue

                    # Check 'exclude_types' (none should match)
                    if "exclude_types" in config:
                        exclude_types = set(config["exclude_types"])
                        if exclude_types.intersection(file_types):
                            continue

                    type_filtered.append(f)
                except Exception:
                    # If we can't identify the file type, include it
                    type_filtered.append(f)

            filtered = type_filtered

        return filtered

    def check_file(self, file_path: str) -> List[Tuple[int, str]]:
        """
        Check a single file for work comments without Jira references.

        Parameters
        ----------
        file_path : str
            Path to the file to check

        Returns
        -------
        list of tuple
            List of tuples containing (line_number, line_content) for violations
        """
        violations: List[Tuple[int, str]] = []

        # Skip if file doesn't exist (e.g., deleted files)
        if not os.path.isfile(file_path):
            return violations

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    # Check if line contains a work comment
                    if self.comment_pattern.search(line):
                        # Check if it also contains a Jira reference
                        # If jira_pattern is None, ALL work comments are violations
                        if self.jira_pattern is None or not self.jira_pattern.search(
                            line
                        ):
                            # Skip if line has noqa exclusion
                            if not self.noqa_pattern.search(line):
                                violations.append((line_num, line.rstrip()))
                        # If we have a current ticket, check if this TODO is for it  # noqa: FIX001
                        elif (
                            self.jira_pattern is not None
                            and self.current_ticket_id
                            and self.current_ticket_id in line
                        ):
                            self.ticket_todos.append(
                                (file_path, line_num, line.rstrip())
                            )
        except Exception as e:
            print(f"⚠️  Warning: Could not read {file_path}: {e}", file=sys.stderr)

        return violations

    def check_files(self, file_paths: Optional[List[str]]) -> int:
        """
        Check files for violations. Behavior depends on check_unstaged flag.

        Parameters
        ----------
        file_paths : list of str or None
            List of file paths to check (staged files). If None and check_unstaged is False,
            prints a warning and returns 0.

        Returns
        -------
        int
            Exit code (0 if no violations in staged files, 1 if violations found in staged files)
        """
        # Determine which files are staged and which are all repo files
        staged_files = file_paths if file_paths else []
        all_repo_files = []

        # Handle the case where no files are provided
        if not file_paths:
            if not self.check_unstaged:
                # No files and not checking unstaged - nothing to do
                if not self.quiet:
                    print(
                        "⚠️  Warning: No files provided and --check-unstaged not set. Nothing to check."
                    )
                return 0  # Immediate success
            else:
                # Check all unstaged files, filtered by pre-commit config
                all_repo_files = self.get_all_repo_files()
                precommit_config = self.parse_precommit_config()
                filtered_repo_files = self.filter_files_by_precommit_config(
                    all_repo_files, precommit_config
                )
                files_to_check = filtered_repo_files
        else:
            # We have staged files
            if self.check_unstaged:
                # Also check unstaged files for warnings
                all_repo_files = self.get_all_repo_files()
                # Filter unstaged files by pre-commit config
                precommit_config = self.parse_precommit_config()
                filtered_repo_files = self.filter_files_by_precommit_config(
                    all_repo_files, precommit_config
                )
                # Add any repo files not in the staged list for warning-only checks
                unstaged_files = [
                    f for f in filtered_repo_files if f not in staged_files
                ]
                files_to_check = staged_files + unstaged_files
            else:
                # Only check the provided (staged) files
                files_to_check = staged_files

        # Track violations separately for staged vs unstaged
        staged_violations = []
        unstaged_violations = []
        file_statuses = []

        # Verbose mode: Show configuration at the beginning
        if self.verbose:
            if self.jira_prefixes:
                print(
                    f"🔍 Checking work comments for Jira references to projects {', '.join(self.jira_prefixes)}... "
                    f"Checking for: {', '.join(self.comment_prefixes)}"
                )
            else:
                print(
                    f"🔍 Disallowing ALL work comments (no Jira prefix specified)... "
                    f"Checking for: {', '.join(self.comment_prefixes)}"
                )
            if not file_paths:
                print(
                    "📁 No specific files provided, checking all tracked files in repository"
                )

        # Try to use grep for batch processing (much faster for many files)
        grep_results = {}
        if len(files_to_check) > 3:  # Use grep for 4+ files for efficiency
            grep_results = self.find_todos_with_grep(files_to_check)

        # Check each file (use grep results if available, otherwise fall back to file-by-file)
        for file_path in files_to_check:
            is_staged = file_path in staged_files

            # Use grep results if available, otherwise check individual file
            if file_path in grep_results:
                violations = grep_results[file_path]
            else:
                violations = self.check_file(file_path)

            if violations:
                if is_staged:
                    staged_violations.append((file_path, violations))
                    file_statuses.append(
                        (file_path, False, True)
                    )  # has violations, is staged
                    self.exit_code = 1  # Only fail for staged files
                else:
                    unstaged_violations.append((file_path, violations))
                    file_statuses.append(
                        (file_path, False, False)
                    )  # has violations, not staged
            else:
                file_statuses.append(
                    (file_path, True, is_staged)
                )  # clean, staged status

        # Output staged violations as errors (blocking)
        for file_path, violations in staged_violations:
            if not self.quiet:
                for line_num, line_content in violations:
                    print(f"❌ ERROR: {file_path}:{line_num}: {line_content}")

        # Output unstaged violations as warnings (non-blocking)
        if unstaged_violations and not self.quiet:
            if staged_violations:
                print("")  # Blank line between errors and warnings
            print("⚠️  WARNING: Dangling TODOs found in unstaged files (non-blocking):")
            for file_path, violations in unstaged_violations:
                for line_num, line_content in violations:
                    print(f"⚠️  {file_path}:{line_num}: {line_content}")

        # Show ticket-specific TODOs with warning symbol (not in quiet mode)
        if self.ticket_todos and not self.quiet:
            print("")  # Blank line before ticket TODOs
            print(
                f"⚠️  Unresolved TODOs for current branch ticket {self.current_ticket_id}:"
            )
            for file_path, line_num, line_content in self.ticket_todos:
                # Indicate if it's in a staged file
                staged_indicator = " [STAGED]" if file_path in staged_files else ""
                print(f"⚠️  {file_path}:{line_num}: {line_content}{staged_indicator}")

        # Verbose mode: Show file status summary and help text
        if self.verbose:
            print("")  # Blank line before summary
            for file_info in file_statuses:
                if len(file_info) == 3:
                    file_path, is_clean, is_staged = file_info
                    status_icon = "✅" if is_clean else "❌"
                    staged_text = " (staged)" if is_staged else " (unstaged)"
                    print(f"{status_icon} {file_path}{staged_text}")
                else:
                    # Fallback for old format
                    file_path, is_clean = file_info
                    status_icon = "✅" if is_clean else "❌"
                    print(f"{status_icon} {file_path}")

            # Show help text only if violations were found in staged files
            if self.exit_code == 1:
                print("")
                if self.jira_prefixes:
                    print("💡 Please add Jira issue references to work comments like:")
                    # Use first prefix for examples, but mention all are valid
                    first_jira = self.jira_prefixes[0]

                    # Generate examples based on the actual comment prefixes being checked
                    # Use up to 3 different comment prefixes for examples
                    example_prefixes = self.comment_prefixes[:3]
                    example_formats = [
                        ("//", "Implement user authentication"),
                        ("#", "Handle edge case for empty input"),
                        ("/*", "Temporary workaround for API issue", "*/"),
                    ]

                    for i, comment_prefix in enumerate(example_prefixes):
                        if i < len(example_formats):
                            fmt = example_formats[i]
                            if len(fmt) == 3:  # Multi-line comment style
                                print(
                                    f"   {fmt[0]} {comment_prefix} {first_jira}-{123 + i}: {fmt[1]} {fmt[2]}"
                                )
                            else:  # Single-line comment style
                                print(
                                    f"   {fmt[0]} {comment_prefix} {first_jira}-{123 + i}: {fmt[1]}"
                                )

                    if len(self.jira_prefixes) > 1:
                        other_prefixes = ", ".join(self.jira_prefixes[1:])
                        print(f"   (Also valid: {other_prefixes})")
                else:
                    print("💡 Work comments (TODO, FIXME, etc.) are not allowed.")  # noqa: FIX001
                    print(
                        "   Please remove them or specify a Jira prefix to allow tracked work items."
                    )

        # Return 0 if succeed_always is True, otherwise return the actual exit code
        return 0 if self.succeed_always else self.exit_code
