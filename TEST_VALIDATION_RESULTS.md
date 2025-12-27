# Konveyor Test Validation Results

## Executive Summary

**Status**: 0/50 tests passing (0%)
**Root Cause**: Generated test code doesn't match specific rule patterns
**Severity**: High - Requires prompt improvements

## Test Execution Results

Ran `kantra test` on all 50 generated test files:
- **Tests Executed**: 50/50
- **Tests Passed**: 0/50 (0%)
- **Incidents Found**: 0 (expected: ~50-100+)

All tests ran successfully but found **zero incidents**, indicating the generated code doesn't trigger any rules.

## Root Cause Analysis

### Issue: Generic Code vs. Specific Patterns

**Example: Button Rule**

Rule `patternfly-v5-to-patternfly-v6-button-00000` looks for:
```tsx
<Button variant="plain">
  <span>Icon</span>
</Button>
```

Generated test code:
- ✗ Imports `Button` component
- ✗ Contains 565 lines of JSX
- ✗ **Never uses `<Button>` in JSX**
- ✗ **Never includes `variant="plain"` attribute**

### Pattern Observed Across All Tests

1. **AI generates comprehensive imports** - Imports many components ✓
2. **AI generates valid JSX code** - Syntactically correct ✓
3. **AI generates generic examples** - Basic component usage ✓
4. **AI misses specific deprecated patterns** - Doesn't match rule conditions ✗

## Why This Happens

### Current Prompt Approach
```
Generate test code that uses these deprecated patterns:
- Rule button-00000: Button variant='plain' with icon children
```

**AI Interpretation**: "Generate code with Buttons"
**What we need**: "Generate `<Button variant='plain'><Icon /></Button>`"

### Missing Specificity

The prompts extract rule descriptions but don't parse the actual `when` conditions:

```yaml
when:
  and:
  - nodejs.referenced:
      pattern: Button
  - builtin.filecontent:
      pattern: <Button[^>]*\bvariant=['"]plain['"][^>]*>
```

The AI sees "Button variant='plain' description" but doesn't understand it needs to generate literal JSX matching the regex pattern.

## Recommended Fixes

### 1. Parse Rule Patterns (Recommended)

Extract actual patterns from `when` conditions:

```python
def extract_test_code_hint(rule):
    """Extract what code to generate from rule conditions."""
    when = rule.get('when', {})

    # For builtin.filecontent, extract the exact pattern
    if 'builtin.filecontent' in when:
        pattern = when['builtin.filecontent']['pattern']
        # For <Button[^>]*\bvariant=['"]plain['"][^>]*>
        # Generate hint: "Must include <Button variant="plain"> JSX tag"
        return create_jsx_hint_from_regex(pattern)

    # For nodejs.referenced
    if 'nodejs.referenced' in when:
        # Ensure the component is actually used, not just imported
        return f"Must use {when['nodejs.referenced']['pattern']} in JSX"
```

### 2. Enhanced Prompts

**Before**:
```
- Rule button-00000: Button variant='plain' with icon children should be replaced
  Pattern: <Button[^>]*\bvariant=['"]plain['"][^>]*> (location: FILE_CONTENT)
```

**After**:
```
- Rule button-00000: Button variant='plain' with icon children

  YOU MUST GENERATE THIS EXACT CODE:
  ```tsx
  <Button variant="plain">
    <SomeIcon />
  </Button>
  ```

  This code must:
  1. Use the Button component from @patternfly/react-core
  2. Have variant="plain" attribute
  3. Contain an icon element as a child
```

### 3. Pattern-to-Code Translation

Add a function to convert regex patterns to example code:

```python
PATTERN_TEMPLATES = {
    r'<Button[^>]*\bvariant=.*plain': '''<Button variant="plain">
  <TimesIcon />
</Button>''',
    r'<Card[^>]*\bisFlat': '<Card isFlat>...</Card>',
    # etc.
}
```

### 4. Validation Step

After generating test code, validate it matches the rule pattern:

```python
import re

def validate_generated_code(code, rule):
    """Check if generated code actually matches rule patterns."""
    when = rule.get('when', {})

    if 'builtin.filecontent' in when:
        pattern = when['builtin.filecontent']['pattern']
        if not re.search(pattern, code):
            return False, f"Code doesn't match pattern: {pattern}"

    return True, "OK"
```

## Implementation Priority

### Phase 1: Quick Fix (Manual)
- Manually create 2-3 test files with correct patterns
- Validate they work with kantra
- Use as templates

### Phase 2: Improved Prompts (Medium effort)
- Extract `when` conditions from rules
- Include literal code examples in prompts
- Add "YOU MUST INCLUDE" sections

### Phase 3: Pattern Parser (High effort)
- Parse regex patterns from `builtin.filecontent`
- Generate code examples programmatically
- Validate generated code matches patterns
- Retry generation if validation fails

## Example: Correct Test Code

**File**: `tests/data/button/src/App.tsx` (note: .tsx not .ts)

```tsx
import React from 'react';
import { Button } from '@patternfly/react-core';
import { TimesIcon } from '@patternfly/react-icons';

// Rule patternfly-v5-to-patternfly-v6-button-00000
// This Button with variant="plain" and icon children should trigger the rule
const ButtonExample: React.FC = () => {
  return (
    <div>
      <Button variant="plain">
        <TimesIcon />
      </Button>
    </div>
  );
};

export default ButtonExample;
```

**Expected**: kantra finds 1 incident for rule `button-00000`

## Next Steps

1. ✓ Document issue (this file)
2. Implement Phase 2 (improved prompts) in `generate_test_data.py`
3. Regenerate tests with better prompts
4. Validate with kantra
5. Iterate until >80% pass rate

## Additional Findings

### File Extensions
- Generated files are `.ts` but should be `.tsx` for JSX content
- Update `get_language_config()` to use `.tsx` for React components

### Provider Detection
- Tests correctly specify `nodejs` + `builtin` providers ✓
- Konveyor is loading the providers correctly ✓
- Issue is purely with code content, not test structure ✓
