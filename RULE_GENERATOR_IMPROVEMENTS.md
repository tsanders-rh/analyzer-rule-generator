# Rule Generator Improvements

Based on comparison between auto-generated output and manually-cleaned PatternFly rules.

## Priority 1: High Impact Issues

### 1. Pattern Granularity for Multiple Values

**Problem**: When a migration involves multiple specific value replacements (e.g., pixel-to-rem conversions), the LLM currently creates one generic rule instead of multiple specific rules.

**Example**:
```yaml
# Current Output (1 generic rule):
- pattern: --pf-v5--global--breakpoint--
  description: breakpoint pixel values should be replaced with breakpoint rem values

# Desired Output (5 specific rules):
- pattern: 576px
  description: 576px should be replaced with 36rem
- pattern: 768px
  description: 768px should be replaced with 48rem
# ... etc
```

**Impact**: HIGH - Generic patterns are less actionable and may miss edge cases

**Recommended Fix**:
Update the extraction prompt to explicitly instruct the LLM:
```
When you identify a migration that involves multiple specific value replacements:
- CREATE SEPARATE PATTERNS for each specific value
- DO NOT create a generic catch-all pattern
- Each pattern should have an exact source value and exact target value

Examples where you should create multiple patterns:
- Pixel-to-rem conversions (576px→36rem, 768px→48rem, etc.)
- Enum value renames (alignLeft→alignStart, alignRight→alignEnd)
- Multiple component renames
```

**Location to Fix**: `src/rule_generator/extraction.py`, `_build_extraction_prompt()` method

---

### 2. String Value Detection Strategy

**Problem**: For string value replacements (like `variant="button-group"` → `variant="action-group"`), we need to detect just the string value, not the component.

**Current Behavior**:
- New output uses `builtin.filecontent` with pattern `button-group`
- This is correct but could be more specific

**Recommended Enhancement**:
Add guidance in the prompt that for enum/string value changes:
```
For prop value changes (e.g., variant="old" → variant="new"):
- Use builtin.filecontent provider
- Pattern should match the STRING VALUE only (not the component)
- Example: pattern: "button-group" (not "ToolbarGroup")
- filePattern: "\.(j|t)sx?$" for JSX/TSX files
```

**Impact**: MEDIUM - Ensures better targeting of string value changes

**Location to Fix**: `src/rule_generator/extraction.py`, language-specific instructions

---

## Priority 2: Medium Impact Issues

### 3. Naming Convention Consistency

**Problem**: File naming uses inconsistent framework version format
- Cleaned: `patternfly-5-to-patternfly-6-*`
- Generated: `patternfly-v5-to-patternfly-v6-*`

**Recommended Fix**:
Normalize framework names in the generator to strip "v" prefixes for cleaner naming:
```python
def normalize_framework_name(name: str) -> str:
    """Normalize framework name for file naming (strip v prefix)."""
    # patternfly-v5 → patternfly-5
    # spring-boot-3 → spring-boot-3
    return re.sub(r'-v(\d+)', r'-\1', name)
```

**Impact**: LOW - Cosmetic only

**Location to Fix**: `scripts/generate_rules.py`, filename generation section

---

### 4. Description Specificity

**Problem**: Descriptions are sometimes too generic

**Current**: `"breakpoint pixel values should be replaced with breakpoint rem values"`
**Better**: `"576px should be replaced with 36rem"`

**Recommended Fix**:
Add to extraction prompt:
```
Description Guidelines:
- Use SPECIFIC values in descriptions when possible
- Format: "{source_value} should be replaced with {target_value}"
- Example: "576px should be replaced with 36rem" (not "pixel values should be replaced")
- Example: "alignLeft should be replaced with alignStart" (not "alignment values should be updated")
```

**Impact**: MEDIUM - Improves rule clarity and debugging

**Location to Fix**: `src/rule_generator/extraction.py`, extraction prompt

---

### 5. Example Code Simplification

**Problem**: Generated examples include verbose import statements and export syntax

**Current**:
```javascript
import { AccordionContent } from "@patternfly/react-core";
export const AccordionContentRemoveIsHiddenPropInput = () => (
  <AccordionContent isHidden />
);
```

**Better**:
```javascript
<AccordionContent isHidden />
```

**Recommended Fix**:
Add to extraction prompt:
```
Example Code Guidelines:
- Keep examples MINIMAL - focus on the pattern being changed
- DO NOT include imports unless the import itself is changing
- DO NOT include export/function wrappers
- Show only the relevant code that demonstrates the change
```

**Impact**: LOW - Improves readability

**Location to Fix**: `src/rule_generator/extraction.py`, extraction prompt

---

## Priority 3: Low Impact Issues

### 6. Concern Naming Granularity

**Observation**: New output has very granular concerns (48 files) vs cleaned (23 files)

This is actually GOOD for organization, but consider:
- Some concerns could be merged (e.g., `removed-props` and `renamed-props` could stay separate OR be combined into `component-props`)
- Current granularity makes it easier to navigate

**Recommendation**: Keep current behavior, but consider adding a CLI flag for "merge similar concerns"

**Impact**: VERY LOW

---

## Summary of Recommended Changes

### Immediate Actions (High Priority):

1. **Update extraction prompt** to explicitly request separate patterns for multiple value mappings
2. **Add specific guidance** for string value detection vs component detection
3. **Enhance description format** to prefer specific values over generic terms

### Code Changes Needed:

**File**: `src/rule_generator/extraction.py`

Add to `_build_extraction_prompt()` around line 360:

```python
**CRITICAL: Pattern Granularity Rules**

When a migration involves MULTIPLE specific value replacements:
1. Create SEPARATE patterns for EACH value pair
2. DO NOT create generic catch-all patterns
3. Each pattern must have exact source and target values

Examples requiring SEPARATE patterns:
- Pixel conversions: Create separate rules for 576px→36rem, 768px→48rem, etc.
- Enum renames: Create separate rules for alignLeft→alignStart, alignRight→alignEnd
- String values: Create separate rules for button-group→action-group, chip-group→label-group

Description Format:
- Use specific values: "576px should be replaced with 36rem"
- NOT generic: "pixel values should be replaced with rem values"

Example Code:
- Keep minimal - only show the changed part
- Omit imports unless import path is changing
- Omit export/function wrappers
```

### Testing:

After implementing changes, test on the PatternFly upgrade guide to verify:
1. Breakpoint rules are split into 5 separate rules (not 1)
2. Toolbar alignment rules are split (alignLeft, alignRight separately)
3. Descriptions use specific values
4. Examples are minimal

---

## Additional Observations

### What the Generator Does WELL:

1. ✅ Comprehensive coverage (106 rules vs 56 - captured more patterns)
2. ✅ Good concern organization (granular file splitting)
3. ✅ Correct provider selection (nodejs vs builtin)
4. ✅ Proper detection patterns for most cases
5. ✅ Good documentation links

### Potential Future Enhancements:

1. Add validation step to check for "generic" patterns and suggest splits
2. Add pattern similarity detection to merge near-duplicates
3. Add confidence scoring to patterns
4. Generate test cases for each rule
