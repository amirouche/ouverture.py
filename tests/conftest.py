"""
Shared pytest fixtures for ouverture tests.

This module provides common fixtures used across all test modules.
"""
import ast
import sys
from pathlib import Path

import pytest

# Add parent directory to path so we can import ouverture
sys.path.insert(0, str(Path(__file__).parent.parent))

import ouverture

# Export normalize_code_for_test for use in test modules
__all__ = ['normalize_code_for_test', 'mock_ouverture_dir', 'sample_function_code',
           'sample_function_file', 'sample_async_function_code', 'sample_async_function_file']


def normalize_code_for_test(code: str) -> str:
    """
    Normalize code string to match ast.unparse() output format.

    All normalized code strings in tests MUST go through this function to ensure
    they match the format that ouverture produces. This is because ast.unparse()
    always outputs code with proper line breaks and indentation, regardless of
    the input format.

    The function:
    1. Parses code into AST
    2. Clears all line/column information recursively (using ouverture.ast_clear_locations)
    3. Fixes missing locations
    4. Unparses back to string

    Example:
        # Wrong - this format never exists in practice:
        normalized_code = "def _ouverture_v_0(): return 42"

        # Correct - use this helper:
        normalized_code = normalize_code_for_test("def _ouverture_v_0(): return 42")
        # Returns: "def _ouverture_v_0():\\n    return 42"
    """
    tree = ast.parse(code)
    ouverture.ast_clear_locations(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


@pytest.fixture
def mock_ouverture_dir(tmp_path, monkeypatch):
    """
    Fixture to monkey patch directory_get_ouverture to return a temp directory.
    This ensures tests work with pytest-xdist (parallel test runner).
    """
    def _get_temp_ouverture_dir():
        return tmp_path / '.ouverture'

    monkeypatch.setattr(ouverture, 'directory_get_ouverture', _get_temp_ouverture_dir)
    return tmp_path


@pytest.fixture
def sample_function_code():
    """Sample function code for testing."""
    return '''def calculate_sum(first, second):
    """Add two numbers"""
    result = first + second
    return result'''


@pytest.fixture
def sample_function_file(tmp_path, sample_function_code):
    """Create a temporary file with sample function code."""
    test_file = tmp_path / "sample.py"
    test_file.write_text(sample_function_code, encoding='utf-8')
    return test_file


@pytest.fixture
def sample_async_function_code():
    """Sample async function code for testing."""
    return '''async def fetch_data(url):
    """Fetch data from URL"""
    response = await http_get(url)
    return response'''


@pytest.fixture
def sample_async_function_file(tmp_path, sample_async_function_code):
    """Create a temporary file with sample async function code."""
    test_file = tmp_path / "async_sample.py"
    test_file.write_text(sample_async_function_code, encoding='utf-8')
    return test_file
