"""CLI for preventing dangling TODOs."""

import argparse
import os
import sys
from typing import List, Optional

from prevent_dangling_todos.prevent_todos import TodoChecker


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser for the CLI
    """
    parser = argparse.ArgumentParser(
        prog="prevent-dangling-todos",
        description=(
            "Check source files for TODO/FIXME comments without Jira issue references.\n\n"
            "This tool helps maintain code quality by ensuring all work comments "
            "(TODO, FIXME, etc.) are properly linked to tracking issues.\n\n"
            "Configuration can be provided via command line arguments or environment variables:\n"
            "  JIRA_PREFIX=PREFIX1,PREFIX2,PREFIX3\n"
            "  COMMENT_PREFIX=TODO,FIXME,XXX\n\n"
            "Command line arguments take precedence over environment variables."
        ),
        epilog=(
            "Examples:\n"
            "  %(prog)s -j MYJIRA file1.py file2.js\n"
            "      Check specific files for dangling TODOs\n\n"
            "  %(prog)s --jira-prefix MYJIRA,PROJECT,TEAM file.py\n"
            "      Use multiple Jira project prefixes (comma-separated)\n\n"
            "  %(prog)s -j PROJECT src/**/*.py\n"
            "      Check all Python files with PROJECT prefix\n\n"
            "  %(prog)s -j MYJIRA -c TODO,FIXME *.js\n"
            "      Check only TODO and FIXME comments\n\n"
            "  JIRA_PREFIX=MYJIRA,PROJECT %(prog)s file.py\n"
            "      Use environment variable for Jira prefixes\n\n"
            "  COMMENT_PREFIX=TODO,FIXME %(prog)s -j MYJIRA file.py\n"
            "      Environment variable for comment prefixes, CLI for Jira\n\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Positional argument for files
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Source files to check for dangling work comments",
    )

    # Optional arguments
    parser.add_argument(
        "-j",
        "--jira-prefix",
        metavar="PREFIXES",
        help=(
            "Jira project prefix(es) to look for. For multiple prefixes, separate with commas: "
            "'MYJIRA,PROJECT,TEAM'. Can also be set via JIRA_PREFIX environment variable. "
            "Required if JIRA_PREFIX environment variable is not set."
        ),
    )

    parser.add_argument(
        "-c",
        "--comment-prefix",
        metavar="PREFIXES",
        help=(
            "Comment prefix(es) to check. For multiple prefixes, separate with commas: "
            "'TODO,FIXME,XXX'. Can also be set via COMMENT_PREFIX environment variable. "
            "Default: TODO, FIXME, XXX, HACK, BUG, REVIEW, OPTIMIZE, REFACTOR"
        ),
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Only output violation lines without decorative text or tips",
    )

    parser.add_argument(
        "--succeed-always",
        action="store_true",
        help=(
            "Always exit with code 0, even when dangling TODOs are found. "
            "Useful for alerting developers without blocking commits."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
        help="Show program version and exit",
    )

    return parser


def _parse_comma_separated(value: Optional[str]) -> Optional[List[str]]:
    """
    Parse a comma-separated string into a list, handling None and empty values.

    Parameters
    ----------
    value : str or None
        Comma-separated string to parse

    Returns
    -------
    list of str or None
        Parsed list of non-empty strings, or None if input was None or empty
    """
    if not value:
        return None

    # Split by comma and strip whitespace, filter empty strings
    parsed = [item.strip() for item in value.split(",")]
    parsed = [item for item in parsed if item]  # Remove empty strings

    return parsed if parsed else None


def main(argv: Optional[List[str]] = None) -> None:
    """
    Main entry point for the script.

    Parameters
    ----------
    argv : list of str, optional
        Command line arguments. If None, defaults to sys.argv[1:]
    """
    parser = create_parser()

    # Handle being called with no arguments or as entry point
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    # Parse environment variables
    env_jira_prefixes = _parse_comma_separated(os.environ.get("JIRA_PREFIX"))
    env_comment_prefixes = _parse_comma_separated(os.environ.get("COMMENT_PREFIX"))

    # Parse CLI arguments
    cli_jira_prefixes = _parse_comma_separated(args.jira_prefix)
    cli_comment_prefixes = _parse_comma_separated(args.comment_prefix)

    # Determine final values (CLI overrides env vars)
    final_jira_prefixes = cli_jira_prefixes or env_jira_prefixes
    final_comment_prefixes = cli_comment_prefixes or env_comment_prefixes
    final_succeed_always = args.succeed_always

    # Validate that jira_prefixes are provided from some source
    if not final_jira_prefixes:
        print(
            "Error: Jira project prefix(es) must be specified either via --jira-prefix argument "
            "or JIRA_PREFIX environment variable.",
            file=sys.stderr,
        )
        print("\nExamples:", file=sys.stderr)
        print("  prevent-dangling-todos --jira-prefix MYJIRA file.py", file=sys.stderr)
        print(
            "  prevent-dangling-todos --jira-prefix MYJIRA,PROJECT file.py",
            file=sys.stderr,
        )
        print(
            "  JIRA_PREFIX=MYJIRA,PROJECT prevent-dangling-todos file.py",
            file=sys.stderr,
        )
        sys.exit(2)

    # Configuration warning for conflicting options
    if args.quiet and final_succeed_always:
        print(
            "Warning: Using --quiet with --succeed-always may reduce visibility of TODO violations. "
            "Consider using only --succeed-always if you want to see violation details.",
            file=sys.stderr,
        )

    # Initialize checker with configuration
    checker = TodoChecker(
        jira_prefixes=final_jira_prefixes,
        quiet=args.quiet,
        comment_prefixes=final_comment_prefixes,
        succeed_always=final_succeed_always,
    )

    # Check files and exit with appropriate code
    exit_code = checker.check_files(args.files)
    sys.exit(exit_code)
