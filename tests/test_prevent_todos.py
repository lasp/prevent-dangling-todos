"""Unit tests for the prevent_todos module."""

from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from prevent_dangling_todos.prevent_todos import TodoChecker


class TestTodoChecker:
    """Test the TodoChecker class."""

    @pytest.fixture
    def checker(self):
        """Create a TodoChecker instance."""
        return TodoChecker(jira_prefixes="MYJIRA")

    def test_initialization(self, checker):
        """Test TodoChecker initialization."""
        assert checker.jira_prefixes == ["MYJIRA"]
        assert checker.quiet is False
        assert checker.exit_code == 0
        assert "TODO" in checker.comment_prefixes
        assert "FIXME" in checker.comment_prefixes

    def test_pattern_building(self, checker):
        """Test comprehensive regex pattern building and matching."""
        # Test comment pattern matching
        assert checker.comment_pattern.search("TODO: test")
        assert checker.comment_pattern.search("FIXME: test")
        assert checker.comment_pattern.search("XXX: test")

        # Test case sensitive comment matching
        assert not checker.comment_pattern.search("todo: lowercase")
        assert checker.comment_pattern.search("TODO: uppercase")
        assert not checker.comment_pattern.search("ToDo: mixed case")

        # Test JIRA pattern matching with case sensitivity
        assert checker.jira_pattern.search("MYJIRA-123")
        assert not checker.jira_pattern.search("myjira-456")
        assert not checker.jira_pattern.search("MyJira-789")

        # Test pattern specificity - should not match other prefixes
        assert not checker.jira_pattern.search("PROJECT-123")
        assert not checker.jira_pattern.search("WRONG-123")

        # Test with custom checker for different prefix
        custom_checker = TodoChecker(jira_prefixes="PROJECT")
        assert custom_checker.jira_pattern.search("PROJECT-123")
        assert not custom_checker.jira_pattern.search("project-456")
        assert not custom_checker.jira_pattern.search("MYJIRA-123")

    def test_file_checking(self, checker, clean_test_file, violation_test_file):
        """Test comprehensive file checking functionality."""
        # Test 1: Clean file with no violations
        violations = checker.check_file(clean_test_file)
        assert len(violations) == 0

        # Test 2: File with violations
        violations = checker.check_file(violation_test_file)
        assert len(violations) > 0

        # Verify specific violations and line-by-line processing
        violation_lines = [v[0] for v in violations]
        violation_contents = [v[1] for v in violations]

        # Check specific violation content
        assert 3 in violation_lines  # Line with "TODO: This is a violation"
        assert any(
            "TODO: This is a violation" in content for content in violation_contents
        )
        assert any(
            "FIXME: Another violation" in content for content in violation_contents
        )

        # Test line-by-line processing format
        for line_num, line_content in violations:
            assert isinstance(line_num, int)
            assert line_num > 0
            assert isinstance(line_content, str)
            assert len(line_content) > 0

        # Test multiple violation types are caught
        assert len(violations) >= 5  # Based on test file content
        violation_texts = [v[1] for v in violations]
        assert any("TODO:" in text for text in violation_texts)
        assert any("FIXME:" in text for text in violation_texts)
        assert any("XXX:" in text for text in violation_texts)

        # Test 3: Nonexistent file handling
        violations = checker.check_file("nonexistent_file.py")
        assert len(violations) == 0

    def test_check_files_exit_code(self, checker, clean_test_file, violation_test_file):
        """Test check_files method returns correct exit codes."""
        # Clean file should return 0
        exit_code = checker.check_files([clean_test_file])
        assert exit_code == 0

        # Reset checker for next test
        checker.exit_code = 0

        # File with violations should return 1
        exit_code = checker.check_files([violation_test_file])
        assert exit_code == 1

    def test_custom_comment_prefixes(self):
        """Test TodoChecker with custom comment prefixes."""
        checker = TodoChecker(jira_prefixes="TEST", comment_prefixes=["TODO", "CUSTOM"])

        # Should match custom prefixes
        assert checker.comment_pattern.search("TODO: test")
        assert checker.comment_pattern.search("CUSTOM: test")

        # Should not match excluded prefixes
        assert not checker.comment_pattern.search("FIXME: test")
        assert not checker.comment_pattern.search("HACK: test")

    def test_quiet_vs_standard_modes(
        self, clean_test_file, violation_test_file, capsys
    ):
        """Test output differences between quiet and standard modes."""
        # Test 1: Quiet mode with violations - should have no output
        quiet_checker = TodoChecker(jira_prefixes="MYJIRA", quiet=True)
        exit_code = quiet_checker.check_files([violation_test_file])
        assert exit_code == 1

        captured = capsys.readouterr()
        # In quiet mode, should have no output at all
        assert captured.out == ""

        # Test 2: Quiet mode with no violations - should output nothing
        quiet_checker.exit_code = 0  # Reset
        exit_code = quiet_checker.check_files([clean_test_file])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert captured.out == ""

        # Test 3: Standard mode with violations - only show violations with red X
        standard_checker = TodoChecker(jira_prefixes="MYJIRA", quiet=False)
        exit_code = standard_checker.check_files([violation_test_file])
        assert exit_code == 1

        captured = capsys.readouterr()
        # Standard mode should only show violations with red X
        assert "❌" in captured.out
        assert "TODO: This is a violation" in captured.out
        # Should not show config info or help text in standard mode
        assert (
            "🔍 Checking work comments for Jira references to projects"
            not in captured.out
        )
        assert (
            "💡 Please add Jira issue references to work comments like:"
            not in captured.out
        )

    def test_multiple_jira_prefixes(self, test_data_dir, capsys):
        """Test comprehensive multiple JIRA prefix functionality."""
        # Test 1: Initialization with multiple prefixes
        checker = TodoChecker(jira_prefixes=["MYJIRA", "PROJECT", "TEAM"])
        assert checker.jira_prefixes == ["MYJIRA", "PROJECT", "TEAM"]

        # Test with string input (backward compatibility)
        single_checker = TodoChecker(jira_prefixes="SINGLE")
        assert single_checker.jira_prefixes == ["SINGLE"]

        # Test 2: Pattern matching with multiple prefixes
        multi_checker = TodoChecker(jira_prefixes=["ALPHA", "BETA", "GAMMA"])

        # Should match any of the prefixes (case sensitive)
        assert multi_checker.jira_pattern.search("ALPHA-123")
        assert multi_checker.jira_pattern.search("BETA-456")
        assert multi_checker.jira_pattern.search("GAMMA-789")
        assert not multi_checker.jira_pattern.search("alpha-123")  # Case sensitive

        # Should not match other prefixes
        assert not multi_checker.jira_pattern.search("DELTA-123")
        assert not multi_checker.jira_pattern.search("MYJIRA-456")

        # Test 3: File checking with multiple prefixes
        # Clean file with MYJIRA references should pass
        test_file = str(test_data_dir / "test_file_clean.py")
        violations = checker.check_file(test_file)
        assert len(violations) == 0  # All have MYJIRA prefix

        # File with violations should fail
        test_file = str(test_data_dir / "test_file_with_violations.py")
        violations = checker.check_file(test_file)
        assert len(violations) > 0  # Has violations without prefixes

        violation_contents = [v[1] for v in violations]
        assert any(
            "TODO: This is a violation" in content for content in violation_contents
        )
        assert any(
            "FIXME: Another violation" in content for content in violation_contents
        )

        # Test 4: Standard mode output with violations
        test_file = str(test_data_dir / "test_file_with_violations.py")
        exit_code = multi_checker.check_files([test_file])

        assert exit_code == 1
        captured = capsys.readouterr()

        # Standard mode should only show violations with red X
        assert "❌" in captured.out
        assert "TODO: This is a violation" in captured.out
        # Should not show config info or help text in standard mode
        assert "ALPHA-XXXX|BETA-XXXX|GAMMA-XXXX" not in captured.out

    def test_succeed_always_initialization(self):
        """Test TodoChecker initialization with succeed_always parameter."""
        # Test default behavior (succeed_always=False)
        checker = TodoChecker(jira_prefixes="MYJIRA")
        assert checker.succeed_always is False

        # Test explicit succeed_always=True
        checker = TodoChecker(jira_prefixes="MYJIRA", succeed_always=True)
        assert checker.succeed_always is True

        # Test with other parameters
        checker = TodoChecker(
            jira_prefixes=["MYJIRA", "PROJECT"],
            comment_prefixes=["TODO", "FIXME"],
            quiet=True,
            succeed_always=True,
        )
        assert checker.succeed_always is True
        assert checker.quiet is True
        assert checker.jira_prefixes == ["MYJIRA", "PROJECT"]

    def test_succeed_always_exit_code_behavior(self, test_data_dir, capsys):
        """Test exit code behavior with succeed_always flag."""
        test_file = str(test_data_dir / "test_file_with_violations.py")

        # Test 1: Normal behavior - should return 1 for violations
        checker = TodoChecker(jira_prefixes="MYJIRA", succeed_always=False)
        exit_code = checker.check_files([test_file])
        assert exit_code == 1
        assert checker.exit_code == 1  # Internal state should also be 1

        # Test 2: succeed_always=True - should return 0 despite violations
        checker_succeed = TodoChecker(jira_prefixes="MYJIRA", succeed_always=True)
        exit_code = checker_succeed.check_files([test_file])
        assert exit_code == 0  # Should return 0 due to succeed_always
        assert (
            checker_succeed.exit_code == 1
        )  # Internal state should still track violations

        captured = capsys.readouterr()
        # Should still show violations in output (standard mode)
        assert "❌" in captured.out
        assert "TODO: This is a violation" in captured.out

        # Test 3: Clean file with succeed_always - should return 0
        clean_file = str(test_data_dir / "test_file_clean.py")
        checker_succeed.exit_code = 0  # Reset
        exit_code = checker_succeed.check_files([clean_file])
        assert exit_code == 0
        assert checker_succeed.exit_code == 0

    def test_succeed_always_with_quiet_mode(self, test_data_dir, capsys):
        """Test succeed_always behavior combined with quiet mode."""
        test_file = str(test_data_dir / "test_file_with_violations.py")

        checker = TodoChecker(jira_prefixes="MYJIRA", quiet=True, succeed_always=True)
        exit_code = checker.check_files([test_file])

        assert exit_code == 0  # Should return 0 due to succeed_always
        captured = capsys.readouterr()

        # Quiet mode should have no output at all
        assert captured.out == ""

    def test_succeed_always_preserves_logging_behavior(self, test_data_dir, capsys):
        """Test that succeed_always doesn't change violation detection or logging."""
        test_file = str(test_data_dir / "test_file_with_violations.py")

        # Compare output between normal and succeed_always modes
        checker_normal = TodoChecker(jira_prefixes="MYJIRA", succeed_always=False)
        exit_code_normal = checker_normal.check_files([test_file])
        output_normal = capsys.readouterr()

        checker_succeed = TodoChecker(jira_prefixes="MYJIRA", succeed_always=True)
        exit_code_succeed = checker_succeed.check_files([test_file])
        output_succeed = capsys.readouterr()

        # Exit codes should differ
        assert exit_code_normal == 1
        assert exit_code_succeed == 0

        # But output should be identical (same logging behavior)
        assert output_normal.out == output_succeed.out
        assert output_normal.err == output_succeed.err

        # Both should have detected the same violations internally
        assert checker_normal.exit_code == checker_succeed.exit_code == 1


class TestTicketTodoTracking:
    """Test tracking of TODOs for the current branch ticket."""

    @pytest.fixture
    def test_data_dir(self):
        """Get test data directory."""
        return Path(__file__).parent / "test_data"

    def test_current_ticket_id_initialization(self):
        """Test TodoChecker initialization with current_ticket_id."""
        # Test without current_ticket_id
        checker = TodoChecker(jira_prefixes="MYJIRA")
        assert checker.current_ticket_id is None
        assert checker.ticket_todos == []

        # Test with current_ticket_id
        checker = TodoChecker(jira_prefixes="MYJIRA", current_ticket_id="MYJIRA-123")
        assert checker.current_ticket_id == "MYJIRA-123"
        assert checker.ticket_todos == []

    def test_ticket_todo_tracking(self, test_data_dir):
        """Test that TODOs matching current ticket are tracked separately."""
        # Create checker with current ticket ID that exists in the file
        checker = TodoChecker(jira_prefixes="MYJIRA", current_ticket_id="MYJIRA-100")

        # Check a file that has TODOs with MYJIRA-100
        test_file = str(test_data_dir / "test_file_clean.py")
        violations = checker.check_file(test_file)

        # Should have no violations (all TODOs have references)
        assert len(violations) == 0

        # Should have tracked the MYJIRA-100 TODOs
        assert len(checker.ticket_todos) == 1
        assert any("MYJIRA-100" in todo[2] for todo in checker.ticket_todos)

    def test_ticket_todo_output(self, test_data_dir, capsys):
        """Test yellow warning output for ticket-specific TODOs."""
        # Create checker with current ticket ID
        checker = TodoChecker(
            jira_prefixes="MYJIRA",
            current_ticket_id="MYJIRA-100",
            quiet=False,
        )

        test_file = str(test_data_dir / "test_file_clean.py")
        exit_code = checker.check_files([test_file])

        assert exit_code == 0  # No violations
        captured = capsys.readouterr()

        # Should show yellow warning for ticket TODOs
        assert (
            "⚠️  Unresolved TODOs for current branch ticket MYJIRA-100:" in captured.out
        )
        assert "⚠️" in captured.out
        assert "MYJIRA-100" in captured.out

    def test_no_ticket_todos_no_output(self, test_data_dir, capsys):
        """Test no output when there are no TODOs for current ticket."""
        # Create checker with a ticket ID that doesn't appear in the file
        checker = TodoChecker(
            jira_prefixes="MYJIRA",
            current_ticket_id="MYJIRA-999",
            quiet=False,
        )

        test_file = str(test_data_dir / "test_file_clean.py")
        exit_code = checker.check_files([test_file])

        assert exit_code == 0
        captured = capsys.readouterr()

        # Should not show ticket TODO section if none found
        assert "⚠️  Unresolved TODOs for current branch ticket" not in captured.out

    def test_ticket_todos_quiet_mode(self, test_data_dir, capsys):
        """Test that ticket TODOs are suppressed in quiet mode."""
        checker = TodoChecker(
            jira_prefixes="MYJIRA",
            current_ticket_id="MYJIRA-100",
            quiet=True,
        )

        test_file = str(test_data_dir / "test_file_clean.py")
        exit_code = checker.check_files([test_file])

        assert exit_code == 0
        captured = capsys.readouterr()

        # Quiet mode should suppress all output
        assert captured.out == ""

    def test_ticket_todos_with_violations(self, test_data_dir, capsys):
        """Test ticket TODOs shown along with violations."""
        # Create a test file with both violations and ticket TODOs
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# TODO: This has no reference\n")
            f.write("# TODO MYJIRA-123: This is for the current ticket\n")
            f.write("# FIXME: Another violation\n")
            f.write("# TODO MYJIRA-456: This is for a different ticket\n")
            temp_file = f.name

        try:
            checker = TodoChecker(
                jira_prefixes="MYJIRA",
                current_ticket_id="MYJIRA-123",
            )

            exit_code = checker.check_files([temp_file])
            assert exit_code == 1  # Has violations

            captured = capsys.readouterr()

            # Should show violations with red X
            assert "❌" in captured.out
            assert "TODO: This has no reference" in captured.out
            assert "FIXME: Another violation" in captured.out

            # Should also show ticket TODOs with yellow warning
            assert (
                "⚠️  Unresolved TODOs for current branch ticket MYJIRA-123:"
                in captured.out
            )
            assert "TODO MYJIRA-123: This is for the current ticket" in captured.out

            # Should not show TODOs for other tickets in the yellow section
            assert (
                "TODO MYJIRA-456" not in captured.out.split("⚠️  Unresolved TODOs")[1]
                if "⚠️  Unresolved TODOs" in captured.out
                else True
            )

        finally:
            import os

            os.unlink(temp_file)

    def test_ticket_todos_do_not_affect_exit_code(self, test_data_dir):
        """Test that ticket TODOs don't cause exit code failures."""
        checker = TodoChecker(
            jira_prefixes="MYJIRA",
            current_ticket_id="MYJIRA-100",
        )

        test_file = str(test_data_dir / "test_file_clean.py")
        exit_code = checker.check_files([test_file])

        # Should succeed even though there are TODOs for the current ticket
        assert exit_code == 0
        assert len(checker.ticket_todos) > 0  # Should have found ticket TODOs

    def test_without_current_ticket_id(self, test_data_dir, capsys):
        """Test behavior when no current_ticket_id is provided."""
        checker = TodoChecker(
            jira_prefixes="MYJIRA",
            current_ticket_id=None,  # No current ticket
        )

        test_file = str(test_data_dir / "test_file_clean.py")
        exit_code = checker.check_files([test_file])

        assert exit_code == 0
        captured = capsys.readouterr()

        # Should not track or show any ticket TODOs
        assert len(checker.ticket_todos) == 0
        assert "⚠️  Unresolved TODOs for current branch ticket" not in captured.out

    def test_find_todos_with_grep(self, tmp_path):
        """Test grep-based TODO detection."""
        checker = TodoChecker(jira_prefixes="TEST", quiet=True)

        # Create test files
        file1 = tmp_path / "file1.py"
        file1.write_text("# TODO: Missing reference\n# TODO TEST-123: Valid\n")

        file2 = tmp_path / "file2.py"
        file2.write_text("# FIXME: Another missing\nprint('hello')\n")

        # Test grep functionality
        results = checker.find_todos_with_grep([str(file1), str(file2)])

        # Should find violations in both files
        assert str(file1) in results
        assert str(file2) in results

        # Check specific violations
        file1_violations = results[str(file1)]
        assert any("TODO: Missing reference" in v[1] for v in file1_violations)
        # Should not include the valid TODO
        assert not any("TODO TEST-123" in v[1] for v in file1_violations)

        file2_violations = results[str(file2)]
        assert any("FIXME: Another missing" in v[1] for v in file2_violations)

    def test_get_all_repo_files(self):
        """Test repository file discovery."""
        checker = TodoChecker(jira_prefixes="TEST", quiet=True)

        # Mock subprocess.run for git ls-files
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "file1.py\nfile2.js\nREADME.md\ntest.png\ntests/test_file.py"
        )

        with patch("subprocess.run", return_value=mock_result):
            files = checker.get_all_repo_files()

            # Should include source files
            assert "file1.py" in files
            assert "file2.js" in files

            # Should exclude README, images, and test files
            assert "README.md" not in files
            assert "test.png" not in files
            assert "tests/test_file.py" not in files

    def test_check_files_with_no_files_provided(self, capsys):
        """Test check_files when no files are provided (None)."""
        checker = TodoChecker(jira_prefixes="TEST", quiet=False)

        # Mock get_all_repo_files
        with patch.object(
            checker, "get_all_repo_files", return_value=["file1.py", "file2.py"]
        ):
            with patch.object(checker, "check_file", return_value=[]):
                exit_code = checker.check_files(None)

                # Should succeed with no violations
                assert exit_code == 0

    def test_staged_vs_unstaged_output(self, tmp_path, capsys):
        """Test that staged and unstaged violations are displayed differently."""
        checker = TodoChecker(jira_prefixes="TEST", quiet=False)

        # Create test files
        staged_file = tmp_path / "staged.py"
        staged_file.write_text("# TODO: Staged violation\n")

        unstaged_file = tmp_path / "unstaged.py"
        unstaged_file.write_text("# FIXME: Unstaged violation\n")

        # Mock get_all_repo_files to return both files
        with patch.object(
            checker,
            "get_all_repo_files",
            return_value=[str(staged_file), str(unstaged_file)],
        ):
            # Pass only staged file as argument
            exit_code = checker.check_files([str(staged_file)])

            # Should fail because staged file has violations
            assert exit_code == 1

            captured = capsys.readouterr()
            # Check for different output formats
            assert "ERROR:" in captured.out
            assert "WARNING:" in captured.out
            assert "Staged violation" in captured.out
            assert "Unstaged violation" in captured.out
