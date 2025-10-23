# Response to Engineer's Feedback on File Pattern Matching

## Their Feedback

> "I am not sure if I follow the file match pattern issue, it'd be better to use regex patterns instead of glob patterns in rules as we already use regexes in other providers extensively."

## Clarification Needed

I want to make sure I understand the suggestion correctly. Are you proposing:

**Option A:** Use regex instead of glob for the `filePattern` field?
```yaml
# Instead of glob syntax
filePattern: "*.{ts,tsx}"

# Use regex syntax
filePattern: ".*\\.(ts|tsx)$"
```

**Option B:** Something else?

## Current State Analysis

### Two Different Pattern Types in Rules

1. **Content Patterns** (already use regex ✅)
   - Field: `pattern` in `builtin.filecontent`
   - Already uses: `regexp2` library for regex matching
   - Example: `pattern: "import.*React"` matches file content

2. **File Patterns** (currently limited glob)
   - Field: `filePattern` in `builtin.filecontent`
   - Currently uses: `filepath.Match()` - only supports `*.ext` syntax
   - Example: `filePattern: "*.tsx"` matches filenames
   - **Issue:** Can't match multiple extensions without brace expansion

### Current Code Path

```go
// provider/lib.go - filterFilesByPathsOrPatterns()

// First tries regex on the full pattern
regex, regexErr := regexp.Compile(pattern)
if regexErr == nil && (regex.MatchString(file) || regex.MatchString(filepath.Base(file))) {
    patternMatched = true
}

// If not valid regex, falls back to filepath.Match
else if regexErr != nil {
    m, err := filepath.Match(pattern, file)
    // ...
}
```

The code **already tries regex first**, then falls back to `filepath.Match()` if the pattern isn't valid regex.

## The Problem with Current Approach

When users write rules like:
```yaml
filePattern: "*.tsx"
```

This pattern:
- Is **not** valid regex (throws error)
- Falls back to `filepath.Match()`
- Works for single extensions
- **Doesn't work** for `*.{ts,tsx}` (brace expansion not supported by `filepath.Match()`)

## Proposed Solutions

### Solution 1: Use Regex for File Patterns (Engineer's Suggestion?)

**Pros:**
- Consistent with content pattern matching
- Already partially supported (regex tried first)
- More powerful pattern matching

**Cons:**
- **Breaking change:** Existing rules use glob syntax `*.tsx`
- **User confusion:** `*.tsx` is not valid regex, would need to be `.*\.tsx$`
- **Migration needed:** All existing rules would break
- **Less intuitive:** Glob syntax is more familiar for file matching

**Example Migration Required:**
```yaml
# Current (glob syntax)
filePattern: "*.tsx"

# Would need to change to (regex syntax)
filePattern: ".*\\.tsx$"

# Multi-extension would be:
filePattern: ".*\\.(ts|tsx)$"
```

### Solution 2: Add Glob Support (Current PR Approach)

**Pros:**
- **Backward compatible:** Existing `*.tsx` patterns still work
- **Intuitive:** Glob syntax familiar for file matching
- **Extends capability:** Adds brace expansion without breaking changes
- **Fallback chain:** Try regex → try glob → try filepath.Match()

**Cons:**
- Adds another library dependency

**Code Flow:**
```go
// Try regex first (existing)
regex, regexErr := regexp.Compile(pattern)
if regexErr == nil && regex.MatchString(file) {
    patternMatched = true
}
// Try glob (NEW)
else if regexErr != nil {
    g, globErr := glob.Compile(pattern)
    if globErr == nil && g.Match(file) {
        patternMatched = true
    }
    // Fall back to filepath.Match (existing)
    else {
        m, _ := filepath.Match(pattern, file)
        patternMatched = m
    }
}
```

### Solution 3: Support Both Explicitly

Add a `patternType` field to rules:
```yaml
# Glob pattern (default for backward compatibility)
filePattern: "*.{ts,tsx}"
patternType: "glob"

# Regex pattern
filePattern: ".*\\.(ts|tsx)$"
patternType: "regex"
```

**Pros:**
- Clear and explicit
- Supports both use cases
- No guessing/fallback needed

**Cons:**
- More verbose
- Requires rule schema changes

## My Recommendation

**Keep the PR approach (Solution 2)** for these reasons:

1. **Backward Compatibility:**
   - Existing rules with `*.tsx` continue to work
   - No migration needed for existing rulesets

2. **Intuitive for Users:**
   - File patterns use file-matching syntax (globs)
   - Content patterns use content-matching syntax (regex)
   - This matches user expectations

3. **Already Partially There:**
   - The code already tries regex first
   - Just adding glob as another fallback before `filepath.Match()`

4. **Real-World Use:**
   - Rule authors expect `*.{ts,tsx}` to work (common shell/glob syntax)
   - Regex for file matching is less intuitive: `.*\\.tsx$` vs `*.tsx`

## Questions for Discussion

1. **Is there a reason to prefer regex file patterns?**
   - Performance concern with glob library?
   - Desire to standardize on regex everywhere?

2. **Backward compatibility concern?**
   - If we switch to regex-only, what happens to existing `*.tsx` patterns?
   - Are you proposing to keep both (current PR) or replace glob with regex?

3. **Alternative approach?**
   - Would you prefer Solution 3 (explicit `patternType` field)?
   - Or keep current approach but document that both regex and glob work?

## Code Example: Both Work with Current PR

```yaml
# These would all work:

# Glob syntax (simple)
filePattern: "*.tsx"

# Glob syntax (brace expansion)
filePattern: "*.{ts,tsx}"

# Regex syntax (for complex cases)
filePattern: ".*\\.(ts|tsx)$"

# Regex syntax (path matching)
filePattern: "^src/.*\\.tsx$"
```

The fallback chain handles all cases naturally.

## Bottom Line

I'm happy to adjust the approach based on your preferences! The key question is:

**Do you want to:**
- A) Keep glob support for file patterns (backward compatible, intuitive)
- B) Switch to regex-only for file patterns (breaking change, more powerful)
- C) Support both explicitly with a `patternType` field

Let me know which direction you'd prefer and I can update the PR accordingly!

---

## Additional Context: Why This Matters for PatternFly Migration

The use case is generating rules for PatternFly v5 → v6 TypeScript/React migrations:

```yaml
# Need to scan TypeScript AND React files
- ruleID: find-deprecated-component
  when:
    builtin.filecontent:
      pattern: "OldComponent"
      filePattern: "*.{ts,tsx,js,jsx}"  # All TS/JS files
  message: Component renamed

# Need to scan CSS AND TypeScript files
- ruleID: find-old-css-variable
  when:
    builtin.filecontent:
      pattern: "--pf-v5-global-.*"
      filePattern: "*.{css,scss,ts,tsx}"  # CSS vars in CSS or inline styles
  message: CSS variable updated
```

Without brace expansion (or regex), we'd need separate rules for each file type, making rulesets much more verbose.
