# TypeScript Provider Test Setup

This directory contains test files for validating the TypeScript provider integration with Konveyor analyzer.

## Files

- **`test-react-app/`**: Sample React TypeScript application with code that should trigger the test rules
  - `src/Component.tsx`: Contains various React patterns that violate migration rules
  - `package.json`: Project dependencies
  - `tsconfig.json`: TypeScript configuration

- **`provider_settings.json`**: Provider configuration for TypeScript language server
- **`../../test-rules/typescript-provider-test.yaml`**: Test rules that use TypeScript provider

## Prerequisites

Before running the tests, ensure you have:

1. **TypeScript Language Server** installed:
   ```bash
   npm install -g typescript-language-server typescript
   which typescript-language-server
   ```

2. **Generic Provider Binary** installed (see docs/typescript-provider-setup.md for instructions):
   ```bash
   which generic-external-provider
   ```

3. **Kantra** installed:
   ```bash
   which kantra
   ```

## Running the Test

**Important:** The TypeScript provider requires running `konveyor-analyzer` directly, not through kantra. See [TypeScript Provider Setup](../../../docs/typescript-provider-setup.md) for full details.

### Step 1: Build Konveyor Analyzer

```bash
# Clone and build analyzer-lsp if you haven't already
cd ~/Workspace
git clone https://github.com/konveyor/analyzer-lsp.git
cd analyzer-lsp
make build

# Verify the binary
./konveyor-analyzer --help
```

### Step 2: Update Provider Settings

The `provider_settings.json` file has been pre-configured, but you may need to verify the paths match your system:

```bash
# Find your typescript-language-server path
which typescript-language-server
# Update provider_settings.json if the path differs from /opt/homebrew/bin/typescript-language-server
```

The correct format should be:

```json
[
  {
    "name": "generic",
    "binaryPath": "/usr/local/bin/generic-external-provider",
    "initConfig": [
      {
        "location": "/absolute/path/to/test-react-app",
        "analysisMode": "full",
        "providerSpecificConfig": {
          "name": "typescript",
          "lspServerName": "typescript-language-server",
          "lspServerPath": "/your/path/to/typescript-language-server",
          "lspServerArgs": ["--stdio"],
          "workspaceFolder": "/absolute/path/to/test-react-app"
        }
      }
    ]
  }
]
```

**Note:** All paths must be absolute paths.

### Step 3: Run Analysis with Konveyor Analyzer

**Do NOT use kantra** - it runs in a container and cannot access the TypeScript provider.

```bash
# From the analyzer-lsp directory
cd ~/Workspace/analyzer-lsp

./konveyor-analyzer \
  --provider-settings=/Users/tsanders/Workspace/analyzer-rule-generator/examples/test-apps/typescript/provider_settings.json \
  --rules=/Users/tsanders/Workspace/analyzer-rule-generator/examples/test-rules/typescript-provider-test.yaml \
  --output-file=/Users/tsanders/Workspace/analyzer-rule-generator/examples/test-apps/typescript/output.yaml \
  --context-lines=10 \
  --verbose=4
```

**Why not kantra?**
- Kantra runs in a container and cannot access the generic-external-provider binary on your host
- Kantra cannot access the typescript-language-server binary on your host
- The generic provider needs to spawn processes on the host system

### Step 3: Review Results

Check `output.yaml` for violations. You should see violations for:

1. **typescript-provider-test-00000**: propTypes on function component in `Component.tsx`
2. **typescript-provider-test-00010**: React.FC usage in `Component.tsx`
3. **typescript-provider-test-00030**: componentWillMount in LegacyComponent class
4. **typescript-provider-test-00040**: Import from react-router instead of react-router-dom

## Expected Violations

The test app (`test-react-app/src/Component.tsx`) contains code that intentionally violates the test rules:

| Line | Issue | Rule ID |
|------|-------|---------|
| 5-12 | Function component with propTypes | typescript-provider-test-00000 |
| 15 | Usage of React.FC type | typescript-provider-test-00010 |
| 21-26 | componentWillMount lifecycle method | typescript-provider-test-00030 |
| 3 | Import from react-router | typescript-provider-test-00040 |

## Troubleshooting

### Error: "unable to init the providers" with kantra

If you see this error when using kantra:
```
time="..." level=error msg="unable to init the providers" error="generic client name not found" provider=typescript
```

**Solution:** You cannot use kantra with the TypeScript provider. Use `konveyor-analyzer` directly as shown in Step 3.

### Error: "connection refused"

```
error="rpc error: code = Unavailable desc = connection error"
```

**Solutions:**
1. Verify you're running `konveyor-analyzer` directly (not kantra)
2. Ensure generic-external-provider binary exists and is executable:
   ```bash
   ls -la /usr/local/bin/generic-external-provider
   chmod +x /usr/local/bin/generic-external-provider
   ```
3. Verify provider_settings.json uses absolute paths

### Error: "yaml: unmarshal errors"

```
error="yaml: unmarshal errors:\n  line 1: cannot unmarshal !!map into []provider.Config"
```

**Solution:** Ensure provider_settings.json is an array (starts with `[`):
```json
[
  {
    "name": "generic",
    ...
  }
]
```

### No violations detected

1. Verify TypeScript language server is accessible:
   ```bash
   typescript-language-server --stdio
   # Should start and wait for input (Ctrl+C to exit)
   ```

2. Check analyzer output for errors:
   ```bash
   # Look for TypeScript provider initialization
   grep -i "typescript\|generic\|error" output.yaml
   ```

3. Verify all paths in provider_settings.json are absolute paths

4. Ensure tsconfig.json exists in test-react-app directory

### Language server not found

```bash
# Install if missing
npm install -g typescript-language-server typescript

# Find the installed path
which typescript-language-server

# Update provider_settings.json with the correct path
# macOS with Homebrew: /opt/homebrew/bin/typescript-language-server
# Linux or macOS: /usr/local/bin/typescript-language-server
```

## Notes

- **Cannot use kantra:** The TypeScript provider requires running `konveyor-analyzer` directly on the host system, not through kantra's containerized environment
- The TypeScript provider uses the Language Server Protocol (LSP) for semantic analysis
- Rules with `typescript.referenced` require the language server to analyze code structure
- Rules with `builtin.filecontent` use regex pattern matching and don't require the language server
- Make sure `tsconfig.json` is present in the project root for proper TypeScript analysis
- All paths in `provider_settings.json` must be absolute paths
