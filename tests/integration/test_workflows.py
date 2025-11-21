"""
Integration tests for end-to-end workflows.

Tests that exercise complete CLI workflows combining multiple commands.
"""
import ast
from unittest.mock import patch

import pytest

import ouverture
from tests.conftest import normalize_code_for_test


def test_end_to_end_roundtrip_simple_function(mock_ouverture_dir):
    """Test add then get produces equivalent code"""
    # Create test file
    test_file = mock_ouverture_dir / "test.py"
    original_code = '''def calculate_sum(first, second):
    """Add two numbers"""
    result = first + second
    return result'''
    test_file.write_text(original_code, encoding='utf-8')

    # Add function
    hash_value = None
    with patch('sys.stdout') as mock_stdout:
        with patch('builtins.print') as mock_print:
            ouverture.function_add(f"{test_file}@eng")
            # Extract hash from print calls
            for call in mock_print.call_args_list:
                args = str(call)
                if 'Hash:' in args:
                    hash_value = args.split('Hash: ')[1].split("'")[0]

    assert hash_value is not None

    # Get function back
    output = []
    with patch('builtins.print', side_effect=lambda x: output.append(x)):
        ouverture.function_get(f"{hash_value}@eng")

    retrieved_code = '\n'.join(output)

    # Parse both to compare structure
    original_tree = ast.parse(original_code)
    retrieved_tree = ast.parse(retrieved_code)

    # Should have same structure (function name, args, etc.)
    orig_func = original_tree.body[0]
    retr_func = retrieved_tree.body[0]

    assert orig_func.name == retr_func.name
    assert len(orig_func.args.args) == len(retr_func.args.args)


def test_end_to_end_multilingual_same_hash(mock_ouverture_dir):
    """Test that equivalent functions in different languages produce same hash"""
    # English version
    eng_file = mock_ouverture_dir / "english.py"
    eng_file.write_text('''def calculate_sum(first_number, second_number):
    """Calculate the sum of two numbers."""
    result = first_number + second_number
    return result''', encoding='utf-8')

    # French version (same logic, different names/docstring)
    fra_file = mock_ouverture_dir / "french.py"
    fra_file.write_text('''def calculate_sum(first_number, second_number):
    """Calculer la somme de deux nombres."""
    result = first_number + second_number
    return result''', encoding='utf-8')

    # Add both
    eng_hash = None
    fra_hash = None

    with patch('builtins.print') as mock_print:
        ouverture.function_add(f"{eng_file}@eng")
        for call in mock_print.call_args_list:
            args = str(call)
            if 'Hash:' in args:
                eng_hash = args.split('Hash: ')[1].split("'")[0]

    with patch('builtins.print') as mock_print:
        ouverture.function_add(f"{fra_file}@fra")
        for call in mock_print.call_args_list:
            args = str(call)
            if 'Hash:' in args:
                fra_hash = args.split('Hash: ')[1].split("'")[0]

    # Should have the same hash
    assert eng_hash == fra_hash

    # Should be able to retrieve in both languages
    with patch('builtins.print'):
        ouverture.function_get(f"{eng_hash}@eng")
        ouverture.function_get(f"{fra_hash}@fra")


def test_workflow_add_show(mock_ouverture_dir):
    """Test add then show workflow"""
    # Create test file
    test_file = mock_ouverture_dir / "greet.py"
    test_file.write_text('''def greet(name):
    """Greet someone by name"""
    return f"Hello, {name}!"
''', encoding='utf-8')

    # Add function
    hash_value = None
    with patch('builtins.print') as mock_print:
        ouverture.function_add(f"{test_file}@eng")
        for call in mock_print.call_args_list:
            args = str(call)
            if 'Hash:' in args:
                hash_value = args.split('Hash: ')[1].split("'")[0]

    assert hash_value is not None

    # Show function
    output = []
    def capture_print(x='', **kwargs):
        output.append(str(x))

    with patch('builtins.print', side_effect=capture_print):
        ouverture.function_show(f"{hash_value}@eng")

    output_text = '\n'.join(output)

    # Should contain the original function
    assert 'def greet' in output_text
    assert 'name' in output_text
    assert 'Hello' in output_text


def test_workflow_add_migrate_show(mock_ouverture_dir):
    """Test add (v0) then migrate then show workflow"""
    func_hash = "a1b2c3d4" + "0" * 56  # Valid hex hash
    lang = "eng"
    normalized_code = normalize_code_for_test("def _ouverture_v_0(): return 99")
    docstring = "Return 99"
    name_mapping = {"_ouverture_v_0": "ninety_nine"}
    alias_mapping = {}

    # Create v0 function directly
    with patch('sys.stdout'):
        ouverture.function_save_v0(func_hash, lang, normalized_code, docstring, name_mapping, alias_mapping)

    # Verify it's v0
    assert ouverture.schema_detect_version(func_hash) == 0

    # Migrate to v1
    with patch('sys.stdout'):
        ouverture.schema_migrate_function_v0_to_v1(func_hash, keep_v0=False)

    # Verify it's now v1
    assert ouverture.schema_detect_version(func_hash) == 1

    # Load function to verify data integrity after migration
    loaded_code, loaded_name, loaded_alias, loaded_doc = ouverture.function_load(func_hash, lang)
    assert loaded_doc == docstring
    assert loaded_name == name_mapping

    # Show function
    output = []
    def capture_print(x='', **kwargs):
        output.append(str(x))

    with patch('builtins.print', side_effect=capture_print):
        ouverture.function_show(f"{func_hash}@{lang}")

    output_text = '\n'.join(output)

    # Should contain the function
    assert 'def ninety_nine' in output_text
    assert 'Return 99' in output_text


def test_workflow_multilang_variants(mock_ouverture_dir):
    """Test adding same function in multiple languages with different variant comments"""
    func_hash = "e1f2a3b4" + "0" * 56  # Valid hex hash
    normalized_code = normalize_code_for_test("def _ouverture_v_0(_ouverture_v_1): return _ouverture_v_1 * 2")
    metadata = ouverture.metadata_create()

    # Create function
    ouverture.function_save_v1(func_hash, normalized_code, metadata)

    # Add English formal variant
    ouverture.mapping_save_v1(
        func_hash, "eng",
        "Double the input value",
        {"_ouverture_v_0": "double_value", "_ouverture_v_1": "input_value"},
        {},
        "Formal documentation style"
    )

    # Add English casual variant
    ouverture.mapping_save_v1(
        func_hash, "eng",
        "Times two!",
        {"_ouverture_v_0": "times_two", "_ouverture_v_1": "x"},
        {},
        "Casual short names"
    )

    # Add French variant
    ouverture.mapping_save_v1(
        func_hash, "fra",
        "Doubler la valeur",
        {"_ouverture_v_0": "doubler", "_ouverture_v_1": "valeur"},
        {},
        "Français standard"
    )

    # List English mappings - should have 2
    eng_mappings = ouverture.mappings_list_v1(func_hash, "eng")
    assert len(eng_mappings) == 2

    # List French mappings - should have 1
    fra_mappings = ouverture.mappings_list_v1(func_hash, "fra")
    assert len(fra_mappings) == 1

    # Show should display menu for English (multiple variants)
    output = []
    def capture_print(x='', **kwargs):
        output.append(str(x))

    with patch('builtins.print', side_effect=capture_print):
        ouverture.function_show(f"{func_hash}@eng")

    output_text = '\n'.join(output)
    assert "Multiple mappings found" in output_text
    assert "Formal documentation style" in output_text
    assert "Casual short names" in output_text

    # Show should display code directly for French (single variant)
    output = []
    with patch('builtins.print', side_effect=capture_print):
        ouverture.function_show(f"{func_hash}@fra")

    output_text = '\n'.join(output)
    assert "def doubler" in output_text


def test_workflow_function_with_ouverture_import(mock_ouverture_dir):
    """Test adding and retrieving a function that imports from ouverture pool"""
    # First, add a helper function
    helper_file = mock_ouverture_dir / "helper.py"
    helper_file.write_text('''def helper(x):
    """A helper function"""
    return x * 2
''', encoding='utf-8')

    helper_hash = None
    with patch('builtins.print') as mock_print:
        ouverture.function_add(f"{helper_file}@eng")
        for call in mock_print.call_args_list:
            args = str(call)
            if 'Hash:' in args:
                helper_hash = args.split('Hash: ')[1].split("'")[0]

    assert helper_hash is not None

    # Now add a function that uses the helper
    main_file = mock_ouverture_dir / "main.py"
    main_file.write_text(f'''from ouverture.pool import object_{helper_hash} as helper

def process(value):
    """Process a value using helper"""
    return helper(value) + 1
''', encoding='utf-8')

    main_hash = None
    with patch('builtins.print') as mock_print:
        ouverture.function_add(f"{main_file}@eng")
        for call in mock_print.call_args_list:
            args = str(call)
            if 'Hash:' in args:
                main_hash = args.split('Hash: ')[1].split("'")[0]

    assert main_hash is not None

    # Retrieve and verify
    output = []
    def capture_print(x='', **kwargs):
        output.append(str(x))

    with patch('builtins.print', side_effect=capture_print):
        ouverture.function_show(f"{main_hash}@eng")

    output_text = '\n'.join(output)

    # Should have restored the import with alias
    assert "from ouverture.pool import" in output_text
    assert "as helper" in output_text
    assert "def process" in output_text
