"""End-to-end tests for branch-specific TODO tracking feature."""  # noqa: FIX001

import tempfile
from unittest.mock import MagicMock, patch

import pytest

from prevent_dangling_todos.cli import main


class TestEndToEndBranchTodos:
    """Test the complete branch-specific TODO tracking feature."""  # noqa: FIX001

    def test_branch_with_ticket_shows_yellow_warnings(self, capsys):
        """Test that TODOs for current branch ticket show as yellow warnings."""
        # Create a test file with various TODOs
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# TODO: This has no reference\n")  # noqa: FIX001
            f.write("# TODO LIBSDC-123: This is for the current ticket\n")  # noqa: FIX001
            f.write("# FIXME: Another violation\n")
            f.write("# TODO LIBSDC-456: This is for a different ticket\n")  # noqa: FIX001
            f.write("# TODO LIBSDC-123: Another item for current ticket\n")  # noqa: FIX001
            temp_file = f.name

        try:
            # Mock git branch detection to return a branch with LIBSDC-123
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "feature/LIBSDC-123-add-new-feature\n"
                mock_run.return_value = mock_result

                with pytest.raises(SystemExit) as exc_info:
                    main(["-j", "LIBSDC", temp_file])

                assert exc_info.value.code == 1  # Has violations

                captured = capsys.readouterr()

                # Should show violations with red X
                assert "❌" in captured.out
                assert "TODO: This has no reference" in captured.out  # noqa: FIX001
                assert "FIXME: Another violation" in captured.out

                # Should show yellow warnings for current ticket TODOs
                assert (
                    "⚠️  Unresolved TODOs for current branch ticket LIBSDC-123:"
                    in captured.out
                )
                assert "TODO LIBSDC-123: This is for the current ticket" in captured.out  # noqa: FIX001
                assert (
                    "TODO LIBSDC-123: Another item for current ticket" in captured.out  # noqa: FIX001
                )

                # Should NOT show other ticket TODOs in yellow section
                assert "LIBSDC-456" not in captured.out.split("⚠️  Unresolved TODOs")[1]

        finally:
            import os

            os.unlink(temp_file)

    def test_branch_without_ticket_shows_note(self, capsys):
        """Test that branches without tickets show informational note."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# TODO LIBSDC-123: Properly referenced TODO\n")  # noqa: FIX001
            temp_file = f.name

        try:
            # Mock git branch detection to return main branch
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "main\n"
                mock_run.return_value = mock_result

                with pytest.raises(SystemExit) as exc_info:
                    main(["-j", "LIBSDC", temp_file])

                assert exc_info.value.code == 0  # No violations

                captured = capsys.readouterr()

                # Should show note about no ticket in branch
                assert (
                    "Note: No ticket ID detected in current branch 'main'"
                    in captured.out
                )

                # Should not show any yellow warnings
                assert (
                    "⚠️  Unresolved TODOs for current branch ticket" not in captured.out
                )

        finally:
            import os

            os.unlink(temp_file)

    def test_git_detection_failure_shows_note(self, capsys):
        """Test that git detection failures show informational note."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# TODO LIBSDC-123: Properly referenced TODO\n")  # noqa: FIX001
            temp_file = f.name

        try:
            # Mock git command failure
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 1
                mock_run.return_value = mock_result

                with pytest.raises(SystemExit) as exc_info:
                    main(["-j", "LIBSDC", temp_file])

                assert exc_info.value.code == 0  # No violations

                captured = capsys.readouterr()

                # Should show note about detection failure
                assert "Note: Unable to detect current git branch" in captured.out

                # Should not show any yellow warnings
                assert (
                    "⚠️  Unresolved TODOs for current branch ticket" not in captured.out
                )

        finally:
            import os

            os.unlink(temp_file)

    def test_quiet_mode_suppresses_all_branch_output(self, capsys):
        """Test that quiet mode suppresses branch detection messages and ticket TODOs."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# TODO: This has no reference\n")  # noqa: FIX001
            f.write("# TODO LIBSDC-123: This is for the current ticket\n")  # noqa: FIX001
            temp_file = f.name

        try:
            # Mock git branch detection
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "feature/LIBSDC-123-test\n"
                mock_run.return_value = mock_result

                with pytest.raises(SystemExit) as exc_info:
                    main(["-j", "LIBSDC", "--quiet", temp_file])

                assert exc_info.value.code == 1  # Has violations

                captured = capsys.readouterr()

                # Quiet mode should suppress everything
                assert captured.out == ""

        finally:
            import os

            os.unlink(temp_file)

    def test_verbose_mode_with_ticket_todos(self, capsys):
        """Test verbose mode shows all information including ticket TODOs."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# TODO LIBSDC-123: This is for the current ticket\n")  # noqa: FIX001
            temp_file = f.name

        try:
            # Mock git branch detection
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "feature/LIBSDC-123-test\n"
                mock_run.return_value = mock_result

                with pytest.raises(SystemExit) as exc_info:
                    main(["-j", "LIBSDC", "--verbose", temp_file])

                assert exc_info.value.code == 0  # No violations

                captured = capsys.readouterr()

                # Should show config info
                assert "🔍 Checking work comments for ticket references" in captured.out

                # Should show yellow warnings for ticket TODOs
                assert (
                    "⚠️  Unresolved TODOs for current branch ticket LIBSDC-123:"
                    in captured.out
                )

                # Should show file status
                assert f"✅ {temp_file}" in captured.out

        finally:
            import os

            os.unlink(temp_file)

    def test_multiple_jira_prefixes_with_branch_detection(self, capsys):
        """Test branch detection works with multiple Jira prefixes."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# TODO PROJECT-456: This is for the current ticket\n")  # noqa: FIX001
            f.write("# TODO TEAM-789: This is for a different project\n")  # noqa: FIX001
            temp_file = f.name

        try:
            # Mock git branch with PROJECT prefix
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "bugfix/PROJECT-456-fix-issue\n"
                mock_run.return_value = mock_result

                with pytest.raises(SystemExit) as exc_info:
                    main(["-j", "LIBSDC,PROJECT,TEAM", temp_file])

                assert exc_info.value.code == 0  # No violations

                captured = capsys.readouterr()

                # Should show yellow warnings only for PROJECT-456
                assert (
                    "⚠️  Unresolved TODOs for current branch ticket PROJECT-456:"
                    in captured.out
                )
                assert (
                    "TODO PROJECT-456: This is for the current ticket" in captured.out  # noqa: FIX001
                )

                # Should not show TEAM-789 in yellow warnings
                yellow_section = (
                    captured.out.split("⚠️  Unresolved TODOs")[1]
                    if "⚠️  Unresolved TODOs" in captured.out
                    else ""
                )
                assert "TEAM-789" not in yellow_section

        finally:
            import os

            os.unlink(temp_file)

    def test_succeed_always_with_ticket_todos(self, capsys):
        """Test that --succeed-always works with ticket TODOs."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# TODO: No reference\n")  # noqa: FIX001
            f.write("# TODO LIBSDC-123: Current ticket\n")  # noqa: FIX001
            temp_file = f.name

        try:
            # Mock git branch detection
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "feature/LIBSDC-123-test\n"
                mock_run.return_value = mock_result

                with pytest.raises(SystemExit) as exc_info:
                    main(["-j", "LIBSDC", "--succeed-always", temp_file])

                assert exc_info.value.code == 0  # succeed-always forces exit 0

                captured = capsys.readouterr()

                # Should still show violations
                assert "❌" in captured.out
                assert "TODO: No reference" in captured.out  # noqa: FIX001

                # Should show ticket TODOs
                assert (
                    "⚠️  Unresolved TODOs for current branch ticket LIBSDC-123:"
                    in captured.out
                )

        finally:
            import os

            os.unlink(temp_file)
