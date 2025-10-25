# Node.js Provider Rule Generation (TypeScript/JavaScript)

This document describes the Node.js provider support in the analyzer rule generator for TypeScript and JavaScript code analysis.

## Overview

The rule generator now supports creating rules for three different providers:
1. **Java Provider** - For Java code analysis using `java.referenced`
2. **Node.js Provider** - For TypeScript/JavaScript semantic analysis using `nodejs.referenced`
3. **Builtin Provider** - For text/regex pattern matching using `builtin.filecontent`

## When to Use Node.js Provider

The Node.js provider (`nodejs.referenced`) uses the TypeScript Language Server to perform semantic analysis. It's ideal for finding **symbol declarations and references** in TypeScript and JavaScript code.

### What Node.js Provider CAN Find ✅

The `nodejs.referenced` provider finds symbol references in TypeScript/JavaScript code:

- **Functions**: `function MyComponent() {}`
- **Classes**: `class MyComponent extends React.Component {}`
- **Variables/Constants**: `const MyComponent = () => {}`
- **Types**: `type Props = {...}`, `interface ComponentProps {...}`
- **Exported symbols**: `export const helper = () => {}`
- **Imported symbols**: References to imported functions, classes, types

### What Node.js Provider CANNOT Find ❌

The Node.js provider cannot filter by file extension using the `location` field. Common misconceptions:

- ❌ **WRONG**: `nodejs.referenced` with `location: ".tsx"` (location is NOT for file filtering!)
- ❌ **WRONG**: `nodejs.referenced` with `location: "CLASS"` (location types are Java-specific)

**IMPORTANT**: The `location` field in `nodejs.referenced` is for code reference types (like Java's TYPE, FIELD, METHOD_CALL), NOT for file extension filtering.

### When to Use Builtin Provider Instead

Use `builtin.filecontent` with `filePattern` for file-specific matching:

✅ **Correct way to filter by file extension**:
```yaml
when:
  builtin.filecontent:
    pattern: "React"
    filePattern: "\\.tsx$"  # Regex: matches .tsx files only
```

✅ **Match multiple file types with regex**:
```yaml
when:
  builtin.filecontent:
    pattern: "import.*React"
    filePattern: "\\.(j|t)sx?$"  # Regex: .js, .jsx, .ts, .tsx
```

Also use `builtin.filecontent` for:
- Complex regex patterns across multiple lines
- Text matching that doesn't need semantic understanding
- CSS, SCSS, HTML, JSON, and other non-JS/TS files

## Rule Generation Updates

### 1. Schema Changes (`src/rule_generator/schema.py`)

Updated `provider_type` field to include `"nodejs"`:

```python
provider_type: Optional[str] = Field(
    default=None,
    description="Provider type: 'java', 'nodejs', or 'builtin' (auto-detected if not specified)"
)
```

Added `NodejsReferenced` model:

```python
class NodejsReferenced(BaseModel):
    """Nodejs provider condition for referenced code in JavaScript/TypeScript."""
    pattern: str = Field(..., description="Pattern to match (supports wildcards)")
    # Note: The location field should NOT be used for file filtering.
    # It's for code reference types (like Java's TYPE, FIELD, METHOD_CALL).
    # For file filtering, use builtin.filecontent with filePattern instead.
```

### 2. LLM Prompt Updates (`src/rule_generator/extraction.py`)

Updated LLM prompt with Node.js provider instructions:

**Option 1: Node.js Provider (for semantic symbol analysis)**
```json
{
  "source_pattern": "MyComponent",
  "target_pattern": "NewComponent",
  "source_fqn": "MyComponent",
  "provider_type": "nodejs",
  "file_pattern": null,
  "location_type": null
}
```

**Option 2: Builtin Provider (for file-specific text matching)**
```json
{
  "source_pattern": "import.*React",
  "target_pattern": null,
  "source_fqn": "import.*React",
  "provider_type": "builtin",
  "file_pattern": "\\.(j|t)sx?$",
  "location_type": null
}
```

**IMPORTANT**: Never use `file_pattern` with `nodejs.referenced`. Use `builtin.filecontent` with `filePattern` for file filtering.

### 3. Generator Logic Updates (`src/rule_generator/generator.py`)

Updated Node.js provider rule generation:

```python
elif provider == "nodejs":
    # Use nodejs.referenced for semantic symbol analysis in JavaScript/TypeScript
    # Note: nodejs.referenced finds symbol references in TypeScript/JavaScript code
    # (functions, classes, variables, types, interfaces, etc.)
    #
    # IMPORTANT: Do NOT use location field for file filtering.
    # The location field is for code reference types (like Java's TYPE, FIELD, METHOD_CALL),
    # not for filtering by file extension.
    #
    # For file-specific matching, use builtin.filecontent with filePattern instead.
    condition = {
        "nodejs.referenced": {
            "pattern": pattern.source_fqn or pattern.source_pattern
        }
    }
    return condition
```

Key changes:
- Changed from `typescript.referenced` to `nodejs.referenced` (correct provider name)
- Added clear warnings about NOT using location field for file filtering
- LLM chooses between `nodejs` (semantic) vs `builtin` (text/file-specific) provider
- For file filtering, use `builtin.filecontent` with `filePattern` (regex)

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
2. Choose `nodejs` provider for symbol references (components, functions, types)
3. Choose `builtin` provider for file-specific text matching
4. Generate regex patterns for `filePattern` when using `builtin.filecontent`

## Important Notes

### File Patterns (builtin.filecontent only)

**Use regex syntax for `filePattern` field:**

✅ **Correct** - Regex patterns (for builtin.filecontent):
- `"\\.tsx$"` - React TypeScript files only (.tsx extension)
- `"\\.ts$"` - TypeScript files only (.ts extension)
- `"\\.(j|t)sx?$"` - All JS/JSX/TS/TSX files (.js, .jsx, .ts, .tsx)
- `"\\.(css|scss)$"` - CSS and SCSS files (.css, .scss)

❌ **Wrong** - Glob patterns (don't work with filePattern):
- `"*.tsx"` - ❌ Wrong! This is glob syntax, not regex
- `"*.{ts,tsx}"` - ❌ Wrong! Brace expansion doesn't work in filePattern
- Use regex `"\\.tsx?$"` instead

### Provider Selection Logic

The LLM will choose the provider based on:

1. **Node.js Provider** (`nodejs.referenced`): For semantic symbol finding
   - React components: `MyComponent`, `useCustomHook`
   - Utility functions: `formatDate`, `calculateTotal`
   - Class names: `AuthService`, `DataStore`
   - Types and interfaces: `Props`, `ComponentState`
   - **No file filtering** - matches across all JS/TS files

2. **Builtin Provider** (`builtin.filecontent`): For file-specific or complex patterns
   - Imports: `import { ... } from 'react'` in `.tsx` files only
   - Code patterns in specific file types: `React.FC` in `.tsx` files
   - CSS variables: `--pf-` in `.css` or `.scss` files
   - Any pattern that needs `filePattern` for file type filtering

## Testing

To verify Node.js provider rules work correctly:

1. **Generate rules** using the script
2. **Review generated YAML** to ensure:
   - `nodejs.referenced` is used for symbol matching (no `filePattern`)
   - `builtin.filecontent` is used for file-specific patterns (with regex `filePattern`)
   - NO `location` field in `nodejs.referenced` rules
3. **Test with analyzer**:
   ```bash
   cd ~/Workspace/analyzer-lsp
   ./konveyor-analyzer \
       --provider-settings=/path/to/provider_settings.json \
       --rules=/path/to/generated-rules.yaml \
       --output-file=/path/to/output.yaml
   ```

## Common Mistakes to Avoid

❌ **Don't do this:**
```yaml
# WRONG: Using location field for file filtering
when:
  nodejs.referenced:
    pattern: "React"
    location: ".tsx"  # ❌ Wrong! location is NOT for file extensions
```

✅ **Do this instead:**
```yaml
# CORRECT: Use builtin.filecontent with filePattern for file filtering
when:
  builtin.filecontent:
    pattern: "React"
    filePattern: "\\.tsx$"  # ✅ Correct! Regex pattern for .tsx files
```

---

❌ **Don't do this:**
```yaml
# WRONG: Using file_pattern with nodejs provider
when:
  nodejs.referenced:
    pattern: "MyComponent"
    filePattern: "*.tsx"  # ❌ Wrong! nodejs.referenced doesn't support filePattern
```

✅ **Do this instead:**
```yaml
# CORRECT: nodejs.referenced without file filtering (matches all JS/TS files)
when:
  nodejs.referenced:
    pattern: "MyComponent"  # ✅ Correct! Finds MyComponent in all JS/TS files
```

## See Also

- [TypeScript Provider Setup Guide](provider-setup.md) - How to configure and run the Node.js/TypeScript provider
- [TypeScript Provider PR #930](https://github.com/konveyor/analyzer-lsp/pull/930) - Upstream PR for TypeScript/React support
