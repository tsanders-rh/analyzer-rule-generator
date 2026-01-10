# Kantra Bug Report: Node.js Provider Fails with EOF Error

## Summary

All Node.js provider tests fail immediately with `rpc error: code = Unavailable desc = error reading from server: EOF` because the TypeScript language server is not available at the configured path within the kantra container.

## Environment

- **Kantra Image**: `quay.io/konveyor/kantra:latest` (pulled 2026-01-05)
- **Container Tool**: podman
- **Kantra Version**: latest

## Root Cause

**The issue is that `kantra test` and `kantra analyze` use different container architectures:**

### How `kantra analyze` Works ✅

`kantra analyze` **spawns separate provider containers** from images like `quay.io/konveyor/generic-external-provider`:
- Console output shows: `✓ Started provider containers`
- Each provider (nodejs, python, etc.) runs in its own dedicated container
- The generic-external-provider container **DOES** have typescript-language-server at `/usr/local/bin/`
- Result: **Works perfectly** - nodejs.referenced rules detect violations

### How `kantra test` Works ❌

`kantra test` **runs providers from within the main kantra container**:
- Uses the `generic-external-provider` binary embedded in the kantra container
- Tries to find LSP servers in the kantra container's filesystem
- The kantra container does **NOT** have typescript-language-server installed
- Result: **Fails with EOF** - provider initialization crashes

### Architecture Difference

Kantra uses a multi-container architecture:
1. **Main kantra container**: Contains `konveyor-analyzer` and `generic-external-provider` binary
2. **Separate provider containers**: `quay.io/konveyor/generic-external-provider`, `quay.io/konveyor/java-external-provider`, etc.

The LSP servers (typescript-language-server, pylsp) are only in the provider containers, NOT in the main kantra container.

## Evidence

### 1. typescript-language-server NOT in kantra container

```bash
$ podman run --rm --entrypoint ls quay.io/konveyor/kantra:latest -la /usr/local/bin/typescript-language-server
ls: cannot access '/usr/local/bin/typescript-language-server': No such file or directory
```

### 2. typescript-language-server IS in generic-external-provider container

```bash
$ podman run --rm --entrypoint ls quay.io/konveyor/generic-external-provider:latest -la /usr/local/bin/ | grep typescript
lrwxrwxrwx. 1 root root 58 Dec 11 20:53 typescript-language-server -> ../lib/node_modules/typescript-language-server/lib/cli.mjs
```

### 3. kantra analyze WORKS with nodejs provider

```bash
$ kantra analyze --input demo-output/react-17-to-react-18/tests/data/server-rendering \
  --output /tmp/kantra-analyze-test \
  --rules demo-output/react-17-to-react-18/rules/react-17-to-react-18-server-rendering.yaml

Running source analysis...
  ✓ Created volume
  ✓ Started provider containers          ← Spawns separate containers!
  ✓ Initialized providers (builtin, nodejs)
  ✓ Started rules engine
  ✓ Preparing nodejs provider 100%
  ✓ Loaded 537 rules
  ✓ Processing rules 100%

$ grep -A5 "react-17-to-react-18-00040" /tmp/kantra-analyze-test/output.yaml
    react-17-to-react-18-00040:
      description: renderToNodeStream should be replaced with renderToPipeableStream
      # ✓ Successfully detected nodejs.referenced violation!
```

### 4. kantra test FAILS with EOF Error - Logs from analysis.log

```
time="2026-01-05T15:23:52Z" level=info msg="provider configuration"
config="{\"lspServerPath\":\"/usr/local/bin/typescript-language-server\",\"workspaceFolders\":[\"/data/data/server-rendering\"]}"

time="2026-01-05T15:23:52Z" level=error msg="unable to init the providers"
error="rpc error: code = Unavailable desc = error reading from server: EOF" provider=nodejs

time="2026-01-05T15:23:52Z" level=error msg="Error inside ProviderInit, after g.Init."
error="rpc error: code = Unavailable desc = error reading from server: EOF" logger=nodejs provider=grpc
```

### 5. Provider Configuration in kantra test runner

From `pkg/testing/runner.go` in kantra source:

```go
{
    Name:       "nodejs",
    BinaryPath: "/usr/local/bin/generic-external-provider",
    InitConfig: []provider.InitConfig{
        {
            AnalysisMode: provider.FullAnalysisMode,
            ProviderSpecificConfig: map[string]interface{}{
                "lspServerName":                 "nodejs",
                provider.LspServerPathConfigKey: "/usr/local/bin/typescript-language-server",  // ← WRONG - not in kantra container
                "lspServerArgs":                 []string{"--stdio"},
                "workspaceFolders":              []string{},
                "dependencyFolders":             []string{},
            },
        },
    },
}
```

## Impact

- **100% failure rate** for all nodejs.referenced provider tests
- **Blocks testing** of JavaScript/TypeScript migration rules that use `nodejs.referenced`
- **Tests using `builtin.filecontent` work fine** as they don't need the LSP server

### Affected Rules

Rules using `nodejs.referenced` pattern matching fail:
```yaml
when:
  nodejs.referenced:
    pattern: renderToNodeStream
```

### Working Alternative

Rules using `builtin.filecontent` work correctly:
```yaml
when:
  builtin.filecontent:
    pattern: renderToNodeStream\(
    filePattern: \.(j|t)sx?$
```

## Comparison with Other Providers

| Provider | LSP Server Path in Config | Actually Exists in kantra Container? | Status |
|----------|--------------------------|-------------------------------------|---------|
| Go | `/root/go/bin/gopls` | ❌ No (wrong path - should be `/usr/local/bin/gopls`) | **FAILS** |
| Node.js | `/usr/local/bin/typescript-language-server` | ❌ No (only in separate container) | **FAILS** |
| Python | `/usr/local/bin/pylsp` | ⚠️  Unknown (needs verification) | Unknown |
| Java | `/jdtls/bin/jdtls` | ✅ Yes (`/jdtls` dir exists) | Works |

## Proposed Solutions

### Option 1: Make `kantra test` Use Provider Containers (Recommended)

**Change `kantra test` to spawn separate provider containers** like `kantra analyze` does.

Currently:
- ❌ `kantra test`: Runs providers from main kantra container binary
- ✅ `kantra analyze`: Spawns dedicated provider containers

**Fix**: Modify `pkg/testing/runner.go` to use the same container spawning approach as analyze.

**Pros:**
- Consistent behavior between test and analyze
- Providers have all their dependencies (LSP servers, etc.)
- Matches the intended multi-container architecture

**Cons:**
- May be slower to spawn multiple containers
- Slightly more complex test setup

### Option 2: Install LSP Servers in Main Kantra Container

Add typescript-language-server, pylsp, and other LSP servers to the main kantra container Dockerfile.

**Pros:**
- Quick fix - just update Dockerfile
- Consistent with how gopls is installed (`/usr/local/bin/gopls` exists in kantra)
- Faster test execution (no container spawning)

**Cons:**
- Increases kantra container size significantly (adds Node.js, npm, Python, pip, etc.)
- Duplicates LSP servers across multiple containers
- Goes against the multi-container architecture design

### Option 3: Use builtin.filecontent Instead

As a workaround, convert rules to use `builtin.filecontent` with regex patterns:

**Before:**
```yaml
when:
  nodejs.referenced:
    pattern: renderToNodeStream
```

**After:**
```yaml
when:
  builtin.filecontent:
    pattern: renderToNodeStream\(
    filePattern: \.(j|t)sx?$
```

**Pros:**
- Works immediately without container changes
- Faster execution (no LSP overhead)

**Cons:**
- Less precise (text matching vs semantic analysis)
- Potential false positives

## Steps to Reproduce

1. Create a rule using nodejs.referenced:
```yaml
- ruleID: test-nodejs-00001
  when:
    nodejs.referenced:
      pattern: someFunction
  message: Test message
```

2. Create a test YAML:
```yaml
rulesPath: ../rules/test.yaml
providers:
- name: nodejs
  dataPath: ./data/test
tests:
- ruleID: test-nodejs-00001
  testCases:
  - name: tc - 1
    hasIncidents:
      atLeast: 1
```

3. Run kantra test:
```bash
kantra test test.test.yaml
```

4. Observe EOF error:
```
error="rpc error: code = Unavailable desc = error reading from server: EOF" provider=nodejs
```

## Verification Commands

### Check what's in kantra container
```bash
podman run --rm --entrypoint ls quay.io/konveyor/kantra:latest -la /usr/local/bin/
```

### Check what's in generic-external-provider container
```bash
podman run --rm --entrypoint ls quay.io/konveyor/generic-external-provider:latest -la /usr/local/bin/
```

### Run a test and capture logs
```bash
kantra test your-test.yaml 2>&1 | tee test-output.log
find /var/folders -name "analysis.log" -mmin -5 | head -1 | xargs cat
```

## Related Issues

- This is similar to the Go provider gopls path bug (see KANTRA_GOPLS_BUG_REPORT.md)
- Both issues stem from LSP server path misconfigurations in `pkg/testing/runner.go`

## Status

**UNRESOLVED** - nodejs.referenced tests fail with EOF errors

**Workaround**: Use `builtin.filecontent` patterns instead of `nodejs.referenced` for JavaScript/TypeScript rules.
