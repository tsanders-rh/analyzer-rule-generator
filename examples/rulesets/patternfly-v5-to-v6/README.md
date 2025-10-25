# PatternFly v5 to v6 Migration Ruleset

A comprehensive set of Konveyor Analyzer rules to automate detection of breaking changes when migrating from PatternFly v5 to v6.

## Overview

This ruleset contains **10 AI-generated rules** covering the major breaking changes documented in the [PatternFly v6 Upgrade Guide](https://www.patternfly.org/get-started/upgrade/). The rules use both the **Node.js provider** (for semantic code analysis) and the **builtin provider** (for CSS and text pattern matching) to detect deprecated patterns in your codebase.

## What's Covered

### Component Migrations (5 rules)
- ✅ `Chip` → `Label` component replacement
- ✅ `Tile` → `Card` component replacement
- ✅ `Text` → `Content` component rename
- ✅ `ExpandableSection` `isActive` prop removal
- ✅ `EmptyState` refactoring detection

### CSS & Styling (3 rules)
- ✅ CSS variable prefix: `--pf-v5-global--` → `--pf-t--global--`
- ✅ CSS class prefix: `pf-v5-` → `pf-v6-`
- ✅ React token syntax: `global_FontSize_lg` → `t_global_font_size_lg`

### Import Path Changes (1 rule)
- ✅ Chart imports: `@patternfly/react-charts` → `@patternfly/react-charts/victory`

### Other Changes (1 rule)
- ✅ Breakpoint variable prefix updates

## Coverage

**High Coverage (100%):**
- Component name changes
- CSS variable/class prefix changes
- Import path migrations
- Token syntax updates

**Partial Coverage:**
- Props and methods (detected, but may have some false positives)

**Intentionally Excluded:**
- Manual code review items
- Runtime behavior changes
- Complex refactorings requiring human judgment

**Estimated Coverage:** ~80-85% of automatable migration patterns

## Quick Start

### Prerequisites

- [Podman](https://podman.io/) 4+ or [Docker](https://www.docker.com/) 24+
- [kantra CLI](https://github.com/konveyor/kantra/releases) (recommended) or [konveyor-analyzer](https://github.com/konveyor/analyzer-lsp)

### Option 1: Using kantra (Recommended)

kantra automatically handles provider containers and dependencies:

```bash
# Download the ruleset
curl -O https://raw.githubusercontent.com/tsanders-rh/analyzer-rule-generator/main/examples/rulesets/patternfly-v5-to-v6/patternfly-v5-to-v6.yaml

# Run analysis on your PatternFly application
kantra analyze \
  --input /path/to/your/patternfly-app \
  --rules patternfly-v5-to-v6.yaml \
  --output /path/to/output-dir

# View results
open /path/to/output-dir/static-report/index.html
```

**What kantra does:**
1. Detects TypeScript/JavaScript files in your app
2. Pulls required container images (generic-external-provider, analyzer-lsp)
3. Starts provider containers automatically
4. Runs analysis and generates an HTML report

### Option 2: Using konveyor-analyzer Directly

For development or custom setups:

```bash
# Install TypeScript Language Server
npm install -g typescript typescript-language-server

# Create provider settings (see examples/rulesets/patternfly-v5-to-v6/provider-settings-example.json)

# Run analysis
konveyor-analyzer \
  --provider-settings=nodejs-provider-settings.json \
  --rules=patternfly-v5-to-v6.yaml \
  --output-file=analysis-output.yaml \
  --verbose=1
```

## Expected Performance

With the Node.js provider for semantic analysis:

- **Analysis Time:** 5-7 seconds (with `node_modules` excluded)
- **False Positives:** ~5% (semantic matches only)
- **Manual Review:** Low effort

Compared to builtin provider only:

- **Analysis Time:** 30-45 seconds
- **False Positives:** ~15-20%
- **Manual Review:** High effort

## Rule Categories

Rules are tagged with effort estimates and categories:

- **mandatory**: Must be fixed for v6 compatibility
- **potential**: Likely needs changes, review required

Effort scale: 1 (trivial) to 10 (complex refactoring)

## Example Output

```yaml
- ruleID: patternfly-5-to-patternfly-6-components-00000
  description: Chip should be replaced with Label
  when:
    nodejs.referenced:
      pattern: Chip
  message: |
    The Chip component has been replaced with Label in PatternFly 6

    Before:
    import { Chip } from '@patternfly/react-core'

    After:
    import { Label } from '@patternfly/react-core'
  effort: 5
  category: potential
  labels:
    - konveyor.io/source=patternfly-5
    - konveyor.io/target=patternfly-6
```

## Integration with Konveyor AI

These rules work seamlessly with [Konveyor AI](https://github.com/konveyor/kai) for automated refactoring:

1. Run analysis with this ruleset to detect violations
2. Use Konveyor AI to generate fix suggestions
3. Review and apply AI-suggested changes
4. Re-run analysis to verify fixes

The semantic analysis from the Node.js provider gives Konveyor AI better context for more accurate refactoring suggestions.

## Generating Your Own Rules

This ruleset was created using the [analyzer-rule-generator](https://github.com/tsanders-rh/analyzer-rule-generator). To generate rules for other migrations:

```bash
# Clone the generator
git clone https://github.com/tsanders-rh/analyzer-rule-generator.git
cd analyzer-rule-generator

# Generate rules from a migration guide
python src/rule_generator/main.py \
  --guide-url "https://example.com/upgrade-guide" \
  --source-version "v1" \
  --target-version "v2" \
  --output-dir examples/output/
```

See the [analyzer-rule-generator README](https://github.com/tsanders-rh/analyzer-rule-generator#readme) for details.

## Contributing

Found a missing pattern or false positive? Contributions welcome!

1. Fork the [analyzer-rule-generator repo](https://github.com/tsanders-rh/analyzer-rule-generator)
2. Update the ruleset or generator
3. Submit a PR with test cases

## Resources

- [PatternFly v6 Upgrade Guide](https://www.patternfly.org/get-started/upgrade/)
- [Konveyor Analyzer Documentation](https://github.com/konveyor/analyzer-lsp)
- [Kantra CLI](https://github.com/konveyor/kantra)
- [Node.js Provider PR](https://github.com/konveyor/analyzer-lsp/pull/930)
- [Blog: Automating UI Migrations with AI](https://tsanders-rh.github.io/)

## License

This ruleset is provided as-is for use with Konveyor Analyzer. See the [analyzer-rule-generator LICENSE](https://github.com/tsanders-rh/analyzer-rule-generator/blob/main/LICENSE) for details.

---

**Questions or issues?** Open an issue on the [analyzer-rule-generator repo](https://github.com/tsanders-rh/analyzer-rule-generator/issues).
