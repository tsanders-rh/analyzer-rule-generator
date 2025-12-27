# Builtin Provider: Cannot Match Patterns Across Newlines on Linux/macOS

## Problem Description

The builtin provider's filecontent search processes files line-by-line on Linux and macOS, which prevents matching regex patterns that span across multiple lines. This causes rules with patterns like `<Masthead[^>]*>[^<]*<MastheadToggle` to fail when the matching elements are on different lines in the source code.

## Environment

- **OS**: Linux (Docker container) and macOS
- **Component**: analyzer-lsp builtin provider
- **Affected Code**: `provider/internal/builtin/service_client.go:529` (Linux) and `service_client.go:554-576` (macOS)

## Current Behavior

### On Linux
```bash
grep -o -n --with-filename -P -- pattern files...
```

### On macOS
```bash
perl -ne 'if (/%v/) { print "$ARGV:$.:$1\n" } close ARGV if eof;'
```

Both approaches process the file line-by-line. The `grep` command naturally operates on lines, and the Perl `-n` flag iterates over each line. When a pattern uses character classes like `[^<]*` to match across elements, neither tool can find matches if those elements span multiple lines.

## Expected Behavior

Patterns should match across newlines, similar to how the builtin provider works on Windows (which uses `regexp2.Multiline`).

## Reproduction

### Rule Example
```yaml
- ruleID: patternfly-v5-to-patternfly-v6-component-structure-00000
  when:
    and:
    - builtin.filecontent:
        pattern: <Masthead[^>]*>[^<]*<MastheadToggle|<Masthead[^>]*>[^<]*<MastheadBrand
        filePattern: \.(j|t)sx?$
```

### Test Code (Multi-line JSX - Real World Code)
```tsx
// This SHOULD match but DOESN'T on Linux or macOS
<Masthead>
  <MastheadToggle>Foo</MastheadToggle>
  <MastheadBrand>Bar</MastheadBrand>
</Masthead>
```

### Test Code (Single-line JSX - Workaround)
```tsx
// This DOES match, but is not realistic production code
<Masthead><MastheadToggle>Foo</MastheadToggle><MastheadBrand>Bar</MastheadBrand></Masthead>
```

## Analysis Log Evidence

From `analysis.log`:
```
time="2025-12-18T06:19:29Z" level=unknown msg="using direct grep (fast path)" pattern="<Masthead[^>]*>[^<]*<MastheadToggle|<Masthead[^>]*>[^<]*<MastheadBrand" totalFiles=1
time="2025-12-18T06:19:29Z" level=unknown msg="no incidents found" ruleID=patternfly-v5-to-patternfly-v6-component-structure-00000
```

The pattern should have matched the JSX code, but grep found 0 incidents because the tags are on separate lines.

## Root Cause

In `service_client.go:performFileContentSearch()`:

- **Windows** (line 500-512): Uses `regexp2.Compile(trimmedPattern, regexp2.Multiline)` ✓ WORKS
- **Linux** (line 524-544): Uses `grep -P` ✗ FAILS for multiline patterns
- **macOS** (line 554-576): Uses `perl -ne` ✗ FAILS for multiline patterns (the `-n` flag processes line-by-line)

Both grep and `perl -ne` lack multiline support.

## Proposed Solutions

### Option 1: Use pcregrep with -M flag (Linux) and perl -0777 (macOS) (Recommended)

**For Linux**: Replace `grep -P` with `pcregrep -M`:
```go
args := []string{"-o", "-n", "-M", "--", pattern}
cmd := exec.Command("pcregrep", args...)
```

**For macOS**: Replace `perl -ne` with `perl -0777 -ne`:
```perl
perl -0777 -ne 'while (/$pattern/g) { ... }'
```

The `-M` flag (pcregrep) and `-0777` flag (perl) enable multiline mode where patterns can match across newlines.

**Pros**: Clean, well-supported tools
**Cons**: Requires pcregrep to be installed in containers (Linux only)

### Option 2: Use parallelWalk on all platforms (like Windows)

Remove the platform check and use the `regexp2.Multiline` approach on all platforms:
```go
trimmedPattern := strings.Trim(pattern, "\"")
patternRegex, err := regexp2.Compile(trimmedPattern, regexp2.Multiline)
if err != nil {
    return nil, fmt.Errorf("could not compile provided regex pattern '%s': %v", pattern, err)
}
matches, err := b.parallelWalk(locations, patternRegex)
```

**Pros**: No external dependency, consistent across all platforms, already implemented and tested on Windows
**Cons**: May be slower than grep/perl for large projects

### Option 3: Use grep with null-separated input (Linux only - not recommended)

Use `grep -z` which treats null bytes as line separators:
```go
args := []string{"-o", "-z", "-n", "--with-filename", "-P", "--", pattern}
```

**Pros**: Uses standard grep
**Cons**: May have other side effects; less tested; doesn't solve the macOS problem

## Impact

This issue affects any rule that needs to match JSX/TSX elements spanning multiple lines, which is standard formatting in modern JavaScript/TypeScript codebases. Without this fix, rules must either:
1. Force developers to write unrealistic single-line code
2. Be written in a way that doesn't properly detect the deprecated patterns

## Testing

After implementing the fix, the following test should pass:

**File**: `src/App.tsx`
```tsx
import React from 'react';
import { Masthead, MastheadToggle, MastheadBrand } from '@patternfly/react-core';

const App: React.FC = () => {
  return (
    <div>
      {/* Rule patternfly-v5-to-patternfly-v6-component-structure-00000 */}
      <Masthead>
        <MastheadToggle>Foo</MastheadToggle>
        <MastheadBrand>Bar</MastheadBrand>
      </Masthead>
    </div>
  );
};

export default App;
```

**Expected**: The rule should find 1 incident at the `<Masthead>` element.

## Additional Context

Related files:
- `provider/internal/builtin/service_client.go:497-663` (performFileContentSearch, parallelWalk)
- `provider/lib.go:372` (MultilineGrep - already exists for other use cases)

The `MultilineGrep` function in `lib.go` already supports multiline patterns using `(?s)` flag, but it's only used for `getLocation()`, not for the initial pattern search.
