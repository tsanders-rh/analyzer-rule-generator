# PatternFly v5 to v6 Test Generation Baseline

## Summary

Generated and validated test data for 19 PatternFly migration rule files using AI-powered test generation.

**Overall Results: 77/112 rules passing (68.75%)**
- Excluding component-props (non-deterministic due to provider bug)

## Files with 100% Pass Rate (11 files, 36 rules)

| File | Rules | Status |
|------|-------|--------|
| card | 2/2 | ✓ PASS |
| cleanup | 2/2 | ✓ PASS |
| component-groups | 5/5 | ✓ PASS |
| components | 7/7 | ✓ PASS |
| deprecated-components | 7/7 | ✓ PASS |
| empty-state | 4/4 | ✓ PASS |
| import-paths | 1/1 | ✓ PASS |
| login | 1/1 | ✓ PASS |
| menu | 1/1 | ✓ PASS |
| removed-components | 3/3 | ✓ PASS |
| renamed-interfaces | 3/3 | ✓ PASS |

## Files with Partial Pass Rate (7 files, 41/76 rules)

| File | Rules | Pass Rate | Notes |
|------|-------|-----------|-------|
| import-path | 3/4 | 75% | Rule 00030 blocked by multiline grep (#1043) |
| interface-renames | 1/2 | 50% | Needs manual fixes |
| promoted-components | 1/2 | 50% | Needs manual fixes |
| removed-props | 7/17 | 41% | Missing required props in generated code |
| renamed-props | 7/19 | 37% | Missing required props in generated code |
| toolbar | 5/9 | 56% | Missing required props in generated code |
| patternfly-v6 | 17/23 | 74% | Missing required props in generated code |

## Skipped Due to Provider Issues (1 file, ~27/41 rules)

| File | Rules | Pass Rate | Reason |
|------|-------|-----------|--------|
| component-props | ~27/41 | ~66% | Non-deterministic test results (issue #1045) |

**Non-deterministic behavior:** The same test produces different results on each run (26-30 passing out of 41). This indicates race conditions in the provider code when handling large numbers of rules.

## Provider Issues Discovered

### Issue #1043: Multiline Grep Cannot Match Patterns Across Newlines

**Impact:** Rules using patterns like `import[\s\S]*Component[\s\S]*from[\s\S]*['"]@package['"]` fail when imports span multiple lines.

**Affected platforms:**
- Linux: Uses `grep -P` (line-by-line processing)
- macOS: Uses `perl -ne` (line-by-line processing)
- Windows: Works correctly with `regexp2.Multiline`

**Workaround:** Consolidate multi-line imports to single lines in test data.

**URL:** https://github.com/konveyor/analyzer-lsp/issues/1043

### Issue #1045: Non-Deterministic Test Results

**Impact:** Large rule files (40+ rules) produce different pass/fail results on consecutive runs without any code changes.

**Example:**
```
Run 1: 28/41 passing (68%)
Run 2: 27/41 passing (66%)
Run 3: 26/41 passing (63%)
```

**Root cause:** Race conditions when `nodejs.referenced` and `builtin.filecontent` conditions are evaluated concurrently.

**Affected:** component-props.yaml (41 rules)

**URL:** https://github.com/konveyor/analyzer-lsp/issues/1045

## Test Generation Approach

### Script Used
`scripts/generate_test_data.py` with improved message extraction:
- Prioritizes "Before:" code examples from rule messages
- Handles literal `\n` sequences in YAML
- Generates minimal, focused test code

### Manual Fixes Required

Common fixes applied:
1. **Single-line imports:** Consolidate multi-line imports to work around grep limitation
2. **Missing props:** Add required props that AI didn't generate (e.g., `href`, `variant`)
3. **Export statements:** Some rules check for `export` patterns, not just imports
4. **Variable references:** Add variables for props like `isActive` to trigger `nodejs.referenced`

### Example Fixes

**Import consolidation:**
```tsx
// Generated (multiline - fails)
import {
  Component1,
  Component2
} from '@patternfly/react-core';

// Fixed (single line - passes)
import { Component1, Component2 } from '@patternfly/react-core';
```

**Missing prop:**
```tsx
// Generated (missing required prop)
<LoginMainFooterLinksItem>Content</LoginMainFooterLinksItem>

// Fixed (added href prop)
<LoginMainFooterLinksItem href="https://example.com">Content</LoginMainFooterLinksItem>
```

## Recommendations

### Short Term
1. **Proceed with submission** for the 11 files with 100% pass rate (36 rules)
2. **Document known issues** for partially passing files
3. **Exclude component-props** until provider race condition is fixed

### Medium Term
1. **Wait for provider fixes** (#1043, #1045) before addressing partially passing files
2. **Re-run generation** for failed rules after provider fixes are merged
3. **Add manual fixes** for remaining failures that aren't provider-related

### Long Term
1. **Improve AI prompts** to generate correct props more reliably
2. **Add validation step** to detect missing required props before test execution
3. **Create regression test suite** to catch provider issues early

## Files Location

All generated test files are in:
```
/Users/tsanders/Workspace/rulesets/preview/nodejs/patternfly/tests/
```

Structure:
```
tests/
├── data/
│   ├── card/
│   │   ├── package.json
│   │   └── src/App.tsx
│   ├── cleanup/
│   ├── ... (19 directories total)
│
├── patternfly-v5-to-patternfly-v6-card.test.yaml
├── patternfly-v5-to-patternfly-v6-cleanup.test.yaml
└── ... (19 test.yaml files)
```

## Next Steps

1. Review generated files in `/Users/tsanders/Workspace/rulesets/preview/nodejs/patternfly/tests`
2. Run all tests: `kantra test tests/*.test.yaml`
3. Consider submitting the 11 files with 100% pass rate
4. Wait for provider fixes before addressing partial failures
5. Re-generate and validate after provider fixes are merged

## Lessons Learned

1. **Provider limitations matter:** Static analysis tools have real constraints (grep, race conditions)
2. **AI needs guidance:** Extracting code from rule messages is more reliable than regex parsing
3. **Test early, test often:** Discovered critical provider bugs through systematic testing
4. **Single-line imports:** Necessary workaround until multiline grep is fixed
5. **Large rule files:** Expose concurrency issues that small files don't trigger
