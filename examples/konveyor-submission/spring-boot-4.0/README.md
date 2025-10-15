# spring-boot-3.5 to spring-boot-4.0 Migration Rules

## Overview

This package contains analyzer rules for migrating from spring-boot-3.5 to spring-boot-4.0.

Generated from: https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide

## Files

- `migration-rules.yaml` - Migration rules
- `tests/migration-rules.test.yaml` - Test definitions
- `tests/data/` - Test application code

## Testing

Run tests locally:

```bash
kantra test tests/migration-rules.test.yaml
```

## Installation

Copy files to Konveyor rulesets repository:

```bash
# Determine target directory (e.g., spring-boot, openjdk21, etc.)
TARGET_DIR=/path/to/rulesets/default/generated/YOUR_TECHNOLOGY

# Copy rules
cp migration-rules.yaml $TARGET_DIR/

# Copy tests
cp -r tests/* $TARGET_DIR/tests/

# Run tests
cd $TARGET_DIR
kantra test tests/migration-rules.test.yaml
```

## Next Steps

1. **Complete test data**
   - Edit `tests/data/*/pom.xml` to add dependencies
   - Edit `tests/data/*/src/main/java/com/example/Application.java` with code that uses deprecated APIs
   - Ensure each rule has at least one violation in test code

2. **Run tests locally**
   - Install Kantra: https://github.com/konveyor/kantra
   - Run: `kantra test tests/migration-rules.test.yaml`
   - Verify all tests pass

3. **Submit to Konveyor**
   - Fork https://github.com/konveyor/rulesets
   - Create feature branch
   - Copy files to appropriate directory
   - Create PR with test results

See `docs/konveyor-submission-guide.md` for detailed instructions.
