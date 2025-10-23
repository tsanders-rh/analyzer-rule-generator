# Steps to Create Combined PR for TypeScript/React Support

## Overview

Create a single PR that combines both fixes:
1. TypeScript Provider: Add .tsx/.jsx support + skip node_modules
2. Brace Expansion: Support glob patterns like *.{ts,tsx}

## Prerequisites

- ✅ Fork created: https://github.com/tsanders-rh/analyzer-lsp
- ✅ Fix 1 branch: `fix/nodejs-tsx-support` (committed and pushed)
- ✅ Fix 2 branch: `fix/brace-expansion-support` (committed and pushed)

## Step-by-Step Instructions

### Step 1: Navigate to Repository and Update Main

```bash
cd ~/Workspace/analyzer-lsp

# Ensure main is up to date
git checkout main
git fetch origin
git pull origin main
```

### Step 2: Create Combined Branch

```bash
# Create new branch for combined PR
git checkout -b fix/typescript-react-support
```

### Step 3: Merge Both Fix Branches

```bash
# Merge TypeScript provider fixes
git merge fix/nodejs-tsx-support --no-edit

# Merge brace expansion fixes
git merge fix/brace-expansion-support --no-edit
```

**Expected result:** Both sets of changes should merge cleanly since they modify different files.

### Step 4: Verify Combined Changes

```bash
# Check status
git status

# Review all changes
git log --oneline -5

# See diff from main
git diff main
```

**Files that should be modified:**
1. `external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go`
2. `provider/lib.go`
3. `go.mod`
4. `external-providers/generic-external-provider/go.mod` (if modified)

### Step 5: Rebuild to Verify Everything Works

```bash
# Clean build
make build

# Verify binaries were created
ls -la konveyor-analyzer
ls -la external-providers/generic-external-provider/generic-external-provider
```

### Step 6: Add Test Files to PR (Recommended)

Copy test files to the analyzer-lsp repository:

```bash
# Create test directory in analyzer-lsp
mkdir -p ~/Workspace/analyzer-lsp/test

# Copy test files
cp /Users/tsanders/Workspace/analyzer-rule-generator/pr-test-files/* ~/Workspace/analyzer-lsp/test/

# Add to git
cd ~/Workspace/analyzer-lsp
git add test/
git commit -s -m "Add test files for TypeScript/React support"
```

This makes it easier for reviewers to verify the fixes.

### Step 7: Run Quick Test (Optional but Recommended)

```bash
# Test with the brace expansion test rules
./konveyor-analyzer \
  --provider-settings=/Users/tsanders/Workspace/analyzer-rule-generator/examples/test-apps/typescript/builtin-provider-settings.json \
  --rules=/Users/tsanders/Workspace/analyzer-rule-generator/examples/test-apps/typescript/brace-expansion-test.yaml \
  --output-file=/tmp/combined-pr-test-output.yaml \
  --verbose=1

# Check for violations (should find matches)
grep -c "violations:" /tmp/combined-pr-test-output.yaml
```

### Step 7: Create Combined Commit (If Needed)

If you want a single clean commit instead of multiple merge commits:

```bash
# Squash the commits into one
git reset --soft main

# Create single combined commit
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

These fixes enable comprehensive TypeScript/React migration rule authoring
and are needed for PatternFly v5 to v6 migration support.

Fixes enable trialing Konveyor AI for PatternFly migrations.
EOF
)"
```

**OR** if you want to keep the individual commits (cleaner history):

```bash
# Just verify the commits look good
git log --oneline main..HEAD
```

### Step 8: Push Combined Branch to Fork

```bash
# Push to your fork
git push fork fix/typescript-react-support
```

**Expected output:**
```
To https://github.com/tsanders-rh/analyzer-lsp.git
 * [new branch]      fix/typescript-react-support -> fix/typescript-react-support
```

### Step 9: Create Pull Request

Using GitHub CLI:

```bash
cd ~/Workspace/analyzer-lsp

gh pr create \
  --repo konveyor/analyzer-lsp \
  --base main \
  --head tsanders-rh:fix/typescript-react-support \
  --title "Enable TypeScript/React analysis support" \
  --body "$(cat <<'EOF'
## Summary

This PR enables TypeScript and React codebase analysis in Konveyor by fixing two critical issues that currently prevent the generic provider from analyzing TypeScript/React codebases.

**Context:** These fixes are needed to trial Konveyor AI for a PatternFly v5 → v6 migration on a TypeScript/React codebase.

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

**Implementation Note:** This fix adds glob pattern support as an additional fallback in the existing pattern matching chain. The code already tries regex first (for content matching), and this PR adds glob support before falling back to `filepath.Match()`. This maintains backward compatibility - existing patterns continue to work, and both regex and glob patterns are now supported for file matching.

**Pattern Matching Flow:**
1. Try regex pattern matching (existing)
2. Try glob pattern matching (NEW - supports `*.{ts,tsx}`)
3. Fall back to `filepath.Match()` (existing)

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
- `*.{tsx,jsx}` - Successfully matched `.tsx` files ✅
- `*.{ts,tsx,js,jsx}` - Successfully matched `.tsx` and `.js` files ✅
- `*.{css,scss,js,jsx,ts,tsx}` - Successfully matched `.css` files ✅

**Real-world Test:**
- Generated PatternFly v5 → v6 migration rules using brace expansion patterns
- Rules successfully found violations in test applications
- Example: `filePattern: "*.{css,scss,js,jsx,ts,tsx}"` worked correctly

### Test Files for Reviewers

This PR includes test files in the `test/` directory for easy verification:

**`test/test-tsx-support.yaml`** - Verifies .tsx file detection:
```yaml
- ruleID: test-tsx-support-00000
  description: Test that .tsx files are scanned
  when:
    builtin.filecontent:
      pattern: "import.*React"
      filePattern: "*.tsx"
  message: Found React import in .tsx file
```

**`test/test-brace-expansion.yaml`** - Verifies brace expansion patterns:
```yaml
- ruleID: test-brace-expansion-00000
  description: Test brace expansion with *.{ts,tsx,js,jsx}
  when:
    builtin.filecontent:
      pattern: "React"
      filePattern: "*.{ts,tsx,js,jsx}"
  message: Found React reference using brace expansion pattern

- ruleID: test-brace-expansion-00010
  description: Test brace expansion with *.{css,scss}
  when:
    builtin.filecontent:
      pattern: "--pf-"
      filePattern: "*.{css,scss}"
  message: Found PatternFly CSS variable using brace expansion
```

**`test/README.md`** - Quick test instructions (5 minutes)

Reviewers can test the fixes in ~5 minutes using the provided test files and sample React TypeScript app.

## Files Changed

1. `external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go`
   - Add .tsx/.jsx file extension support
   - Uncomment node_modules skip logic

2. `provider/lib.go`
   - Add gobwas/glob import
   - Update filterFilesByPathsOrPatterns to use glob library

3. `go.mod`
   - Add github.com/gobwas/glob v0.2.3 dependency

4. `test/test-tsx-support.yaml` (NEW)
   - Test rule to verify .tsx files are scanned

5. `test/test-brace-expansion.yaml` (NEW)
   - Test rules to verify brace expansion patterns work

6. `test/README.md` (NEW)
   - Quick test instructions for reviewers (5 minutes)

## Backward Compatibility

Both fixes are backward compatible:

1. **TypeScript Provider:** Only affects nodejs provider behavior - adds support for previously ignored file types

2. **Brace Expansion:** Extends the existing pattern matching chain without breaking changes:
   - Existing glob patterns like `*.tsx` continue to work
   - Regex patterns (already supported) continue to work
   - NEW: Brace expansion patterns like `*.{ts,tsx}` now work
   - The implementation tries each approach in order: regex → glob → filepath.Match()
   - If one fails, it falls back to the next approach

**Why Glob Instead of Regex-Only:**
- File patterns using glob syntax (`*.{ts,tsx}`) are more intuitive than regex (`.*\.(ts|tsx)$`)
- Matches user expectations for file matching (similar to shell globs)
- Backward compatible with existing rules
- Users can still use regex patterns if they need more complex matching

## Use Case

These fixes enable trialing Konveyor AI for PatternFly v5 → v6 migrations on TypeScript/React codebases. The workflow is:

1. Generate migration rules from PatternFly v6 upgrade documentation
2. Use TypeScript provider to analyze React components
3. Identify migration needs (component renames, prop changes, etc.)
4. Use Konveyor AI to suggest fixes

This could serve as a valuable use case / case study for Konveyor AI with TypeScript/React migrations.

## Checklist

- [x] Tested locally with TypeScript/React project
- [x] Verified .tsx files are now scanned
- [x] Verified node_modules is skipped
- [x] Verified analysis completes quickly (5-7s vs timeout)
- [x] Tested brace expansion patterns (*.{ts,tsx}, *.{css,scss}, etc.)
- [x] Verified backward compatibility with existing patterns
- [x] Signed commits with `-s` flag
- [x] Build succeeds with `make build`
- [x] Included test files for reviewers to verify fixes
EOF
)"
```

### Step 10: Verify PR Was Created

```bash
# List your open PRs
gh pr list --repo konveyor/analyzer-lsp --author tsanders-rh

# View the PR you just created
gh pr view --repo konveyor/analyzer-lsp --web
```

## Troubleshooting

### Issue: Merge Conflicts

If you get merge conflicts:

```bash
# Abort and try manual merge
git merge --abort

# Manually cherry-pick commits
git cherry-pick <commit-from-tsx-support>
git cherry-pick <commit-from-brace-expansion>
```

### Issue: Push Rejected

If push is rejected:

```bash
# Force push (safe since this is a new branch)
git push fork fix/typescript-react-support --force
```

### Issue: Wrong Commits in Branch

If you need to start over:

```bash
# Delete local branch
git checkout main
git branch -D fix/typescript-react-support

# Delete remote branch
git push fork --delete fix/typescript-react-support

# Start over from Step 2
```

## Post-PR Tasks

After creating the PR:

1. **Monitor for CI/CD failures:**
   ```bash
   gh pr checks --repo konveyor/analyzer-lsp
   ```

2. **Respond to review comments promptly**

3. **Update PR if requested:**
   ```bash
   # Make changes to files
   git add <files>
   git commit -s -m "Address review feedback: <description>"
   git push fork fix/typescript-react-support
   ```

## Success Indicators

✅ PR created successfully
✅ CI/CD checks pass (green checkmarks)
✅ No merge conflicts with main
✅ All commits signed with DCO (`-s` flag)
✅ Clear description and test evidence provided

## Next Steps After PR Merge

Once merged:
1. Delete local branches: `git branch -D fix/nodejs-tsx-support fix/brace-expansion-support fix/typescript-react-support`
2. Update local main: `git checkout main && git pull origin main`
3. Consider documentation PR for TypeScript provider usage
4. Test with next analyzer-lsp release
