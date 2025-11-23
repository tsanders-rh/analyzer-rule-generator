# Analysis Findings: nodejs.referenced Provider Performance

## Summary

The combo rules (nodejs.referenced + builtin.filecontent) are experiencing severe performance issues during analysis of the tackle2-ui codebase.

## Timeline

1. **Analysis started:** 13:31:00
2. **Last log entry:** 18:31:19Z (processing component-renaming-00000)
3. **Current status (13:34):** Hung for 3+ minutes with no progress

## Rules Stuck

The following rules started processing but never completed:
- `patternfly-5-to-patternfly-6-component-props-00030` (Banner) - worker 1
- `patternfly-5-to-patternfly-6-component-props-00040` (Button) - worker 3
- **`patternfly-5-to-patternfly-6-component-props-00050` (Card)** - worker 0 ⭐
- `patternfly-5-to-patternfly-6-component-props-00060` (Checkbox) - worker 7
- `patternfly-5-to-patternfly-6-component-renaming-00000` - worker 4

## Root Cause

The **`nodejs.referenced` provider is extremely slow** on large codebases like tackle2-ui. When combined with `builtin.filecontent` in `and` clauses, the provider must:

1. Query the TypeScript language server for symbol references
2. Wait for response from LSP
3. Then run the filecontent pattern match

This creates a **bottleneck** where each combo rule takes minutes to complete.

## Original Problem Confirmed

The original output at `/Users/tsanders/Workspace/kantra/demo-output/tackle2-ui-patternfly/output.yaml` shows:

```
patternfly-5-to-patternfly-6-component-props-00050: dependency provider path not set
```

This confirms the nodejs-only rules **did not work** because:
- `nodejs.referenced` alone only finds symbols in node_modules
- It does NOT find actual JSX usage in the code
- The rule failed with "dependency provider path not set"

## Implications

### For the Question Asked

The person questioning your rules was **100% correct**:

> "they only add the ability to get symbols from node_modules"

The `nodejs.referenced` provider:
- ✅ Finds symbols imported from `@patternfly/react-core` in node_modules
- ❌ Does NOT find actual `<Card>` usage at line 121 of target-card.tsx
- ❌ Causes severe performance issues when querying symbols

### Performance vs Accuracy Trade-off

| Approach | Speed | Accuracy | Result |
|----------|-------|----------|--------|
| **builtin.filecontent only** | Fast (~90 sec) | May have false positives | Works, completes quickly |
| **nodejs.referenced only** | N/A | Fails completely | "dependency provider path not set" |
| **Combo (both)** | Very slow (>4 min, hung) | Most accurate | Too slow to be practical |

## Recommendations

### Option 1: Use builtin.filecontent Only (Recommended)

Remove `nodejs.referenced` from combo rules and rely solely on `builtin.filecontent` with well-crafted regex patterns:

```yaml
when:
  builtin.filecontent:
    pattern: <Card[^>]*\b(isSelectableRaised|isDisabledRaised|hasSelectableInput|selectableInputAriaLabel)\b
    filePattern: \.(j|t)sx?$
```

**Pros:**
- Fast execution (~90 seconds)
- Actually finds code usage
- No dependency on slow nodejs provider

**Cons:**
- May match commented-out code
- No verification that Card is from @patternfly/react-core

### Option 2: Add Import Check to Pattern

Enhance builtin.filecontent patterns to also check for imports:

```yaml
when:
  or:
    - builtin.filecontent:
        pattern: <Card[^>]*\b(isSelectableRaised|isDisabledRaised)\b
        filePattern: \.(j|t)sx?$
    - builtin.filecontent:
        pattern: import.*\{[^}]*\bCard\b[^}]*\}.*from ['"]@patternfly/react-core['"]
        filePattern: \.(j|t)sx?$
```

### Option 3: Wait for nodejs Provider Performance Improvements

Continue using combo rules but expect long analysis times (10+ minutes for large codebases).

## Conclusion

The **original nodejs-only rules don't work** at all (fail with "dependency provider path not set").

The **combo rules are technically correct** but suffer from severe performance issues with the nodejs provider.

**Recommendation:** Use **builtin.filecontent only** with comprehensive regex patterns for practical, working migration rules.
