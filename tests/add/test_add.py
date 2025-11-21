"""
Tests for the 'add' CLI command.

Tests adding functions to the ouverture pool.
"""
from unittest.mock import patch

import pytest

import ouverture
from tests.conftest import normalize_code_for_test


def test_add_function_missing_lang_suffix():
    """Test that missing @lang suffix causes error"""
    with pytest.raises(SystemExit):
        with patch('sys.stderr'):
            ouverture.function_add("example.py")


def test_add_function_invalid_lang_code():
    """Test that invalid language code causes error"""
    with pytest.raises(SystemExit):
        with patch('sys.stderr'):
            ouverture.function_add("example.py@en")  # Should be 3 chars


def test_add_function_file_not_found():
    """Test that missing file causes error"""
    with pytest.raises(SystemExit):
        with patch('sys.stderr'):
            ouverture.function_add("nonexistent.py@eng")


def test_add_function_syntax_error(tmp_path):
    """Test that syntax error in file causes error"""
    test_file = tmp_path / "bad.py"
    test_file.write_text("def foo( invalid syntax", encoding='utf-8')

    with pytest.raises(SystemExit):
        with patch('sys.stderr'):
            ouverture.function_add(f"{test_file}@eng")


def test_add_function_success(mock_ouverture_dir):
    """Test successfully adding a function"""
    test_file = mock_ouverture_dir / "test.py"
    test_file.write_text('''
def calculate_sum(a, b):
    """Add two numbers"""
    return a + b
''', encoding='utf-8')

    with patch('sys.stdout'):
        ouverture.function_add(f"{test_file}@eng")

    # Verify .ouverture directory was created
    ouverture_objects = mock_ouverture_dir / '.ouverture/objects'
    assert ouverture_objects.exists()

    # Verify JSON files were created (v1 format: object.json + mapping.json)
    json_files = list(ouverture_objects.rglob('*.json'))
    assert len(json_files) == 2  # object.json + mapping.json for v1 format


def test_add_function_with_imports(mock_ouverture_dir):
    """Test adding a function that has imports"""
    test_file = mock_ouverture_dir / "with_imports.py"
    test_file.write_text('''
import math

def calculate_sqrt(x):
    """Calculate square root"""
    return math.sqrt(x)
''', encoding='utf-8')

    with patch('sys.stdout'):
        ouverture.function_add(f"{test_file}@eng")

    # Verify files were created
    ouverture_objects = mock_ouverture_dir / '.ouverture/objects'
    json_files = list(ouverture_objects.rglob('*.json'))
    assert len(json_files) == 2


def test_add_function_with_comment(mock_ouverture_dir):
    """Test adding a function with a comment annotation"""
    test_file = mock_ouverture_dir / "with_comment.py"
    test_file.write_text('''
def greet(name):
    """Say hello"""
    return f"Hello, {name}!"
''', encoding='utf-8')

    # Add with comment parameter
    with patch('sys.stdout'):
        ouverture.function_add(f"{test_file}@eng", comment="Formal greeting style")

    # Verify the mapping was created with comment
    ouverture_objects = mock_ouverture_dir / '.ouverture/objects'
    mapping_files = list(ouverture_objects.rglob('mapping.json'))
    assert len(mapping_files) == 1

    import json
    with open(mapping_files[0], 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data['comment'] == "Formal greeting style"
