# Rule Generator Improvements - Summary

## Overview

This branch (`fix/improve-rule-deduplication-and-validation`) implements comprehensive improvements to the analyzer rule generator to address issues found in the PatternFly v5→v6 migration rules.

## Problems Addressed

Based on analysis of three PatternFly rule sets (`combo-final`, `improved-detection`, `improved-detection-combo`), the following critical issues were identified:

### 1. Duplicate Rules (Most Critical)
- **Problem**: Same migration pattern appearing in multiple concern files
- **Example**: "Button isActive → isPressed" appeared in `button.yaml`, `component-props.yaml`, AND `components.yaml`
- **Impact**: 9+ duplicate rules in improved-detection-combo, 15+ in combo-final
- **Root Cause**: LLM assigns multiple concerns to same pattern, no cross-concern deduplication

### 2. Overly Broad Patterns
- **Problem**: Patterns matching too broadly, causing false positives
- **Examples**:
  - `isActive` - matches everywhere (variables, comments, all components)
  - `global_.*` - matches any variable starting with "global_"
  - `alignLeft` - matches in comments, strings, CSS
- **Impact**: 4 critical overly broad patterns per ruleset
- **Root Cause**: LLM sometimes ignores combo rule instructions, no validation

### 3. Data Errors
- **Problem**: Source and target identical
- **Example**: Package version "^5" → "^5" (should be "^6")
- **Impact**: Useless rules that don't guide migration
- **Root Cause**: No validation that source ≠ target

## Solutions Implemented

### 1. Automatic Pattern Validation (`src/rule_generator/extraction.py`)

Added `_validate_and_fix_patterns()` method that:

**Auto-Fixes:**
- ✅ Detects component prop patterns like "Button isActive"
- ✅ Automatically converts to combo rules (nodejs.referenced + builtin.filecontent)
- ✅ Generates proper `when_combo` configuration

**Rejects:**
- ❌ Overly generic prop names as standalone patterns (isActive, title, onClick, etc.)
- ❌ Overly broad wildcards (`.`*`, `.+`, etc.)
- ❌ Identical source and target patterns

**Helper Methods:**
- `_looks_like_prop_pattern()` - Detects "ComponentName propName" patterns
- `_convert_to_combo_rule()` - Auto-generates combo rule configuration
- `_is_overly_broad_pattern()` - Validates pattern specificity

### 2. Cross-Concern Deduplication (`scripts/generate_rules.py`)

Added deduplication logic after rule generation:

```python
# Track unique patterns by (when condition, description)
# Skip duplicates found in other concerns
# Report: "Skipping duplicate: X (already in Y concern)"
```

**Benefits:**
- Eliminates all duplicate rules across concerns
- Shows which concern "won" for each pattern
- Reports total duplicates removed

### 3. Validation Report (`scripts/generate_rules.py`)

Added `validate_rules()` function that checks:

- Overly broad builtin patterns (pattern < 5 characters)
- Missing file patterns on builtin rules
- Identical source/target in descriptions

**Output:**
```
============================================================
Validation Report
============================================================
  ⚠ overly_broad (2 issues):
    - rule-00050: pattern too short 'id'
    - rule-00120: pattern too short 'name'
  ⚠ missing_file_pattern (3 issues):
    - rule-00080: builtin without filePattern
    ...
```

### 4. Improved LLM Prompts (`src/rule_generator/extraction.py`)

Strengthened validation warnings in prompt:

```
**AUTOMATIC VALIDATION - RULES WILL BE ENFORCED:**

Your patterns will be automatically validated. Patterns violating
these rules will be REJECTED or AUTO-FIXED:

1. ✅ AUTO-FIX: Component-specific prop changes will be converted to combo rules
2. ❌ REJECT: Generic prop names as standalone patterns
3. ❌ REJECT: Source and target must be different
4. ❌ REJECT: Overly broad patterns
```

## Expected Impact

### Before Improvements:
- **combo-final**: 15+ duplicates, 3 contradictory rules, multiple overly broad patterns
- **improved-detection**: 12 duplicates, 2 contradictory rules
- **improved-detection-combo**: 9 duplicates, 4 overly broad patterns, 1 data error

### After Improvements:
- ✅ **Zero duplicates** across all concerns
- ✅ **Auto-fixed** component prop patterns to combo rules
- ✅ **Rejected** overly broad patterns before generation
- ✅ **Validation report** catches any remaining issues
- ✅ **Clear feedback** on what was fixed/rejected

## Testing Instructions

To test these improvements on PatternFly migration:

```bash
# Regenerate PatternFly v5→v6 rules with improvements
python scripts/generate_rules.py \
  --guide https://www.patternfly.org/get-started/upgrade/ \
  --source patternfly-v5 \
  --target patternfly-v6 \
  --follow-links \
  --max-depth 1 \
  --output examples/output/patternfly-v6-improved
```

**Expected output:**
```
[2/3] Extracting patterns with LLM...
  ! Auto-converting to combo rule: Button isActive
  ! Auto-converting to combo rule: Modal title
  ! Rejecting overly broad pattern: isActive
  ! Rejecting overly broad pattern: alignLeft
  ✓ Extracted N patterns

[3/3] Generating analyzer rules...
  → Deduplicating rules across concerns...
    ! Skipping duplicate: Button isActive... (already in component-props)
    ! Skipping duplicate: Modal title... (already in components)
  ✓ Removed 9 duplicate rules
  ✓ Generated N rules across M concern(s)

============================================================
Validation Report
============================================================
  ✓ No validation issues found
```

## Files Changed

1. **`src/rule_generator/extraction.py`** (+105 lines)
   - Added `_validate_and_fix_patterns()` method
   - Added `_looks_like_prop_pattern()` helper
   - Added `_convert_to_combo_rule()` helper
   - Added `_is_overly_broad_pattern()` validation
   - Updated `_extract_patterns_single()` to call validation
   - Enhanced LLM prompt with validation warnings

2. **`scripts/generate_rules.py`** (+80 lines)
   - Added cross-concern deduplication logic
   - Added `validate_rules()` function
   - Added validation report output
   - Improved output formatting with separators

## Next Steps

1. **Test on PatternFly**: Run generator with improvements on PatternFly migration guide
2. **Compare outputs**: Compare new output with `improved-detection-combo` to verify improvements
3. **Document patterns**: Update documentation with examples of auto-fixes
4. **Consider thresholds**: Add configuration for validation thresholds if needed

## Related Analysis Documents

- `examples/output/ANALYSIS_FINDINGS.md` - Original analysis of three rule sets
- `examples/output/patternfly-improved-detection-combo/COMBO_RULES_README.md` - Combo rules documentation
- Agent analysis reports (in conversation history) - Detailed findings for each ruleset

## Backward Compatibility

These changes are **fully backward compatible**:
- No breaking changes to existing APIs
- No changes to output format (YAML structure unchanged)
- Only affects rule quality and duplicate elimination
- Existing valid patterns continue to work

## Configuration

No new configuration options required. Validation is automatic and cannot be disabled (by design - ensures rule quality).

Optional future enhancement: Add `--validation-level` flag for strict/lenient modes.
