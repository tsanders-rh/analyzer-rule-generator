# Non-Deterministic Test Results in Konveyor Analyzer

## Summary

Running the same test file multiple times produces different pass/fail results, indicating race conditions or non-deterministic behavior in the analyzer providers.

## Environment

- **Platform**: macOS (Darwin 25.1.0)
- **Kantra**: Latest version from ~/Workspace/kantra/bin/kantra
- **Test File**: `patternfly-v5-to-patternfly-v6-component-props.test.yaml`
- **Rule File**: `patternfly-v5-to-patternfly-v6-component-props.yaml` (41 rules)
- **Providers Used**: `nodejs` and `builtin`

## Reproduction Steps

1. Create a test with 41 rules using both `nodejs.referenced` and `builtin.filecontent` conditions
2. Run the same test 3 times consecutively without changing any files:
   ```bash
   cd tests
   kantra test patternfly-v5-to-patternfly-v6-component-props.test.yaml
   kantra test patternfly-v5-to-patternfly-v6-component-props.test.yaml
   kantra test patternfly-v5-to-patternfly-v6-component-props.test.yaml
   ```

## Expected Behavior

The same test file should produce identical results on every run when the source code and rules haven't changed.

## Actual Behavior

Test results vary randomly across runs:

```
Run 1: 28/41 passing (68.29%)
Run 2: 27/41 passing (65.85%)
Run 3: 26/41 passing (63.41%)
```

Different individual rules pass/fail on each run. For example:
- Rule `00050` passes in run 1, fails in run 2, passes in run 3
- Rule `00140` fails in run 1, passes in run 2, fails in run 3

## Example Rule Pattern

Most failing rules use this pattern structure:

```yaml
when:
  and:
    - nodejs.referenced:
        pattern: ComponentName
    - builtin.filecontent:
        pattern: <ComponentName[^>]*\bpropName\b
        filePattern: \.(j|t)sx?$
```

## Test Data Example

```tsx
import { Page, Masthead } from '@patternfly/react-core';

// Rule patternfly-v5-to-patternfly-v6-component-props-00050
<Page header={<Masthead />} />
```

Rule pattern: `<Page[^>]*\bheader\b`
- Sometimes matches → test passes
- Sometimes doesn't match → test fails
- Code never changes between runs

## Impact

- Cannot reliably validate rule correctness
- Test suites are unreliable for CI/CD
- Makes it difficult to debug actual rule issues vs. provider issues
- Blocks submission of rules because tests may pass locally but fail in CI

## Hypothesis

Possible causes:
1. **Race conditions**: Concurrent provider execution may have timing-dependent behavior
2. **Caching issues**: Provider cache may not invalidate correctly between runs
3. **File system race**: Reading files while provider is analyzing
4. **Provider initialization**: nodejs and builtin providers may not synchronize properly

## Related Issues

- This is separate from #1043 (multiline grep issue)
- This affects patterns that DO work with grep when they trigger

## Additional Context

The issue appears when:
- Multiple rules test the same file
- Rules use `and` conditions combining `nodejs.referenced` + `builtin.filecontent`
- Test file has 40+ rules (may be related to concurrency/load)

Simpler test files with 2-5 rules appear to have consistent results.

## Workaround

None known. Running tests multiple times and accepting "best result" is not viable for production use.
