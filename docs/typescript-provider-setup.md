# TypeScript/JavaScript Provider Setup for Konveyor

This guide explains how to configure a TypeScript/JavaScript language server provider for Konveyor analyzer using the existing generic provider.

## Overview

Konveyor's analyzer-lsp supports a generic provider that can interface with any Language Server Protocol (LSP) compliant language server. Instead of building a custom provider from scratch, we can leverage the existing generic provider to add TypeScript/JavaScript analysis capabilities.

## Prerequisites

- Konveyor analyzer-lsp installed
- TypeScript language server (`typescript-language-server`)
- Node.js and npm installed

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

## Step 2: Obtain Generic Provider Binary

The generic provider binary is required to run custom language server providers with Konveyor. There are two ways to obtain it:

### Option 1: Extract from Kantra Container

**⚠️ Important:** This method only works on **Linux**. The kantra container contains Linux binaries that won't run natively on macOS or Windows. If you're on macOS, use **Option 2: Build from Source** instead.

For Linux users:

```bash
# Check if kantra is installed
which kantra

# Check available kantra container images
podman images | grep konveyor

# Extract the generic provider binary from the kantra container
podman run --rm --entrypoint sh \
  -v ~/Downloads:/output:Z \
  quay.io/konveyor/kantra:latest \
  -c "cp /usr/local/bin/generic-external-provider /output/"

# Install to your PATH
sudo cp ~/Downloads/generic-external-provider /usr/local/bin/
chmod +x /usr/local/bin/generic-external-provider

# Verify installation
generic-external-provider --help
```

**Note:** Replace `latest` with your specific kantra version tag if needed (e.g., `v0.8.1-alpha.1`).

### Option 2: Build from Source (Required for macOS)

**For macOS users:** This is the recommended method since the container binaries are Linux-only.

```bash
# Prerequisites: Go 1.21+ must be installed
# Install Go on macOS:
brew install go

# Clone the analyzer-lsp repository
git clone https://github.com/konveyor/analyzer-lsp.git
cd analyzer-lsp

# Build the generic provider (creates a native binary for your OS)
make external-generic

# The binary will be located at:
# external-providers/generic-external-provider/generic-external-provider

# Verify it's a native binary
file external-providers/generic-external-provider/generic-external-provider
# macOS: Should show "Mach-O 64-bit executable"
# Linux: Should show "ELF 64-bit executable"

# Install to your PATH
sudo cp external-providers/generic-external-provider/generic-external-provider \
        /usr/local/bin/
chmod +x /usr/local/bin/generic-external-provider

# Verify installation
generic-external-provider --help
```

### Verify Installation

After installation, verify the binary is accessible:

```bash
which generic-external-provider
# Should output: /usr/local/bin/generic-external-provider
```

## Step 3: Build Konveyor Analyzer from Source

**Important:** The generic TypeScript provider requires running `konveyor-analyzer` directly on your host system, not through kantra's container. This is because the analyzer needs access to:
- The generic-external-provider binary on your host
- The TypeScript language server on your host
- Your project files with proper paths

```bash
# Clone the analyzer-lsp repository
cd ~/Workspace  # or your preferred directory
git clone https://github.com/konveyor/analyzer-lsp.git
cd analyzer-lsp

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
    "name": "generic",
    "binaryPath": "/usr/local/bin/generic-external-provider",
    "initConfig": [
      {
        "location": "/absolute/path/to/your/typescript/project",
        "analysisMode": "full",
        "providerSpecificConfig": {
          "name": "typescript",
          "lspServerName": "typescript-language-server",
          "lspServerPath": "/usr/local/bin/typescript-language-server",
          "lspServerArgs": ["--stdio"],
          "workspaceFolder": "/absolute/path/to/your/typescript/project"
        }
      }
    ]
  }
]
```

### Configuration Fields Explained

- **`name`**: Must be `"generic"` for the generic external provider
- **`binaryPath`**: Absolute path to the generic-external-provider binary
- **`location`**: Absolute path to the TypeScript/JavaScript project to analyze
- **`analysisMode`**:
  - `"full"`: Analyze source code and dependencies
  - `"source-only"`: Only analyze source code
- **`providerSpecificConfig`**:
  - **`name`**: Identifier for this language server (e.g., `"typescript"`)
  - **`lspServerName`**: Name of the language server
  - **`lspServerPath`**: Absolute path to the language server executable (use `which typescript-language-server`)
  - **`lspServerArgs`**: Arguments to pass to the language server (usually `["--stdio"]`)
  - **`workspaceFolder`**: Absolute path to project root for the language server context

**Note:** All paths must be absolute paths, not relative paths.

## Step 5: Write Rules Using TypeScript Provider

Once configured, you can write analyzer rules that leverage TypeScript semantic analysis.

### Example Rule: Detect Function Components with propTypes

```yaml
- ruleID: react-18-to-react-19-proptypes
  description: Function components should not use propTypes
  when:
    typescript.referenced:
      pattern: "propTypes"
      location: "FUNCTION_DECLARATION"
  message: |
    React 19 deprecates propTypes on function components.
    Use TypeScript types or PropTypes on class components instead.
  effort: 5
  category: mandatory
  labels:
    - konveyor.io/source=react-18
    - konveyor.io/target=react-19
```

### Available Query Capabilities

With TypeScript language server, you can query:

- **Symbol references**: Find where types, functions, classes are used
- **Type information**: Get type definitions and inheritance
- **Call hierarchies**: Understand function call chains
- **Code structure**: Distinguish between functions, classes, methods
- **Import/export analysis**: Track module dependencies

## Step 6: Update Rule Generator

To make the rule generator automatically create TypeScript-aware rules, update the pattern detection logic:

### File: `src/rule_generator/rule_builder.py`

```python
def _build_when_condition(self, pattern: MigrationPattern) -> Optional[Dict]:
    """Build when condition based on pattern type."""

    # Existing logic for builtin.filecontent, builtin.xml, etc.

    # Add TypeScript provider support
    if pattern.file_type in ['.ts', '.tsx', '.js', '.jsx']:
        # Check if pattern requires semantic analysis
        if self._requires_semantic_analysis(pattern):
            return {
                "typescript.referenced": {
                    "pattern": pattern.search_pattern,
                    "location": self._infer_location_context(pattern)
                }
            }

    # Fall back to file content matching
    return {
        "builtin.filecontent": {
            "pattern": pattern.search_pattern,
            "filePattern": self._get_file_pattern(pattern.file_type)
        }
    }

def _requires_semantic_analysis(self, pattern: MigrationPattern) -> bool:
    """Determine if pattern needs TypeScript language server."""
    semantic_keywords = [
        'function component',
        'class component',
        'type definition',
        'interface',
        'generic type',
        'implicit return'
    ]

    return any(keyword in pattern.description.lower()
               for keyword in semantic_keywords)

def _infer_location_context(self, pattern: MigrationPattern) -> str:
    """Infer AST location context from pattern description."""
    context_map = {
        'function': 'FUNCTION_DECLARATION',
        'class': 'CLASS_DECLARATION',
        'method': 'METHOD_DECLARATION',
        'import': 'IMPORT_DECLARATION',
        'variable': 'VARIABLE_DECLARATION'
    }

    for keyword, location in context_map.items():
        if keyword in pattern.description.lower():
            return location

    return "ANY"
```

## Step 7: Testing the Setup

### 7.1 Create a Test TypeScript Project

```typescript
// test-project/src/component.tsx
import React from 'react';
import PropTypes from 'prop-types';

// This should trigger the rule
function MyComponent(props: any) {
  return <div>{props.name}</div>;
}

MyComponent.propTypes = {
  name: PropTypes.string
};
```

Don't forget to create a `tsconfig.json` in your test project root:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "jsx": "react",
    "lib": ["ES2020", "DOM"],
    "strict": false,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

### 7.2 Run Analysis with Konveyor Analyzer

**Important:** Use `konveyor-analyzer` directly, not `kantra`:

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

### 7.3 Verify Results

Check `output.yaml` for violations detected by the TypeScript provider.

Example expected output:

```yaml
- name: custom-rules
  violations:
    typescript-provider-test-00000:
      - uri: file:///path/to/test-project/src/component.tsx
        message: |
          React 19 deprecates propTypes on function components.
          Use TypeScript types or PropTypes on class components instead.
```

## Troubleshooting

### "unable to init the providers" error with kantra

**Error:**
```
time="..." level=error msg="unable to init the providers" error="generic client name not found" provider=typescript
```

**Solution:** You cannot use kantra (containerized analyzer) with the TypeScript generic provider. You must use `konveyor-analyzer` directly on your host system. See Step 7.2 for details.

### "unable to find provider for: typescript" error

**Error:**
```
level=error msg="failed parsing conditions for provider" capability=referenced error="unable to find provider for: typescript"
```

**Cause:** The provider configuration is incorrect or the generic provider binary cannot be found.

**Solution:**
1. Verify provider_settings.json is an array format (starts with `[`)
2. Verify `name` is set to `"generic"` not `"typescript"`
3. Add `"name": "typescript"` inside `providerSpecificConfig`
4. Ensure absolute paths are used for all paths

### "connection refused" error

**Error:**
```
error="rpc error: code = Unavailable desc = connection error: desc = \"transport: Error while dialing: dial tcp [::1]:43945: connect: connection refused\""
```

**Solution:**
- Ensure the generic-external-provider binary path is correct and executable
- Verify you're running konveyor-analyzer directly, not through kantra
- Check that the binary has execute permissions: `chmod +x /usr/local/bin/generic-external-provider`

### Language Server Not Found

```bash
# Check if typescript-language-server is in PATH
which typescript-language-server

# Update provider_settings.json with the full absolute path
"lspServerPath": "/opt/homebrew/bin/typescript-language-server"  # macOS with Homebrew
# or
"lspServerPath": "/usr/local/bin/typescript-language-server"      # Linux or macOS
```

### No Violations Detected

1. Verify provider is loaded:
   ```bash
   # Run analyzer with --verbose=4 and check logs
   grep -i "typescript\|generic" output.yaml
   ```

2. Test language server directly:
   ```bash
   typescript-language-server --stdio
   # Should start and wait for input (Ctrl+C to exit)
   ```

3. Ensure `tsconfig.json` exists in project root:
   ```json
   {
     "compilerOptions": {
       "target": "ES2020",
       "module": "commonjs",
       "jsx": "react",
       "lib": ["ES2020", "DOM"]
     },
     "include": ["src/**/*"]
   }
   ```

4. Verify all paths in provider_settings.json are absolute paths

### Provider Configuration Format Error

**Error:**
```
error="yaml: unmarshal errors:\n  line 1: cannot unmarshal !!map into []provider.Config"
```

**Solution:** The provider_settings.json must be an array. Ensure your configuration starts with `[` and ends with `]`:

```json
[
  {
    "name": "generic",
    ...
  }
]
```

## Limitations

Current limitations when using generic provider with TypeScript:

1. **Cannot use kantra**: The TypeScript generic provider requires running `konveyor-analyzer` directly on the host system. It cannot be used with kantra's containerized analyzer because:
   - The container cannot access the host's generic-external-provider binary
   - The container cannot access the host's typescript-language-server binary
   - The generic provider needs to spawn the language server process on the host

2. **Provider Queries**: The exact query capabilities exposed by the generic provider for TypeScript are still being documented. Current known capabilities include:
   - `typescript.referenced`: Find references to symbols with location context
   - Location contexts: `FUNCTION_DECLARATION`, `CLASS_DECLARATION`, `METHOD_DECLARATION`, `IMPORT_DECLARATION`, `TYPE_ALIAS_DECLARATION`, `INTERFACE_DECLARATION`, `VARIABLE_DECLARATION`

3. **AST Context**: May not support all TypeScript AST node types. The generic provider wraps the TypeScript language server's LSP capabilities.

4. **Performance**: Full workspace analysis can be slow for large TypeScript projects, especially with semantic analysis enabled.

5. **Absolute Paths Required**: All paths in provider_settings.json must be absolute paths. Relative paths will not work.

## Next Steps

1. **Test with Real Migration Guides**: Try React 19, Angular, or TypeScript upgrade guides
2. **Document Query Patterns**: Build a library of TypeScript provider query examples
3. **Contribute to Konveyor**: Share TypeScript provider configuration upstream
4. **Enhance Rule Generator**: Add more sophisticated TypeScript pattern detection

## References

- [Konveyor analyzer-lsp](https://github.com/konveyor/analyzer-lsp)
- [Provider Documentation](https://github.com/konveyor/analyzer-lsp/blob/main/docs/providers.md)
- [TypeScript Language Server](https://github.com/typescript-language-server/typescript-language-server)
- [Language Server Protocol Specification](https://microsoft.github.io/language-server-protocol/)
