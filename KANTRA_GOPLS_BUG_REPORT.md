# Kantra Bug Report: Go Provider Fails with EOF Error Due to Hardcoded gopls Path

## Summary

All Go provider tests fail immediately with `rpc error: code = Unavailable desc = error reading from server: EOF` because kantra hardcodes the gopls path as `/root/go/bin/gopls`, but the actual binary is located at `/usr/local/bin/gopls` in the current container images.

## Environment

- **Kantra Image**: `quay.io/konveyor/kantra:latest` (pulled 2025-12-31)
- **Container Tool**: podman
- **gopls Version**: v0.20.0 (located at `/usr/local/bin/gopls` inside container)

## Root Cause

The Go provider configuration in `pkg/testing/runner.go` has a hardcoded incorrect path:

**File**: `pkg/testing/runner.go:66-79`
```go
{
    Name:       "go",
    BinaryPath: "/usr/local/bin/generic-external-provider",
    InitConfig: []provider.InitConfig{
        {
            AnalysisMode: provider.FullAnalysisMode,
            ProviderSpecificConfig: map[string]interface{}{
                "lspServerName":                 "generic",
                provider.LspServerPathConfigKey: "/root/go/bin/gopls",  // ← WRONG PATH
                "lspServerArgs":                 []string{},
                "dependencyProviderPath":        "/usr/local/bin/golang-dependency-provider",
            },
        },
    },
},
```

## Evidence

### 1. Actual gopls Location in Container

```bash
$ podman run --rm --entrypoint which quay.io/konveyor/kantra:latest gopls
/usr/local/bin/gopls

$ podman run --rm --entrypoint gopls quay.io/konveyor/kantra:latest version
Build info
-----------
golang.org/x/tools/gopls v0.20.0
```

### 2. Error Logs

From `analysis.log`:
```
time="2026-01-01T02:18:26Z" level=info msg="provider configuration"
config="{\"lspServerPath\":\"/root/go/bin/gopls\",\"workspaceFolders\":[\"/data/data/deprecated-packages\"]}"

time="2026-01-01T02:18:26Z" level=error msg="Error inside ProviderInit, after g.Init."
error="rpc error: code = Unavailable desc = error reading from server: EOF"

time="2026-01-01T02:18:26Z" level=error msg="unable to init the providers"
error="rpc error: code = Unavailable desc = error reading from server: EOF" provider=go
```

### 3. Provider Override Not Working

Test files can specify custom provider settings:

**Example test YAML**:
```yaml
providers:
- name: go
  dataPath: /path/to/data
  initConfig:
    lspServerPath: /usr/local/bin/gopls  # ← This override is IGNORED
```

However, `getMergedProviderConfig()` (lines 497-534) only merges:
- `workspaceFolders`
- `lspServerArgs` (for logging)

It **does not merge** the `lspServerPath` from test file overrides, so the hardcoded wrong path is always used.

## Impact

- **100% failure rate** for all Go provider tests
- **Provider configuration overrides** in test files are ineffective for `lspServerPath`
- **Blocks testing** of Go migration rules
- **Other providers work fine** (Python uses `/usr/local/bin/pylsp`, NodeJS uses `/usr/local/bin/typescript-language-server`, both correct)

## Proposed Fixes

### Option 1: Update Hardcoded Path (Quick Fix)

Change line 73 in `pkg/testing/runner.go`:
```go
provider.LspServerPathConfigKey: "/usr/local/bin/gopls",  // Changed from /root/go/bin/gopls
```

### Option 2: Enable Provider Override (Better Fix)

Enhance `getMergedProviderConfig()` to properly merge `initConfig` from test files, allowing users to override the `lspServerPath` and other provider-specific settings.

**Example enhancement** (in the `case "go":` section around line 518):
```go
case "go":
    initConf.ProviderSpecificConfig["workspaceFolders"] = []string{dataPath}

    // Allow override of lspServerPath from test file
    if override.InitConfig != nil && len(override.InitConfig) > 0 {
        if lspPath, ok := override.InitConfig[0].ProviderSpecificConfig[provider.LspServerPathConfigKey]; ok {
            initConf.ProviderSpecificConfig[provider.LspServerPathConfigKey] = lspPath
        }
    }

    lspArgs, ok := initConf.ProviderSpecificConfig["lspServerArgs"].([]string)
    if ok {
        initConf.ProviderSpecificConfig["lspServerArgs"] = append(lspArgs,
            "--logfile", path.Join(outputPath, "go-server.log"), "-vv")
    }
```

## Steps to Reproduce

1. Create a test YAML file with Go provider:
```yaml
rulesPath: /path/to/rules.yaml
providers:
- name: go
  dataPath: /path/to/go/code
tests:
- ruleID: test-rule-00001
  testCases:
  - name: test case 1
    hasIncidents:
      atLeast: 1
```

2. Run kantra test:
```bash
kantra test /path/to/test.yaml
```

3. Observe EOF error in logs:
```
Error inside ProviderInit, after g.Init. error="rpc error: code = Unavailable desc = error reading from server: EOF"
```

## Related Code References

- Default provider config: `pkg/testing/runner.go:45-125`
- Provider merge logic: `pkg/testing/runner.go:497-534`
- TODO comment acknowledging issue: `pkg/testing/runner.go:43-44`

## Additional Notes

The code contains a TODO comment (lines 43-44) suggesting the developers are aware that the hardcoded defaults are problematic:
```go
// TODO (pgaikwad): we need to move the default config to a common place
// to be shared between kantra analyze command and this
```

This bug appears to have been introduced when the gopls binary location changed in the container image, but the hardcoded path in the test runner was not updated.
