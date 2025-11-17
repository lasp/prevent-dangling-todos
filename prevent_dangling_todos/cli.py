"""CLI for preventing dangling TODOs."""

import argparse
import os
import re
import subprocess
import sys
from typing import List, Optional, Tuple

from prevent_dangling_todos.prevent_todos import TodoChecker

# Default comment prefixes to check (matches flake8-fixme plugin FIX001-FIX004)
DEFAULT_COMMENT_PREFIXES = ["TODO", "FIXME", "XXX", "HACK"]  # noqa: FIX001


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
            "Check source files for TODO/FIXME comments without ticket references.\n\n"  # noqa: FIX001
            "This tool helps maintain code quality by ensuring all work comments "
            "(TODO, FIXME, etc.) are properly linked to issue trackers (Jira, GitHub, Linear, etc.).\n\n"  # noqa: FIX001
            "Configuration can be provided via command line arguments or environment variables:\n"
            "  TICKET_PREFIX=PREFIX1,PREFIX2,PREFIX3  (or JIRA_PREFIX for backward compat)\n"
            "  COMMENT_PREFIX=TODO,FIXME,XXX\n\n"  # noqa: FIX001
            "Command line arguments take precedence over environment variables."
        ),
        epilog=(
            "Examples:\n"
            "  %(prog)s -t MYJIRA file1.py file2.js\n"
            "      Check specific files for dangling TODOs (Jira example)\n\n"
            "  %(prog)s -t GITHUB src/**/*.py\n"
            "      Check all Python files with GitHub issue prefix\n\n"
            "  %(prog)s --ticket-prefix MYJIRA,GITHUB,LINEAR file.py\n"
            "      Use multiple ticket prefixes (comma-separated)\n\n"
            "  %(prog)s -t MYJIRA -c TODO,FIXME *.js\n"  # noqa: FIX001
            "      Check only TODO and FIXME comments\n\n"  # noqa: FIX001
            "  TICKET_PREFIX=MYJIRA,PROJECT %(prog)s file.py\n"
            "      Use environment variable for ticket prefixes\n\n"
            "  COMMENT_PREFIX=TODO,FIXME %(prog)s -t MYJIRA file.py\n"  # noqa: FIX001
            "      Environment variable for comment prefixes, CLI for ticket prefix\n\n"
            "  %(prog)s -j MYJIRA file.py\n"
            "      [DEPRECATED] Use -t instead of -j\n\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Positional argument for files (now optional)
    parser.add_argument(
        "files",
        nargs="*",
        default=None,
        metavar="FILE",
        help="Source files to check for dangling work comments. If not provided, checks all tracked files in the repository.",
    )

    # Optional arguments
    parser.add_argument(
        "-t",
        "--ticket-prefix",
        metavar="PREFIXES",
        help=(
            "Ticket prefix(es) to look for from any issue tracker (Jira, GitHub, Linear, etc.). "
            "For multiple prefixes, separate with commas: 'MYJIRA,GITHUB,LINEAR'. "
            "Can also be set via TICKET_PREFIX environment variable. "
            "If not specified, ALL work comments (TODO, FIXME, etc.) will be disallowed."  # noqa: FIX001
        ),
    )

    parser.add_argument(
        "-j",
        "--jira-prefix",
        metavar="PREFIXES",
        help=(
            "[DEPRECATED: Use -t/--ticket-prefix instead] "
            "Ticket prefix(es) to look for. Can also be set via JIRA_PREFIX environment variable."
        ),
    )

    parser.add_argument(
        "-c",
        "--comment-prefix",
        metavar="PREFIXES",
        help=(
            "Comment prefix(es) to check. For multiple prefixes, separate with commas: "
            "'TODO,FIXME,XXX'. Can also be set via COMMENT_PREFIX environment variable. "  # noqa: FIX001
            f"Default: {', '.join(DEFAULT_COMMENT_PREFIXES)}"
        ),
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Silent mode: no output, just exit codes",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose mode: show configuration, violations, file status summary, and help text",
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
        "-u",
        "--check-unstaged",
        action="store_true",
        help=(
            "Also check unstaged files for dangling work comments (as warnings). "
            "By default, only staged files passed to the hook are checked."
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


def _get_current_git_branch() -> Tuple[Optional[str], Optional[str]]:
    """
    Get the current git branch name.

    Returns
    -------
    tuple of (Optional[str], Optional[str])
        (branch_name, error_message) - Returns (None, error_msg) if detection fails
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            if branch:
                return branch, None
            return None, "Unable to detect current git branch"
        return None, "Unable to detect current git branch"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None, "Unable to detect current git branch"


def _extract_ticket_id(
    branch_name: str, ticket_prefixes: List[str] | None
) -> Optional[str]:
    """
    Extract a ticket ID from a branch name if it matches any of the ticket prefixes.

    Parameters
    ----------
    branch_name : str
        The git branch name
    ticket_prefixes : list[str] | None
        List of valid ticket/issue prefixes (e.g., JIRA, GITHUB, LINEAR)

    Returns
    -------
    str or None
        The ticket ID (e.g., "LIBSDC-123", "GITHUB-456") if found, otherwise None
    """
    if not branch_name or not ticket_prefixes:
        return None

    # Build a pattern to match any of the ticket prefixes followed by a dash and numbers
    # This will match patterns like LIBSDC-123, GITHUB-456 anywhere in the branch name
    for prefix in ticket_prefixes:
        pattern = rf"{re.escape(prefix)}-\d+"
        match = re.search(pattern, branch_name)
        if match:
            return match.group(0)

    return None


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

    # Parse environment variables (new + deprecated)
    env_ticket_prefixes = _parse_comma_separated(os.environ.get("TICKET_PREFIX"))
    env_jira_prefixes = _parse_comma_separated(
        os.environ.get("JIRA_PREFIX")
    )  # Deprecated
    env_comment_prefixes = _parse_comma_separated(os.environ.get("COMMENT_PREFIX"))

    # Parse CLI arguments (new + deprecated)
    cli_ticket_prefixes = _parse_comma_separated(args.ticket_prefix)
    cli_jira_prefixes = _parse_comma_separated(args.jira_prefix)  # Deprecated
    cli_comment_prefixes = _parse_comma_separated(args.comment_prefix)

    # Show deprecation warnings
    if cli_jira_prefixes and not args.quiet:
        print(
            "Warning: -j/--jira-prefix is deprecated. Use -t/--ticket-prefix instead.",
            file=sys.stderr,
        )
    if env_jira_prefixes and not env_ticket_prefixes and not args.quiet:
        print(
            "Warning: JIRA_PREFIX environment variable is deprecated. Use TICKET_PREFIX instead.",
            file=sys.stderr,
        )

    # Determine final values with proper precedence
    # Priority: --ticket-prefix > --jira-prefix > TICKET_PREFIX > JIRA_PREFIX
    final_ticket_prefixes = (
        cli_ticket_prefixes
        or cli_jira_prefixes
        or env_ticket_prefixes
        or env_jira_prefixes
    )
    final_comment_prefixes = (
        cli_comment_prefixes or env_comment_prefixes or DEFAULT_COMMENT_PREFIXES
    )
    final_succeed_always = args.succeed_always

    # Note: ticket_prefixes is now optional. If not provided, ALL work comments are disallowed.
    if not final_ticket_prefixes and not args.quiet:
        print(
            "Note: No ticket prefix specified. ALL work comments (TODO, FIXME, etc.) will be disallowed."  # noqa: FIX001
        )

    # Configuration validation for conflicting options
    if args.quiet and args.verbose:
        print(
            "Error: --quiet and --verbose are mutually exclusive options.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.quiet and final_succeed_always:
        print(
            "Warning: Using --quiet with --succeed-always may reduce visibility of TODO violations. "  # noqa: FIX001
            "Consider using only --succeed-always if you want to see violation details.",
            file=sys.stderr,
        )

    # Detect current git branch and extract ticket ID
    branch_name, branch_error = _get_current_git_branch()
    current_ticket_id = None
    branch_detection_msg = None

    if branch_error:
        branch_detection_msg = f"Note: {branch_error}"
    elif branch_name and final_ticket_prefixes:
        current_ticket_id = _extract_ticket_id(branch_name, final_ticket_prefixes)
        if not current_ticket_id:
            branch_detection_msg = (
                f"Note: No ticket ID detected in current branch '{branch_name}'"
            )

    # Initialize checker with configuration
    # Pass empty list if no ticket prefixes (will disallow ALL work comments)
    checker = TodoChecker(
        ticket_prefixes=final_ticket_prefixes if final_ticket_prefixes else [],
        quiet=args.quiet,
        verbose=args.verbose,
        comment_prefixes=final_comment_prefixes,
        succeed_always=final_succeed_always,
        current_ticket_id=current_ticket_id,
        check_unstaged=args.check_unstaged,
    )

    # Check files and exit with appropriate code
    # If no files provided, checker will check all tracked files in repo
    exit_code = checker.check_files(args.files if args.files else None)

    # Show branch detection message if needed (not in quiet mode)
    if branch_detection_msg and not args.quiet:
        print(f"\n{branch_detection_msg}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
