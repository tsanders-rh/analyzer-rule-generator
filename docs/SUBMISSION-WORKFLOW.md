# Konveyor Submission Workflow - Executive Summary

## Overview

This document provides a high-level overview of the process for submitting AI-generated analyzer rules to the [Konveyor rulesets repository](https://github.com/konveyor/rulesets).

## Quick Start

### 1. Generate Rules
```bash
python scripts/generate_rules.py \
  --guide "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide" \
  --source spring-boot-3.5 \
  --target spring-boot-4.0 \
  --output rules/spring-boot-4.0.yaml \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219
```

### 2. Prepare Submission Package
```bash
python scripts/prepare_submission.py \
  --rules rules/spring-boot-4.0.yaml \
  --source spring-boot-3.5 \
  --target spring-boot-4.0 \
  --guide-url "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide" \
  --output submission/spring-boot-4.0 \
  --data-dir-name mongodb
```

### 3. Complete Test Data
Edit the generated test files:
- `submission/spring-boot-4.0/tests/data/mongodb/pom.xml` - Add dependencies
- `submission/spring-boot-4.0/tests/data/mongodb/src/main/java/com/example/Application.java` - Add code with violations

### 4. Test Locally
```bash
# Install Kantra
# Download from: https://github.com/konveyor/kantra/releases

kantra test submission/spring-boot-4.0/tests/migration-rules.test.yaml
```

### 5. Submit to Konveyor
```bash
# Fork and clone Konveyor rulesets
git clone https://github.com/YOUR_USERNAME/rulesets.git
cd rulesets

# Create branch
git checkout -b add-spring-boot-4.0-rules

# Copy files to appropriate directory
TARGET_DIR=default/generated/spring-boot
cp submission/spring-boot-4.0/migration-rules.yaml $TARGET_DIR/spring-boot-3.5-to-4.0-mongodb.yaml
cp submission/spring-boot-4.0/tests/migration-rules.test.yaml $TARGET_DIR/tests/spring-boot-3.5-to-4.0-mongodb.test.yaml
cp -r submission/spring-boot-4.0/tests/data/mongodb $TARGET_DIR/tests/data/

# Test in Konveyor repo
kantra test $TARGET_DIR/tests/spring-boot-3.5-to-4.0-mongodb.test.yaml

# Commit and push
git add $TARGET_DIR/
git commit -m "Add Spring Boot 3.5 to 4.0 MongoDB migration rules"
git push origin add-spring-boot-4.0-rules

# Create PR on GitHub
```

## Konveyor Repository Structure

```
konveyor/rulesets/
└── default/generated/
    ├── spring-boot/                   # Technology directory
    │   ├── ruleset.yaml               # Ruleset metadata
    │   ├── spring-boot-2.x-to-3.0-removals.yaml     # Rule files
    │   ├── spring-boot-2.x-to-3.0-security.yaml
    │   └── tests/                     # Test directory
    │       ├── spring-boot-2.x-to-3.0-removals.test.yaml  # Test files
    │       ├── spring-boot-2.x-to-3.0-security.test.yaml
    │       └── data/                  # Test data
    │           ├── removals/          # Test app per rule file
    │           │   ├── pom.xml
    │           │   └── src/main/java/...
    │           └── security/
    │               ├── pom.xml
    │               └── src/main/java/...
    ├── openjdk21/                     # Another technology
    └── ...
```

## File Naming Conventions

| Type | Format | Example |
|------|--------|---------|
| Rule File | `{source}-to-{target}-{topic}.yaml` | `spring-boot-3.5-to-4.0-mongodb.yaml` |
| Test File | `{rule-file}.test.yaml` | `spring-boot-3.5-to-4.0-mongodb.test.yaml` |
| Rule ID | `{source}-to-{target}-{number}` | `spring-boot-3.5-to-spring-boot-4.0-00010` |

**Important:**
- Use hyphens in file names (not underscores)
- Rule IDs use 5-digit numbers with increments of 10
- Test data directory name should match rule topic (e.g., "mongodb", "removals")

## Test File Structure

```yaml
# Path to rule file being tested
rulesPath: ../spring-boot-3.5-to-4.0-mongodb.yaml

# Test data source
providers:
  - name: java
    dataPath: data/mongodb

# Test cases (one per rule)
tests:
  - ruleID: spring-boot-3.5-to-spring-boot-4.0-00001
    testCases:
      - name: tc-1
        analysisParams:
          mode: "source-only"
        hasIncidents:
          atLeast: 1

  - ruleID: spring-boot-3.5-to-spring-boot-4.0-00002
    testCases:
      - name: tc-1
        analysisParams:
          mode: "source-only"
        hasIncidents:
          atLeast: 1
```

## Test Data Requirements

Your test application must:

1. **Be minimal but complete** - Just enough code to trigger rules
2. **Include dependencies** - Valid `pom.xml` with required libraries
3. **Use deprecated APIs** - Code that violates the rules
4. **One violation per rule** - Each rule should have at least one match

**Example pom.xml:**
```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.5.0</version>  <!-- Source version -->
</parent>

<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-mongodb</artifactId>
    </dependency>
</dependencies>
```

**Example Application.java:**
```java
package com.example;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

@Configuration
public class MongoConfig {
    // Should trigger rule for spring.data.mongodb.host
    @Value("${spring.data.mongodb.host}")
    private String mongoHost;
}
```

## Testing with Kantra

```bash
# Install Kantra
# Mac:
brew install podman
podman machine init
podman machine start
# Download kantra from: https://github.com/konveyor/kantra/releases
xattr -d com.apple.quarantine kantra
sudo mv kantra /usr/local/bin/

# Run tests
kantra test tests/your-rule-file.test.yaml

# Expected output:
# ✓ spring-boot-3.5-to-spring-boot-4.0-00001 tc-1 passed
# ✓ spring-boot-3.5-to-spring-boot-4.0-00002 tc-1 passed
# All tests passed!
```

## Common Issues

### No incidents found
**Problem:** Test passes but reports 0 incidents when expecting 1+

**Solutions:**
- Verify test code actually uses the deprecated API
- Check pom.xml includes required dependencies
- Ensure pattern in rule matches the code structure
- Check location type (ANNOTATION vs TYPE vs PACKAGE)

### Wrong incident count
**Problem:** Expected 1 incident, found 3

**Solutions:**
- Test code has multiple violations - update test: `hasIncidents: { atLeast: 3 }`
- Or reduce violations in test code to match expectation

### Rule file not found
**Problem:** `Error: rule file not found`

**Solution:** Check `rulesPath` is correct relative path from test file
```yaml
rulesPath: ../migration-rules.yaml  # Correct (test file is in tests/)
rulesPath: migration-rules.yaml     # Wrong
```

## Submission Checklist

Before submitting your PR:

- [ ] Rules generated from authoritative migration guide
- [ ] Rule IDs follow 5-digit format with increments of 10
- [ ] File names use hyphens and describe content
- [ ] Test file created with `.test.yaml` extension
- [ ] Test data directory contains complete Maven project
- [ ] Test code includes violations for each rule
- [ ] All tests pass locally with `kantra test`
- [ ] Files placed in correct technology directory
- [ ] Commit message references migration guide URL
- [ ] PR description includes test results
- [ ] Branch is up-to-date with upstream main

## PR Template

```markdown
## Description

Add analyzer rules for migrating from Spring Boot 3.5 to 4.0, covering MongoDB property migrations.

## Changes

- Added `spring-boot-3.5-to-4.0-mongodb.yaml` with 13 rules
- Added test file and test application
- All tests passing with Kantra

## Rules Generated

Generated from: https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide#mongodb

Total rules: 13 (all mandatory)

## Testing

```bash
kantra test tests/spring-boot-3.5-to-4.0-mongodb.test.yaml
# ✓ All 13 tests passed
```

## Checklist

- [x] Rules follow naming conventions
- [x] All tests pass locally
- [x] Test data is minimal and complete
- [x] Commit message follows guidelines
```

## Resources

- **Full Documentation:** [docs/konveyor-submission-guide.md](konveyor-submission-guide.md)
- **Konveyor Rulesets Repo:** https://github.com/konveyor/rulesets
- **Kantra CLI:** https://github.com/konveyor/kantra
- **Analyzer-LSP Docs:** https://github.com/konveyor/analyzer-lsp/blob/main/docs/rules.md

## Example Submission

A complete example submission package is available at:
```
examples/konveyor-submission/spring-boot-4.0/
├── migration-rules.yaml                    # 17 rules
├── README.md                               # Instructions
└── tests/
    ├── migration-rules.test.yaml           # Test definitions
    └── data/mongodb/                       # Test application skeleton
        ├── pom.xml
        └── src/main/java/com/example/Application.java
```

This package was generated automatically using:
```bash
python scripts/prepare_submission.py \
  --rules examples/output/spring-boot-4.0/migration-rules.yaml \
  --source spring-boot-3.5 \
  --target spring-boot-4.0 \
  --guide-url "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide" \
  --output examples/konveyor-submission/spring-boot-4.0
```

## Getting Help

- **Konveyor Community:** https://github.com/konveyor/community
- **Slack:** #konveyor and #konveyor-dev channels
- **Mailing List:** konveyor-ug-mig-exp@googlegroups.com
- **Issues:** Open an issue describing your migration challenge

---

For complete details, see [konveyor-submission-guide.md](konveyor-submission-guide.md)
