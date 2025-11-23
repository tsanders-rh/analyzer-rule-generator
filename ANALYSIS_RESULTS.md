# Analysis Results: Improved PatternFly v5→v6 Rules

## Test Environment
- **Ruleset**: `examples/output/patternfly-v6/improved/` (158 rules)
- **Codebase**: tackle2-ui
- **Analysis Output**: `/tmp/patternfly-test-20251123-140040/output.yaml`
- **Total Incidents**: 1,313 across 28 violation types

## Summary

### Overall Assessment
The improved rules generate **significant false positives** due to overly broad pattern matching. The main issues are:

1. **Generic prop name matching** - Rules match prop names globally without component context
2. **Common word matching** - Rules match common identifiers like "title", "description", "isActive"
3. **No component scoping** - Detections don't verify they're on the correct component

### Estimated False Positive Rate: **~60-80%**

## Detailed Analysis by Rule Type

### 🔴 HIGH FALSE POSITIVE RATE (>70%)

#### 1. `isActive` → `isPressed` (25 incidents)
**Rule**: `patternfly-v5-to-patternfly-v6-component-props-00000`
**Detection**: `builtin.filecontent` with pattern `isActive`

**Issue**: Matches ALL occurrences of "isActive" in JSX/TSX files, not just on Button components

**False Positives Identified**:
- ✗ Line 34: `<BreadcrumbItem isActive={isLast}>` - This is BreadcrumbItem, NOT Button
- ✗ Line 106: `<BreadcrumbItem to="#" isActive>` - BreadcrumbItem, NOT Button
- ✗ Line 115: `<BreadcrumbItem to="#" isActive>` - BreadcrumbItem, NOT Button
- ✗ getActiveItemDerivedState.ts - Variable name `isActive`, not a prop

**True Positive Rate**: Estimated **<10%**
**Recommendation**: Change to `nodejs.referenced` for Button component or use more specific pattern

---

#### 2. `title` → `titleText` (370 incidents!!!)
**Rule**: `patternfly-v5-to-patternfly-v6-renamed-props-00020`
**Detection**: `nodejs.referenced` with pattern `title`

**Issue**: Matches EVERY occurrence of the word "title" as an identifier in the codebase

**False Positives**:
- ✗ Type definitions: `title: string;` in interfaces
- ✗ Object properties: `{ title: "My Title" }`
- ✗ Function parameters: `function setTitle(title: string)`
- ✗ HTML attributes: Not even React components!

**True Positive Rate**: Estimated **<5%**
**This is the worst offender** - 370 incidents with maybe 10-20 actual issues

---

#### 3. `description` → `bodyText` (135 incidents)
**Rule**: `patternfly-v5-to-patternfly-v6-renamed-props-00010`
**Detection**: `nodejs.referenced` with pattern `description`

**Issue**: Same as `title` - matches all occurrences of "description" as identifier

**False Positives**:
- ✗ Type definitions
- ✗ Object properties
- ✗ Function parameters
- ✗ Variable names

**True Positive Rate**: Estimated **<5%**

---

#### 4. `isDisabled` → `disabled` (137 incidents)
**Rule**: `patternfly-v5-to-patternfly-v6-component-props-00380`

**Issue**: Matches isDisabled on ALL components, but this prop change may only apply to specific components

**True Positive Rate**: Estimated **30-50%** (needs verification)

---

#### 5. `isExpanded` → `expanded` (84 incidents)
**Rule**: `patternfly-v5-to-patternfly-v6-component-props-00390`

**Issue**: Same as isDisabled - may match unrelated components

**True Positive Rate**: Estimated **30-50%**

---

#### 6. `isOpen` → `open` (203 incidents)
**Rule**: `patternfly-v5-to-patternfly-v6-component-props-00400`

**Issue**: Matches isOpen on ALL components

**True Positive Rate**: Estimated **30-50%**

---

### 🟡 MEDIUM FALSE POSITIVE RATE (30-60%)

#### 7. `<Text>` → `<Content>` (78 incidents)
**Rule**: `patternfly-v5-to-patternfly-v6-components-00040`

**Issue**: May match non-PatternFly Text components or custom Text components

**True Positive Rate**: Estimated **50-70%**
**Needs**: Verification that these are PatternFly Text components

---

#### 8. `TextContent` → `Content` (71 incidents)
**Rule**: `patternfly-v5-to-patternfly-v6-component-rename-00020`

**True Positive Rate**: Estimated **70-90%** (more specific component name)

---

### 🟢 LOW FALSE POSITIVE RATE (<30%)

#### 9. Modal Imports (34 incidents each)
**Rules**:
- `deprecated-components-00050`: Deprecated Modal import
- `promoted-components-00010`: Next Modal import

**Issue**: These are import-specific and likely accurate

**True Positive Rate**: Estimated **80-95%**

---

#### 10. CSS Variables (55 total incidents)
**Rules**:
- `css-tokens-00000`: --pf-v5-global-- → --pf-t--global-- (43 incidents)
- `css-variables-00000`: --pf-v5-global-- → --pf-t--global-- (12 incidents)
- `css-variables-00010`: --pf-v5-global → --pf-v6-global (12 incidents)

**True Positive Rate**: Estimated **90-95%**
**Note**: These are CSS-specific patterns, less likely to have false positives

---

#### 11. Component-Specific Renames (Low incident count)
**Rules** with 1-5 incidents:
- MastheadBrand → MastheadLogo (1 incident)
- Masthead structure (1 incident)
- Chip → Label (1 incident)
- ToolbarChipGroup → ToolbarLabelGroup (1 incident)

**True Positive Rate**: Estimated **80-95%**

---

## Root Cause Analysis

### Problem 1: Overly Broad `builtin.filecontent` Patterns
Rules using simple string patterns like `isActive`, `alignRight` match everywhere in files.

**Example**:
```yaml
when:
  builtin.filecontent:
    pattern: isActive
    filePattern: \.(j|t)sx?$
```

This matches:
- ✗ `<Button isActive />` ✓ CORRECT
- ✗ `<BreadcrumbItem isActive />` ✗ WRONG COMPONENT
- ✗ `const isActive = true` ✗ VARIABLE NAME
- ✗ `function checkIsActive()` ✗ FUNCTION NAME

---

### Problem 2: Overly Broad `nodejs.referenced` Patterns
Rules using common words like `title`, `description` as patterns match ALL identifier references.

**Example**:
```yaml
when:
  nodejs.referenced:
    pattern: title
```

This matches:
- ✗ `<NotAuthorized title="..." />` ✓ CORRECT (but rare)
- ✗ `interface Foo { title: string; }` ✗ TYPE DEFINITION
- ✗ `const title = "My Title"` ✗ VARIABLE
- ✗ `{ title: "..." }` ✗ OBJECT PROPERTY
- ✗ `function setTitle(title: string)` ✗ PARAMETER

---

## Recommendations

### Immediate Fixes Needed

#### 1. Remove Generic Identifier Rules
**DELETE or FIX these rules** - they cause massive false positives:
- `title` → `titleText` (370 FPs)
- `description` → `bodyText` (135 FPs)
- `isActive`, `isDisabled`, `isExpanded`, `isOpen` without component context

#### 2. Add Component Context to Prop Rules
For prop changes that only apply to specific components, the pattern MUST include component name:

**Bad**:
```yaml
when:
  builtin.filecontent:
    pattern: isActive
```

**Better** (but still not perfect):
```yaml
when:
  builtin.filecontent:
    pattern: <Button.*isActive
```

**Best** (if nodejs provider supported it):
```yaml
when:
  nodejs.referenced:
    pattern: Button
    # Then check for isActive prop
```

#### 3. Focus on High-Confidence Rules
Keep rules that have low false positive rates:
- ✅ Import path changes
- ✅ CSS variable changes
- ✅ Specific component renames (not common words)
- ✅ Structural changes (like Masthead structure)

#### 4. Add Severity/Confidence Levels
Mark rules with high false positive potential as "needs-review" or lower category.

---

## Breakdown by Accuracy

### High Accuracy (>80% true positives) - 155 incidents
- CSS variables: 55 incidents
- Modal imports: 68 incidents
- Specific component renames: 32 incidents

### Medium Accuracy (50-80% true positives) - ~400 incidents
- Text/TextContent → Content: 149 incidents
- Component-specific props: ~250 incidents

### Low Accuracy (<50% true positives) - ~758 incidents
- title: 370 incidents (Mostly false)
- description: 135 incidents (Mostly false)
- isActive/isDisabled/isExpanded/isOpen: 253 incidents (Many false)

---

## Recommended Actions

### Short Term (Fix Critical Issues)
1. **Remove** rules for `title`, `description` - too generic
2. **Review** all `isActive`, `isDisabled`, `isExpanded`, `isOpen` rules
3. **Keep** CSS variables, import paths, specific component renames

### Medium Term (Improve Detection)
1. Add component-scoped detection for prop changes
2. Create combo rules (component + prop pattern)
3. Add exclusion patterns for type definitions, object properties

### Long Term (Architecture)
1. Investigate if nodejs provider can detect props on specific components
2. Create validation layer to filter obvious false positives
3. Add confidence scoring to rules

---

## Conclusion

While the improved rule generator successfully created **11x more specific breakpoint rules**, it also introduced **major false positive issues** by:
1. Using overly generic patterns for common prop names
2. Not scoping prop detections to specific components
3. Matching common identifiers like "title" and "description" everywhere

**Overall effectiveness**: ~40% of incidents are likely true positives (525 out of 1313)

**Next steps**: Focus on improving pattern specificity and component-scoped detection strategies.
