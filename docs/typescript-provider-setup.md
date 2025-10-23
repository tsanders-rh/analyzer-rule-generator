# TypeScript/JavaScript Provider Setup for Konveyor

This guide explains how to configure a TypeScript/JavaScript language server provider for Konveyor analyzer using the existing generic provider.

## Overview

Konveyor's analyzer-lsp supports a generic provider that can interface with any Language Server Protocol (LSP) compliant language server. Instead of building a custom provider from scratch, we can leverage the existing generic provider to add TypeScript/JavaScript analysis capabilities.

## ⚠️ Important: Required Fixes

**As of October 2025**, the generic provider's nodejs client has bugs that prevent TypeScript analysis from working properly. You must apply fixes before using it:

1. **Missing .tsx/.jsx support** - The provider only scans `.ts` and `.js` files, missing React components
2. **Scans node_modules** - Without the fix, it tries to scan all dependency files causing extreme slowness

See [Applying Required Fixes](#applying-required-fixes) below for instructions.

## Prerequisites

- Konveyor analyzer-lsp installed
- TypeScript language server (`typescript-language-server`)
- Node.js and npm installed
- Go 1.21+ (to build the fixed generic provider)

## Step 1: Install TypeScript Language Server

```bash
npm install -g typescript-language-server typescript
```

This installs:
- `typescript-language-server`: The LSP server for TypeScript/JavaScript
- `typescript`: The TypeScript compiler (required dependency)

Verify installation:
```bash
typescript-language-server --version
which typescript-language-server
```

## Step 2: Apply Required Fixes to Generic Provider

### Clone and Apply Fixes

```bash
# Clone the analyzer-lsp repository
git clone https://github.com/konveyor/analyzer-lsp.git
cd analyzer-lsp

# Create a branch for the fixes
git checkout -b fix/nodejs-tsx-support

# Apply Fix 1: Add .tsx and .jsx file support
# Edit: external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go
# Lines 151-162, change from:
#   if filepath.Ext(path) == ".ts" {
#     langID = "typescript"
# To:
#   ext := filepath.Ext(path)
#   if ext == ".ts" || ext == ".tsx" {
#     langID = "typescriptreact"

# Apply Fix 2: Skip node_modules directory
# Same file, lines 147-150, uncomment:
#   if info.IsDir() && info.Name() == "node_modules" {
#     return filepath.SkipDir
#   }
```

### Detailed Fix Instructions

Edit `external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go`:

**Fix 1: Add .tsx/.jsx support (lines 151-162)**

Before:
```go
if !info.IsDir() {
    if filepath.Ext(path) == ".ts" {
        langID = "typescript"
        path = "file://" + path
        nodeFiles = append(nodeFiles, path)
    }
    if filepath.Ext(path) == ".js" {
        langID = "javascript"
        path = "file://" + path
        nodeFiles = append(nodeFiles, path)
    }
}
```

After:
```go
if !info.IsDir() {
    ext := filepath.Ext(path)
    if ext == ".ts" || ext == ".tsx" {
        langID = "typescriptreact"
        path = "file://" + path
        nodeFiles = append(nodeFiles, path)
    }
    if ext == ".js" || ext == ".jsx" {
        langID = "javascriptreact"
        path = "file://" + path
        nodeFiles = append(nodeFiles, path)
    }
}
```

**Fix 2: Skip node_modules (lines 147-150)**

Before:
```go
// TODO source-only mode
// if info.IsDir() && info.Name() == "node_modules" {
//     return filepath.SkipDir
// }
```

After:
```go
// TODO source-only mode
if info.IsDir() && info.Name() == "node_modules" {
    return filepath.SkipDir
}
```

### Build the Fixed Binary

```bash
# Build the generic provider with fixes
make external-generic

# Install to your PATH
sudo cp external-providers/generic-external-provider/generic-external-provider \
        /usr/local/bin/

# Verify installation
generic-external-provider --help
```

## Step 3: Build Konveyor Analyzer from Source

**Important:** The generic TypeScript provider requires running `konveyor-analyzer` directly on your host system, not through kantra's container.

```bash
# Clone the analyzer-lsp repository (if not already done)
cd ~/Workspace/analyzer-lsp

# Build the analyzer (creates konveyor-analyzer binary)
make build

# Verify the binary was created
ls -la konveyor-analyzer
./konveyor-analyzer --help
```

## Step 4: Configure Generic Provider

Create a `provider_settings.json` file with the TypeScript provider configuration.

**Important:** The configuration must be an array of provider objects.

```json
[
  {
    "name": "typescript",
    "binaryPath": "/usr/local/bin/generic-external-provider",
    "initConfig": [
      {
        "location": "/absolute/path/to/your/typescript/project",
        "analysisMode": "full",
        "providerSpecificConfig": {
          "lspServerName": "nodejs",
          "lspServerPath": "/opt/homebrew/bin/typescript-language-server",
          "lspServerArgs": ["--stdio"],
          "workspaceFolders": ["file:///absolute/path/to/your/typescript/project"],
          "dependencyFolders": []
        }
      }
    ]
  }
]
```

### Configuration Fields Explained

- **`name`**: Provider name used in rules (e.g., `"typescript"`)
- **`binaryPath`**: Absolute path to the generic-external-provider binary
- **`location`**: Absolute path to the TypeScript/JavaScript project to analyze
- **`analysisMode`**:
  - `"full"`: Analyze source code and dependencies
  - `"source-only"`: Only analyze source code
- **`providerSpecificConfig`**:
  - **`lspServerName`**: Must be `"nodejs"` (uses the nodejs service client for TypeScript)
  - **`lspServerPath`**: Absolute path to typescript-language-server (use `which typescript-language-server`)
  - **`lspServerArgs`**: Arguments to pass to the language server (usually `["--stdio"]`)
  - **`workspaceFolders`**: Array of workspace folders as `file://` URIs
  - **`dependencyFolders`**: Folders to exclude from analysis (optional)

**Note:** All paths must be absolute paths, not relative paths.

## Step 5: Write Rules Using TypeScript Provider

Once configured, you can write analyzer rules that leverage TypeScript semantic analysis.

### Example Rule: Find Components

```yaml
- ruleID: find-mycomponent
  description: Find references to MyComponent
  when:
    typescript.referenced:
      pattern: "MyComponent"
  message: Found MyComponent usage
  effort: 1
  category: potential
```

### TypeScript Provider Capabilities and Limitations

#### What `typescript.referenced` CAN find:

✅ **Top-level symbol declarations:**
- Functions: `function MyComponent() {}`
- Classes: `class MyComponent extends React.Component {}`
- Variables/Constants: `const MyComponent = () => {}`
- Exported symbols

✅ **References to those symbols:**
- Where they're imported
- Where they're called/used
- Where they're exported

#### What `typescript.referenced` CANNOT find:

❌ **Methods inside classes:**
```typescript
class MyClass {
  componentWillMount() {} // Cannot search for "componentWillMount"
}
```
→ **Workaround:** Use `builtin.filecontent` with pattern `"componentWillMount"`

❌ **Types/interfaces from imported libraries:**
```typescript
const MyComponent: React.FC = () => {} // Cannot search for "React.FC"
```
→ **Workaround:** Use `builtin.filecontent` with pattern `"React\\.FC"`

❌ **Properties assigned to objects:**
```typescript
MyComponent.propTypes = {} // Cannot search for "propTypes" directly
```
→ **Workaround:** Search for the component name or use `builtin.filecontent`

❌ **Type annotations, generics, nested symbols**

#### Best Practices for Writing Rules

1. **For top-level symbols** → Use `typescript.referenced`:
   ```yaml
   typescript.referenced:
     pattern: "MyComponent"
   ```

2. **For methods, properties, type references** → Use `builtin.filecontent`:
   ```yaml
   builtin.filecontent:
     pattern: "componentWillMount|componentWillReceiveProps"
     filePattern: "*.tsx"
   ```

3. **For complex patterns** → Combine both or use `builtin.filecontent` with regex

4. **File patterns:**
   - ✅ Use: `"*.tsx"` or `"*.ts"`
   - ❌ Don't use: `"*.{ts,tsx}"` (brace expansion not supported)

### Example: React Migration Rules

```yaml
# Find deprecated lifecycle methods (use builtin.filecontent)
- ruleID: react-deprecated-lifecycle
  when:
    builtin.filecontent:
      pattern: "componentWillMount|componentWillReceiveProps|componentWillUpdate"
      filePattern: "*.tsx"
  message: Deprecated lifecycle method found
  category: mandatory

# Find specific component usage (use typescript.referenced)
- ruleID: find-legacy-component
  when:
    typescript.referenced:
      pattern: "LegacyComponent"
  message: Legacy component still in use
  category: potential

# Find React.FC usage (use builtin.filecontent)
- ruleID: react-fc-usage
  when:
    builtin.filecontent:
      pattern: "React\\.FC"
      filePattern: "*.tsx"
  message: React.FC is no longer recommended
  category: potential
```

## Step 6: Run Analysis

Use `konveyor-analyzer` directly (not kantra):

```bash
# From the analyzer-lsp directory
cd ~/Workspace/analyzer-lsp

./konveyor-analyzer \
  --provider-settings=/path/to/provider_settings.json \
  --rules=/path/to/rules.yaml \
  --output-file=/path/to/output.yaml \
  --context-lines=10 \
  --verbose=4
```

**Why not kantra?**
- Kantra runs in a container and cannot access your host's generic-external-provider binary
- Kantra cannot access your host's typescript-language-server binary
- The generic provider needs to spawn the language server process on the host system

## Troubleshooting

### Analysis Takes Forever / Hangs

**Problem:** Provider is scanning `node_modules` directory

**Solution:** Ensure you applied Fix 2 (skip node_modules). Without this fix, the provider tries to scan all dependency files (can be 500+ files) with a 2-second delay per file.

### No .tsx Files Found

**Problem:** Provider only finds `.ts` files, missing React components

**Solution:** Ensure you applied Fix 1 (.tsx/.jsx support). The original code only looks for `.ts` and `.js` extensions.

### "unable to init the providers" error

**Error:**
```
level=error msg="unable to init the providers" error="generic client name not found"
```

**Solution:**
1. Verify provider_settings.json uses `"lspServerName": "nodejs"` (not "typescript" or "generic")
2. Ensure the configuration is an array format `[{...}]`

### Symbols Not Found

**Problem:** `typescript.referenced` returns "unmatched" for patterns

**Possible Causes:**
1. **Searching for methods/properties** → Use `builtin.filecontent` instead
2. **Searching for imported types** → Use `builtin.filecontent` instead
3. **Wrong file extension** → Ensure `.tsx` files are included
4. **Symbol not declared in analyzed code** → TypeScript LSP only finds symbols declared in your code, not in dependencies

### File Pattern Not Working

**Problem:** Rules with `filePattern: "*.{ts,tsx}"` don't match

**Solution:** Brace expansion not supported. Use separate rules or omit filePattern:
```yaml
# Instead of: "*.{ts,tsx}"
# Use:
filePattern: "*.tsx"
```

## Performance Considerations

1. **First Analysis is Slow**: The TypeScript language server needs to:
   - Parse `tsconfig.json`
   - Load type definitions
   - Index the workspace
   - First run can take 5-10 seconds

2. **Subsequent Analyses**: Much faster (2-3 seconds) as files are cached

3. **Large Workspaces**: For projects with 100+ files, consider:
   - Using `"analysisMode": "source-only"`
   - Analyzing subdirectories separately
   - Using `builtin.filecontent` when semantic analysis isn't needed

## Contributing Fixes Upstream

The fixes described in this guide should be contributed back to analyzer-lsp:

1. Fork https://github.com/konveyor/analyzer-lsp
2. Create a branch: `git checkout -b fix/nodejs-tsx-support`
3. Apply the fixes described above
4. Commit with descriptive messages
5. Push and create a Pull Request

### Suggested PR Description

```
Fix TypeScript/JavaScript analysis in nodejs service client

This PR fixes two critical issues preventing TypeScript/React analysis:

1. **Add .tsx/.jsx file support**: The nodejs client only scanned .ts and .js files,
   missing React components in .tsx files. Updated to recognize .tsx/.jsx extensions
   and use proper language IDs (typescriptreact/javascriptreact).

2. **Skip node_modules directory**: Uncommented the node_modules skip logic to prevent
   scanning dependency files. Without this, analysis could take 15+ minutes scanning
   hundreds of dependency files with 2-second delays.

Fixes enable successful TypeScript/React codebase analysis with the generic provider.
```

## Next Steps

1. **Test with Real Migration Guides**: Try React 19, Next.js, or TypeScript upgrade guides
2. **Document Query Patterns**: Build a library of TypeScript provider query examples
3. **Contribute Fixes**: Share these fixes upstream to help the community
4. **Enhance Rule Generator**: Add TypeScript pattern detection to your rule generator

## References

- [Konveyor analyzer-lsp](https://github.com/konveyor/analyzer-lsp)
- [Provider Documentation](https://github.com/konveyor/analyzer-lsp/blob/main/docs/providers.md)
- [TypeScript Language Server](https://github.com/typescript-language-server/typescript-language-server)
- [Language Server Protocol Specification](https://microsoft.github.io/language-server-protocol/)
