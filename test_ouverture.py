"""
Comprehensive unit tests for ouverture.py
"""
import ast
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import ouverture


class TestASTNormalizer:
    """Tests for the ASTNormalizer class"""

    def test_visit_name_with_mapping(self):
        """Test that Name nodes are renamed according to mapping"""
        mapping = {"x": "_ouverture_v_1", "y": "_ouverture_v_2"}
        normalizer = ouverture.ASTNormalizer(mapping)

        code = "z = x + y"
        tree = ast.parse(code)
        normalizer.visit(tree)
        result = ast.unparse(tree)

        assert "_ouverture_v_1" in result
        assert "_ouverture_v_2" in result

    def test_visit_name_without_mapping(self):
        """Test that unmapped names remain unchanged"""
        mapping = {"x": "_ouverture_v_1"}
        normalizer = ouverture.ASTNormalizer(mapping)

        code = "z = x + y"
        tree = ast.parse(code)
        normalizer.visit(tree)
        result = ast.unparse(tree)

        assert "_ouverture_v_1" in result
        assert "y" in result  # y should remain unchanged

    def test_visit_arg_with_mapping(self):
        """Test that function arguments are renamed"""
        mapping = {"x": "_ouverture_v_1", "y": "_ouverture_v_2"}
        normalizer = ouverture.ASTNormalizer(mapping)

        code = "def foo(x, y): return x + y"
        tree = ast.parse(code)
        normalizer.visit(tree)
        result = ast.unparse(tree)

        assert "_ouverture_v_1" in result
        assert "_ouverture_v_2" in result

    def test_visit_functiondef_with_mapping(self):
        """Test that function names are renamed"""
        mapping = {"foo": "_ouverture_v_0"}
        normalizer = ouverture.ASTNormalizer(mapping)

        code = "def foo(): pass"
        tree = ast.parse(code)
        normalizer.visit(tree)
        result = ast.unparse(tree)

        assert "_ouverture_v_0" in result
        assert "foo" not in result


class TestCollectNames:
    """Tests for collect_names function"""

    def test_collect_simple_names(self):
        """Test collecting variable names"""
        code = "x = 1\ny = 2\nz = x + y"
        tree = ast.parse(code)
        names = ouverture.collect_names(tree)

        assert "x" in names
        assert "y" in names
        assert "z" in names

    def test_collect_function_names(self):
        """Test collecting function names and arguments"""
        code = "def foo(a, b): return a + b"
        tree = ast.parse(code)
        names = ouverture.collect_names(tree)

        assert "foo" in names
        assert "a" in names
        assert "b" in names

    def test_empty_tree(self):
        """Test collecting names from empty module"""
        tree = ast.parse("")
        names = ouverture.collect_names(tree)

        assert len(names) == 0


class TestGetImportedNames:
    """Tests for get_imported_names function"""

    def test_import_statement(self):
        """Test extracting names from import statement"""
        code = "import math"
        tree = ast.parse(code)
        names = ouverture.get_imported_names(tree)

        assert "math" in names

    def test_import_with_alias(self):
        """Test extracting aliased import names"""
        code = "import numpy as np"
        tree = ast.parse(code)
        names = ouverture.get_imported_names(tree)

        assert "np" in names
        assert "numpy" not in names

    def test_from_import(self):
        """Test extracting names from from-import"""
        code = "from collections import Counter"
        tree = ast.parse(code)
        names = ouverture.get_imported_names(tree)

        assert "Counter" in names

    def test_from_import_with_alias(self):
        """Test extracting aliased from-import names"""
        code = "from collections import Counter as C"
        tree = ast.parse(code)
        names = ouverture.get_imported_names(tree)

        assert "C" in names
        assert "Counter" not in names

    def test_multiple_imports(self):
        """Test extracting names from multiple imports"""
        code = """
import math
from collections import Counter
import numpy as np
"""
        tree = ast.parse(code)
        names = ouverture.get_imported_names(tree)

        assert "math" in names
        assert "Counter" in names
        assert "np" in names


class TestCheckUnusedImports:
    """Tests for check_unused_imports function"""

    def test_all_imports_used(self):
        """Test when all imports are used"""
        code = """
import math
def foo():
    return math.sqrt(4)
"""
        tree = ast.parse(code)
        imported = ouverture.get_imported_names(tree)
        all_names = ouverture.collect_names(tree)

        result = ouverture.check_unused_imports(tree, imported, all_names)
        assert result is True

    def test_unused_import(self):
        """Test when an import is unused"""
        code = """
import math
def foo():
    return 4
"""
        tree = ast.parse(code)
        imported = ouverture.get_imported_names(tree)
        all_names = ouverture.collect_names(tree)

        result = ouverture.check_unused_imports(tree, imported, all_names)
        assert result is False


class TestSortImports:
    """Tests for sort_imports function"""

    def test_sort_simple_imports(self):
        """Test sorting import statements"""
        code = """
import sys
import ast
import os
"""
        tree = ast.parse(code)
        sorted_tree = ouverture.sort_imports(tree)
        result = ast.unparse(sorted_tree)

        # ast should come before os, os before sys
        assert result.index("ast") < result.index("os")
        assert result.index("os") < result.index("sys")

    def test_sort_from_imports(self):
        """Test sorting from-import statements"""
        code = """
from os import path
from collections import Counter
from ast import parse
"""
        tree = ast.parse(code)
        sorted_tree = ouverture.sort_imports(tree)
        result = ast.unparse(sorted_tree)

        # Should be sorted by module name
        assert result.index("from ast") < result.index("from collections")
        assert result.index("from collections") < result.index("from os")

    def test_imports_before_code(self):
        """Test that imports remain before code"""
        code = """
import sys
def foo():
    pass
import os
"""
        tree = ast.parse(code)
        sorted_tree = ouverture.sort_imports(tree)
        result = ast.unparse(sorted_tree)

        # All imports should come before the function
        func_pos = result.index("def foo")
        assert result.index("import") < func_pos


class TestExtractFunctionDef:
    """Tests for extract_function_def function"""

    def test_extract_simple_function(self):
        """Test extracting a simple function"""
        code = """
def foo():
    return 42
"""
        tree = ast.parse(code)
        func_def, imports = ouverture.extract_function_def(tree)

        assert func_def is not None
        assert func_def.name == "foo"
        assert len(imports) == 0

    def test_extract_function_with_imports(self):
        """Test extracting function with imports"""
        code = """
import math
from collections import Counter

def process():
    return 42
"""
        tree = ast.parse(code)
        func_def, imports = ouverture.extract_function_def(tree)

        assert func_def is not None
        assert func_def.name == "process"
        assert len(imports) == 2

    def test_no_function_raises_error(self):
        """Test that missing function raises ValueError"""
        code = "x = 42"
        tree = ast.parse(code)

        with pytest.raises(ValueError, match="No function definition found"):
            ouverture.extract_function_def(tree)

    def test_multiple_functions_raises_error(self):
        """Test that multiple functions raise ValueError"""
        code = """
def foo():
    pass

def bar():
    pass
"""
        tree = ast.parse(code)

        with pytest.raises(ValueError, match="Only one function definition is allowed"):
            ouverture.extract_function_def(tree)


class TestCreateNameMapping:
    """Tests for create_name_mapping function"""

    def test_function_name_always_v0(self):
        """Test that function name always maps to _ouverture_v_0"""
        code = "def my_function(x): return x"
        tree = ast.parse(code)
        func_def, imports = ouverture.extract_function_def(tree)

        forward, reverse = ouverture.create_name_mapping(func_def, imports)

        assert forward["my_function"] == "_ouverture_v_0"
        assert reverse["_ouverture_v_0"] == "my_function"

    def test_sequential_numbering(self):
        """Test that variables get sequential numbers"""
        code = """
def foo(a, b):
    c = a + b
    return c
"""
        tree = ast.parse(code)
        func_def, imports = ouverture.extract_function_def(tree)

        forward, reverse = ouverture.create_name_mapping(func_def, imports)

        # foo should be v_0
        assert forward["foo"] == "_ouverture_v_0"
        # Other names should be numbered sequentially
        assert all(name.startswith("_ouverture_v_") for name in forward.values())

    def test_builtins_not_renamed(self):
        """Test that built-in functions are not renamed"""
        code = """
def foo(items):
    return len(items)
"""
        tree = ast.parse(code)
        func_def, imports = ouverture.extract_function_def(tree)

        forward, reverse = ouverture.create_name_mapping(func_def, imports)

        # len is a built-in and should not be in the mapping
        assert "len" not in forward
        assert "items" in forward

    def test_imported_names_not_renamed(self):
        """Test that imported names are not renamed"""
        code = """
import math

def foo(x):
    return math.sqrt(x)
"""
        tree = ast.parse(code)
        func_def, imports = ouverture.extract_function_def(tree)

        forward, reverse = ouverture.create_name_mapping(func_def, imports)

        # math is imported and should not be renamed
        assert "math" not in forward
        assert "x" in forward

    def test_ouverture_aliases_not_renamed(self):
        """Test that ouverture aliases are excluded from renaming"""
        code = """
def foo(x):
    return helper(x)
"""
        tree = ast.parse(code)
        func_def, imports = ouverture.extract_function_def(tree)

        # Simulate that 'helper' is an ouverture alias
        ouverture_aliases = {"helper"}
        forward, reverse = ouverture.create_name_mapping(func_def, imports, ouverture_aliases)

        # helper should not be renamed
        assert "helper" not in forward
        assert "x" in forward


class TestRewriteOuvertureImports:
    """Tests for rewrite_ouverture_imports function"""

    def test_rewrite_ouverture_import_with_alias(self):
        """Test rewriting ouverture import with alias"""
        code = "from ouverture import abc123 as helper"
        tree = ast.parse(code)
        imports = tree.body

        new_imports, alias_mapping = ouverture.rewrite_ouverture_imports(imports)

        # Should rewrite to couverture without alias
        result = ast.unparse(ast.Module(body=new_imports, type_ignores=[]))
        assert "from couverture import abc123" in result
        assert "as helper" not in result

        # Should track the alias
        assert alias_mapping["abc123"] == "helper"

    def test_rewrite_ouverture_import_without_alias(self):
        """Test rewriting ouverture import without alias"""
        code = "from ouverture import abc123"
        tree = ast.parse(code)
        imports = tree.body

        new_imports, alias_mapping = ouverture.rewrite_ouverture_imports(imports)

        result = ast.unparse(ast.Module(body=new_imports, type_ignores=[]))
        assert "from couverture import abc123" in result
        assert len(alias_mapping) == 0

    def test_non_ouverture_imports_unchanged(self):
        """Test that non-ouverture imports remain unchanged"""
        code = "import math\nfrom collections import Counter"
        tree = ast.parse(code)
        imports = tree.body

        new_imports, alias_mapping = ouverture.rewrite_ouverture_imports(imports)

        result = ast.unparse(ast.Module(body=new_imports, type_ignores=[]))
        assert "import math" in result
        assert "from collections import Counter" in result
        assert len(alias_mapping) == 0


class TestReplaceOuvertureCalls:
    """Tests for replace_ouverture_calls function"""

    def test_replace_aliased_call(self):
        """Test replacing aliased ouverture function calls"""
        code = """
def foo(x):
    return helper(x)
"""
        tree = ast.parse(code)
        alias_mapping = {"abc123": "helper"}
        name_mapping = {}

        new_tree = ouverture.replace_ouverture_calls(tree, alias_mapping, name_mapping)
        result = ast.unparse(new_tree)

        # helper(x) should become abc123._ouverture_v_0(x)
        assert "abc123._ouverture_v_0" in result
        assert "helper" not in result

    def test_non_aliased_names_unchanged(self):
        """Test that non-aliased names remain unchanged"""
        code = """
def foo(x):
    return other(x)
"""
        tree = ast.parse(code)
        alias_mapping = {"abc123": "helper"}
        name_mapping = {}

        new_tree = ouverture.replace_ouverture_calls(tree, alias_mapping, name_mapping)
        result = ast.unparse(new_tree)

        # other should remain unchanged
        assert "other" in result


class TestClearLocations:
    """Tests for clear_locations function"""

    def test_clear_all_location_info(self):
        """Test that all location info is cleared"""
        code = "def foo(x): return x + 1"
        tree = ast.parse(code)

        # Verify locations exist initially
        for node in ast.walk(tree):
            if hasattr(node, 'lineno'):
                assert node.lineno is not None
                break

        ouverture.clear_locations(tree)

        # Verify all locations are None
        for node in ast.walk(tree):
            if hasattr(node, 'lineno'):
                assert node.lineno is None
            if hasattr(node, 'col_offset'):
                assert node.col_offset is None


class TestExtractDocstring:
    """Tests for extract_docstring function"""

    def test_extract_existing_docstring(self):
        """Test extracting an existing docstring"""
        code = '''
def foo():
    """This is a docstring"""
    return 42
'''
        tree = ast.parse(code)
        func_def, _ = ouverture.extract_function_def(tree)

        docstring, func_without_doc = ouverture.extract_docstring(func_def)

        assert docstring == "This is a docstring"
        assert len(func_without_doc.body) == 1  # Only return statement
        assert isinstance(func_without_doc.body[0], ast.Return)

    def test_function_without_docstring(self):
        """Test function without docstring returns empty string"""
        code = """
def foo():
    return 42
"""
        tree = ast.parse(code)
        func_def, _ = ouverture.extract_function_def(tree)

        docstring, func_without_doc = ouverture.extract_docstring(func_def)

        assert docstring == ""
        assert len(func_without_doc.body) == 1

    def test_multiline_docstring(self):
        """Test extracting multiline docstring"""
        code = '''
def foo():
    """
    This is a multiline
    docstring
    """
    return 42
'''
        tree = ast.parse(code)
        func_def, _ = ouverture.extract_function_def(tree)

        docstring, func_without_doc = ouverture.extract_docstring(func_def)

        assert "multiline" in docstring
        assert "docstring" in docstring


class TestNormalizeAST:
    """Tests for normalize_ast function"""

    def test_normalize_simple_function(self):
        """Test normalizing a simple function"""
        code = """
def calculate_sum(first, second):
    \"\"\"Add two numbers\"\"\"
    result = first + second
    return result
"""
        tree = ast.parse(code)

        code_with_doc, code_without_doc, docstring, name_mapping, alias_mapping = \
            ouverture.normalize_ast(tree, "eng")

        assert "_ouverture_v_0" in code_with_doc  # Function name normalized
        assert docstring == "Add two numbers"
        assert "_ouverture_v_0" in name_mapping.values()
        assert code_without_doc != code_with_doc  # Should differ by docstring

    def test_normalize_imports_sorted(self):
        """Test that imports are sorted during normalization"""
        code = """
import sys
import ast
import os

def foo():
    return 42
"""
        tree = ast.parse(code)

        code_with_doc, _, _, _, _ = ouverture.normalize_ast(tree, "eng")

        # Verify imports are sorted
        assert code_with_doc.index("import ast") < code_with_doc.index("import os")
        assert code_with_doc.index("import os") < code_with_doc.index("import sys")

    def test_normalize_with_ouverture_import(self):
        """Test normalizing function with ouverture import"""
        code = """
from ouverture import abc123 as helper

def foo(x):
    \"\"\"Process with helper\"\"\"
    return helper(x)
"""
        tree = ast.parse(code)

        code_with_doc, code_without_doc, docstring, name_mapping, alias_mapping = \
            ouverture.normalize_ast(tree, "eng")

        # Should rewrite to couverture
        assert "from couverture import abc123" in code_with_doc
        assert "as helper" not in code_with_doc

        # Should track alias
        assert alias_mapping["abc123"] == "helper"

        # Should replace calls
        assert "abc123._ouverture_v_0" in code_with_doc


class TestComputeHash:
    """Tests for compute_hash function"""

    def test_hash_deterministic(self):
        """Test that same input produces same hash"""
        code = "def foo(): return 42"

        hash1 = ouverture.compute_hash(code)
        hash2 = ouverture.compute_hash(code)

        assert hash1 == hash2

    def test_hash_format(self):
        """Test that hash is 64 hex characters"""
        code = "def foo(): return 42"

        hash_value = ouverture.compute_hash(code)

        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value)

    def test_different_code_different_hash(self):
        """Test that different code produces different hash"""
        code1 = "def foo(): return 42"
        code2 = "def bar(): return 43"

        hash1 = ouverture.compute_hash(code1)
        hash2 = ouverture.compute_hash(code2)

        assert hash1 != hash2


class TestSaveFunction:
    """Tests for save_function function"""

    def test_save_new_function(self, tmp_path):
        """Test saving a new function"""
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            hash_value = "a" * 64
            lang = "eng"
            normalized_code = "def _ouverture_v_0(): return 42"
            docstring = "Test function"
            name_mapping = {"_ouverture_v_0": "foo"}
            alias_mapping = {}

            # Capture stdout
            with patch('sys.stdout'):
                ouverture.save_function(hash_value, lang, normalized_code,
                                       docstring, name_mapping, alias_mapping)

            # Verify file was created
            json_path = Path('.ouverture/objects/aa') / (('a' * 62) + '.json')
            assert json_path.exists()

            # Verify content
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert data['hash'] == hash_value
            assert data['normalized_code'] == normalized_code
            assert data['docstrings']['eng'] == docstring
            assert data['name_mappings']['eng'] == name_mapping

        finally:
            os.chdir(original_cwd)

    def test_save_additional_language(self, tmp_path):
        """Test adding another language to existing function"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            hash_value = "b" * 64
            normalized_code = "def _ouverture_v_0(): return 42"

            # Save English version
            with patch('sys.stdout'):
                ouverture.save_function(hash_value, "eng", normalized_code,
                                       "English doc", {"_ouverture_v_0": "foo"}, {})

            # Save French version
            with patch('sys.stdout'):
                ouverture.save_function(hash_value, "fra", normalized_code,
                                       "French doc", {"_ouverture_v_0": "foo"}, {})

            # Verify both languages are present
            json_path = Path('.ouverture/objects/bb') / (('b' * 62) + '.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert 'eng' in data['docstrings']
            assert 'fra' in data['docstrings']
            assert data['docstrings']['eng'] == "English doc"
            assert data['docstrings']['fra'] == "French doc"

        finally:
            os.chdir(original_cwd)


class TestReplaceDocstring:
    """Tests for replace_docstring function"""

    def test_replace_existing_docstring(self):
        """Test replacing an existing docstring"""
        code = '''
def foo():
    """Old docstring"""
    return 42
'''
        new_doc = "New docstring"

        result = ouverture.replace_docstring(code, new_doc)

        assert "New docstring" in result
        assert "Old docstring" not in result

    def test_add_docstring_when_none_exists(self):
        """Test adding docstring to function without one"""
        code = """
def foo():
    return 42
"""
        new_doc = "Added docstring"

        result = ouverture.replace_docstring(code, new_doc)

        assert "Added docstring" in result

    def test_remove_docstring_with_empty_string(self):
        """Test removing docstring by passing empty string"""
        code = '''
def foo():
    """Remove this"""
    return 42
'''
        result = ouverture.replace_docstring(code, "")

        assert "Remove this" not in result
        tree = ast.parse(result)
        func_def = tree.body[0]

        # Should only have return statement
        assert len(func_def.body) == 1
        assert isinstance(func_def.body[0], ast.Return)


class TestDenormalizeCode:
    """Tests for denormalize_code function"""

    def test_denormalize_variable_names(self):
        """Test denormalizing variable names"""
        normalized = """
def _ouverture_v_0(_ouverture_v_1, _ouverture_v_2):
    _ouverture_v_3 = _ouverture_v_1 + _ouverture_v_2
    return _ouverture_v_3
"""
        name_mapping = {
            "_ouverture_v_0": "calculate",
            "_ouverture_v_1": "first",
            "_ouverture_v_2": "second",
            "_ouverture_v_3": "result"
        }
        alias_mapping = {}

        result = ouverture.denormalize_code(normalized, name_mapping, alias_mapping)

        assert "calculate" in result
        assert "first" in result
        assert "second" in result
        assert "result" in result
        assert "_ouverture_v_" not in result

    def test_denormalize_ouverture_imports(self):
        """Test denormalizing ouverture imports"""
        normalized = """
from couverture import abc123

def _ouverture_v_0(_ouverture_v_1):
    return abc123._ouverture_v_0(_ouverture_v_1)
"""
        name_mapping = {
            "_ouverture_v_0": "process",
            "_ouverture_v_1": "data"
        }
        alias_mapping = {
            "abc123": "helper"
        }

        result = ouverture.denormalize_code(normalized, name_mapping, alias_mapping)

        # Should restore import with alias
        assert "from ouverture import abc123 as helper" in result

        # Should restore function calls
        assert "helper(data)" in result
        assert "abc123._ouverture_v_0" not in result


class TestAddFunction:
    """Integration tests for add_function command"""

    def test_add_function_missing_lang_suffix(self):
        """Test that missing @lang suffix causes error"""
        with pytest.raises(SystemExit):
            with patch('sys.stderr'):
                ouverture.add_function("example.py")

    def test_add_function_invalid_lang_code(self):
        """Test that invalid language code causes error"""
        with pytest.raises(SystemExit):
            with patch('sys.stderr'):
                ouverture.add_function("example.py@en")  # Should be 3 chars

    def test_add_function_file_not_found(self):
        """Test that missing file causes error"""
        with pytest.raises(SystemExit):
            with patch('sys.stderr'):
                ouverture.add_function("nonexistent.py@eng")

    def test_add_function_syntax_error(self, tmp_path):
        """Test that syntax error in file causes error"""
        test_file = tmp_path / "bad.py"
        test_file.write_text("def foo( invalid syntax", encoding='utf-8')

        with pytest.raises(SystemExit):
            with patch('sys.stderr'):
                ouverture.add_function(f"{test_file}@eng")

    def test_add_function_success(self, tmp_path):
        """Test successfully adding a function"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            test_file = tmp_path / "test.py"
            test_file.write_text('''
def calculate_sum(a, b):
    """Add two numbers"""
    return a + b
''', encoding='utf-8')

            with patch('sys.stdout'):
                ouverture.add_function(f"{test_file}@eng")

            # Verify .ouverture directory was created
            assert Path('.ouverture/objects').exists()

            # Verify at least one JSON file was created
            json_files = list(Path('.ouverture/objects').rglob('*.json'))
            assert len(json_files) == 1

        finally:
            os.chdir(original_cwd)


class TestGetFunction:
    """Integration tests for get_function command"""

    def test_get_function_missing_lang_suffix(self):
        """Test that missing @lang suffix causes error"""
        with pytest.raises(SystemExit):
            with patch('sys.stderr'):
                ouverture.get_function("abc123")

    def test_get_function_invalid_lang_code(self):
        """Test that invalid language code causes error"""
        with pytest.raises(SystemExit):
            with patch('sys.stderr'):
                ouverture.get_function("abc123@en")  # Should be 3 chars

    def test_get_function_invalid_hash_format(self):
        """Test that invalid hash format causes error"""
        with pytest.raises(SystemExit):
            with patch('sys.stderr'):
                ouverture.get_function("notahash@eng")

    def test_get_function_not_found(self):
        """Test that non-existent function causes error"""
        with pytest.raises(SystemExit):
            with patch('sys.stderr'):
                hash_value = "a" * 64
                ouverture.get_function(f"{hash_value}@eng")

    def test_get_function_language_not_found(self, tmp_path):
        """Test that requesting unavailable language causes error"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Create a function with only English
            hash_value = "c" * 64
            with patch('sys.stdout'):
                ouverture.save_function(hash_value, "eng",
                                       "def _ouverture_v_0(): return 42",
                                       "English doc",
                                       {"_ouverture_v_0": "foo"}, {})

            # Try to get it in French
            with pytest.raises(SystemExit):
                with patch('sys.stderr'):
                    ouverture.get_function(f"{hash_value}@fra")

        finally:
            os.chdir(original_cwd)

    def test_get_function_success(self, tmp_path):
        """Test successfully retrieving a function"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
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
                ouverture.save_function(hash_value, "eng", normalized_code,
                                       "Add two numbers", name_mapping, {})

            # Retrieve it
            with patch('sys.stdout') as mock_stdout:
                ouverture.get_function(f"{hash_value}@eng")

                # Verify it was printed (can't easily capture print output)
                # Just verify no exception was raised

        finally:
            os.chdir(original_cwd)


class TestEndToEnd:
    """End-to-end integration tests"""

    def test_roundtrip_simple_function(self, tmp_path):
        """Test add then get produces equivalent code"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Create test file
            test_file = tmp_path / "test.py"
            original_code = '''def calculate_sum(first, second):
    """Add two numbers"""
    result = first + second
    return result'''
            test_file.write_text(original_code, encoding='utf-8')

            # Add function
            hash_value = None
            with patch('sys.stdout') as mock_stdout:
                with patch('builtins.print') as mock_print:
                    ouverture.add_function(f"{test_file}@eng")
                    # Extract hash from print calls
                    for call in mock_print.call_args_list:
                        args = str(call)
                        if 'Hash:' in args:
                            hash_value = args.split('Hash: ')[1].split("'")[0]

            assert hash_value is not None

            # Get function back
            output = []
            with patch('builtins.print', side_effect=lambda x: output.append(x)):
                ouverture.get_function(f"{hash_value}@eng")

            retrieved_code = '\n'.join(output)

            # Parse both to compare structure
            original_tree = ast.parse(original_code)
            retrieved_tree = ast.parse(retrieved_code)

            # Should have same structure (function name, args, etc.)
            orig_func = original_tree.body[0]
            retr_func = retrieved_tree.body[0]

            assert orig_func.name == retr_func.name
            assert len(orig_func.args.args) == len(retr_func.args.args)

        finally:
            os.chdir(original_cwd)

    def test_multilingual_same_hash(self, tmp_path):
        """Test that equivalent functions in different languages produce same hash"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # English version
            eng_file = tmp_path / "english.py"
            eng_file.write_text('''def calculate_sum(first_number, second_number):
    """Calculate the sum of two numbers."""
    result = first_number + second_number
    return result''', encoding='utf-8')

            # French version (same logic, different names/docstring)
            fra_file = tmp_path / "french.py"
            fra_file.write_text('''def calculate_sum(first_number, second_number):
    """Calculer la somme de deux nombres."""
    result = first_number + second_number
    return result''', encoding='utf-8')

            # Add both
            eng_hash = None
            fra_hash = None

            with patch('builtins.print') as mock_print:
                ouverture.add_function(f"{eng_file}@eng")
                for call in mock_print.call_args_list:
                    args = str(call)
                    if 'Hash:' in args:
                        eng_hash = args.split('Hash: ')[1].split("'")[0]

            with patch('builtins.print') as mock_print:
                ouverture.add_function(f"{fra_file}@fra")
                for call in mock_print.call_args_list:
                    args = str(call)
                    if 'Hash:' in args:
                        fra_hash = args.split('Hash: ')[1].split("'")[0]

            # Should have the same hash
            assert eng_hash == fra_hash

            # Should be able to retrieve in both languages
            with patch('builtins.print'):
                ouverture.get_function(f"{eng_hash}@eng")
                ouverture.get_function(f"{fra_hash}@fra")

        finally:
            os.chdir(original_cwd)
