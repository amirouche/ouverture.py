# Issue: `couverture` Typo in Import Rewriting

## Description

The codebase contains a typo where `couverture` is used instead of `ouverture` during import normalization. This appears to be unintentional.

## Location

**File**: `ouverture.py`
**Lines**: 183-213 (in `rewrite_ouverture_imports()`) and 364-429 (in `denormalize_code()`)

### Current Behavior

**Normalization** (ouverture.py:206):
```python
new_imp = ast.ImportFrom(
    module='couverture',  # ← TYPO: should be 'ouverture'
    names=new_names,
    level=0
)
```

**Denormalization** (ouverture.py:410):
```python
if node.module == 'couverture':  # ← Checking for typo
    node.module = 'ouverture'
```

### Example

**Original code:**
```python
from ouverture import abc123def as helper
```

**Currently normalized to:**
```python
from couverture import abc123def  # ← TYPO: should be 'ouverture'
```

**Should normalize to:**
```python
from ouverture import abc123def  # ← CORRECT: keep 'ouverture'
```

## Why This Matters

1. **Confusion**: `couverture` is French for "coverage" and appears to be a typo
2. **Consistency**: The module name should remain `ouverture` throughout
3. **Clarity**: Using `ouverture` makes the normalization intent clearer

## Impact

- The typo currently works as an internal marker to identify ouverture imports during denormalization
- However, this is unnecessary - we can simply check `if node.module == 'ouverture'` since there is no external `ouverture` package
- Existing `.ouverture/objects/` JSON files contain `from couverture import ...` in normalized code

## Proposed Fix

### Changes Required

1. **In `rewrite_ouverture_imports()`** (ouverture.py:206):
   ```python
   new_imp = ast.ImportFrom(
       module='ouverture',  # ← Keep as 'ouverture'
       names=new_names,
       level=0
   )
   ```

2. **In `denormalize_code()`** (ouverture.py:410):
   ```python
   if node.module == 'ouverture':  # ← Check for 'ouverture' instead
       # Add aliases back from alias_mapping
   ```

3. **Migration**: Either:
   - Delete `.ouverture/` directory and re-add examples, OR
   - Create migration script to update existing JSON files

### Migration Script (Optional)

```python
import json
from pathlib import Path

def migrate_json_files():
    """Replace 'couverture' with 'ouverture' in all JSON files"""
    for json_file in Path('.ouverture/objects').rglob('*.json'):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Replace in normalized_code
        if 'normalized_code' in data:
            data['normalized_code'] = data['normalized_code'].replace(
                'from couverture import',
                'from ouverture import'
            )

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Migrated: {json_file}")
```

## Testing

After the fix, verify:

1. Add a function with ouverture imports
2. Check the JSON file contains `from ouverture import ...`
3. Retrieve the function using `get` command
4. Verify aliases are correctly restored

## Priority

**Low** - This is cosmetic but should be fixed for code clarity. The current implementation works correctly despite the typo.
