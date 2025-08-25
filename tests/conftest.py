"""Pytest configuration and fixtures for prevent-dangling-todos tests."""

import sys
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def clean_test_file(test_data_dir):
    """Return path to test file with no violations."""
    return str(test_data_dir / "test_file_clean.py")


@pytest.fixture
def violation_test_file(test_data_dir):
    """Return path to test file with violations."""
    return str(test_data_dir / "test_file_with_violations.py")


@pytest.fixture
def single_todo_file(test_data_dir):
    """Return path to test file for testing prefix filtering."""
    return str(test_data_dir / "test_file_single_todo.py")
