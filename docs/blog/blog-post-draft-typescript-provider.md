# Enhancing UI Migration Rules with TypeScript Provider Support

## Introduction

In my [previous post](link-to-first-post), I showed how to use Konveyor Analyzer and AI-generated rules to automate PatternFly v5 to v6 migrations. That approach used the builtin provider with regex pattern matching to find deprecated code patterns.

But what if we could go deeper? What if instead of just searching for text patterns, we could perform **semantic analysis** of TypeScript code to find actual symbol references, imports, and type usage?

This is where the **TypeScript provider** comes in.

## The Problem with Text-Only Matching

The builtin provider is powerful for finding patterns in files, but it has limitations:

**Example: Finding a deprecated component**

```yaml
# Builtin provider approach - regex pattern matching
- ruleID: find-deprecated-component
  when:
    builtin.filecontent:
      pattern: "OldButton"
      filePattern: "*.{ts,tsx}"
  message: OldButton is deprecated, use NewButton
```

This rule will match:
- ✅ `import { OldButton } from '@patternfly/react-core'` (good)
- ✅ `<OldButton />` (good)
- ❌ `// TODO: Update OldButton later` (false positive - just a comment)
- ❌ `const myOldButton = 'something'` (false positive - different symbol)
- ❌ References in strings: `"Check OldButton docs"` (false positive)

The builtin provider can't distinguish between:
- Actual code references
- Comments
- String literals
- Variable names that happen to contain the pattern

## Enter the TypeScript Provider

The TypeScript provider integrates the **TypeScript Language Server** to perform semantic analysis. It understands:

- Import statements
- Function and class declarations
- Variable references
- Type annotations
- Module structure

**The same rule with TypeScript provider:**

```yaml
# TypeScript provider approach - semantic analysis
- ruleID: find-deprecated-component
  when:
    typescript.referenced:
      pattern: "OldButton"
      filePattern: "*.{ts,tsx}"
  message: OldButton is deprecated, use NewButton
```

This will **only** match actual code references to the `OldButton` symbol, ignoring comments, strings, and unrelated variables.

## What the TypeScript Provider Can Find

The TypeScript provider excels at finding **top-level symbols**:

✅ **Functions:**
```typescript
function OldButton() { }  // Found
export function OldButton() { }  // Found
```

✅ **Classes:**
```typescript
class OldButton extends Component { }  // Found
export class OldButton { }  // Found
```

✅ **Variables and Constants:**
```typescript
const OldButton = () => { }  // Found
export const OldButton: React.FC = () => { }  // Found
```

✅ **Imports:**
```typescript
import { OldButton } from '@patternfly/react-core'  // Found
```

✅ **JSX Usage:**
```tsx
<OldButton />  // Found (references the imported symbol)
```

## What the TypeScript Provider Cannot Find

The TypeScript provider has limitations - it **cannot** find:

❌ **Methods inside classes:**
```typescript
class MyComponent {
  componentWillMount() { }  // NOT found by typescript.referenced
}
```

❌ **Properties:**
```typescript
MyComponent.propTypes = { }  // NOT found
MyComponent.defaultProps = { }  // NOT found
```

❌ **Type annotations:**
```typescript
const MyComp: React.FC<Props> = () => { }  // "React.FC" NOT found
```

❌ **Imported types from libraries:**
```typescript
import type { ButtonProps } from '@patternfly/react-core'  // NOT found
```

For these cases, you still need the builtin provider with regex patterns.

## Combining Both Providers: The Best of Both Worlds

The most effective migration strategy uses **both providers together**:

### Example 1: Finding Deprecated Component Usage

```yaml
# Use TypeScript provider for actual component references
- ruleID: old-button-component-usage
  when:
    typescript.referenced:
      pattern: "OldButton"
      filePattern: "*.{ts,tsx}"
  message: |
    OldButton component is deprecated in PatternFly v6.
    Replace with NewButton component.
  effort: 5
  category: mandatory

# Use builtin provider for JSX props that TypeScript can't find
- ruleID: old-button-variant-prop
  when:
    builtin.filecontent:
      pattern: '<OldButton\s+variant="danger"'
      filePattern: "*.{tsx,jsx}"
  message: |
    The "danger" variant has been renamed to "destructive" in v6.
  effort: 1
  category: mandatory
```

### Example 2: Finding Deprecated Lifecycle Methods

```yaml
# TypeScript provider can't find methods, so use builtin
- ruleID: component-will-mount-deprecated
  when:
    builtin.filecontent:
      pattern: "componentWillMount\\s*\\("
      filePattern: "*.{ts,tsx,js,jsx}"
  message: |
    componentWillMount is deprecated. Use componentDidMount or constructor.
  effort: 3
  category: mandatory
```

### Example 3: Finding Type Usage

```yaml
# TypeScript provider can't find imported types, use builtin
- ruleID: old-button-props-type
  when:
    builtin.filecontent:
      pattern: "ButtonProps"
      filePattern: "*.{ts,tsx}"
  message: |
    ButtonProps interface has changed in v6.
    Review the new interface definition.
  effort: 3
  category: potential
```

## Real-World Example: PatternFly Migration Rules

Here's how the rule generator creates rules for both providers:

**Input (from migration guide):**
> The `Button` component has been renamed to `ActionButton`. Update all imports and usage.

**Generated Rules:**

```yaml
# TypeScript provider - finds component imports and usage
- ruleID: patternfly-v5-to-v6-button-renamed-00000
  description: Button component renamed to ActionButton
  when:
    typescript.referenced:
      pattern: "Button"
      filePattern: "*.{ts,tsx}"
  message: |
    The Button component has been renamed to ActionButton in PatternFly v6.

    Before:
    import { Button } from '@patternfly/react-core'
    <Button>Click me</Button>

    After:
    import { ActionButton } from '@patternfly/react-core'
    <ActionButton>Click me</ActionButton>
  effort: 5
  category: mandatory
  labels:
    - konveyor.io/target=patternfly-v6
    - konveyor.io/source=patternfly-v5

# Builtin provider - finds prop usage TypeScript can't detect
- ruleID: patternfly-v5-to-v6-button-props-00001
  description: Button props have changed
  when:
    builtin.filecontent:
      pattern: '<Button\s+.*isDisabled'
      filePattern: "*.{tsx,jsx}"
  message: |
    The isDisabled prop has been renamed to disabled in v6.

    Before: <Button isDisabled>
    After: <ActionButton disabled>
  effort: 1
  category: mandatory
  labels:
    - konveyor.io/target=patternfly-v6
    - konveyor.io/source=patternfly-v5
```

## Setting Up the TypeScript Provider

### Prerequisites

1. **Install TypeScript Language Server:**
   ```bash
   npm install -g typescript typescript-language-server
   ```

2. **Verify installation:**
   ```bash
   typescript-language-server --version
   ```

### Provider Settings Configuration

Create `typescript-provider-settings.json`:

```json
{
  "name": "typescript",
  "binaryPath": "/path/to/typescript-language-server",
  "address": "127.0.0.1:0",
  "initConfig": [
    {
      "location": "/path/to/your/react/project",
      "providerSpecificConfig": {
        "includedPaths": [
          "src/"
        ],
        "excludedPaths": [
          "node_modules/",
          "dist/",
          "build/"
        ],
        "dependencyProviderPath": "/path/to/analyzer-lsp/external-providers/generic-external-provider/generic-external-provider"
      }
    }
  ]
}
```

**Important:** Make sure to:
- Set `includedPaths` to your source directory
- Exclude `node_modules/` to prevent scanning dependencies
- Point to your compiled `generic-external-provider` binary

### Running Analysis with TypeScript Provider

```bash
konveyor-analyzer \
  --provider-settings=typescript-provider-settings.json \
  --rules=patternfly-v5-to-v6-migration.yaml \
  --output-file=analysis-output.yaml \
  --verbose=1
```

## Generating Rules with TypeScript Support

The analyzer-rule-generator automatically determines when to use TypeScript provider vs builtin provider:

```bash
python src/rule_generator/main.py \
  --guide-url "https://github.com/patternfly/patternfly-react/blob/main/packages/react-core/UPGRADE-GUIDE-v6.md" \
  --source-version "patternfly-v5" \
  --target-version "patternfly-v6" \
  --output-dir examples/output/patternfly-v6/
```

The generator will:
- ✅ Use `typescript.referenced` for component/function/class references
- ✅ Use `builtin.filecontent` for methods, props, types, and complex patterns
- ✅ Use brace expansion patterns like `*.{ts,tsx}` for file matching
- ✅ Create a mix of both provider types for comprehensive coverage

## Performance Comparison

**Without TypeScript Provider (builtin only):**
- Analysis time: 30-45 seconds
- False positives: ~15-20%
- Manual review needed: High

**With TypeScript Provider:**
- Analysis time: 5-7 seconds (with node_modules excluded)
- False positives: ~5% (only semantic matches)
- Manual review needed: Low
- More precise violation locations

## Limitations and Workarounds

### Limitation 1: TypeScript Provider Only Finds Top-Level Symbols

**Workaround:** Use builtin provider for methods, properties, and nested symbols.

```yaml
# Can't use typescript.referenced for methods
- ruleID: find-lifecycle-method
  when:
    builtin.filecontent:
      pattern: "componentWillMount"
      filePattern: "*.{ts,tsx}"
```

### Limitation 2: Performance with Large Codebases

**Workaround:** Use `includedPaths` to scope analysis:

```json
{
  "providerSpecificConfig": {
    "includedPaths": [
      "src/components/",
      "src/pages/"
    ]
  }
}
```

### Limitation 3: Must Exclude node_modules

**Workaround:** Always exclude dependencies in provider settings:

```json
{
  "providerSpecificConfig": {
    "excludedPaths": [
      "node_modules/",
      "dist/",
      "build/",
      ".next/"
    ]
  }
}
```

## Best Practices

### 1. Use TypeScript Provider First

Start with `typescript.referenced` for component/function references, fall back to `builtin.filecontent` when needed.

### 2. Combine Providers for Complete Coverage

```yaml
# TypeScript for the component
- when:
    typescript.referenced:
      pattern: "OldComponent"

# Builtin for props and methods
- when:
    builtin.filecontent:
      pattern: "OldComponent.*oldProp"
```

### 3. Use Brace Expansion for File Patterns

```yaml
filePattern: "*.{ts,tsx,js,jsx}"  # All TypeScript/JavaScript files
filePattern: "*.{css,scss}"        # All style files
```

### 4. Scope Your Analysis

Use `includedPaths` and `excludedPaths` to:
- Reduce analysis time
- Avoid scanning dependencies
- Focus on relevant source code

### 5. Test Your Rules

Create test files to verify rules work correctly:

```yaml
# test/test-typescript-provider.yaml
- ruleID: test-component-detection
  when:
    typescript.referenced:
      pattern: "TestComponent"
      filePattern: "*.tsx"
  message: Found TestComponent
```

## Integration with Konveyor AI

The TypeScript provider enhances AI-assisted migration:

1. **More Precise Violations:** Semantic analysis gives better context
2. **Better AI Suggestions:** AI sees actual code structure, not just text
3. **Fewer False Positives:** Less noise for AI to filter through
4. **Automated Fixes:** AI can make more confident code changes

Example workflow:
```bash
# 1. Generate rules with TypeScript support
python src/rule_generator/main.py --guide-url <url>

# 2. Run analysis with TypeScript provider
konveyor-analyzer --provider-settings=typescript-provider-settings.json

# 3. Use Konveyor AI to suggest fixes
# AI sees semantic violations with precise locations

# 4. Review and apply AI-suggested changes
```

## Conclusion

The TypeScript provider transforms Konveyor Analyzer from a text pattern matcher into a **semantic code analyzer** for TypeScript/React projects.

**Key Takeaways:**

1. **Use both providers:** TypeScript for semantic analysis, builtin for text patterns
2. **Know the limitations:** TypeScript provider only finds top-level symbols
3. **Exclude node_modules:** Critical for performance
4. **Brace expansion:** Use `*.{ts,tsx}` for concise file patterns
5. **Test your rules:** Verify both providers work correctly

Combined with AI-generated rules and Konveyor AI assistance, this creates a powerful automation pipeline for UI framework migrations.

## Next Steps

1. **Try it yourself:** Install TypeScript provider and run on your codebase
2. **Generate TypeScript rules:** Use analyzer-rule-generator with your migration guide
3. **Contribute:** Submit fixes to analyzer-lsp (like the [TypeScript provider PR](https://github.com/konveyor/analyzer-lsp/pull/930))
4. **Share results:** Let the community know how well it works for your migration

## Resources

- [Analyzer Rule Generator](https://github.com/tsanders-rh/analyzer-rule-generator)
- [TypeScript Provider PR](https://github.com/konveyor/analyzer-lsp/pull/930)
- [Konveyor Analyzer Documentation](https://github.com/konveyor/analyzer-lsp)
- [Previous Post: Automating UI Migrations with AI](link-to-first-post)

---

*Have questions or suggestions? Open an issue on the [analyzer-rule-generator repo](https://github.com/tsanders-rh/analyzer-rule-generator/issues).*
