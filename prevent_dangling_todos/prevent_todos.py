#!/usr/bin/env python3
"""
Pre-commit hook to check that TODO, FIXME, and other work comments include Jira issue references.

Usage: python prevent_todos.py file1.py file2.js ...
"""

import sys
import re
import os
from typing import List, Optional, Tuple, Union


class TodoChecker:
    """
    Check files for work comments that lack Jira issue references.

    This class provides functionality to scan source code files for TODO, FIXME,
    and other work comments, ensuring they include proper Jira issue references.

    Attributes
    ----------
    jira_prefixes : list of str
        List of valid Jira project prefixes
    comment_prefixes : list of str
        List of comment prefixes to check (e.g., TODO, FIXME)
    quiet : bool
        Whether to suppress decorative output
    succeed_always : bool
        Whether to always exit with code 0 even when violations are found
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
        succeed_always: bool = False,
    ):
        """
        Initialize the TodoChecker.

        Parameters
        ----------
        jira_prefixes : str or list of str
            The Jira project prefix(es) to look for (e.g., "MYJIRA" or ["MYJIRA", "PROJECT"])
        comment_prefixes : list of str, optional
            Comment prefixes to check (e.g., ["TODO", "FIXME"]). If None, uses default list.
        quiet : bool, optional
            If True, only output violations without decorative text or tips. Default is False.
        succeed_always : bool, optional
            If True, always exit with code 0 even when violations are found. Default is False.
        """
        # Always store as list internally
        if isinstance(jira_prefixes, str):
            self.jira_prefixes = [jira_prefixes]
        else:
            self.jira_prefixes = jira_prefixes

        self.quiet = quiet
        self.succeed_always = succeed_always
        self.exit_code = 0

        # Comment prefixes that should require Jira references
        if comment_prefixes is None:
            # Default list if not specified
            self.comment_prefixes = [
                "TODO",
                "FIXME",
                "XXX",
                "HACK",
                "BUG",
                "REVIEW",
                "OPTIMIZE",
                "REFACTOR",
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
        - jira_pattern: Matches Jira issue references
        """
        # Pattern to find work comments
        prefixes_pattern = "|".join(self.comment_prefixes)
        self.comment_pattern = re.compile(rf"\b({prefixes_pattern})\b", re.IGNORECASE)

        # Pattern to find Jira references - match any of the allowed prefixes
        jira_prefixes_pattern = "|".join(
            re.escape(prefix) for prefix in self.jira_prefixes
        )
        self.jira_pattern = re.compile(rf"({jira_prefixes_pattern})-\d+", re.IGNORECASE)

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
                        if not self.jira_pattern.search(line):
                            violations.append((line_num, line.rstrip()))
        except Exception as e:
            print(f"⚠️  Warning: Could not read {file_path}: {e}", file=sys.stderr)

        return violations

    def check_files(self, file_paths: List[str]) -> int:
        """
        Check multiple files for violations.

        Parameters
        ----------
        file_paths : list of str
            List of file paths to check

        Returns
        -------
        int
            Exit code (0 if no violations, 1 if violations found)
        """
        if not self.quiet:
            print(
                f"🔍 Checking work comments for Jira references to projects {', '.join(self.jira_prefixes)}..."
            )
            print(f"   Checking for: {', '.join(self.comment_prefixes)}")

        for file_path in file_paths:
            violations = self.check_file(file_path)

            if violations:
                if self.quiet:
                    # In quiet mode, just output the violations
                    for line_num, line_content in violations:
                        print(f"{file_path}:{line_num}: {line_content}")
                else:
                    # Show all allowed prefixes consistently
                    prefixes_display = "|".join(
                        f"{prefix}-XXXX" for prefix in self.jira_prefixes
                    )
                    print(
                        f"❌ {file_path} - Work comment missing Jira reference ({prefixes_display}):"
                    )
                    for line_num, line_content in violations:
                        print(f"   {line_num}: {line_content}")
                self.exit_code = 1

        if not self.quiet:
            if self.exit_code == 0:
                print("✅ All work comments have proper Jira references")
            else:
                print("")
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

        # Return 0 if succeed_always is True, otherwise return the actual exit code
        return 0 if self.succeed_always else self.exit_code
