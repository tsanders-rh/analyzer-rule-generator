# Konveyor Rulesets Submission Guide

## Overview

This guide documents the process for submitting AI-generated analyzer rules to the [Konveyor rulesets repository](https://github.com/konveyor/rulesets) with proper tests.

## Prerequisites

### 1. Install Kantra

Kantra is Konveyor's CLI tool for analyzing applications and testing rules. You can use either the native binary or run it in a container.

#### Option A: Native Binary (Recommended)

**Installation:**
```bash
# Download from releases
# https://github.com/konveyor/kantra/releases

# For Mac users, remove quarantine attribute
xattr -d com.apple.quarantine kantra

# Add to PATH
sudo mv kantra /usr/local/bin/
chmod +x /usr/local/bin/kantra

# Verify installation
kantra version
```

**Requirements:**
- Podman 4+ or Docker 24+ (Kantra uses containers internally to run the analyzer)

```bash
# For Mac/Windows: Start podman machine before using Kantra
podman machine init
podman machine start

# Verify podman is running
podman ps
```

#### Option B: Container Image

Run Kantra directly from the container image without installing the binary:

```bash
# Using Podman (recommended)
podman run -v $(pwd):/app:Z quay.io/konveyor/kantra:latest version

# Using Docker
docker run -v $(pwd):/app quay.io/konveyor/kantra:latest version
```

**When to use containers:**
- Don't want to install the binary
- Running in CI/CD pipelines
- Ensuring consistent environment across team

**Usage examples:**
```bash
# Test rules with Podman
podman run -v $(pwd):/app:Z quay.io/konveyor/kantra:latest test /app/tests/my-rules.test.yaml

# Test rules with Docker
docker run -v $(pwd):/app quay.io/konveyor/kantra:latest test /app/tests/my-rules.test.yaml
```

**Note:** The rest of this guide uses `kantra` command for brevity. If using containers, replace `kantra` with the appropriate `podman run` or `docker run` command.

### 2. Fork and Clone Konveyor Rulesets

```bash
# Fork the repository on GitHub
# https://github.com/konveyor/rulesets

# Clone your fork
git clone https://github.com/YOUR_USERNAME/rulesets.git
cd rulesets

# Add upstream remote
git remote add upstream https://github.com/konveyor/rulesets.git
```

### 3. Understanding DCO Requirements

**IMPORTANT:** All Konveyor repositories require DCO (Developer Certificate of Origin) sign-off on commits.

**What is DCO?**
- A lightweight way to certify that you wrote or have the right to submit the code
- Required by Konveyor for all contributions
- Added automatically with the `-s` flag when committing

**How to sign commits:**
```bash
# Always use -s flag when committing to Konveyor repositories
git commit -s -m "Your commit message"

# This adds a "Signed-off-by" line to your commit message
# Signed-off-by: Your Name <your.email@example.com>
```

**If you forget:**
```bash
# Amend the last commit to add sign-off
git commit --amend -s --no-edit

# For multiple commits, use interactive rebase
git rebase -i HEAD~3  # for last 3 commits
# Mark commits as 'edit', then for each:
git commit --amend -s --no-edit
git rebase --continue
```

**Configure git globally:**
```bash
# Set your name and email (required for DCO)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Understanding the Repository Structure

### Directory Layout

```
default/generated/
├── spring-boot/                              # Technology-specific directory
│   ├── ruleset.yaml                          # Ruleset metadata
│   ├── spring-boot-2.x-to-3.0-removals.yaml  # Rule file
│   ├── spring-boot-2.x-to-3.0-security.yaml  # Rule file
│   └── tests/                                # Test directory
│       ├── spring-boot-2.x-to-3.0-removals.test.yaml  # Test file
│       └── data/                             # Test data
│           └── removals/                     # Test project per rule file
│               ├── pom.xml                   # Maven project
│               └── src/                      # Source code with violations
│                   └── main/java/...
├── openjdk21/                                # Another technology
│   ├── ruleset.yaml
│   ├── 204-removed-apis.windup.yaml
│   └── tests/
└── ...
```

### Naming Conventions

**Rule Files:**
- Format: `{source}-to-{target}-{topic}.yaml`
- Example: `spring-boot-3.5-to-4.0-mongodb.yaml`
- Use hyphens, indicate target technology and concern

**Test Files:**
- Format: `{rule-file-name}.test.yaml`
- Example: `spring-boot-3.5-to-4.0-mongodb.test.yaml`

**Rule IDs:**
- Format: `{source}-to-{target}-{number}`
- Number in 5-digit format with increments of 10
- Example: `spring-boot-3.5-to-spring-boot-4.0-00010`

## Submission Workflow

### Phase 1: Generate Rules with AI

This is what our tool does!

```bash
# Generate rules from migration guide
python scripts/generate_rules.py \
  --guide "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide" \
  --source spring-boot-3.5 \
  --target spring-boot-4.0 \
  --output rules/spring-boot-4.0-mongodb.yaml \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219
```

**Output:** AI-generated rules ready for testing

### Phase 2: Prepare Test Data

You can generate test data either **automatically with AI** or manually.

#### Option A: Generate Test Data with AI (Recommended)

Use the AI-powered test data generator to automatically create test code:

```bash
python scripts/generate_test_data.py \
  --rules examples/output/spring-boot-4.0/migration-rules.yaml \
  --output submission/spring-boot-4.0/tests/data/mongodb \
  --source spring-boot-3.5 \
  --target spring-boot-4.0 \
  --guide-url "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide" \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219
```

This generates:
- ✅ Complete `pom.xml` with correct dependencies
- ✅ Java application code with violations for each rule
- ✅ Comments mapping code to rule IDs
- ✅ Realistic usage patterns for static analysis

**Review the generated code** to ensure it properly triggers the rules.

#### Option B: Create Test Data Manually

Create a test application that contains code violations the rules should detect.

**Directory Structure:**
```
default/generated/spring-boot/tests/data/mongodb/
├── pom.xml                    # Maven project with dependencies
└── src/main/java/com/example/
    ├── MongoConfig.java       # Uses spring.data.mongodb properties
    └── Application.java       # Application code
```

**Test Application Requirements:**
1. **Minimal but complete** - Just enough code to trigger rules
2. **One test project per rule file** - Each rule file gets its own test directory
3. **Use old/deprecated APIs** - Code should contain violations
4. **Include dependencies** - pom.xml with relevant Spring Boot version

**Example pom.xml:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.5.0</version>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>mongodb-test</artifactId>
    <version>0.0.1-SNAPSHOT</version>

    <properties>
        <java.version>17</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-mongodb</artifactId>
        </dependency>
    </dependencies>
</project>
```

**Example MongoConfig.java:**
```java
package com.example;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

@Configuration
public class MongoConfig {
    // This should trigger rule for spring.data.mongodb.host
    @Value("${spring.data.mongodb.host}")
    private String mongoHost;

    // This should trigger rule for spring.data.mongodb.uri
    @Value("${spring.data.mongodb.uri}")
    private String mongoUri;
}
```

### Phase 3: Create Test Definitions

Create a `.test.yaml` file that tells Kantra how to test the rules.

**File:** `default/generated/spring-boot/tests/spring-boot-3.5-to-4.0-mongodb.test.yaml`

```yaml
# Path to the rule file being tested
rulesPath: ../spring-boot-3.5-to-4.0-mongodb.yaml

# Define test data sources
providers:
  - name: java  # Provider name (must be 'java' for Java rules)
    dataPath: data/mongodb  # Path to test application

# Test cases
tests:
  # One test block per rule
  - ruleID: spring-boot-3.5-to-spring-boot-4.0-00001
    testCases:
      - name: tc-1
        analysisParams:
          mode: "source-only"  # Analyze source code only
        hasIncidents:
          atLeast: 1  # Expect at least 1 violation

  - ruleID: spring-boot-3.5-to-spring-boot-4.0-00002
    testCases:
      - name: tc-1
        analysisParams:
          mode: "source-only"
        hasIncidents:
          atLeast: 1

  # ... one block per rule in the file
```

**Test Configuration Options:**

| Field | Description | Example |
|-------|-------------|---------|
| `rulesPath` | Path to rule file (relative to test file) | `../my-rules.yaml` |
| `providers.name` | Provider type | `java`, `builtin` |
| `providers.dataPath` | Path to test data | `data/mongodb` |
| `analysisParams.mode` | Analysis mode | `source-only`, `binary` |
| `hasIncidents.atLeast` | Minimum expected violations | `1`, `2`, `0` |

### Phase 4: Run Tests Locally

```bash
cd rulesets/default/generated/spring-boot

# Run tests for a specific rule file
kantra test tests/spring-boot-3.5-to-4.0-mongodb.test.yaml

# Expected output:
# ✓ spring-boot-3.5-to-spring-boot-4.0-00001 tc-1 passed
# ✓ spring-boot-3.5-to-spring-boot-4.0-00002 tc-1 passed
# All tests passed!
```

**Common Test Issues:**

| Issue | Cause | Solution |
|-------|-------|----------|
| No incidents found | Test data doesn't use the pattern | Verify test code uses deprecated API |
| Wrong incident count | Multiple violations in test code | Adjust `atLeast` or refine test data |
| Rule not found | Wrong ruleID in test file | Check ruleID matches rule file |
| Test data not found | Wrong `dataPath` | Verify path relative to test file |

### Phase 5: Prepare for Submission

```bash
# Create feature branch
git checkout -b add-spring-boot-4.0-mongodb-rules

# Determine target directory
# For Spring Boot: default/generated/spring-boot/
TARGET_DIR=default/generated/spring-boot

# Copy generated rules
cp rules/spring-boot-4.0-mongodb.yaml $TARGET_DIR/

# Copy test files
cp tests/spring-boot-3.5-to-4.0-mongodb.test.yaml $TARGET_DIR/tests/
cp -r tests/data/mongodb $TARGET_DIR/tests/data/

# Verify structure
tree $TARGET_DIR/
# spring-boot/
# ├── spring-boot-3.5-to-4.0-mongodb.yaml
# └── tests/
#     ├── spring-boot-3.5-to-4.0-mongodb.test.yaml
#     └── data/
#         └── mongodb/
#             ├── pom.xml
#             └── src/...

# Run all tests
kantra test $TARGET_DIR/tests/*.test.yaml

# Stage changes
git add $TARGET_DIR/

# Commit with DCO sign-off
# Note: Konveyor requires DCO (Developer Certificate of Origin) on all commits
git commit -s -m "Add Spring Boot 3.5 to 4.0 MongoDB migration rules

Generated rules for MongoDB property migrations in Spring Boot 4.0.
Includes test cases covering property renames from spring.data.mongodb.*
to spring.mongodb.* namespace.

Rules generated using AI from official Spring Boot 4.0 Migration Guide:
https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide#mongodb

Coverage:
- 13 property rename rules
- Test application with property usage examples
- All tests passing with kantra test
"
```

### Phase 6: Update CI Test Expectations (go-konveyor-tests)

When submitting new rules, you also need to update the CI test expectations in the `go-konveyor-tests` repository.

**Why this is needed:**
- The `go-konveyor-tests` repository contains integration tests that verify analysis results
- Your new rules will change the analysis output (new violations, dependencies, tags)
- CI test expectations need to be updated to reflect these changes

**See:** [Updating CI Tests Guide](updating-ci-tests.md) for complete step-by-step instructions.

**Quick workflow:**
```bash
# 1. Run Kantra analysis on test application
kantra analyze \
    --input /path/to/test/application \
    --output /tmp/analysis-output \
    --rules /path/to/your/konveyor-rulesets \
    --target cloud-readiness \
    --target quarkus

# 2. Update test case expectations
python scripts/update_test_dependencies.py \
    --analysis-dir /tmp/analysis-output \
    --normalize-path "/shared/source/sample" \
    --test-case ~/go-konveyor-tests/analysis/tc_daytrader_deps.go

# 3. Review and submit PR to go-konveyor-tests
cd ~/go-konveyor-tests
git diff analysis/tc_daytrader_deps.go
git add analysis/tc_daytrader_deps.go
git commit -s -m "Update DayTrader test case for new Spring Boot migration rules"
git push origin update-daytrader-deps
```

**Reference documentation:**
- [Updating CI Tests Guide](updating-ci-tests.md) - Complete workflow
- [CI Test Updater Script Reference](ci-test-updater.md) - Script documentation

### Phase 7: Submit Pull Requests

You will submit **two pull requests** that need to be reviewed together:

```bash
# PR #1: Rules to konveyor/rulesets
git push origin add-spring-boot-4.0-mongodb-rules
# Create PR at https://github.com/konveyor/rulesets/compare

# PR #2: Test expectations to konveyor/go-konveyor-tests
cd ~/go-konveyor-tests
git push origin update-daytrader-deps
# Create PR at https://github.com/konveyor/go-konveyor-tests/compare
```

**Important:** Link the two PRs together by referencing each in the PR descriptions.

**PR Description Template (konveyor/rulesets):**
```markdown
## Description

This PR adds analyzer rules for migrating from Spring Boot 3.5 to 4.0, specifically covering MongoDB property migrations.

## Changes

- Added `spring-boot-3.5-to-4.0-mongodb.yaml` with 13 rules
- Added test file `spring-boot-3.5-to-4.0-mongodb.test.yaml`
- Added test application in `tests/data/mongodb/`

## Rules Generated

Rules were generated using AI from the official Spring Boot 4.0 Migration Guide:
https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide#mongodb

Total rules: 13
- **Mandatory:** 13
- **Potential:** 0

## Testing

All tests pass locally with `kantra test`:

```bash
kantra test tests/spring-boot-3.5-to-4.0-mongodb.test.yaml
# ✓ All 13 tests passed
```

## Related PR

- go-konveyor-tests PR: [link to PR updating test expectations]

## Checklist

- [x] Rules follow naming conventions
- [x] Rule IDs use 5-digit numbering with increments of 10
- [x] Test file created with matching name
- [x] Test data application created
- [x] All tests pass locally with kantra
- [x] CI test expectations updated in go-konveyor-tests
- [x] Commit message follows guidelines
- [x] Branch is up-to-date with main
```

**PR Description Template (go-konveyor-tests):**
```markdown
## Description

Updates CI test expectations for new Spring Boot 3.5 to 4.0 MongoDB migration rules.

## Changes

- Updated `tc_daytrader_deps.go` with new insights, dependencies, and tags

## Analysis Results

- **Insights:** 32 violations found
- **Effort:** 430 (increased from 318 due to new rules)
- **Dependencies:** 8 technology dependencies
- **Tags:** 69 technology tags

## Related PR

- konveyor/rulesets PR: [link to rules PR]

## Testing

Generated from Kantra analysis output using:
```bash
python scripts/update_test_dependencies.py \
    --analysis-dir /tmp/analysis-output \
    --normalize-path "/shared/source/sample" \
    --test-case analysis/tc_daytrader_deps.go
```
```

## Best Practices

### Rule Organization

1. **Group related rules** - Keep related migration concerns in one file
2. **One rule file per topic** - Don't mix unrelated changes
3. **Descriptive names** - File names should indicate what they cover
4. **Consistent numbering** - Use increments of 10 for rule IDs

### Test Data Quality

1. **Minimal code** - Just enough to trigger the rules
2. **Clear examples** - Each violation should be obvious
3. **Complete projects** - Include valid pom.xml and dependencies
4. **One violation per rule** - Helps verify test accuracy

### Testing Strategy

1. **Test locally first** - Don't submit until tests pass
2. **Test all rules** - Every rule should have at least one test case
3. **Verify incident counts** - Make sure expected violations occur
4. **Check false positives** - Ensure rules don't fire incorrectly

## Troubleshooting

### Kantra Test Failures

**Problem:** `Error: rule file not found`
```bash
# Solution: Check rulesPath is relative to test file location
rulesPath: ../spring-boot-3.5-to-4.0-mongodb.yaml  # Correct
rulesPath: spring-boot-3.5-to-4.0-mongodb.yaml     # Wrong
```

**Problem:** `No incidents found for rule`
```bash
# Solution: Verify test data actually uses the deprecated pattern
# Check:
# 1. Does test code import/use the old API?
# 2. Does pom.xml include required dependencies?
# 3. Is the pattern in the rule correct?
```

**Problem:** `Expected 1 incident, found 3`
```bash
# Solution: Test code has multiple violations
# Options:
# 1. Update test: hasIncidents: { atLeast: 3 }
# 2. Reduce violations in test code
```

### Missing Dependencies

**Problem:** Kantra requires Podman but not installed
```bash
# Install Podman
# Mac: brew install podman
# Linux: see https://podman.io/getting-started/installation

# Start podman machine (Mac/Windows only)
podman machine init
podman machine start
```

## CI/CD Integration

The Konveyor rulesets repository runs automated tests on all PRs using GitHub Actions.

### What CI Tests

1. **YAML Linting** - Validates YAML syntax
   - All `.yaml` files must be valid YAML
   - Proper indentation (2 spaces)
   - No syntax errors

2. **Rule Schema Validation** - Validates rule structure
   - Required fields: `ruleID`, `description`, `effort`, `when`, `message`
   - Valid categories: `mandatory`, `potential`, `optional`
   - Effort in range 1-10

3. **Test Execution** - Runs all `.test.yaml` files with Kantra
   - Each rule must have at least one test
   - Tests must pass (expected incidents found)
   - Test data must compile/be valid

### Ensuring CI Success

Our generated files already meet CI requirements:

**✅ Generated Rules (`migration-rules.yaml`):**
- Valid YAML format
- All required fields present
- Proper schema structure

**✅ Generated Tests (`migration-rules.test.yaml`):**
- Test case for every rule
- Proper `rulesPath` reference
- Valid `provider` and `dataPath` configuration

**✅ Generated Test Data:**
- Compil able code (when using `generate_test_data.py`)
- Valid build files (pom.xml, package.json, etc.)
- Contains violations for each rule

### Pre-Flight CI Check

Before submitting your PR, run these local checks to ensure CI will pass:

```bash
# 1. Validate YAML syntax
yamllint migration-rules.yaml
# or
python -c "import yaml; yaml.safe_load(open('migration-rules.yaml'))"

# 2. Run tests with Kantra (this is what CI does)
kantra test tests/migration-rules.test.yaml

# 3. Verify test data compiles
cd tests/data/mongodb
mvn compile  # for Java
# npm install && npm run build  # for TypeScript
# go build  # for Go
```

### Common CI Failures

| Issue | Cause | Fix |
|-------|-------|-----|
| YAML syntax error | Invalid YAML | Check indentation, quotes |
| Test file not found | Wrong `rulesPath` | Ensure relative path is correct |
| No incidents found | Test data doesn't trigger rule | Add violations to test code |
| Test data won't compile | Missing dependencies | Update pom.xml/package.json |
| Schema validation failed | Missing required field | Add all required rule fields |

### GitHub Actions Workflow

The CI runs approximately:

```yaml
name: Test Rules
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Kantra
        run: |
          # Download and install Kantra
      - name: Run Tests
        run: |
          # For each .test.yaml file:
          kantra test <test-file>.test.yaml
```

Your PR must pass all checks before merging.

## Examples

### Example 1: Spring Boot 4.0 MongoDB Rules

This is what we generated!

**Location:** `default/generated/spring-boot/`

**Files:**
- `spring-boot-3.5-to-4.0-mongodb.yaml` - 13 property migration rules
- `tests/spring-boot-3.5-to-4.0-mongodb.test.yaml` - Test definitions
- `tests/data/mongodb/` - Test application

**Test Results:** All 13 rules passing

### Example 2: OpenJDK 21 Removed APIs

**Location:** `default/generated/openjdk21/`

**Files:**
- `204-removed-apis.windup.yaml` - API removal rules
- `tests/204-removed-apis.test.yaml` - Tests

This follows the same pattern and can be used as a reference.

## Additional Resources

- [Konveyor Rulesets Repository](https://github.com/konveyor/rulesets)
- [Konveyor Analyzer-LSP Docs](https://github.com/konveyor/analyzer-lsp/blob/main/docs/rules.md)
- [Kantra CLI Documentation](https://github.com/konveyor/kantra)
- [Spring Boot Migration Guide](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide)

## Summary Checklist

Before submitting to Konveyor:

### Rules Submission (konveyor/rulesets)

- [ ] Rules generated with AI from authoritative migration guide
- [ ] Rule IDs follow naming convention (5-digit, increments of 10)
- [ ] Rule file named descriptively with hyphens
- [ ] Test file created with `.test.yaml` extension
- [ ] Test data directory contains minimal, complete test application
- [ ] Test application pom.xml has correct dependencies
- [ ] Test application code contains violations for each rule
- [ ] All tests pass locally with `kantra test`
- [ ] Feature branch created from latest main
- [ ] Files added to appropriate technology directory
- [ ] Commit message is descriptive and references migration guide
- [ ] Branch is up-to-date with upstream main

### CI Test Expectations (go-konveyor-tests)

- [ ] Ran Kantra analysis on test application with new rules
- [ ] Updated test case file using `update_test_dependencies.py`
- [ ] Used `--normalize-path "/shared/source/sample"` parameter
- [ ] Reviewed changes to insights, effort, dependencies, and tags
- [ ] Committed with DCO sign-off (`git commit -s`)
- [ ] Created PR to go-konveyor-tests
- [ ] Linked both PRs together in descriptions
