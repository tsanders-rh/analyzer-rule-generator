# PatternFly v5 Test Project

This is a minimal test project containing known PatternFly v5 patterns that should trigger violations when analyzed with the `patternfly-v5-to-v6.yaml` ruleset.

## Expected Violations

When running the ruleset against this project, you should see violations for:

### Component Violations (src/App.tsx)
1. **Chip component** - should be replaced with Label
2. **Tile component** - should be replaced with Card
3. **Text component** - should be replaced with Content
4. **ExpandableSection isActive prop** - should be removed
5. **EmptyState component** - requires refactoring
6. **Chart import path** - should use `/victory` subpath

### CSS Violations (src/styles.css)
7. **CSS variable prefix** `--pf-v5-global--` - should change to `--pf-t--global--` (multiple instances)
8. **CSS class prefix** `pf-v5-` - should change to `pf-v6-` (multiple instances)
9. **Breakpoint variable prefix** - should change from `--pf-v5-global--breakpoint--` to `--pf-t--global--breakpoint--`

### Token Violations (src/tokens.ts)
10. **React token syntax** `global_*` - should change to `t_global_*` (multiple instances)

## Running the Analysis

Using kantra:

```bash
# From the analyzer-rule-generator root directory
kantra analyze \
  --input examples/rulesets/patternfly-v5-to-v6/test-project \
  --rules examples/rulesets/patternfly-v5-to-v6/patternfly-v5-to-v6.yaml \
  --output test-output
```

## Validation

After running analysis, you should see:
- **~15-20 total violations** (some rules match multiple instances)
- Violations distributed across all 3 source files
- Mix of `mandatory` and `potential` categories
- Effort estimates ranging from 1-7

This validates that the ruleset correctly detects PatternFly v5 to v6 migration patterns.
