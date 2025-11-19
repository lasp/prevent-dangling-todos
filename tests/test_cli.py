"""Unit tests for the CLI module."""

from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from prevent_dangling_todos.cli import (
    main,
    create_parser,
    _get_current_git_branch,
    _extract_ticket_id,
)


class TestCLI:
    """Test the CLI functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.test_data_dir = Path(__file__).parent / "test_data"

    def test_help_text(self, capsys):
        """Test that --help displays comprehensive help text."""
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()

        # Check for key elements in help text
        assert "Check source files for TODO/FIXME comments" in captured.out
        assert "--ticket-prefix" in captured.out  # New primary option
        assert "--jira-prefix" in captured.out  # Deprecated but still shown
        assert "--comment-prefix" in captured.out
        assert "--quiet" in captured.out
        assert "Examples:" in captured.out
        assert "multiple ticket prefixes" in captured.out
        assert "comma-separated" in captured.out
        assert "environment variable" in captured.out

    def test_version_flag(self, capsys):
        """Test --version flag displays version."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "prevent-dangling-todos 1.0.0" in captured.out

    def test_no_arguments_checks_all_files(self, capsys):
        """Test that running without arguments checks all tracked files with no ticket prefix (disallow ALL TODOs)."""
        # Mock git ls-files to return test files
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "file1.py\nfile2.js"
            mock_run.return_value = mock_result

            with pytest.raises(SystemExit) as exc_info:
                main([])

            # Should run successfully (no ticket prefix means disallow all TODOs)
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            # Should show informational message about no ticket prefix
            assert "No ticket prefix specified" in captured.out
            assert "ALL work comments" in captured.out

    def test_clean_file_passes(self, capsys):
        """Test that a file with properly referenced TODOs passes with no output."""
        test_file = str(self.test_data_dir / "test_file_clean.py")

        # Mock git to avoid branch detection output
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1  # Simulate git not available
            mock_run.return_value = mock_result

            with pytest.raises(SystemExit) as exc_info:
                main(["-j", "MYJIRA", test_file])

            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            # Should show git detection failure note
            assert "Note: Unable to detect current git branch" in captured.out

    def test_file_with_violations_fails(self, capsys):
        """Test that a file with violations fails with exit code 1 and shows violations with red X."""
        test_file = str(self.test_data_dir / "test_file_with_violations.py")

        with pytest.raises(SystemExit) as exc_info:
            main(["--jira-prefix", "MYJIRA", test_file])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()

        # Standard mode should show violations with red X marks
        assert "❌" in captured.out
        assert "TODO: This is a violation" in captured.out
        assert "FIXME: Another violation" in captured.out

        # Should not show config info or help text in standard mode
        assert "🔍 Checking work comments" not in captured.out
        assert "💡 Please add ticket/issue references" not in captured.out

    def test_multiple_jira_prefixes(self, capsys):
        """Test multiple JIRA prefixes in both success and failure cases."""
        # Test 1: Multiple prefixes with all valid references - should pass with no output
        test_file = str(
            self.test_data_dir / "test_file_clean.py"
        )  # All have MYJIRA prefix

        # Mock git to avoid branch detection output
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1  # Simulate git not available
            mock_run.return_value = mock_result

            with pytest.raises(SystemExit) as exc_info:
                main(["-j", "MYJIRA,PROJECT,TEAM", test_file])

            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            # Should show git detection failure note
            assert "Note: Unable to detect current git branch" in captured.out

        # Test 2: Multiple prefixes with violations - should only show violations
        test_file = str(self.test_data_dir / "test_file_with_violations.py")

        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA,PROJECT,TEAM", test_file])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()

        # Should show violations with red X marks
        assert "❌" in captured.out
        assert "TODO: This is a violation" in captured.out
        # Should not show config info or help text in standard mode
        assert "projects MYJIRA, PROJECT, TEAM" not in captured.out
        assert "(Also valid: PROJECT, TEAM)" not in captured.out

    def test_comment_prefixes_filter(self, capsys):
        """Test filtering specific comment prefixes."""
        test_file = str(self.test_data_dir / "test_file_single_todo.py")

        # Test checking only TODO comments
        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA", "-c", "TODO", test_file])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()

        # Should find TODO violation but not show config info in standard mode
        assert "TODO: This TODO has no reference" in captured.out
        assert "❌" in captured.out
        # Should not show config info in standard mode
        assert "Checking for: TODO" not in captured.out
        # Should not show FIXME violations since we're only checking TODO
        assert "FIXME: Missing reference FIXME" not in captured.out

    def test_quiet_mode(self, capsys):
        """Test quiet mode produces no output at all."""
        test_file = str(self.test_data_dir / "test_file_with_violations.py")

        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA", "--quiet", test_file])

        # Should still exit with code 1 for violations
        assert exc_info.value.code == 1
        captured = capsys.readouterr()

        # Quiet mode should have no output at all
        assert captured.out == ""
        assert "🔍" not in captured.out
        assert "❌" not in captured.out
        assert "💡" not in captured.out
        assert "✅" not in captured.out

    def test_multiple_files(self, capsys):
        """Test checking multiple files at once."""
        clean_file = str(self.test_data_dir / "test_file_clean.py")
        violation_file = str(self.test_data_dir / "test_file_with_violations.py")

        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA", clean_file, violation_file])

        # Should fail if any file has violations
        assert exc_info.value.code == 1
        captured = capsys.readouterr()

        # Should show violations from the problematic file
        assert "test_file_with_violations.py" in captured.out
        assert "❌" in captured.out
        # Should not show config info in standard mode
        assert "Work comment missing Jira reference" not in captured.out

    def test_environment_variables(self, capsys, monkeypatch):
        """Test comprehensive environment variable support and parsing."""
        test_file = str(self.test_data_dir / "test_file_clean.py")

        # Mock git to avoid branch detection output
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1  # Simulate git not available
            mock_run.return_value = mock_result

            # Test 1: JIRA_PREFIX environment variable with multiple values - clean file should have no output
            monkeypatch.setenv("JIRA_PREFIX", "MYJIRA,PROJECT")

            with pytest.raises(SystemExit) as exc_info:
                main([test_file])

            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            # Should show git detection failure note
            assert "Note: Unable to detect current git branch" in captured.out

            # Test 2: Both JIRA_PREFIX and COMMENT_PREFIX environment variables with violations
            test_file = str(self.test_data_dir / "test_file_single_todo.py")
            monkeypatch.setenv("JIRA_PREFIX", "MYJIRA")
            monkeypatch.setenv("COMMENT_PREFIX", "TODO,XXX")

            with pytest.raises(SystemExit) as exc_info:
                main([test_file])

            assert exc_info.value.code == 1  # Should find TODO violations
            captured = capsys.readouterr()
            # Standard mode should show violations but not config info
            assert "❌" in captured.out
            assert "TODO: This TODO has no reference" in captured.out
            assert "Checking for: TODO, XXX" not in captured.out

            # Test 3: CLI arguments override environment variables - clean file should have no output
            test_file = str(self.test_data_dir / "test_file_clean.py")
            monkeypatch.setenv("JIRA_PREFIX", "WRONGPREFIX")
            monkeypatch.setenv("COMMENT_PREFIX", "WRONGCOMMENT")

            with pytest.raises(SystemExit) as exc_info:
                main(["-j", "MYJIRA", "-c", "TODO", test_file])

            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            # Should show git detection failure note
            assert "Note: Unable to detect current git branch" in captured.out

            # Test 4: Comma parsing with whitespace and empty values - clean file should have no output
            with pytest.raises(SystemExit) as exc_info:
                main(["-j", " MYJIRA,,PROJECT, ", test_file])

            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            # Should show git detection failure note
            assert "Note: Unable to detect current git branch" in captured.out

    def test_no_jira_prefix_disallows_all_todos(self, capsys):
        """Test that no Jira prefix disallows ALL work comments."""
        test_file = str(self.test_data_dir / "test_file_with_violations.py")

        with pytest.raises(SystemExit) as exc_info:
            main([test_file])

        # Should fail because ALL TODOs are violations when no jira prefix
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        # Should show informational message about no jira prefix
        assert "No ticket prefix specified" in captured.out
        assert "ALL work comments" in captured.out
        # Should show violations
        assert "❌" in captured.out

    def test_no_jira_prefix_clean_file(self, capsys):
        """Test that no Jira prefix with clean file (no TODOs) passes."""
        # Create a temporary file with no TODOs
        test_file = str(self.test_data_dir / "test_file_no_todos.py")

        # Mock git ls-files to return only the test file
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = test_file
            mock_run.return_value = mock_result

            with pytest.raises(SystemExit) as exc_info:
                main([test_file])

            # Should pass because file has no TODOs
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            # Should show informational message about no jira prefix
            assert "No ticket prefix specified" in captured.out

    def test_no_jira_prefix_with_valid_jira_references(self, capsys):
        """Test that even valid Jira references are violations when no jira prefix is specified."""
        test_file = str(
            self.test_data_dir / "test_file_clean.py"
        )  # Has MYJIRA-123 references

        with pytest.raises(SystemExit) as exc_info:
            main([test_file])

        # Should fail because ALL TODOs are violations when no jira prefix
        # (even though they have MYJIRA-123 references)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "❌" in captured.out
        assert "No ticket prefix specified" in captured.out

    def test_succeed_always_cli_option(self, capsys):
        """Test --succeed-always CLI option works correctly."""
        test_file = str(self.test_data_dir / "test_file_with_violations.py")

        # Test with violations but succeed_always should return 0
        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA", "--succeed-always", test_file])

        assert exc_info.value.code == 0  # Should exit with 0 despite violations
        captured = capsys.readouterr()

        # Should still show violations in standard mode (violations only with red X)
        assert "❌" in captured.out
        assert "TODO: This is a violation" in captured.out
        # Should not show config info or help text in standard mode
        assert "Work comment missing Jira reference" not in captured.out
        assert "💡 Please add ticket/issue references" not in captured.out

    def test_quiet_and_succeed_always_warning(self, capsys):
        """Test warning when both --quiet and --succeed-always are used."""
        test_file = str(self.test_data_dir / "test_file_with_violations.py")

        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA", "--quiet", "--succeed-always", test_file])

        assert exc_info.value.code == 0  # Should succeed due to --succeed-always
        captured = capsys.readouterr()

        # Should show configuration warning to stderr
        assert "Warning: Using --quiet with --succeed-always" in captured.err
        assert "may reduce visibility of TODO violations" in captured.err

        # Should have no output to stdout in quiet mode
        assert captured.out == ""

    def test_succeed_always_with_clean_file(self, capsys):
        """Test --succeed-always with clean file (no violations)."""
        test_file = str(self.test_data_dir / "test_file_clean.py")

        # Mock git to avoid branch detection output
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1  # Simulate git not available
            mock_run.return_value = mock_result

            with pytest.raises(SystemExit) as exc_info:
                main(["-j", "MYJIRA", "--succeed-always", test_file])

            assert exc_info.value.code == 0  # Should succeed
            captured = capsys.readouterr()
            # Should show git detection failure note
            assert "Note: Unable to detect current git branch" in captured.out

    def test_help_includes_succeed_always(self, capsys):
        """Test that --help includes information about --succeed-always."""
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()

        # Check for succeed-always option in help text
        assert "--succeed-always" in captured.out
        assert "Always exit with code 0" in captured.out

    def test_verbose_mode_with_violations(self, capsys):
        """Test verbose mode shows config, violations, file status, and help text."""
        test_file = str(self.test_data_dir / "test_file_with_violations.py")

        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA", "--verbose", test_file])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()

        # Should show config info
        assert (
            "🔍 Checking work comments for ticket references to projects MYJIRA"
            in captured.out
        )
        assert "Checking for:" in captured.out

        # Should show violations with red X
        assert "❌" in captured.out
        assert "TODO: This is a violation" in captured.out

        # Should show file status summary
        assert f"❌ {test_file}" in captured.out

        # Should show help text
        assert (
            "💡 Please add ticket/issue references to work comments like:"
            in captured.out
        )

    def test_verbose_mode_with_clean_file(self, capsys):
        """Test verbose mode with clean file shows config and file status but no violations."""
        test_file = str(self.test_data_dir / "test_file_clean.py")

        # Mock subprocess.run to handle both git branch detection and git ls-files
        with patch("subprocess.run") as mock_run:

            def side_effect(cmd, **kwargs):
                mock_result = MagicMock()
                if "rev-parse" in cmd:  # git branch detection
                    mock_result.returncode = 1  # No git
                elif "ls-files" in cmd:  # git ls-files
                    mock_result.returncode = 0
                    # Return only the test file to avoid checking other files
                    mock_result.stdout = test_file
                else:
                    mock_result.returncode = 0
                    mock_result.stdout = ""
                return mock_result

            mock_run.side_effect = side_effect

            with pytest.raises(SystemExit) as exc_info:
                main(["-j", "MYJIRA", "--verbose", test_file])

            assert exc_info.value.code == 0
            captured = capsys.readouterr()

            # Should show config info
            assert (
                "🔍 Checking work comments for ticket references to projects MYJIRA"
                in captured.out
            )
            assert "Checking for:" in captured.out

            # Should show file status with checkmark
            assert f"✅ {test_file}" in captured.out

            # Should not show violations or help text
            assert "❌" not in captured.out
            assert "💡 Please add ticket/issue references" not in captured.out

    def test_verbose_mode_multiple_files(self, capsys):
        """Test verbose mode with multiple files shows status for each."""
        clean_file = str(self.test_data_dir / "test_file_clean.py")
        violation_file = str(self.test_data_dir / "test_file_with_violations.py")

        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA", "--verbose", clean_file, violation_file])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()

        # Should show config info
        assert (
            "🔍 Checking work comments for ticket references to projects MYJIRA"
            in captured.out
        )

        # Should show violations
        assert "❌" in captured.out
        assert "TODO: This is a violation" in captured.out

        # Should show status for both files
        assert f"✅ {clean_file}" in captured.out
        assert f"❌ {violation_file}" in captured.out

        # Should show help text since there were violations
        assert "💡 Please add ticket/issue references" in captured.out

    def test_verbose_quiet_mutually_exclusive(self, capsys):
        """Test that --verbose and --quiet are mutually exclusive."""
        test_file = str(self.test_data_dir / "test_file_clean.py")

        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA", "--verbose", "--quiet", test_file])

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "Error: --quiet and --verbose are mutually exclusive" in captured.err

    def test_help_includes_verbose(self, capsys):
        """Test that --help includes information about --verbose."""
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()

        # Check for verbose option in help text
        assert "--verbose" in captured.out
        assert "Verbose mode" in captured.out

    def test_help_includes_check_unstaged(self, capsys):
        """Test that --help includes information about --check-unstaged."""
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()

        # Check for check-unstaged option in help text
        assert "--check-unstaged" in captured.out
        assert "-u" in captured.out
        assert "unstaged files" in captured.out

    def test_check_unstaged_short_flag(self, capsys):
        """Test that -u short flag works for --check-unstaged."""
        test_file = str(self.test_data_dir / "test_file_with_violations.py")

        # Mock git ls-files to return unstaged files
        with patch("subprocess.run") as mock_run:

            def side_effect(cmd, **kwargs):
                mock_result = MagicMock()
                if "rev-parse" in cmd:
                    mock_result.returncode = 1  # No git branch
                elif "ls-files" in cmd:
                    mock_result.returncode = 0
                    mock_result.stdout = "other.py"
                else:
                    mock_result.returncode = 0
                    mock_result.stdout = ""
                return mock_result

            mock_run.side_effect = side_effect

            with pytest.raises(SystemExit) as exc_info:
                main(["-j", "MYJIRA", "-u", test_file])

            # Should fail because test file has violations
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "❌" in captured.out


class TestBranchDetection:
    """Test git branch detection and ticket ID extraction."""

    def test_get_current_git_branch_success(self):
        """Test successful git branch detection."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "feature/LIBSDC-123-add-feature\n"
            mock_run.return_value = mock_result

            branch, error = _get_current_git_branch()
            assert branch == "feature/LIBSDC-123-add-feature"
            assert error is None

    def test_get_current_git_branch_failure(self):
        """Test git branch detection failure."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            branch, error = _get_current_git_branch()
            assert branch is None
            assert error == "Unable to detect current git branch"

    def test_get_current_git_branch_timeout(self):
        """Test git branch detection timeout."""
        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("git", 5)

            branch, error = _get_current_git_branch()
            assert branch is None
            assert error == "Unable to detect current git branch"

    def test_extract_ticket_id_various_formats(self):
        """Test ticket ID extraction from various branch name formats."""
        # Test typical branch formats
        assert (
            _extract_ticket_id("feature/LIBSDC-123-description", ["LIBSDC"])
            == "LIBSDC-123"
        )
        assert (
            _extract_ticket_id("bugfix/PROJECT-456-fix-bug", ["PROJECT"])
            == "PROJECT-456"
        )
        assert _extract_ticket_id("TEAM-789-simple-branch", ["TEAM"]) == "TEAM-789"
        assert _extract_ticket_id("release/v1.0-MYJIRA-100", ["MYJIRA"]) == "MYJIRA-100"

        # Test multiple prefixes
        assert (
            _extract_ticket_id("feature/ALPHA-123-test", ["ALPHA", "BETA", "GAMMA"])
            == "ALPHA-123"
        )
        assert (
            _extract_ticket_id("feature/BETA-456-test", ["ALPHA", "BETA", "GAMMA"])
            == "BETA-456"
        )

        # Test no match
        assert _extract_ticket_id("main", ["LIBSDC"]) is None
        assert _extract_ticket_id("develop", ["PROJECT"]) is None
        assert _extract_ticket_id("feature/add-new-feature", ["MYJIRA"]) is None
        assert _extract_ticket_id("WRONG-123-branch", ["CORRECT"]) is None

        # Test edge cases
        assert _extract_ticket_id("", ["LIBSDC"]) is None
        assert _extract_ticket_id("some-branch", []) is None
        assert _extract_ticket_id("some-branch", None) is None

    def test_cli_with_branch_detection(self, capsys, monkeypatch):
        """Test CLI integration with branch detection."""
        test_data_dir = Path(__file__).parent / "test_data"
        test_file = str(test_data_dir / "test_file_clean.py")

        # Mock successful branch detection with ticket
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "feature/MYJIRA-123-test-feature\n"
            mock_run.return_value = mock_result

            with pytest.raises(SystemExit) as exc_info:
                main(["-j", "MYJIRA", test_file])

            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            # Clean file with matching branch should have no output
            assert captured.out == ""

    def test_cli_no_ticket_in_branch(self, capsys):
        """Test CLI with branch that has no ticket ID."""
        test_data_dir = Path(__file__).parent / "test_data"
        test_file = str(test_data_dir / "test_file_clean.py")

        # Mock branch without ticket
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "main\n"
            mock_run.return_value = mock_result

            with pytest.raises(SystemExit) as exc_info:
                main(["-j", "MYJIRA", "-v", test_file])

            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            # Should show informational message about no ticket
            assert "No ticket ID detected in current branch 'main'" in captured.out

    def test_cli_git_detection_failure(self, capsys):
        """Test CLI when git branch detection fails."""
        test_data_dir = Path(__file__).parent / "test_data"
        test_file = str(test_data_dir / "test_file_clean.py")

        # Mock git command failure
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result

            with pytest.raises(SystemExit) as exc_info:
                main(["-j", "MYJIRA", test_file])

            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            # Should show informational message about detection failure
            assert "Note: Unable to detect current git branch" in captured.out

    def test_cli_quiet_mode_no_branch_message(self, capsys):
        """Test that branch detection messages are suppressed in quiet mode."""
        test_data_dir = Path(__file__).parent / "test_data"
        test_file = str(test_data_dir / "test_file_clean.py")

        # Mock branch without ticket
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "develop\n"
            mock_run.return_value = mock_result

            with pytest.raises(SystemExit) as exc_info:
                main(["-j", "MYJIRA", "--quiet", test_file])

            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            # Quiet mode should suppress branch detection messages
            assert captured.out == ""

    def test_no_files_argument(self, capsys, monkeypatch):
        """Test that CLI works when no files are provided."""
        # Mock git ls-files to return test files
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "file1.py\nfile2.js\ntest.md"

        with patch("subprocess.run", return_value=mock_result):
            # This should not raise an error
            with pytest.raises(SystemExit) as exc_info:
                main(["-j", "MYJIRA"])

            # Should exit with 0 since no staged files have violations
            assert exc_info.value.code == 0

    def test_no_files_with_verbose(self, capsys):
        """Test verbose output when no files are provided and --check-unstaged is set."""
        # Mock git ls-files
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "file1.py\nfile2.js"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(SystemExit) as exc_info:
                main(["-j", "MYJIRA", "--verbose", "--check-unstaged"])

            assert exc_info.value.code == 0
            captured = capsys.readouterr()

            # Should indicate no files were provided
            assert (
                "No specific files provided" in captured.out
                or "checking all tracked files" in captured.out
            )

    def test_no_files_no_check_unstaged_warning(self, capsys):
        """Test that warning is shown when no files are provided and --check-unstaged is not set."""
        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()

        # Should show warning about nothing to check
        assert "No files provided" in captured.out
        assert "--check-unstaged" in captured.out
        assert "Nothing to check" in captured.out

    def test_staged_vs_unstaged_differentiation(self, capsys, tmp_path):
        """Test that staged files produce errors while unstaged produce warnings when --check-unstaged is set."""
        # Create test files
        staged_file = tmp_path / "staged.py"
        staged_file.write_text("# TODO: Missing reference in staged file\n")

        unstaged_file = tmp_path / "unstaged.py"
        unstaged_file.write_text("# TODO: Missing in unstaged\n")

        # Mock git ls-files to return additional unstaged files
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = f"{staged_file}\n{unstaged_file}"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(SystemExit) as exc_info:
                main(["-j", "MYJIRA", "--check-unstaged", str(staged_file)])

            # Should fail because staged file has violations
            assert exc_info.value.code == 1
            captured = capsys.readouterr()

            # Check for proper formatting
            assert "ERROR:" in captured.out
            assert "WARNING:" in captured.out

    def test_no_check_unstaged_skips_unstaged_files(self, capsys, tmp_path):
        """Test that without --check-unstaged, only staged files are checked."""
        # Create test files
        staged_file = tmp_path / "staged.py"
        staged_file.write_text("# TODO: Missing reference in staged file\n")

        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA", str(staged_file)])

        # Should fail because staged file has violations
        assert exc_info.value.code == 1
        captured = capsys.readouterr()

        # Should only show ERROR for staged file, no WARNING for unstaged
        assert "ERROR:" in captured.out
        assert "WARNING: Dangling TODOs found in unstaged" not in captured.out
