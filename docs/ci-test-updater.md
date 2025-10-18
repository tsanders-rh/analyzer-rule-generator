# CI Test Case Updater - Script Reference

Automated generation and updating of `go-konveyor-tests` test cases from Kantra analysis output.

## Overview

When submitting new rules to Konveyor, you need to:
1. Add your rules to `konveyor/rulesets`
2. Add/update test cases in `konveyor/go-konveyor-tests`

This script automates step 2 by generating complete Go test cases from Kantra analysis output, including:
- **Insights** - Rule violations with incidents (file paths and line numbers)
- **Effort** - Total calculated effort score
- **Dependencies** - Technology dependencies
- **AnalysisTags** - Technology tags from technology-usage ruleset

## Prerequisites

- Python 3.8+
- PyYAML (`pip install pyyaml`)
- Kantra analysis output directory (from running `kantra analyze`)

## Usage

### Update Existing Test Case

Update an existing test case file with all analysis results:

```bash
python scripts/update_test_dependencies.py \
    --analysis-dir /path/to/kantra-analysis-output \
    --normalize-path "/shared/source/sample" \
    --test-case tc_myapp_deps.go
```

### Generate New Test Case

Create a new test case file:

```bash
python scripts/update_test_dependencies.py \
    --analysis-dir /path/to/kantra-analysis-output \
    --normalize-path "/shared/source/sample" \
    --output tc_newapp_deps.go \
    --test-name "NewApp Analysis" \
    --app-name "NewApp"
```

### Preview Without Writing

See what would be generated without writing files:

```bash
python scripts/update_test_dependencies.py \
    --analysis-dir /path/to/kantra-analysis-output \
    --normalize-path "/shared/source/sample" \
    --output tc_test.go \
    --test-name "Test" \
    --app-name "TestApp" \
    --print-only
```

## Command-Line Parameters

### Required Parameters

- `--analysis-dir DIR` - Path to Kantra analysis output directory
  - Script automatically finds `dependencies.yaml` and `output.yaml` in this directory
  - Both files are required

### Output Parameters (mutually exclusive)

- `--test-case FILE` - Path to existing test case file to update
- `--output FILE` - Path for new test case file (requires `--test-name` and `--app-name`)

### Optional Parameters

- `--normalize-path PREFIX` - Normalize incident file paths to match CI environment
  - Example: `--normalize-path "/shared/source/sample"`
  - Converts local paths like `/Users/you/app/module-web/...` to `/shared/source/sample/module-web/...`
  - **Always use this when generating test cases for CI**

- `--print-only` - Preview generated code without writing files

### Parameters for New Test Cases

- `--test-name NAME` - Test case name (required when using `--output`)
- `--app-name NAME` - Application name (required when using `--output`)

## Kantra Analysis Directory Structure

After running `kantra analyze`, the output directory contains:

```
analysis-output/
├── dependencies.yaml    # Technology dependencies (REQUIRED)
├── output.yaml         # Violations and tags (REQUIRED)
└── static-report/      # HTML report
```

The script expects both `dependencies.yaml` and `output.yaml` to exist.

## Workflow Example

### 1. Run Kantra Analysis

```bash
# Analyze application with your rules
# IMPORTANT: Point --rules to your rulesets fork containing your new rules
kantra analyze \
    --input /path/to/test/application \
    --output /tmp/analysis-output \
    --rules /path/to/your/konveyor-rulesets \
    --target cloud-readiness \
    --target quarkus
```

### 2. Generate/Update Test Case

```bash
# Update existing test case
python scripts/update_test_dependencies.py \
    --analysis-dir /tmp/analysis-output \
    --normalize-path "/shared/source/sample" \
    --test-case ~/go-konveyor-tests/analysis/tc_daytrader_deps.go

# Or create new test case
python scripts/update_test_dependencies.py \
    --analysis-dir /tmp/analysis-output \
    --normalize-path "/shared/source/sample" \
    --output ~/go-konveyor-tests/analysis/tc_myapp_new.go \
    --test-name "MyApp Analysis" \
    --app-name "MyApp"
```

### 3. Verify and Commit

```bash
cd ~/go-konveyor-tests

# Review the changes
git diff analysis/tc_daytrader_deps.go

# Commit with DCO sign-off
git add analysis/tc_daytrader_deps.go
git commit -s -m "Update DayTrader test case for new Spring Boot migration rules"
```

## Generated Code Structure

The script generates complete test cases with all sections:

```go
package analysis

import (
	"github.com/konveyor-ecosystem/go-konveyor-tests/data"
	"github.com/konveyor-ecosystem/go-konveyor-tests/hack/addon"
	api "github.com/konveyor/tackle2-hub/api"
)

var MyApp = TC{
	Name: "MyApp Analysis",
	Application: data.MyApp,
	Task: Analyze,
	WithDeps: true,
	Analysis: api.Analysis{
		Effort: 318,
		Insights: []api.Insight{
			{
				Category:    "mandatory",
				Description: "File system - java.net.URL/URI",
				Effort:      1,
				RuleSet:     "cloud-readiness",
				Rule:        "local-storage-00002",
				Incidents: []api.Incident{
					{
						File: "/shared/source/sample/myapp-web/src/main/java/App.java",
						Line: 91,
					},
				},
			},
			// ... more insights
		},
		Dependencies: []api.TechDependency{
			{
				Name:     "org.springframework.boot:spring-boot-starter-web",
				Version:  "2.7.0",
				Provider: "java",
			},
			// ... more dependencies
		},
	},
	AnalysisTags: []api.Tag{
		{Name: "EJB XML", Category: api.Ref{Name: "Bean"}},
		{Name: "Servlet", Category: api.Ref{Name: "HTTP"}},
		{Name: "CDI", Category: api.Ref{Name: "Inversion of Control"}},
		// ... more tags
	},
}
```

## What Gets Generated

The script automatically extracts and generates:

### From `dependencies.yaml`
- ✅ **Dependencies** - All technology dependencies with name, version, provider
- Sorted alphabetically by name

### From `output.yaml`
- ✅ **Insights** - All rule violations with incidents (file paths and line numbers)
  - Sorted by ruleset then rule ID
- ✅ **Effort** - Total calculated effort score (effort × incident count for each rule)
- ✅ **AnalysisTags** - Technology tags from technology-usage ruleset
  - Tags like "EJB XML", "JSF", "CDI", etc.
  - Sorted alphabetically by name

## Update Behavior (REPLACE)

When updating existing test cases, the script uses **REPLACE** logic:
- All Insights are replaced with current analysis results
- All Dependencies are replaced with current analysis results
- All Tags are replaced with current analysis results
- Effort is recalculated from current results

**Why REPLACE makes sense for CI:**
1. Test reflects current state of analysis
2. Detects regressions when results change
3. Handles rule additions/removals cleanly
4. Simpler and clearer behavior

## Path Normalization

The `--normalize-path` parameter is critical for CI compatibility:

**Without normalization:**
```
File: "/Users/you/Workspace/daytrader/daytrader-ee7-web/src/main/java/App.java"
```

**With `--normalize-path "/shared/source/sample"`:**
```
File: "/shared/source/sample/daytrader-ee7-web/src/main/java/App.java"
```

The script intelligently finds project module directories and normalizes paths accordingly.

## Integration with Rule Submission

This tool integrates with the rule submission workflow:

1. **Generate rules** with `generate_rules.py`
2. **Test rules locally** with kantra
3. **Update CI test cases** with this script
4. **Submit PRs** to both repositories:
   - `konveyor/rulesets` - new rules
   - `konveyor/go-konveyor-tests` - updated test expectations
5. **Link PRs** together in descriptions

## Troubleshooting

### "Could not find dependencies.yaml in /path/to/directory"

**Cause:** The `--analysis-dir` doesn't point to a Kantra analysis output directory.

**Solution:**
- Verify the directory exists: `ls /path/to/analysis-output`
- Should contain: `dependencies.yaml`, `output.yaml`, `static-report/`
- Point to the directory, not individual files
- Correct: `--analysis-dir ~/analysis-results`
- Wrong: `--analysis-dir ~/analysis-results/dependencies.yaml`

### "Could not find output.yaml in /path/to/directory"

**Cause:** Missing `output.yaml` file from Kantra analysis.

**Solution:**
- Ensure Kantra analysis completed successfully
- Check analysis output directory contains both required files
- Re-run Kantra analysis if files are missing

### "Could not parse as YAML"

**Cause:** The analyzer output file is not valid YAML.

**Solution:**
- Verify the file exists: `ls -lh /path/to/output.yaml`
- Check it's valid YAML: `cat /path/to/output.yaml | head -50`
- Re-run Kantra analysis if file is corrupted

### No dependencies or insights found

**Cause:** The analyzer output doesn't contain expected data structures.

**Solution:**
- Check Kantra ran successfully: review logs
- Verify you're using correct `--target` labels
- Ensure rules are present in the analysis
- Check `output.yaml` and `dependencies.yaml` manually

### Paths don't match CI expectations

**Cause:** Forgot to use `--normalize-path` parameter.

**Solution:**
- Always use `--normalize-path "/shared/source/sample"` for CI test cases
- This converts local paths to CI-standard paths
- Compare with existing test cases to verify path format

## File Format Reference

### dependencies.yaml Format

```yaml
# List of file objects, each with dependencies
- fileURI: "file:///path/to/pom.xml"
  provider: "java"
  dependencies:
    - name: "org.springframework.boot:spring-boot-starter-web"
      version: "2.7.14"
      provider: "java"
```

### output.yaml Format

```yaml
# List of rulesets
- name: "cloud-readiness"
  violations:
    local-storage-00001:
      description: "File system - Java IO"
      category: "mandatory"
      effort: 1
      incidents:
        - uri: "file:///path/to/App.java"
          lineNumber: 42
          message: "..."

# Technology-usage ruleset (special)
- name: "technology-usage"
  tags:
    - "Bean=EJB XML"
    - "HTTP=Servlet"
    - "Inversion of Control=CDI"
```

## See Also

- [Updating CI Tests Guide](updating-ci-tests.md) - Step-by-step user guide
- [Konveyor Submission Guide](konveyor-submission-guide.md) - Complete submission process
- [go-konveyor-tests repository](https://github.com/konveyor/go-konveyor-tests)
- [Konveyor rulesets repository](https://github.com/konveyor/rulesets)
