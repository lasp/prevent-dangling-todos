"""Unit tests for the CLI module."""

from pathlib import Path
import pytest

from prevent_dangling_todos.cli import main, create_parser


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
        assert "--jira-prefix" in captured.out
        assert "--comment-prefix" in captured.out
        assert "--quiet" in captured.out
        assert "Examples:" in captured.out
        assert "multiple Jira project prefixes" in captured.out
        assert "comma-separated" in captured.out
        assert "environment variable" in captured.out

    def test_version_flag(self, capsys):
        """Test --version flag displays version."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "prevent-dangling-todos 0.1.0" in captured.out

    def test_no_arguments_shows_error(self, capsys):
        """Test that running without arguments shows an error."""
        with pytest.raises(SystemExit) as exc_info:
            main([])

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "error: the following arguments are required: FILE" in captured.err

    def test_clean_file_passes(self, capsys):
        """Test that a file with properly referenced TODOs passes."""
        test_file = str(self.test_data_dir / "test_file_clean.py")

        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA", test_file])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "✅ All work comments have proper Jira references" in captured.out

    def test_file_with_violations_fails(self, capsys):
        """Test that a file with violations fails with exit code 1."""
        test_file = str(self.test_data_dir / "test_file_with_violations.py")

        with pytest.raises(SystemExit) as exc_info:
            main(["--jira-prefix", "MYJIRA", test_file])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()

        # Check for violations in output
        assert "❌" in captured.out
        assert "Work comment missing Jira reference" in captured.out
        assert "TODO: This is a violation" in captured.out
        assert "FIXME: Another violation" in captured.out
        assert "💡 Please add Jira issue references" in captured.out

    def test_multiple_jira_prefixes(self, capsys):
        """Test multiple JIRA prefixes in both success and failure cases."""
        # Test 1: Multiple prefixes with all valid references - should pass
        test_file = str(
            self.test_data_dir / "test_file_clean.py"
        )  # All have MYJIRA prefix

        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA,PROJECT,TEAM", test_file])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "✅ All work comments have proper Jira references" in captured.out
        assert "projects MYJIRA, PROJECT, TEAM" in captured.out

        # Test 2: Single prefix with violations - should fail and show prefix in error
        test_file = str(self.test_data_dir / "test_file_with_violations.py")

        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA,PROJECT,TEAM", test_file])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()

        # Should show all prefixes in error message format
        assert "MYJIRA-XXXX|PROJECT-XXXX|TEAM-XXXX" in captured.out
        # Should find violation examples
        assert "TODO: This is a violation" in captured.out
        assert "(Also valid: PROJECT, TEAM)" in captured.out

    def test_comment_prefixes_filter(self, capsys):
        """Test filtering specific comment prefixes."""
        test_file = str(self.test_data_dir / "test_file_single_todo.py")

        # Test checking only TODO comments
        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA", "-c", "TODO", test_file])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()

        # Should find TODO violation but not FIXME violations
        assert "TODO: This TODO has no reference" in captured.out
        assert "Checking for: TODO" in captured.out
        # Should not show FIXME violations since we're only checking TODO
        assert "FIXME: Missing reference FIXME" not in captured.out

    def test_quiet_mode(self, capsys):
        """Test quiet mode only outputs violation lines."""
        test_file = str(self.test_data_dir / "test_file_with_violations.py")

        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA", "--quiet", test_file])

        # Should still exit with code 1 for violations
        assert exc_info.value.code == 1
        captured = capsys.readouterr()

        # Quiet mode should only show violations in simple format
        assert (
            "test_file_with_violations.py:3: # TODO: This is a violation"
            in captured.out
        )
        # Should not have decorative elements
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

        # Should report violations for the file with issues
        assert "test_file_with_violations.py" in captured.out
        assert "Work comment missing Jira reference" in captured.out

    def test_environment_variables(self, capsys, monkeypatch):
        """Test comprehensive environment variable support and parsing."""
        test_file = str(self.test_data_dir / "test_file_clean.py")

        # Test 1: JIRA_PREFIX environment variable with multiple values
        monkeypatch.setenv("JIRA_PREFIX", "MYJIRA,PROJECT")

        with pytest.raises(SystemExit) as exc_info:
            main([test_file])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "projects MYJIRA, PROJECT" in captured.out

        # Test 2: Both JIRA_PREFIX and COMMENT_PREFIX environment variables
        test_file = str(self.test_data_dir / "test_file_single_todo.py")
        monkeypatch.setenv("JIRA_PREFIX", "MYJIRA")
        monkeypatch.setenv("COMMENT_PREFIX", "TODO,XXX")

        with pytest.raises(SystemExit) as exc_info:
            main([test_file])

        assert exc_info.value.code == 1  # Should find TODO violations
        captured = capsys.readouterr()
        assert "Checking for: TODO, XXX" in captured.out

        # Test 3: CLI arguments override environment variables
        test_file = str(self.test_data_dir / "test_file_clean.py")
        monkeypatch.setenv("JIRA_PREFIX", "WRONGPREFIX")
        monkeypatch.setenv("COMMENT_PREFIX", "WRONGCOMMENT")

        with pytest.raises(SystemExit) as exc_info:
            main(["-j", "MYJIRA", "-c", "TODO", test_file])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        # Should use CLI values, not env vars
        assert "projects MYJIRA" in captured.out
        assert "Checking for: TODO" in captured.out

        # Test 4: Comma parsing with whitespace and empty values
        with pytest.raises(SystemExit) as exc_info:
            main(["-j", " MYJIRA,,PROJECT, ", test_file])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        # Should handle whitespace and filter empty values
        assert "projects MYJIRA, PROJECT" in captured.out

    def test_no_jira_prefix_error(self, capsys):
        """Test error when no Jira prefix provided via CLI or env var."""
        test_file = str(self.test_data_dir / "test_file_clean.py")

        with pytest.raises(SystemExit) as exc_info:
            main([test_file])

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "Error: Jira project prefix(es) must be specified" in captured.err
        assert "Examples:" in captured.err
