# Plan: Contributing TypeScript Provider Fixes to analyzer-lsp

## Overview

This document outlines the plan for contributing critical fixes to the Konveyor analyzer-lsp project to enable TypeScript/JavaScript analysis support.

## Fixes to Contribute

### 1. Add .tsx/.jsx File Support
**File:** `external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go`
**Lines:** 151-162

**Problem:** The nodejs service client only scans `.ts` and `.js` files, completely missing React components in `.tsx` files and JSX in `.jsx` files.

**Impact:** TypeScript React projects cannot be analyzed - the provider sees 0 files.

**Fix:**
```go
// Before (lines 151-162)
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

### 2. Skip node_modules Directory
**File:** `external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go`
**Lines:** 147-150

**Problem:** The code to skip `node_modules` is commented out, causing the provider to:
- Scan all dependency files (often 500+ files in React projects)
- Sleep 2 seconds per file (line 208) to avoid race conditions
- Result: 15+ minute hangs for simple projects

**Impact:** Analysis hangs/times out, making the provider unusable.

**Fix:**
```go
// Before (lines 147-150) - COMMENTED OUT
// TODO source-only mode
// if info.IsDir() && info.Name() == "node_modules" {
//     return filepath.SkipDir
// }

// After - UNCOMMENTED
// TODO source-only mode
if info.IsDir() && info.Name() == "node_modules" {
    return filepath.SkipDir
}
```

## Testing Performed

### Test Setup
- **Project:** React TypeScript app with 1 source file (Component.tsx)
- **Dependencies:** React, PropTypes, React-Router (~562 files in node_modules)
- **Rules:** TypeScript provider rules using `typescript.referenced` capability

### Before Fixes
- ❌ Analysis timeout after 5+ minutes
- ❌ .tsx files not found (0 violations detected)
- ❌ Provider scanned 562 files × 2 seconds = 1,124 seconds = 18.7 minutes

### After Fixes
- ✅ Analysis completes in 5-7 seconds
- ✅ .tsx files found and analyzed
- ✅ Violations correctly detected (tested with MyComponent, propTypes, react-router patterns)
- ✅ Only scans 1 source file (.tsx)

## Steps to Contribute

### 1. Fork and Branch
```bash
# Fork on GitHub: https://github.com/konveyor/analyzer-lsp → tsanders-rh/analyzer-lsp

# Add fork as remote
cd ~/Workspace/analyzer-lsp
git remote add fork git@github.com:tsanders-rh/analyzer-lsp.git

# Create fix branch
git checkout -b fix/nodejs-tsx-support

# Verify current branch
git status
```

### 2. Apply Fixes

Already applied locally:
- ✅ Fix 1: .tsx/.jsx support
- ✅ Fix 2: Skip node_modules

Verify fixes are in place:
```bash
# Check Fix 1 - should show .tsx and .jsx support
git diff external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go | grep -A 5 "ext := filepath.Ext"

# Check Fix 2 - should show uncommented node_modules skip
git diff external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go | grep -A 3 "node_modules"
```

### 3. Commit Changes
```bash
# Stage the changes
git add external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go

# Commit with descriptive message
git commit -s -m "Fix TypeScript/React analysis in nodejs service client

This commit fixes two critical issues preventing TypeScript/React analysis:

1. Add .tsx/.jsx file support: The nodejs client only scanned .ts and .js
   files, missing React components in .tsx files. Updated to recognize
   .tsx/.jsx extensions and use proper language IDs (typescriptreact/
   javascriptreact).

2. Skip node_modules directory: Uncommented the node_modules skip logic
   to prevent scanning dependency files. Without this, analysis could
   take 15+ minutes scanning hundreds of dependency files with 2-second
   delays per file.

Testing:
- React TypeScript project with 1 .tsx source file
- Before: Timeout after 5+ minutes, .tsx files not found
- After: Completes in 5-7 seconds, correctly detects violations

These fixes enable successful TypeScript/React codebase analysis with
the generic provider.

Signed-off-by: Your Name <your.email@example.com>"
```

### 4. Push to Fork
```bash
# Push branch to your fork
git push fork fix/nodejs-tsx-support

# Verify push succeeded
git log --oneline -1
```

**Status:** ✅ Completed
- Branch: `fix/nodejs-tsx-support`
- Commit: `66cef73 Fix TypeScript/React analysis in nodejs service client`
- Fork: https://github.com/tsanders-rh/analyzer-lsp
- Branch URL: https://github.com/tsanders-rh/analyzer-lsp/tree/fix/nodejs-tsx-support

### 5. Create Pull Request

**Status:** ⏳ Ready to create (waiting for additional testing)

**Command to create PR:**
```bash
cd ~/Workspace/analyzer-lsp
gh pr create --repo konveyor/analyzer-lsp --base main --head tsanders-rh:fix/nodejs-tsx-support --title "Fix TypeScript/React analysis in nodejs service client" --body "..."
```

**Title:**
```
Fix TypeScript/React analysis in nodejs service client
```

**Description:**
```markdown
## Summary

This PR fixes two critical issues preventing TypeScript/React analysis in the nodejs service client for the generic provider.

## Issues Fixed

### 1. Missing .tsx/.jsx File Support

**Problem:** The nodejs client only scanned `.ts` and `.js` files, completely missing React components in `.tsx` files.

**Impact:** TypeScript React projects could not be analyzed - the provider found 0 files.

**Fix:** Updated file extension handling to recognize `.tsx` and `.jsx` files and use appropriate language IDs (`typescriptreact`/`javascriptreact`).

### 2. Scans node_modules Directory

**Problem:** The code to skip `node_modules` was commented out, causing the provider to scan all dependency files with a 2-second delay per file.

**Impact:** Analysis would hang for 15+ minutes on typical React projects with ~500 dependency files.

**Fix:** Uncommented the `node_modules` skip logic to prevent scanning dependencies.

## Testing

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

## Files Changed

- `external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go`

## Checklist

- [x] Tested locally with TypeScript/React project
- [x] Verified .tsx files are now scanned
- [x] Verified node_modules is skipped
- [x] Verified analysis completes quickly (5-7s vs timeout)
- [x] Signed commits with `-s` flag
```

### 6. Follow Up

After PR is created:
1. Monitor PR for review feedback
2. Address any requested changes
3. Update documentation if needed
4. Help with additional testing if requested

## Additional Documentation Updates

If PR is accepted, consider follow-up PRs for:

1. **Provider Documentation:** Add TypeScript/JavaScript to supported providers list
2. **Capability Documentation:** Document `typescript.referenced` limitations:
   - Only finds top-level symbols (functions, classes, variables)
   - Cannot find methods, properties, imported types
   - Workarounds using `builtin.filecontent`
3. **Example Rules:** Add TypeScript/React migration rule examples

## Timeline

- **Day 1:** Fork repo and create branch ✅ (Completed)
- **Day 1:** Commit and push fixes ✅ (Completed)
- **Day 1:** Additional testing ⏳ (In Progress)
- **Day 1:** Create PR ⏳ (Pending - waiting for additional testing)
- **Day 2-7:** Respond to review feedback
- **Week 2+:** If accepted, work on documentation PRs

## Success Criteria

- ✅ PR merged to main branch
- ✅ Fixes included in next konveyor/kantra release
- ✅ TypeScript provider documented in official docs
- ✅ Community can use TypeScript analysis without custom builds

## Notes

- Keep fixes minimal and focused on the specific bugs
- Maintain backward compatibility
- Use existing code patterns and style
- Provide thorough testing evidence
- Be responsive to maintainer feedback
