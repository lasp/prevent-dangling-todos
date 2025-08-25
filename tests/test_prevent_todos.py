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
        # Test 1: Quiet mode with violations
        quiet_checker = TodoChecker(jira_prefixes="MYJIRA", quiet=True)
        exit_code = quiet_checker.check_files([violation_test_file])
        assert exit_code == 1

        captured = capsys.readouterr()
        # In quiet mode, should only show violations in simple format
        assert (
            "test_file_with_violations.py:3: # TODO: This is a violation"
            in captured.out
        )
        # Should not have decorative elements
        assert "🔍" not in captured.out
        assert "❌" not in captured.out
        assert "💡" not in captured.out
        assert "✅" not in captured.out

        # Test 2: Quiet mode with no violations - should output nothing
        quiet_checker.exit_code = 0  # Reset
        exit_code = quiet_checker.check_files([clean_test_file])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert captured.out == ""

        # Test 3: Standard mode with violations
        standard_checker = TodoChecker(jira_prefixes="MYJIRA", quiet=False)
        exit_code = standard_checker.check_files([violation_test_file])
        assert exit_code == 1

        captured = capsys.readouterr()
        # Standard mode should have decorative elements and helpful tips
        assert (
            "🔍 Checking work comments for Jira references to projects" in captured.out
        )
        assert "❌" in captured.out
        assert (
            "💡 Please add Jira issue references to work comments like:" in captured.out
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

        # Test 4: Error message display with multiple prefixes
        test_file = str(test_data_dir / "test_file_with_violations.py")
        exit_code = multi_checker.check_files([test_file])

        assert exit_code == 1
        captured = capsys.readouterr()

        # Should show multiple prefixes in error message format
        assert "ALPHA-XXXX|BETA-XXXX|GAMMA-XXXX" in captured.out
        assert "TODO: This is a violation" in captured.out
