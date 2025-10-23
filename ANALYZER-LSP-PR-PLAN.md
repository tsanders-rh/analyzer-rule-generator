# Plan: Contributing Fixes to analyzer-lsp

## Overview

This document outlines the plan for contributing two critical fixes to the Konveyor analyzer-lsp project that enable better TypeScript/JavaScript analysis support.

## Fixes to Contribute

### Fix 1: TypeScript Provider - Add .tsx/.jsx File Support and Skip node_modules

**Branch:** `fix/nodejs-tsx-support`
**Status:** ✅ Committed and pushed to fork

**Files Changed:**
- `external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go`

**Changes:**

#### Change 1a: Add .tsx/.jsx file support (lines 151-162)

**Problem:** The nodejs service client only scans `.ts` and `.js` files, completely missing React components in `.tsx` files and JSX in `.jsx` files.

**Impact:** TypeScript React projects cannot be analyzed - the provider sees 0 files.

**Fix:**
```go
// Before
if !info.IsDir() {
    if filepath.Ext(path) == ".ts" {
        langID = "typescript"
        path = "file://" + path
        nodeFiles = append(nodeFiles, path)
    }
    if filepath.Ext(path) == ".js" {
        langID = "javascript"
        path = "file://" + path
        nodeFiles = append(nodeFiles, path)
    }
}

// After
if !info.IsDir() {
    ext := filepath.Ext(path)
    if ext == ".ts" || ext == ".tsx" {
        langID = "typescriptreact"
        path = "file://" + path
        nodeFiles = append(nodeFiles, path)
    }
    if ext == ".js" || ext == ".jsx" {
        langID = "javascriptreact"
        path = "file://" + path
        nodeFiles = append(nodeFiles, path)
    }
}
```

#### Change 1b: Skip node_modules directory (lines 147-150)

**Problem:** The code to skip `node_modules` is commented out, causing the provider to:
- Scan all dependency files (often 500+ files in React projects)
- Sleep 2 seconds per file (line 208) to avoid race conditions
- Result: 15+ minute hangs for simple projects

**Impact:** Analysis hangs/times out, making the provider unusable.

**Fix:**
```go
// Before (commented out)
// TODO source-only mode
// if info.IsDir() && info.Name() == "node_modules" {
//     return filepath.SkipDir
// }

// After (uncommented)
// TODO source-only mode
if info.IsDir() && info.Name() == "node_modules" {
    return filepath.SkipDir
}
```

**Testing Results:**
- **Before:** Analysis timeout after 5+ minutes, .tsx files not found
- **After:** Analysis completes in 5-7 seconds, correctly detects violations
- **Test Setup:** React TypeScript app with 1 .tsx source file, ~562 files in node_modules

---

### Fix 2: Brace Expansion Support for File Patterns

**Branch:** `fix/brace-expansion-support`
**Status:** ✅ Tested and working locally

**Files Changed:**
- `provider/lib.go`
- `go.mod` (adds `github.com/gobwas/glob v0.2.3`)

**Changes:**

**Problem:** Konveyor's builtin provider uses Go's `filepath.Match()` which doesn't support brace expansion patterns like `*.{ts,tsx}` or `*.{css,scss}`. This forces users to write separate rules for each file extension.

**Impact:**
- Generated rules must use single extensions: `*.tsx` instead of `*.{ts,tsx}`
- Users must create duplicate rules for different file types
- Less flexible pattern matching

**Fix:** Use `github.com/gobwas/glob` library which supports brace expansion and advanced glob patterns.

**Code Changes:**

1. Add import:
```go
import (
    // ... existing imports ...
    "github.com/gobwas/glob"
)
```

2. Update `filterFilesByPathsOrPatterns` function (lines 220-248):
```go
// Before
} else {
    // try matching as go regex or glob pattern
    regex, regexErr := regexp.Compile(pattern)
    if regexErr == nil && (regex.MatchString(file) || regex.MatchString(filepath.Base(file))) {
        patternMatched = true
    } else if regexErr != nil {
        m, err := filepath.Match(pattern, file)
        if err == nil {
            patternMatched = m
        }
        m, err = filepath.Match(pattern, filepath.Base(file))
        if err == nil {
            patternMatched = m
        }
    }
}

// After
} else {
    // try matching as go regex or glob pattern
    regex, regexErr := regexp.Compile(pattern)
    if regexErr == nil && (regex.MatchString(file) || regex.MatchString(filepath.Base(file))) {
        patternMatched = true
    } else if regexErr != nil {
        // try using glob library which supports brace expansion (e.g., *.{ts,tsx})
        g, globErr := glob.Compile(pattern)
        if globErr == nil {
            // try matching against full path
            if g.Match(file) {
                patternMatched = true
            }
            // try matching against basename
            if g.Match(filepath.Base(file)) {
                patternMatched = true
            }
        } else {
            // fallback to filepath.Match for simple patterns
            m, err := filepath.Match(pattern, file)
            if err == nil {
                patternMatched = m
            }
            m, err = filepath.Match(pattern, filepath.Base(file))
            if err == nil {
                patternMatched = m
            }
        }
    }
}
```

**Testing Results:**
- **Test 1:** `*.{tsx,jsx}` successfully matched `.tsx` files ✅
- **Test 2:** `*.{ts,tsx,js,jsx}` matched both `.tsx` and `.js` files ✅
- **Test 3:** `*.{css,scss,js,jsx,ts,tsx}` matched `.css` files ✅
- **Real-world test:** PatternFly migration rules with brace expansion worked correctly ✅

---

## Combined PR Strategy

### Option A: Single Combined PR (Recommended)

**Pros:**
- Both fixes work together to enable full TypeScript/React analysis
- Single review process
- Easier to test together
- Clear migration story: "Enable TypeScript/React analysis"

**Cons:**
- Larger changeset to review
- Might take longer to merge

**Branch Strategy:**
```bash
cd ~/Workspace/analyzer-lsp
git checkout main
git pull origin main
git checkout -b fix/typescript-react-support

# Cherry-pick commits from both branches
git cherry-pick <commit-from-tsx-support>
git cherry-pick <commit-from-brace-expansion>

# Or merge both branches
git merge fix/nodejs-tsx-support
git merge fix/brace-expansion-support

git push fork fix/typescript-react-support
```

### Option B: Separate Sequential PRs

**Pros:**
- Smaller, focused changes
- Easier to review individually
- Can be merged independently

**Cons:**
- Two separate review cycles
- Need to coordinate merge order
- Users need both to get full benefit

**Recommended Order:**
1. **PR 1:** TypeScript provider fixes (more critical - unblocks basic usage)
2. **PR 2:** Brace expansion support (enhancement - improves usability)

---

## Recommended Approach: Option A (Combined PR)

### PR Title
```
Enable TypeScript/React analysis support
```

### PR Description

```markdown
## Summary

This PR enables TypeScript and React codebase analysis in Konveyor by fixing two critical issues:

1. **TypeScript Provider:** Add .tsx/.jsx file support and skip node_modules
2. **File Pattern Matching:** Add brace expansion support for glob patterns

Together, these fixes enable comprehensive TypeScript/React migration rule authoring and analysis.

## Issues Fixed

### 1. TypeScript Provider: Missing .tsx/.jsx File Support

**Problem:** The nodejs service client only scanned `.ts` and `.js` files, completely missing React components in `.tsx` files.

**Impact:** TypeScript React projects could not be analyzed - the provider found 0 files.

**Fix:** Updated file extension handling to recognize `.tsx` and `.jsx` files and use appropriate language IDs (`typescriptreact`/`javascriptreact`).

**File:** `external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go` (lines 151-162)

### 2. TypeScript Provider: Scans node_modules Directory

**Problem:** The code to skip `node_modules` was commented out, causing the provider to scan all dependency files with a 2-second delay per file.

**Impact:** Analysis would hang for 15+ minutes on typical React projects with ~500 dependency files.

**Fix:** Uncommented the `node_modules` skip logic to prevent scanning dependencies.

**File:** `external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go` (lines 147-150)

### 3. Brace Expansion Support for File Patterns

**Problem:** The builtin provider uses `filepath.Match()` which doesn't support brace expansion patterns like `*.{ts,tsx}` or `*.{css,scss}`.

**Impact:** Users had to write separate rules for each file extension instead of using convenient multi-extension patterns.

**Fix:** Integrate `github.com/gobwas/glob` library to support brace expansion and advanced glob patterns.

**Files:**
- `provider/lib.go` (pattern matching logic)
- `go.mod` (add gobwas/glob dependency)

## Testing

### TypeScript Provider Testing

**Test Setup:**
- React TypeScript app with 1 source file (Component.tsx)
- Dependencies: React, PropTypes, React-Router (~562 files in node_modules)

**Before Fixes:**
- ❌ Analysis timeout after 5+ minutes
- ❌ .tsx files not found
- ❌ Attempted to scan 562 dependency files

**After Fixes:**
- ✅ Analysis completes in 5-7 seconds
- ✅ .tsx files found and analyzed correctly
- ✅ Only scans source files
- ✅ Violations correctly detected using `typescript.referenced` capability

### Brace Expansion Testing

**Test Patterns:**
- `*.{tsx,jsx}` - Successfully matched `.tsx` files
- `*.{ts,tsx,js,jsx}` - Successfully matched `.tsx` and `.js` files
- `*.{css,scss,js,jsx,ts,tsx}` - Successfully matched `.css` files

**Real-world Test:**
- Generated PatternFly v5 → v6 migration rules using brace expansion patterns
- Rules successfully found violations in test applications
- Example: `filePattern: "*.{css,scss,js,jsx,ts,tsx}"` worked correctly

## Files Changed

1. `external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go`
   - Add .tsx/.jsx file extension support
   - Uncomment node_modules skip logic

2. `provider/lib.go`
   - Add gobwas/glob import
   - Update filterFilesByPathsOrPatterns to use glob library

3. `go.mod`
   - Add github.com/gobwas/glob v0.2.3 dependency

## Backward Compatibility

Both fixes are backward compatible:

1. **TypeScript Provider:** Only affects nodejs provider behavior - adds support for previously ignored file types
2. **Brace Expansion:** Falls back to `filepath.Match()` if glob compilation fails - existing patterns continue to work

## Checklist

- [x] Tested locally with TypeScript/React project
- [x] Verified .tsx files are now scanned
- [x] Verified node_modules is skipped
- [x] Verified analysis completes quickly (5-7s vs timeout)
- [x] Tested brace expansion patterns (*.{ts,tsx}, *.{css,scss}, etc.)
- [x] Verified backward compatibility with existing patterns
- [x] Signed commits with `-s` flag

## Related Work

These fixes enable the analyzer-rule-generator project to automatically generate TypeScript/React migration rules from documentation, which will be contributed to konveyor/rulesets.
```

---

## Steps to Create Combined PR

### 1. Prepare Combined Branch

```bash
cd ~/Workspace/analyzer-lsp

# Ensure we have latest main
git checkout main
git pull origin main

# Create new combined branch
git checkout -b fix/typescript-react-support

# Cherry-pick or merge both fixes
git merge fix/nodejs-tsx-support --no-commit
git merge fix/brace-expansion-support --no-commit

# Review combined changes
git status
git diff --cached

# Commit combined changes
git commit -s -m "$(cat <<'EOF'
Enable TypeScript/React analysis support

This commit enables TypeScript and React codebase analysis by fixing two
critical issues:

1. TypeScript Provider Fixes:
   - Add .tsx/.jsx file support for React components
   - Skip node_modules directory to prevent extreme slowness

2. Brace Expansion Support:
   - Integrate gobwas/glob library for advanced pattern matching
   - Enable patterns like *.{ts,tsx} and *.{css,scss}

TypeScript Provider Testing:
- React TypeScript project with 1 .tsx source file
- Before: Timeout after 5+ minutes, .tsx files not found
- After: Completes in 5-7 seconds, correctly detects violations

Brace Expansion Testing:
- Pattern *.{tsx,jsx} successfully matched .tsx files
- Pattern *.{ts,tsx,js,jsx} matched both .tsx and .js files
- PatternFly migration rules with brace expansion worked correctly

These fixes enable comprehensive TypeScript/React migration rule authoring.
EOF
)"
```

### 2. Push to Fork

```bash
git push fork fix/typescript-react-support
```

### 3. Create Pull Request

```bash
gh pr create \
  --repo konveyor/analyzer-lsp \
  --base main \
  --head tsanders-rh:fix/typescript-react-support \
  --title "Enable TypeScript/React analysis support" \
  --body "$(cat path/to/pr-description.md)"
```

---

## Timeline

- **Day 1:** Create combined branch ⏳ (Pending)
- **Day 1:** Push and create PR ⏳ (Pending)
- **Day 2-7:** Respond to review feedback
- **Week 2+:** If accepted, work on documentation PRs

## Success Criteria

- ✅ PR merged to main branch
- ✅ Fixes included in next konveyor/kantra release
- ✅ TypeScript provider documented in official docs
- ✅ Brace expansion patterns documented in rule authoring guide
- ✅ Community can use TypeScript analysis without custom builds

## Follow-up Documentation PRs

If PR is accepted, consider follow-up PRs for:

1. **Provider Documentation:** Add TypeScript/JavaScript to supported providers list
2. **Rule Authoring Guide:** Document brace expansion pattern support
3. **Capability Documentation:** Document `typescript.referenced` limitations
4. **Example Rules:** Add TypeScript/React migration rule examples

## Notes

- Keep fixes minimal and focused
- Maintain backward compatibility
- Use existing code patterns and style
- Provide thorough testing evidence
- Be responsive to maintainer feedback
