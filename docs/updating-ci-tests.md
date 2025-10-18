# Updating CI Tests for New Rules

When you submit new rules to Konveyor, you need to update the CI test expectations in the `go-konveyor-tests` repository. This guide shows you how to automate that process.

## Overview

The Konveyor project maintains automated tests that verify:
- Rules still work correctly
- Analysis results are consistent
- Dependencies are detected properly
- No regressions occur

When you add new rules, you need to update the test expectations to reflect what your rules find.

## Prerequisites

1. **Konveyor rulesets fork** - Your rules are ready to submit
2. **go-konveyor-tests fork** - Fork of the test repository
3. **Kantra installed** - CLI tool for running analysis
4. **Test application** - The app your rules analyze

## Step-by-Step Guide

### 1. Fork go-konveyor-tests

```bash
# Go to GitHub and fork:
# https://github.com/konveyor/go-konveyor-tests

# Clone YOUR fork
git clone https://github.com/YOUR_USERNAME/go-konveyor-tests.git
cd go-konveyor-tests

# Add upstream remote
git remote add upstream https://github.com/konveyor/go-konveyor-tests.git

# Create a branch
git checkout -b update-deps-for-my-rules
```

### 2. Identify the Test Case to Update

Test cases are in the `analysis/` directory with names like `tc_APPNAME_deps.go`.

Common test applications:
- **DayTrader** - `tc_daytrader_deps.go` - Java EE trading app
- **Tackle Testapp** - `tc_tackle_testapp_public_deps.go` - Spring Boot app
- **CoolStore** - `tc_coolstore_deps.go` - Microservices demo
- **Tomcat** - `tc_tomcat.go` - Servlet container app

Choose the one that matches what your rules target:

```bash
# List available test cases
ls analysis/tc_*.go

# View an existing test case to see what source/target it uses
cat analysis/tc_daytrader_deps.go
```

**IMPORTANT:** Each test case has specific `--source` and `--target` values. You MUST use the exact same values when running Kantra, otherwise the dependency results won't match what CI expects.

### 3. Run Kantra Analysis

Analyze the test application with your new rules.

**CRITICAL:** Check the test case file to find the exact `--source` and `--target` values used by CI, then use those same values in your Kantra command.

```bash
# Make sure Kantra is installed
kantra --version

# If using Podman on Mac, start machine
podman machine start

# Run analysis - USE THE SAME --source and --target as the test case expects!
# Example for a Java to Quarkus migration:
kantra analyze \
    --input /path/to/test/application \
    --output ./analysis-output \
    --rules /path/to/your/new/rules.yaml \
    --source java \
    --target quarkus

# To find the correct source/target values, check the test case .go file:
# Example from tc_daytrader_deps.go:
#   Analysis: api.Analysis{
#       Labels: []string{
#           "konveyor.io/target=cloud-readiness",
#           "konveyor.io/target=quarkus",
#       },
#   }
#
# In this example: --target cloud-readiness --target quarkus
# Use: grep "konveyor.io/target" to find them quickly
```

**Where to get test applications:**
- DayTrader: https://github.com/WASdev/sample.daytrader7
- Tackle Testapp: https://github.com/konveyor/tackle-testapp
- Or use any Java application that exercises your rules

**Output location:**
The analysis creates a directory (`./analysis-output/`) containing:
- `output.yaml` - Main analysis results with dependencies
- `static-report/` - HTML report
- Other metadata files

### 4. Update Test Dependencies

Use the dependency updater script to update the test case:

```bash
# Navigate to analyzer-rule-generator repo
cd /path/to/analyzer-rule-generator
source venv/bin/activate

# Preview what will be updated (recommended first step)
python scripts/update_test_dependencies.py \
    --analyzer-output /path/to/analysis-output/output.yaml \
    --test-case /path/to/go-konveyor-tests/analysis/tc_daytrader_deps.go \
    --print-only

# If it looks good, update the file
python scripts/update_test_dependencies.py \
    --analyzer-output /path/to/analysis-output/output.yaml \
    --test-case /path/to/go-konveyor-tests/analysis/tc_daytrader_deps.go
```

**Script options:**
- `--analyzer-output` - Path to Kantra's `output.yaml` file
- `--test-case` - Path to the test case `.go` file to update
- `--print-only` - Preview changes without writing (optional)

### 5. Review Changes

```bash
cd /path/to/go-konveyor-tests

# See what changed
git diff analysis/tc_daytrader_deps.go
```

**What to check:**
- ✅ Dependencies list is updated
- ✅ Versions match what analyzer found
- ✅ Provider types are correct (usually "java")
- ✅ Alphabetically sorted by name
- ✅ No syntax errors

### 6. Commit and Push

```bash
# Stage the changes
git add analysis/tc_daytrader_deps.go

# Commit with descriptive message and DCO sign-off
# Note: The -s flag adds "Signed-off-by" for DCO compliance
git commit -s -m "Update DayTrader dependencies for new Spring Boot migration rules

Added dependencies detected by new rules:
- spring-boot-to-quarkus-00010
- spring-boot-to-quarkus-00020
- spring-boot-to-quarkus-00030"

# Push to YOUR fork
git push origin update-deps-for-my-rules
```

**Important:** Konveyor requires DCO (Developer Certificate of Origin) sign-off on all commits. Always use `git commit -s` to automatically add the sign-off.

### 7. Create Pull Request

1. Go to your fork on GitHub: `https://github.com/YOUR_USERNAME/go-konveyor-tests`
2. Click "Pull requests" → "New pull request"
3. Base repository: `konveyor/go-konveyor-tests` base: `main`
4. Head repository: `YOUR_USERNAME/go-konveyor-tests` compare: `update-deps-for-my-rules`
5. Fill in PR details:
   - **Title**: "Update [AppName] dependencies for [RulesetName]"
   - **Description**: Link to your rulesets PR, explain what changed
6. Submit the PR

## Creating a New Test Case

If your rules target an application that doesn't have a test case yet:

```bash
# Generate a new test case file
python scripts/update_test_dependencies.py \
    --analyzer-output /path/to/analysis-output/output.yaml \
    --output /tmp/tc_myapp_deps.go \
    --test-name "MyApp Dependencies" \
    --app-name "MyApp" \
    --print-only
```

**Additional steps for new test cases:**

1. **Add application to data/application.go** (if needed)
2. **Add test case to test_cases.go** in appropriate tier
3. **Consider adding to README.md**
4. **Test locally** before submitting

See [go-konveyor-tests/analysis/README.md](https://github.com/konveyor/go-konveyor-tests/blob/main/analysis/README.md) for details.

## Example Workflow

Here's a complete example of updating DayTrader test case:

```bash
# 1. Setup (one time)
git clone https://github.com/YOUR_USERNAME/go-konveyor-tests.git
cd go-konveyor-tests
git remote add upstream https://github.com/konveyor/go-konveyor-tests.git
git checkout -b update-daytrader-deps

# 2. Get test application
git clone https://github.com/WASdev/sample.daytrader7.git /tmp/daytrader

# 3. Check what target labels the test case uses
cat ~/go-konveyor-tests/analysis/tc_daytrader_deps.go | grep "konveyor.io/target"
# Output: "konveyor.io/target=cloud-readiness", "konveyor.io/target=quarkus"

# 4. Analyze with your new rules - MATCH the targets from step 3!
kantra analyze \
    --input /tmp/daytrader \
    --output /tmp/daytrader-analysis \
    --rules ~/rulesets/my-new-spring-rules.yaml \
    --target cloud-readiness \
    --target quarkus

# 5. Update test case
cd ~/analyzer-rule-generator
source venv/bin/activate
python scripts/update_test_dependencies.py \
    --analyzer-output /tmp/daytrader-analysis/output.yaml \
    --test-case ~/go-konveyor-tests/analysis/tc_daytrader_deps.go

# 6. Review and commit
cd ~/go-konveyor-tests
git diff analysis/tc_daytrader_deps.go
git add analysis/tc_daytrader_deps.go
git commit -s -m "Update DayTrader deps for Spring Boot migration rules"
git push origin update-daytrader-deps

# 7. Create PR on GitHub
```

## Finding Source/Target Values in Test Cases

Each test case file defines what source and target technologies it uses. Here's how to find them:

**Example from `tc_daytrader_deps.go`:**
```go
var DaytraderWithDeps = TC{
    Name:     "Daytrader",
    Application: data.Daytrader,
    Task:     Analyze,
    WithDeps: true,
    Analysis: api.Analysis{
        Labels: []string{
            "konveyor.io/target=cloud-readiness",  // These are the --target values
            "konveyor.io/target=quarkus",
        },
        Dependencies: []api.TechDependency{
            // ... dependencies here
        },
    },
}
```

In this example, you would run Kantra with:
```bash
kantra analyze --target cloud-readiness --target quarkus
```

**Quick command to find target labels:**
```bash
# View the Labels section of any test case
cat analysis/tc_daytrader_deps.go | grep "konveyor.io/target"

# Output will show something like:
#   "konveyor.io/target=cloud-readiness",
#   "konveyor.io/target=quarkus",
```

**Common source/target combinations:**
- `--source java --target quarkus` - Java to Quarkus migration
- `--source java --target cloud-readiness` - Cloud readiness assessment
- `--source eap7 --target eap8` - JBoss EAP upgrade
- `--source jakarta-ee --target jakarta-ee9+` - Jakarta EE upgrade
- `--source springboot --target quarkus` - Spring Boot to Quarkus

**Link to test cases:** Browse [go-konveyor-tests/analysis/](https://github.com/konveyor/go-konveyor-tests/tree/main/analysis) to see all available test cases and their configurations.

## Troubleshooting

### "Could not find Dependencies section"

The script uses regex to find the `Dependencies:` field. This error means the test case file structure is unexpected.

**Solution:**
- Use `--print-only` to see generated code
- Manually copy the dependencies section
- Check the file matches the expected structure

### "Could not parse as YAML or JSON"

The analyzer output file is not valid YAML/JSON.

**Solution:**
- Verify the file exists: `ls -lh /path/to/output.yaml`
- Check it's valid YAML: `cat /path/to/output.yaml | head -50`
- Try a different output file (check the analysis output directory)

### No dependencies found

The analyzer output doesn't contain a `dependencies:` section.

**Solution:**
- Check analyzer ran successfully
- Verify you're pointing to the right file (`output.yaml`)
- Some apps may have zero dependencies (unusual)
- Check analyzer logs for errors

### Dependencies look wrong

The extracted dependencies don't match what you expected.

**Solution:**
- Use `--print-only` to preview before writing
- Verify Kantra analysis completed successfully
- Check the `output.yaml` manually for dependencies
- Ensure you're analyzing the right application

### Test case fails in CI

After updating, the CI tests fail.

**Solution:**
- The dependency list might be incomplete or incorrect
- Re-run Kantra analysis with latest rulesets
- Check for version mismatches
- Verify provider types are correct

## Integration with Rule Submission

This is part of the larger rule submission workflow:

1. ✅ **Generate rules** - Use `generate_rules.py` to create rules
2. ✅ **Test locally** - Run Kantra to verify rules work
3. ✅ **Submit rules PR** - To `konveyor/rulesets`
4. ✅ **Update CI tests** - This guide (update `go-konveyor-tests`)
5. ✅ **Link PRs** - Reference both PRs in each other
6. ✅ **Wait for review** - Maintainers review both together

## Related Documentation

- [Konveyor Submission Guide](konveyor-submission-guide.md) - Complete submission process
- [CI Test Updater](ci-test-updater.md) - Script reference documentation
- [go-konveyor-tests README](https://github.com/konveyor/go-konveyor-tests) - Test repository docs
- [Kantra Documentation](https://github.com/konveyor/kantra) - Analysis tool docs

## Tips and Best Practices

### Match source/target values exactly
**CRITICAL:** Always check the test case file to find the exact `--source` and `--target` values, then use those same values when running Kantra. Mismatched values will cause dependency mismatches and CI failures.

### Always use --print-only first
Preview changes before writing files to catch issues early.

### Keep test apps handy
Clone commonly used test applications once and reuse them.

### Run full ruleset
Include your new rules with the existing rulesets to get complete dependency lists.

### Test the tests
After updating, run the test locally if possible to verify it passes.

### Meaningful commit messages
Explain what rules you added and what changed in the dependencies.

### Link PRs together
When you submit both rulesets and tests PRs, link them in the descriptions.

## Questions?

If you run into issues:
1. Check this documentation
2. Review example test cases in `go-konveyor-tests/analysis/`
3. Ask in the [Konveyor community](https://github.com/konveyor/community)
4. File an issue in `analyzer-rule-generator` repo
