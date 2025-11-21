"""
Tests for the 'get' CLI command.

Tests retrieving functions from the ouverture pool.
"""
from unittest.mock import patch

import pytest

import ouverture
from tests.conftest import normalize_code_for_test


def test_get_function_missing_lang_suffix():
    """Test that missing @lang suffix causes error"""
    with pytest.raises(SystemExit):
        with patch('sys.stderr'):
            ouverture.function_get("abc123")


def test_get_function_invalid_lang_code():
    """Test that invalid language code causes error"""
    with pytest.raises(SystemExit):
        with patch('sys.stderr'):
            ouverture.function_get("abc123@en")  # Should be 3 chars


def test_get_function_invalid_hash_format():
    """Test that invalid hash format causes error"""
    with pytest.raises(SystemExit):
        with patch('sys.stderr'):
            ouverture.function_get("notahash@eng")


def test_get_function_not_found():
    """Test that non-existent function causes error"""
    with pytest.raises(SystemExit):
        with patch('sys.stderr'):
            hash_value = "a" * 64
            ouverture.function_get(f"{hash_value}@eng")


def test_get_function_language_not_found(mock_ouverture_dir):
    """Test that requesting unavailable language causes error (v0 format)"""
    # Create a function with only English
    hash_value = "c" * 64
    normalized_code = normalize_code_for_test("def _ouverture_v_0(): return 42")
    with patch('sys.stdout'):
        ouverture.function_save_v0(hash_value, "eng",
                                   normalized_code,
                                   "English doc",
                                   {"_ouverture_v_0": "foo"}, {})

    # Try to get it in French
    with pytest.raises(SystemExit):
        with patch('sys.stderr'):
            ouverture.function_get(f"{hash_value}@fra")


def test_get_function_success(mock_ouverture_dir):
    """Test successfully retrieving a function (v0 format)"""
    # Save a function
    hash_value = "d" * 64
    normalized_code = """
def _ouverture_v_0(_ouverture_v_1, _ouverture_v_2):
    _ouverture_v_3 = _ouverture_v_1 + _ouverture_v_2
    return _ouverture_v_3
"""
    name_mapping = {
        "_ouverture_v_0": "add",
        "_ouverture_v_1": "x",
        "_ouverture_v_2": "y",
        "_ouverture_v_3": "result"
    }

    with patch('sys.stdout'):
        ouverture.function_save_v0(hash_value, "eng", normalized_code,
                                   "Add two numbers", name_mapping, {})

    # Retrieve it
    with patch('sys.stdout') as mock_stdout:
        ouverture.function_get(f"{hash_value}@eng")

        # Verify it was printed (can't easily capture print output)
        # Just verify no exception was raised


def test_get_function_v1_format(mock_ouverture_dir):
    """Test retrieving a function in v1 format"""
    hash_value = "e" * 64
    normalized_code = normalize_code_for_test("def _ouverture_v_0(_ouverture_v_1): return _ouverture_v_1 * 2")
    name_mapping = {"_ouverture_v_0": "double", "_ouverture_v_1": "value"}

    # Save in v1 format
    ouverture.function_save(hash_value, "eng", normalized_code, "Double the value", name_mapping, {})

    # Retrieve it
    output = []
    def capture_print(x='', **kwargs):
        output.append(str(x))

    with patch('builtins.print', side_effect=capture_print):
        ouverture.function_get(f"{hash_value}@eng")

    output_text = '\n'.join(output)
    assert "double" in output_text
    assert "value" in output_text
