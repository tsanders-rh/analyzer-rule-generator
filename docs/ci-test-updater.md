# CI Test Dependency Updater

Update `go-konveyor-tests` dependency expectations from analyzer output.

## Overview

When submitting new rules to Konveyor, you need to:
1. Add your rules to `konveyor/rulesets`
2. Add/update test cases in `konveyor/go-konveyor-tests`

This script automates step 2 by generating the Go test case code with dependencies extracted from analyzer output.

## Prerequisites

- Python 3.8+
- PyYAML (`pip install pyyaml`)
- Analyzer output file (from running `kantra analyze`)

## Usage

### Update Existing Test Case

Update an existing test case file with new dependencies:

```bash
python scripts/update_test_dependencies.py \
    --analyzer-output analysis_output.yaml \
    --test-case tc_myapp_deps.go
```

### Generate New Test Case

Create a new test case file:

```bash
python scripts/update_test_dependencies.py \
    --analyzer-output analysis_output.yaml \
    --output tc_newapp_deps.go \
    --test-name "NewApp Dependencies" \
    --app-name "NewApp"
```

### Preview Without Writing

See what would be generated without writing files:

```bash
python scripts/update_test_dependencies.py \
    --analyzer-output analysis_output.yaml \
    --output tc_test.go \
    --test-name "Test" \
    --app-name "TestApp" \
    --print-only
```

## Analyzer Output Format

The script accepts YAML or JSON output from the analyzer. It looks for dependencies in these formats:

### Format 1: dependencies key
```yaml
dependencies:
  - name: "org.springframework.boot"
    version: "3.0.0"
    provider: "java"
  - name: "jakarta.persistence-api"
    version: "3.1.0"
    provider: "java"
```

### Format 2: techDependencies key
```yaml
techDependencies:
  - name: "org.springframework.boot"
    version: "3.0.0"
    provider: "java"
```

### Format 3: Direct list
```yaml
- name: "org.springframework.boot"
  version: "3.0.0"
  provider: "java"
```

## Workflow Example

### 1. Run Analyzer

```bash
# Analyze application with your new rules
kantra analyze \
    --input /path/to/app \
    --rules /path/to/your/rules.yaml \
    --output analysis_output
```

### 2. Extract Dependencies

The analyzer output will contain discovered dependencies. Save this to a file:

```bash
# Extract dependencies from analyzer output
# (format varies by analyzer version)
cat analysis_output/output.yaml | yq '.dependencies' > deps.yaml
```

### 3. Update Test Case

```bash
# Update the go-konveyor-tests file
cd /path/to/go-konveyor-tests

python /path/to/update_test_dependencies.py \
    --analyzer-output /path/to/deps.yaml \
    --test-case analysis/tc_myapp_deps.go
```

### 4. Verify and Commit

```bash
# Review the changes
git diff analysis/tc_myapp_deps.go

# Commit if looks good
git add analysis/tc_myapp_deps.go
git commit -m "Update dependencies for myapp test case"
```

## Generated Code Structure

For a new test case, the script generates:

```go
package analysis

import (
	"github.com/konveyor-ecosystem/go-konveyor-tests/data"
	"github.com/konveyor-ecosystem/go-konveyor-tests/hack/addon"
	api "github.com/konveyor/tackle2-hub/api"
)

var MyAppDeps = TC{
	Name: "MyApp Dependencies",
	Application: data.MyApp,
	Task: Task,
	Analysis: api.Analysis{
		Dependencies: []api.TechDependency{
			{
				Name:     "org.springframework.boot",
				Version:  "3.0.0",
				Provider: "java",
			},
			// ... more dependencies
		},
	},
}
```

## Integration with Rule Submission

This tool integrates with the rule submission workflow:

1. **Generate rules** with `generate_rules.py`
2. **Test rules locally** with kantra
3. **Extract dependencies** from test results
4. **Update test cases** with this script
5. **Submit PR** to both repositories:
   - `konveyor/rulesets` - new rules
   - `konveyor/go-konveyor-tests` - updated test expectations

## Troubleshooting

### "Could not find Dependencies section"

The script uses regex to find and replace the `Dependencies:` section. If this fails, the file structure may be different. You can:
- Use `--print-only` to see generated code
- Manually copy the dependencies section

### "Could not parse as YAML or JSON"

Ensure your analyzer output file is valid YAML or JSON. Check for:
- Proper indentation
- Valid syntax
- No syntax errors

### Wrong dependency format

The script expects dependencies with `name`, `version`, and `provider` fields. If your analyzer output uses different field names, you may need to transform it first.

## See Also

- [Konveyor Submission Guide](konveyor-submission-guide.md)
- [go-konveyor-tests repository](https://github.com/konveyor/go-konveyor-tests)
- [Konveyor rulesets repository](https://github.com/konveyor/rulesets)
