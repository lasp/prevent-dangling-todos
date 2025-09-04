"""Unit tests for the prevent_todos module."""

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

        # Test case insensitive comment matching
        assert checker.comment_pattern.search("todo: lowercase")
        assert checker.comment_pattern.search("TODO: uppercase")
        assert checker.comment_pattern.search("ToDo: mixed case")

        # Test JIRA pattern matching with case insensitivity
        assert checker.jira_pattern.search("MYJIRA-123")
        assert checker.jira_pattern.search("myjira-456")
        assert checker.jira_pattern.search("MyJira-789")

        # Test pattern specificity - should not match other prefixes
        assert not checker.jira_pattern.search("PROJECT-123")
        assert not checker.jira_pattern.search("WRONG-123")

        # Test with custom checker for different prefix
        custom_checker = TodoChecker(jira_prefixes="PROJECT")
        assert custom_checker.jira_pattern.search("PROJECT-123")
        assert custom_checker.jira_pattern.search("project-456")
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
        assert "🔍 Checking work comments for Jira references to projects" not in captured.out
        assert "💡 Please add Jira issue references to work comments like:" not in captured.out

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

        # Should match any of the prefixes
        assert multi_checker.jira_pattern.search("ALPHA-123")
        assert multi_checker.jira_pattern.search("BETA-456")
        assert multi_checker.jira_pattern.search("GAMMA-789")
        assert multi_checker.jira_pattern.search("alpha-123")  # Case insensitive

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
        assert checker_succeed.exit_code == 1  # Internal state should still track violations

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

        checker = TodoChecker(
            jira_prefixes="MYJIRA", 
            quiet=True, 
            succeed_always=True
        )
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
