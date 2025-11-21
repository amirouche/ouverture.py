"""
Tests for the 'show' CLI command.

Tests displaying functions from the ouverture pool with mapping exploration.
"""
from unittest.mock import patch

import pytest

import ouverture
from tests.conftest import normalize_code_for_test


def test_function_show_single_mapping(mock_ouverture_dir):
    """Test show command with single mapping - should output code directly"""
    func_hash = "a0001000" + "0" * 56
    lang = "eng"
    normalized_code = normalize_code_for_test("def _ouverture_v_0(): return 42")
    docstring = "Return 42"
    name_mapping = {"_ouverture_v_0": "answer"}
    alias_mapping = {}

    # Create function with single mapping
    ouverture.function_save(func_hash, lang, normalized_code, docstring, name_mapping, alias_mapping)

    # Capture output
    output = []
    def capture_print(x='', **kwargs):
        output.append(str(x))

    with patch('builtins.print', side_effect=capture_print):
        ouverture.function_show(f"{func_hash}@{lang}")

    # Should output the denormalized code directly
    output_text = '\n'.join(output)
    assert 'def answer():' in output_text
    assert 'Return 42' in output_text


def test_function_show_multiple_mappings_menu(mock_ouverture_dir):
    """Test show command with multiple mappings - should show selection menu"""
    func_hash = "a0002000" + "0" * 56
    lang = "eng"
    normalized_code = normalize_code_for_test("def _ouverture_v_0(): return 100")

    # Create function with two mappings
    ouverture.function_save_v1(func_hash, normalized_code, ouverture.metadata_create())
    hash1 = ouverture.mapping_save_v1(func_hash, lang, "Formal doc", {"_ouverture_v_0": "formal_name"}, {}, "Formal variant")
    hash2 = ouverture.mapping_save_v1(func_hash, lang, "Casual doc", {"_ouverture_v_0": "casual_name"}, {}, "Casual variant")

    # Capture output
    output = []
    def capture_print(x='', **kwargs):
        output.append(str(x))

    with patch('builtins.print', side_effect=capture_print):
        ouverture.function_show(f"{func_hash}@{lang}")

    output_text = '\n'.join(output)

    # Should show selection menu
    assert "Multiple mappings found" in output_text
    assert "Formal variant" in output_text
    assert "Casual variant" in output_text
    assert f"show {func_hash}@{lang}@" in output_text


def test_function_show_explicit_mapping_hash(mock_ouverture_dir):
    """Test show command with explicit mapping hash"""
    func_hash = "a0003000" + "0" * 56
    lang = "eng"
    normalized_code = normalize_code_for_test("def _ouverture_v_0(_ouverture_v_1): return _ouverture_v_1")

    # Create function with two mappings
    ouverture.function_save_v1(func_hash, normalized_code, ouverture.metadata_create())
    hash1 = ouverture.mapping_save_v1(func_hash, lang, "First", {"_ouverture_v_0": "first", "_ouverture_v_1": "x"}, {}, "First variant")
    hash2 = ouverture.mapping_save_v1(func_hash, lang, "Second", {"_ouverture_v_0": "second", "_ouverture_v_1": "y"}, {}, "Second variant")

    # Capture output for explicit mapping
    output = []
    def capture_print(x='', **kwargs):
        output.append(str(x))

    with patch('builtins.print', side_effect=capture_print):
        ouverture.function_show(f"{func_hash}@{lang}@{hash2}")

    output_text = '\n'.join(output)

    # Should output the second mapping's code
    assert 'def second(y):' in output_text
    assert 'Second' in output_text
    assert 'def first(x):' not in output_text


def test_function_show_v0_backward_compatibility(mock_ouverture_dir):
    """Test show command works with v0 functions"""
    func_hash = "a0004000" + "0" * 56
    lang = "eng"
    normalized_code = normalize_code_for_test("def _ouverture_v_0(): return 77")
    docstring = "Return 77"
    name_mapping = {"_ouverture_v_0": "seventy_seven"}
    alias_mapping = {}

    # Create v0 function
    ouverture.function_save_v0(func_hash, lang, normalized_code, docstring, name_mapping, alias_mapping)

    # Capture output
    output = []
    def capture_print(x='', **kwargs):
        output.append(str(x))

    with patch('builtins.print', side_effect=capture_print):
        ouverture.function_show(f"{func_hash}@{lang}")

    output_text = '\n'.join(output)

    # Should output the code (v0 has only one mapping per language)
    assert 'def seventy_seven():' in output_text
    assert 'Return 77' in output_text


def test_function_show_invalid_format(mock_ouverture_dir):
    """Test show command with invalid format"""
    with pytest.raises(SystemExit):
        with patch('sys.stderr'):
            ouverture.function_show("invalid_format")


def test_function_show_function_not_found(mock_ouverture_dir):
    """Test show command with non-existent function"""
    func_hash = "notfound" + "0" * 56
    with pytest.raises(SystemExit):
        with patch('sys.stderr'):
            ouverture.function_show(f"{func_hash}@eng")


def test_function_show_language_not_found(mock_ouverture_dir):
    """Test show command with non-existent language"""
    func_hash = "a0005000" + "0" * 56
    lang = "eng"

    # Create function with only English
    ouverture.function_save(func_hash, lang, normalize_code_for_test("def _ouverture_v_0(): pass"), "Doc", {"_ouverture_v_0": "func"}, {})

    # Try to show in French (doesn't exist)
    with pytest.raises(SystemExit):
        with patch('sys.stderr'):
            ouverture.function_show(f"{func_hash}@fra")
