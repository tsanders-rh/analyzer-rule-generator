# TypeScript Provider Rule Generation

This document describes the TypeScript provider support in the analyzer rule generator.

## Overview

The rule generator now supports creating rules for three different providers:
1. **Java Provider** - For Java code analysis using `java.referenced`
2. **TypeScript Provider** - For TypeScript/JavaScript semantic analysis using `typescript.referenced`
3. **Builtin Provider** - For text/regex pattern matching using `builtin.filecontent`

## When to Use TypeScript Provider

The TypeScript provider uses the TypeScript Language Server to perform semantic analysis. It's ideal for finding **top-level symbol declarations** and their references.

### What TypeScript Provider CAN Find ✅

- **Functions**: `function MyComponent() {}`
- **Classes**: `class MyComponent extends React.Component {}`
- **Variables/Constants**: `const MyComponent = () => {}`
- **Exported symbols**: `export const helper = () => {}`

### What TypeScript Provider CANNOT Find ❌

- **Methods inside classes**: `componentWillMount()`, `render()`
- **Properties**: `propTypes`, `defaultProps`, `contextType`
- **Type annotations**: `React.FC`, `React.Component<Props>`
- **Imported types**: Types from libraries (React, etc.)
- **Nested symbols**: Anything not at the top level

### When to Fall Back to Builtin Provider

For patterns the TypeScript provider cannot find, use `builtin.filecontent` with simple regex:

- Lifecycle methods: `componentWillMount`, `componentWillReceiveProps`
- Object properties: `propTypes`, `defaultProps`
- Type annotations: `React.FC`, `React.Component`
- Complex code patterns: Multi-line patterns, specific syntax

## Rule Generation Updates

### 1. Schema Changes (`src/rule_generator/schema.py`)

Updated `provider_type` field to include `"typescript"`:

```python
provider_type: Optional[str] = Field(
    default=None,
    description="Provider type: 'java', 'typescript', or 'builtin' (auto-detected if not specified)"
)
```

### 2. LLM Prompt Updates (`src/rule_generator/extraction.py`)

Added comprehensive TypeScript provider instructions to the LLM prompt:

**Option 1: TypeScript Provider (for semantic analysis)**
```json
{
  "source_pattern": "MyComponent",
  "target_pattern": "NewComponent",
  "source_fqn": "MyComponent",
  "provider_type": "typescript",
  "file_pattern": "*.tsx",
  "location_type": null
}
```

**Option 2: Builtin Provider (for text matching)**
```json
{
  "source_pattern": "componentWillMount",
  "target_pattern": "componentDidMount",
  "source_fqn": "componentWillMount",
  "provider_type": "builtin",
  "file_pattern": "*.tsx",
  "location_type": null
}
```

### 3. Generator Logic Updates (`src/rule_generator/generator.py`)

Simplified TypeScript provider rule generation:

```python
elif provider == "typescript":
    # Use typescript.referenced for semantic symbol analysis
    condition = {
        "typescript.referenced": {
            "pattern": pattern.source_fqn or pattern.source_pattern
        }
    }
    return condition
```

Key changes:
- Removed automatic fallback to `builtin.filecontent` (LLM chooses the right provider)
- Removed location inference (not supported by TypeScript LSP workspace/symbol)
- Simplified to just use the pattern directly

## Usage Example

Generate rules for a React migration guide:

```bash
python scripts/generate_rules.py \
    --guide https://react.dev/blog/2025/04/25/react-19 \
    --source react-18 \
    --target react-19 \
    --output examples/output/react19 \
    --provider anthropic
```

The LLM will automatically:
1. Detect the language as TypeScript/JavaScript
2. Choose `typescript` provider for component names, function names
3. Choose `builtin` provider for lifecycle methods, type annotations
4. Generate appropriate file patterns (`*.tsx`, `*.ts`, `*.jsx`, `*.js`)

## Important Notes

### File Patterns

**Brace expansion IS supported** (with analyzer-lsp brace expansion fix):

✅ Recommended - Use brace expansion for multiple extensions:
- `"*.{ts,tsx}"` - TypeScript and React TypeScript files
- `"*.{js,jsx}"` - JavaScript and React JavaScript files
- `"*.{ts,tsx,js,jsx}"` - All TypeScript/JavaScript files
- `"*.{css,scss}"` - CSS and SCSS files

✅ Also valid - Single extension patterns:
- `"*.tsx"` - React TypeScript files only
- `"*.ts"` - TypeScript files only
- `"*.jsx"` - React JavaScript files only
- `"*.js"` - JavaScript files only

### Provider Selection Logic

The LLM will choose the provider based on:

1. **TypeScript Provider**: For finding symbol declarations
   - React components: `MyComponent`, `useCustomHook`
   - Utility functions: `formatDate`, `calculateTotal`
   - Class names: `AuthService`, `DataStore`

2. **Builtin Provider**: For everything else
   - Methods: `componentWillMount`, `UNSAFE_componentWillUpdate`
   - Properties: `propTypes`, `defaultProps`, `contextType`
   - Types: `React.FC`, `React.Component`, `ComponentType`
   - Imports: `import { ... } from 'react'`

## Testing

To verify TypeScript provider rules work correctly:

1. **Generate rules** using the script
2. **Review generated YAML** to ensure correct provider types
3. **Test with analyzer** using fixed generic-external-provider:
   ```bash
   cd ~/Workspace/analyzer-lsp
   ./konveyor-analyzer \
       --provider-settings=/path/to/provider_settings.json \
       --rules=/path/to/generated-rules.yaml \
       --output-file=/path/to/output.yaml
   ```

## See Also

- [TypeScript Provider Setup Guide](typescript-provider-setup.md) - How to configure and run the TypeScript provider
- [TypeScript Provider PR Plan](../TYPESCRIPT-PROVIDER-PR-PLAN.md) - Upstream contribution plan for provider fixes
