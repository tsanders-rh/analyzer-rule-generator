# Go Provider EOF Error - Root Cause Analysis & Solution

## Problem Summary

When running `kantra test` on Go 1.17→1.18 migration rules, 8 tests fail with:
```
error="rpc error: code = Unavailable desc = error reading from server: EOF" provider=go
```

## Root Cause

**Primary Issue**: System-wide `go.work` file interference
- Location: `/Users/tsanders/go.work`
- Impact: When kantra runs the Go LSP (Language Server Protocol), it detects this workspace file
- Result: LSP tries to use workspace mode but test modules aren't in the workspace
- Consequence: LSP crashes with EOF error when trying to analyze test modules

**Secondary Issue**: Missing `go.sum` files
- Test modules generated without running `go mod tidy`
- Missing dependency checksums cause additional Go toolchain issues

**Tertiary Issue**: Invalid `go.mod` in templates module
- Standard library `text/template` was incorrectly listed as external dependency
- Caused "malformed module path" errors

## Affected Tests

All tests using `go.referenced` provider (8 total):
- ✗ deprecated-packages
- ✗ build-info
- ✗ networking
- ✗ windows-syscalls
- ✗ error-handling
- ✗ text-processing
- ✗ reflection
- ✗ (1 more)

Tests using `builtin.filecontent` work fine:
- ✓ generics (uses builtin.filecontent)
- ✓ go-command (uses builtin.filecontent)

## Solution Applied

### 1. Generated go.sum files for all test modules ✓
```bash
for dir in demo-output/go-1.17-to-go-1.18/tests/data/*/; do
  (cd "$dir" && GOWORK=off go mod tidy)
done
```

Result: All 15 modules now have go.sum files

### 2. Fixed invalid go.mod in templates module ✓
Removed standard library from require section:
```diff
- require (
-   text/template v0.0.0-20170908181559-1c7b8afd
- )
```

### 3. Identified workspace mode issue
The system-wide go.work file at `/Users/tsanders/go.work` needs to be handled.

## Recommended Solutions

### Option 1: Disable workspace mode for tests (Recommended)
Set `GOWORK=off` when running kantra:
```bash
GOWORK=off kantra test demo-output/go-1.17-to-go-1.18/tests/*.test.yaml
```

### Option 2: Add GOWORK=off to test runner
Modify `scripts/generate_test_data.py` to set this environment variable when invoking kantra.

### Option 3: Create local go.work files
Add a `go.work` file in each test data directory:
```go
go 1.17

use .
```

## Test Results After Fix

After generating go.sum files, test status should improve from:
- Before: 6/14 passing (42.86%)
- Expected: Most go.referenced tests should now pass

Remaining failures will be pattern-related, not infrastructure issues.

## Prevention for Future Test Generation

### Update generate_test_data.py to:

1. Always run `go mod tidy` after generating test code:
```python
subprocess.run(['go', 'mod', 'tidy'], cwd=test_data_dir, env={'GOWORK': 'off'})
```

2. Validate go.mod doesn't contain standard library packages:
```python
# Check that require section doesn't have std lib packages
std_lib_packages = ['fmt', 'os', 'io', 'text/template', 'net/http', ...]
```

3. Set GOWORK=off when running kantra tests:
```python
test_env = os.environ.copy()
test_env['GOWORK'] = 'off'
subprocess.run(['kantra', 'test', ...], env=test_env)
```

## Commands to Verify Fix

```bash
# Check all modules have go.sum
find demo-output/go-1.17-to-go-1.18/tests/data -name "go.sum" | wc -l
# Should show: 15

# Test build of all modules
for dir in demo-output/go-1.17-to-go-1.18/tests/data/*/; do
  echo "Testing: $dir"
  (cd "$dir" && GOWORK=off go build)
done

# Run kantra tests with GOWORK=off
GOWORK=off kantra test demo-output/go-1.17-to-go-1.18/tests/*.test.yaml
```

## Root Cause - Deep Dive

After investigating the actual kantra container logs, the issue is:

**gopls (Go Language Server) is crashing inside the kantra container**

Evidence from `/var/folders/.../rules-test-*/analysis.log`:
```
time="2026-01-01T02:09:34Z" level=error msg="Error inside ProviderInit, after g.Init."
error="rpc error: code = Unavailable desc = error reading from server: EOF" logger=go provider=grpc
```

The LSP server path: `/root/go/bin/gopls`
Workspace: `/data/data/deprecated-packages`

**Why gopls crashes:**
1. Go version mismatch between container and test modules
   - User system: Go 1.25.3
   - Container: likely older Go version
   - Test modules: `go 1.17` in go.mod
   - gopls may be incompatible with this combination

2. Missing `go-server.log` indicates gopls crashed before logging
   - This is a hard crash, not a graceful error

3. Container environment limitations
   - Running inside `quay.io/konveyor/kantra:latest` container
   - May have outdated gopls version
   - Limited control over gopls configuration

## Workarounds

### Workaround 1: Use builtin.filecontent instead of go.referenced (Recommended)

Convert rules to use `builtin.filecontent` with regex patterns instead of `go.referenced`:

```yaml
# Instead of this:
when:
  go.referenced:
    pattern: io/ioutil
    location: METHOD_CALL

# Use this:
when:
  builtin.filecontent:
    pattern: ioutil\\.
    filePattern: \\.go$
```

**Pros:**
- Works without gopls
- No container/LSP issues
- Faster execution

**Cons:**
- Less precise (text matching vs semantic analysis)
- May have false positives

### Workaround 2: Update kantra container image

Use a newer kantra image with updated gopls:
```bash
# Pull latest kantra image
podman pull quay.io/konveyor/kantra:latest

# Or specify a specific version
podman pull quay.io/konveyor/kantra:v0.6.0
```

### Workaround 3: Skip go.referenced tests for now

Focus on rules that use `builtin.filecontent`:
- These tests work reliably
- Can validate patterns without LSP
- Convert to go.referenced later when gopls issues are resolved

## Status

✓ go.sum files generated for all modules
✓ Invalid go.mod fixed in templates
✗ gopls crashing in kantra container (unresolved)

**Impact:**
- 8/14 tests fail due to gopls crashes (go.referenced rules)
- 6/14 tests pass (builtin.filecontent rules)

**Recommendation:**
Use `builtin.filecontent` for Go rules until kantra gopls issues are resolved.
