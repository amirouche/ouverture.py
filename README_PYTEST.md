# Pytest Unit Tests for Ouverture

This document describes the pytest unit tests for the Ouverture project.

## Installation

To run the tests, you need to install pytest:

```bash
pip install -r requirements-dev.txt
```

Or install pytest directly:

```bash
pip install pytest pytest-cov
```

## Running Tests

### Run all tests:

```bash
pytest
```

### Run with verbose output:

```bash
pytest -v
```

### Run with coverage report:

```bash
pytest --cov=ouverture --cov-report=html
```

### Run specific test class:

```bash
pytest test_ouverture.py::TestASTNormalizer
```

### Run specific test:

```bash
pytest test_ouverture.py::TestASTNormalizer::test_visit_name_with_mapping
```

## Test Structure

The test suite is organized into the following test classes:

### Unit Tests

1. **TestASTNormalizer** - Tests for the ASTNormalizer class
   - Variable name transformation
   - Function argument renaming
   - Function definition renaming

2. **TestCollectNames** - Tests for collect_names function
   - Collecting variable names
   - Collecting function names and arguments

3. **TestGetImportedNames** - Tests for get_imported_names function
   - Import statement parsing
   - Import with aliases
   - From-import statements

4. **TestCheckUnusedImports** - Tests for check_unused_imports function
   - Detecting used imports
   - Detecting unused imports

5. **TestSortImports** - Tests for sort_imports function
   - Sorting import statements
   - Sorting from-import statements
   - Import ordering relative to code

6. **TestExtractFunctionDef** - Tests for extract_function_def function
   - Extracting function definitions
   - Extracting imports
   - Error handling for missing/multiple functions

7. **TestCreateNameMapping** - Tests for create_name_mapping function
   - Function name mapping to _ouverture_v_0
   - Sequential variable numbering
   - Built-in exclusion from renaming
   - Imported name exclusion
   - Ouverture alias exclusion

8. **TestRewriteOuvertureImports** - Tests for rewrite_ouverture_imports function
   - Rewriting ouverture imports to couverture
   - Alias tracking and removal
   - Preservation of non-ouverture imports

9. **TestReplaceOuvertureCalls** - Tests for replace_ouverture_calls function
   - Replacing aliased function calls
   - Transformation to HASH._ouverture_v_0 format

10. **TestClearLocations** - Tests for clear_locations function
    - Clearing AST location information

11. **TestExtractDocstring** - Tests for extract_docstring function
    - Extracting existing docstrings
    - Handling functions without docstrings
    - Multiline docstring support

12. **TestNormalizeAST** - Tests for normalize_ast function
    - Simple function normalization
    - Import sorting during normalization
    - Ouverture import handling

13. **TestComputeHash** - Tests for compute_hash function
    - Deterministic hashing
    - Hash format validation
    - Different code producing different hashes

14. **TestSaveFunction** - Tests for save_function function
    - Saving new functions
    - Adding additional languages to existing functions
    - JSON file structure validation

15. **TestReplaceDocstring** - Tests for replace_docstring function
    - Replacing existing docstrings
    - Adding docstrings to functions without them
    - Removing docstrings

16. **TestDenormalizeCode** - Tests for denormalize_code function
    - Variable name denormalization
    - Ouverture import restoration
    - Function call restoration

### Integration Tests

17. **TestAddFunction** - Integration tests for add_function CLI command
    - Error handling for missing language suffix
    - Error handling for invalid language codes
    - Error handling for missing files
    - Error handling for syntax errors
    - Successful function addition

18. **TestGetFunction** - Integration tests for get_function CLI command
    - Error handling for missing language suffix
    - Error handling for invalid language codes
    - Error handling for invalid hash format
    - Error handling for non-existent functions
    - Error handling for unavailable languages
    - Successful function retrieval

19. **TestEndToEnd** - End-to-end integration tests
    - Roundtrip testing (add then get)
    - Multilingual function hashing (same logic = same hash)

## Test Coverage

The test suite covers:

- **Core AST manipulation**: All AST transformation and normalization logic
- **Name mapping**: Function and variable name mapping/unmapping
- **Import handling**: Both standard and ouverture imports
- **Hash computation**: Deterministic hashing excluding docstrings
- **Storage**: Content-addressed storage in .ouverture/objects/
- **CLI commands**: Both `add` and `get` commands with error cases
- **End-to-end workflows**: Complete add/get cycles and multilingual support

## Key Test Scenarios

### 1. AST Normalization
Tests verify that:
- Function names always map to `_ouverture_v_0`
- Variables get sequential indices
- Built-ins are never renamed
- Imports are never renamed
- Ouverture aliases are tracked and excluded from renaming

### 2. Multilingual Support
Tests verify that:
- Same logic in different languages produces same hash
- Docstrings are excluded from hash computation
- Language-specific names are preserved in mappings
- Roundtrip (add then get) preserves functionality

### 3. Import Handling
Tests verify that:
- Standard imports remain unchanged
- Ouverture imports are rewritten to couverture
- Aliases are tracked and restored correctly
- Function calls are transformed appropriately

### 4. Error Handling
Tests verify proper error messages for:
- Missing language suffixes
- Invalid language codes (must be 3 characters)
- Missing files
- Syntax errors
- Invalid hash formats
- Non-existent functions
- Unavailable languages

## Test Fixtures

The tests use `tmp_path` pytest fixture for:
- Creating temporary test files
- Creating temporary .ouverture directories
- Ensuring test isolation (no pollution of actual .ouverture)

## Mocking

Tests use `unittest.mock.patch` to:
- Capture stdout/stderr output
- Prevent actual file operations during some tests
- Test error conditions without side effects

## Continuous Integration

These tests are designed to be run in CI/CD pipelines. Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements-dev.txt
      - run: pytest -v --cov=ouverture
```

## Contributing

When adding new functionality to ouverture.py:

1. Write tests first (TDD approach)
2. Ensure all existing tests still pass
3. Aim for >90% code coverage
4. Include both unit tests and integration tests
5. Test error conditions, not just happy paths

## Common Issues

### Import Errors

If you get import errors, make sure ouverture.py is in the Python path:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Temporary Directory Issues

Tests use temporary directories for isolation. If tests fail with path issues, ensure the tmp_path fixture is working correctly.

### Git Ignores

The following directories/files should be in .gitignore:
- `.ouverture/` - Generated function pool
- `__pycache__/` - Python bytecode
- `.pytest_cache/` - Pytest cache
- `htmlcov/` - Coverage reports
- `.coverage` - Coverage data

## Performance

The full test suite should complete in under 10 seconds on modern hardware. If tests are slow:

1. Check for accidentally committed .ouverture directories
2. Ensure tmp_path fixtures are being used correctly
3. Consider using pytest-xdist for parallel execution:
   ```bash
   pip install pytest-xdist
   pytest -n auto
   ```

## Further Reading

- [pytest documentation](https://docs.pytest.org/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Python AST documentation](https://docs.python.org/3/library/ast.html)
