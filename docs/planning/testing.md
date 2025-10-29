# Testing Strategy

Comprehensive testing strategy for the Konveyor Analyzer Rule Generator project.

## Table of Contents

- [Overview](#overview)
- [Testing Levels](#testing-levels)
  - [1. Unit Testing](#1-unit-testing)
  - [2. Integration Testing](#2-integration-testing)
  - [3. End-to-End Testing](#3-end-to-end-testing)
  - [4. Validation Testing](#4-validation-testing)
- [Testing Workflows](#testing-workflows)
- [Test Data Management](#test-data-management)
- [Regression Testing](#regression-testing)
- [CI/CD Integration](#cicd-integration)
- [Manual Testing Procedures](#manual-testing-procedures)
- [Test Coverage Goals](#test-coverage-goals)

## Overview

This document outlines the testing strategy for ensuring the quality and reliability of generated Konveyor analyzer rules. The strategy covers testing at multiple levels, from individual components to complete end-to-end workflows.

### Testing Objectives

1. **Correctness**: Generated rules accurately detect the intended patterns
2. **Completeness**: Rules cover all documented migration scenarios
3. **Reliability**: Rule generation process produces consistent, valid output
4. **Maintainability**: Tests are easy to understand, update, and extend

## Testing Levels

### 1. Unit Testing

Testing individual components of the rule generation pipeline in isolation.

#### Components to Test

**Pattern Extraction (`src/rule_generator/extraction.py`)**
- LLM prompt construction
- Response parsing and JSON extraction
- Pattern object creation
- Location type selection logic
- Error handling for malformed responses

**OpenRewrite Ingestion (`src/rule_generator/openrewrite.py`)**
- Recipe fetching (URL and local files)
- Multi-document YAML parsing
- Recipe formatting for LLM processing
- Error handling for invalid recipes

**Rule Generation (`src/rule_generator/generation.py`)**
- Provider type detection (java vs builtin)
- Rule ID generation and sequencing
- Concern-based file grouping
- YAML formatting and validation

**Guide Ingestion (`src/rule_generator/ingestion.py`)**
- URL fetching and content extraction
- HTML to markdown conversion
- File reading for local guides
- Content cleaning and preparation

#### Unit Test Framework

```python
# Example unit test structure
import pytest
from src.rule_generator.extraction import MigrationPatternExtractor
from src.rule_generator.openrewrite import OpenRewriteRecipeIngester

class TestPatternExtraction:
    def test_location_type_selection_for_packages(self):
        """Test that package patterns use TYPE location"""
        # Mock LLM response with package pattern
        response = '''[{
            "source_fqn": "javax.security.cert.*",
            "location_type": "TYPE"
        }]'''

        # Verify pattern uses TYPE location
        patterns = extractor._parse_extraction_response(response)
        assert patterns[0].location_type == LocationType.TYPE

    def test_openrewrite_recipe_parsing(self):
        """Test OpenRewrite recipe YAML parsing"""
        recipe_yaml = """
        ---
        type: specs.openrewrite.org/v1beta/recipe
        name: UpgradeToJava17
        """

        ingester = OpenRewriteRecipeIngester(recipe_yaml, is_file=False)
        content = ingester.get_content()
        assert "UpgradeToJava17" in content
```

#### Running Unit Tests

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run all unit tests
pytest tests/unit/

# Run with coverage
pytest --cov=src/rule_generator tests/unit/

# Run specific test file
pytest tests/unit/test_extraction.py
```

### 2. Integration Testing

Testing interactions between components and external dependencies.

#### Integration Test Scenarios

**LLM Provider Integration**
- Test with different providers (OpenAI, Anthropic, Google)
- Verify API error handling
- Test rate limiting and retry logic
- Mock LLM responses for deterministic testing

**File System Operations**
- Test output directory creation
- Test file writing and permissions
- Test handling of existing files
- Test cross-platform path handling

**External Resource Fetching**
- Test URL fetching with various sources
- Test handling of network errors
- Test redirect handling
- Test authentication requirements

#### Integration Test Example

```python
class TestRuleGenerationIntegration:
    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response for consistent testing"""
        return '''[{
            "source_pattern": "javax.security.cert",
            "target_pattern": "java.security.cert",
            "source_fqn": "javax.security.cert.*",
            "location_type": "TYPE",
            "complexity": "TRIVIAL",
            "category": "api",
            "concern": "security",
            "rationale": "Package deprecated",
            "example_before": "import javax.security.cert.Certificate;",
            "example_after": "import java.security.cert.Certificate;"
        }]'''

    def test_end_to_end_pattern_to_rule(self, mock_llm_response, tmp_path):
        """Test complete flow from pattern extraction to rule generation"""
        # Setup mock LLM
        with patch('src.rule_generator.llm.LLMProvider.generate') as mock_generate:
            mock_generate.return_value = mock_llm_response

            # Run generation
            output = tmp_path / "output"
            generate_rules(
                guide_content="Test migration guide",
                source="java11",
                target="java17",
                output_dir=str(output)
            )

            # Verify output
            assert (output / "ruleset.yaml").exists()
            rules_file = output / "java11-to-java17-security.yaml"
            assert rules_file.exists()

            # Verify rule content
            with open(rules_file) as f:
                rules = yaml.safe_load(f)
                assert rules[0]['ruleID'] == 'java11-to-java17-security-00000'
                assert rules[0]['when']['java.referenced']['location'] == 'TYPE'
```

### 3. End-to-End Testing

Testing complete workflows from input to validated output.

#### E2E Test Scenarios

**Migration Guide → Rules → Validation**

```bash
# 1. Generate rules from migration guide
python scripts/generate_rules.py \
  --guide https://example.com/migration-guide \
  --source framework-v1 \
  --target framework-v2 \
  --output test-output/

# 2. Verify rule structure
python scripts/validate_rules.py test-output/

# 3. Run Kantra analysis on test application
kantra analyze \
  --input test-data/sample-app \
  --rules test-output/ \
  --output analysis-results/

# 4. Verify violations detected
python scripts/verify_violations.py \
  --expected test-data/expected-violations.yaml \
  --actual analysis-results/output.yaml
```

**OpenRewrite Recipe → Rules → Validation**

```bash
# 1. Generate rules from OpenRewrite recipe
python scripts/generate_rules.py \
  --from-openrewrite https://raw.githubusercontent.com/openrewrite/rewrite-migrate-java/main/src/main/resources/META-INF/rewrite/java-version-17.yml \
  --source java11 \
  --target java17 \
  --output test-output/java17/

# 2. Verify rule syntax and structure
yamllint test-output/java17/*.yaml

# 3. Create test data with known violations
# (Manual or automated test data generation)

# 4. Run Kantra analysis
kantra analyze \
  --input test-data/java11-app \
  --rules test-output/java17/ \
  --output analysis-results/

# 5. Verify expected violations detected
grep "java11-to-java17" analysis-results/output.yaml
```

#### E2E Test Automation

Create automated E2E test script:

```python
#!/usr/bin/env python3
"""
End-to-end test for rule generation and validation.
"""

import subprocess
import yaml
import sys
from pathlib import Path

def run_e2e_test(recipe_url, source, target, test_data_dir):
    """Run complete E2E test workflow"""

    # Step 1: Generate rules
    print(f"Generating rules from {recipe_url}...")
    output_dir = Path(f"test-output/{source}-to-{target}")

    result = subprocess.run([
        "python", "scripts/generate_rules.py",
        "--from-openrewrite", recipe_url,
        "--source", source,
        "--target", target,
        "--output", str(output_dir)
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Rule generation failed: {result.stderr}")
        return False

    # Step 2: Validate rule structure
    print("Validating rule structure...")
    rule_files = list(output_dir.glob("*.yaml"))
    if not rule_files:
        print("No rule files generated")
        return False

    # Step 3: Run Kantra analysis
    print("Running Kantra analysis...")
    analysis_output = Path(f"test-output/analysis-{source}-to-{target}")

    result = subprocess.run([
        "kantra", "analyze",
        "--input", str(test_data_dir),
        "--rules", str(output_dir),
        "--output", str(analysis_output),
        "--overwrite"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Kantra analysis failed: {result.stderr}")
        return False

    # Step 4: Verify violations
    print("Verifying violations...")
    output_yaml = analysis_output / "output.yaml"

    with open(output_yaml) as f:
        data = yaml.safe_load(f)

    violations_found = 0
    for ruleset in data:
        if ruleset.get('name') == f'{source}/{target}':
            violations = ruleset.get('violations', {})
            violations_found = len(violations)
            print(f"Found {violations_found} violations")

            # Verify each violation has incidents
            for rule_id, details in violations.items():
                incidents = details.get('incidents', [])
                if not incidents:
                    print(f"WARNING: Rule {rule_id} has no incidents")

    if violations_found == 0:
        print("No violations detected - test may need review")
        return False

    print(f"E2E test passed: {violations_found} violations detected")
    return True

if __name__ == "__main__":
    # Example test
    success = run_e2e_test(
        recipe_url="https://raw.githubusercontent.com/openrewrite/rewrite-migrate-java/main/src/main/resources/META-INF/rewrite/java-version-17.yml",
        source="java11",
        target="java17",
        test_data_dir="test-data/java11-app"
    )

    sys.exit(0 if success else 1)
```

### 4. Validation Testing

Verifying that generated rules actually work with Kantra.

#### Validation Test Process

**Step 1: Create Test Applications**

For each migration path, create a test application with known violations:

```
test-data/
├── java11-app/
│   ├── pom.xml
│   └── src/main/java/
│       └── com/example/Application.java  # Contains deprecated API usage
├── spring-boot-2/
│   ├── pom.xml
│   └── src/main/java/
│       └── com/example/SpringApp.java    # Contains Spring 2.x patterns
└── patternfly-v5/
    ├── package.json
    └── src/
        └── App.tsx                        # Contains PatternFly v5 usage
```

**Step 2: Document Expected Violations**

Create expected violations file:

```yaml
# test-data/java11-app/expected-violations.yaml
expected_violations:
  - rule_id: java11-to-java17-security-00000
    pattern: javax.security.cert.*
    location: src/main/java/com/example/Application.java
    line: 3

  - rule_id: java11-to-java17-security-00020
    pattern: com.sun.net.ssl.*
    location: src/main/java/com/example/Application.java
    line: 5
```

**Step 3: Run Kantra Analysis**

```bash
kantra analyze \
  --input test-data/java11-app \
  --rules examples/output/java17/ \
  --output validation-results/java11-app
```

**Step 4: Compare Results**

```python
def verify_violations(expected_file, actual_output_yaml):
    """Compare expected vs actual violations"""

    with open(expected_file) as f:
        expected = yaml.safe_load(f)

    with open(actual_output_yaml) as f:
        actual = yaml.safe_load(f)

    expected_rules = {v['rule_id'] for v in expected['expected_violations']}
    actual_rules = set()

    for ruleset in actual:
        violations = ruleset.get('violations', {})
        actual_rules.update(violations.keys())

    missing = expected_rules - actual_rules
    unexpected = actual_rules - expected_rules

    if missing:
        print(f"MISSING violations: {missing}")
        return False

    if unexpected:
        print(f"UNEXPECTED violations: {unexpected}")

    print(f"All expected violations detected!")
    return True
```

## Testing Workflows

### Workflow 1: New Rule Generation Testing

When generating rules from a new source:

1. **Generate Rules**
   ```bash
   python scripts/generate_rules.py \
     --guide <source> \
     --source <framework-v1> \
     --target <framework-v2> \
     --output test-output/new-ruleset/
   ```

2. **Manual Review**
   - Review generated rule files for correctness
   - Check rule IDs, descriptions, messages
   - Verify pattern syntax
   - Confirm location types

3. **Create Test Data**
   - Create minimal test application with violations
   - Document expected violations
   - Add to test-data/ directory

4. **Validation Testing**
   ```bash
   kantra analyze \
     --input test-data/new-ruleset-app \
     --rules test-output/new-ruleset/ \
     --output validation-results/
   ```

5. **Verify Results**
   - Check all expected violations detected
   - Review violation messages for clarity
   - Verify code snippets show correct context

6. **Iterative Refinement**
   - If violations missing: Review and fix patterns
   - If false positives: Refine pattern specificity
   - Re-run validation until correct

### Workflow 2: OpenRewrite Recipe Testing

Specific workflow for OpenRewrite-sourced rules:

1. **Generate Rules from Recipe**
   ```bash
   python scripts/generate_rules.py \
     --from-openrewrite <recipe-url> \
     --source <source-version> \
     --target <target-version> \
     --output test-output/openrewrite/
   ```

2. **Review Generated Patterns**
   - Verify location types (TYPE for packages, METHOD_CALL for methods)
   - Check that package wildcards use TYPE location
   - Confirm provider_type selection (java vs builtin)

3. **Create or Use Existing Test Data**
   - Look for existing test applications
   - Or create minimal reproduction case

4. **Run Kantra Validation**
   ```bash
   kantra analyze \
     --input test-data/test-app \
     --rules test-output/openrewrite/ \
     --output validation-results/ \
     --overwrite
   ```

5. **Analyze Results**
   ```bash
   # Count violations per rule
   grep "ruleID:" validation-results/output.yaml | sort | uniq -c

   # View specific violations
   grep -A 20 "java11-to-java17-security-00000:" validation-results/output.yaml
   ```

6. **Compare with OpenRewrite Behavior** (Optional)
   - Run OpenRewrite on same test app
   - Compare transformations vs detections
   - Verify rules catch same patterns

### Workflow 3: Regression Testing

Ensure changes don't break existing functionality:

1. **Baseline Generation**
   - Run rule generation on known inputs
   - Save output as baseline

2. **Make Changes**
   - Update prompts, code, etc.

3. **Regenerate Rules**
   - Use same inputs as baseline

4. **Compare Outputs**
   ```bash
   # Compare rule structure
   diff -r baseline/ new-output/

   # Compare Kantra results
   diff baseline/output.yaml new-output/output.yaml
   ```

5. **Review Differences**
   - Expected changes: OK
   - Unexpected changes: Investigate
   - Missing violations: Fix regression

## Test Data Management

### Test Data Structure

```
test-data/
├── java11-app/                      # Java 11→17 test app
│   ├── README.md                    # What violations should be detected
│   ├── pom.xml
│   ├── expected-violations.yaml     # Expected Kantra output
│   └── src/
│       └── main/java/...
├── spring-boot-2/                   # Spring Boot 2→3 test app
│   ├── README.md
│   ├── pom.xml
│   ├── expected-violations.yaml
│   └── src/
├── patternfly-v5/                   # PatternFly v5→v6 test app
│   ├── README.md
│   ├── package.json
│   ├── expected-violations.yaml
│   └── src/
└── fixtures/                        # Small code snippets for unit tests
    ├── deprecated-annotations.java
    ├── deprecated-imports.java
    └── deprecated-methods.java
```

### Test Data Guidelines

1. **Minimal Reproduction**
   - Keep test apps as small as possible
   - Include only code needed for violations
   - Document why each file exists

2. **Clear Documentation**
   - README explains what should be detected
   - Comments in code mark violation locations
   - expected-violations.yaml lists all expected detections

3. **Version Control**
   - Commit test data to repository
   - Update when rules change
   - Tag with corresponding rule versions

4. **Maintenance**
   - Review test data when rules update
   - Remove outdated test cases
   - Add new cases for new patterns

### Creating Test Data

**Manual Creation:**
```bash
# Create new test application
mkdir -p test-data/my-migration-test/src/main/java/com/example

# Write code with known violations
cat > test-data/my-migration-test/src/main/java/com/example/App.java <<EOF
package com.example;

import javax.security.cert.X509Certificate;  // Should trigger security-00000

public class App {
    // Test code
}
EOF

# Document expected violations
cat > test-data/my-migration-test/expected-violations.yaml <<EOF
expected_violations:
  - rule_id: java11-to-java17-security-00000
    file: src/main/java/com/example/App.java
    line: 3
EOF
```

**Automated Generation:**
```bash
# Use test data generator (if implemented)
python scripts/generate_test_data.py \
  --rules examples/output/java17/ \
  --output test-data/generated-java17-test/
```

## Regression Testing

### Regression Test Suite

Maintain a suite of regression tests to catch unintended changes:

```bash
#!/bin/bash
# regression-test.sh

echo "Running regression tests..."

# Test 1: OpenRewrite Java 17 recipe
python scripts/generate_rules.py \
  --from-openrewrite https://raw.githubusercontent.com/openrewrite/rewrite-migrate-java/main/src/main/resources/META-INF/rewrite/java-version-17.yml \
  --source java11 \
  --target java17 \
  --output regression-output/java17/

# Verify rule count
rule_count=$(ls regression-output/java17/*.yaml | wc -l)
if [ "$rule_count" -lt 4 ]; then
    echo "FAIL: Expected at least 4 rule files, got $rule_count"
    exit 1
fi

# Test 2: Run Kantra on test data
kantra analyze \
  --input test-data/java11-app \
  --rules regression-output/java17/ \
  --output regression-output/analysis/ \
  --overwrite

# Verify violations detected
violations=$(grep -c "java11-to-java17" regression-output/analysis/output.yaml)
if [ "$violations" -lt 2 ]; then
    echo "FAIL: Expected at least 2 violations, got $violations"
    exit 1
fi

echo "PASS: All regression tests passed"
```

### Regression Test Cases

Document specific scenarios that should always work:

| Test Case | Input | Expected Output | Verification |
|-----------|-------|-----------------|--------------|
| Java 17 Package Detection | OpenRewrite java-version-17.yml | Rules use TYPE location for packages | Check location field |
| Spring Boot Properties | OpenRewrite spring-boot-30.yml | Generates builtin provider rules | Check provider_type |
| PatternFly v6 Regex | Migration guide URL | Rules use proper regex escaping | Check pattern syntax |
| Multiple Concerns | Any comprehensive guide | Rules grouped by concern | Check file names |

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Rule Generation

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov yamllint

      - name: Run unit tests
        run: pytest tests/unit/ --cov=src/rule_generator

      - name: Run integration tests
        run: pytest tests/integration/

      - name: Lint generated rules
        run: |
          python scripts/generate_rules.py \
            --from-openrewrite https://raw.githubusercontent.com/openrewrite/rewrite-migrate-java/main/src/main/resources/META-INF/rewrite/java-version-17.yml \
            --source java11 \
            --target java17 \
            --output ci-output/

          yamllint ci-output/*.yaml

      - name: Install Kantra
        run: |
          curl -L https://github.com/konveyor/kantra/releases/latest/download/kantra-linux-amd64 -o kantra
          chmod +x kantra
          sudo mv kantra /usr/local/bin/

      - name: Run E2E validation
        run: |
          kantra analyze \
            --input test-data/java11-app \
            --rules ci-output/ \
            --output ci-results/

          # Verify violations detected
          grep "java11-to-java17" ci-results/output.yaml

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: ci-results/
```

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: Run unit tests
        entry: pytest tests/unit/
        language: system
        pass_filenames: false

      - id: rule-validation
        name: Validate rule syntax
        entry: yamllint
        language: system
        files: \\.yaml$
        exclude: ^(test-data|examples)/
```

## Manual Testing Procedures

### Procedure 1: Visual Rule Inspection

Manually review generated rules for quality:

**Checklist:**
- [ ] Rule IDs are sequential and unique
- [ ] Descriptions are clear and concise
- [ ] Messages provide actionable guidance
- [ ] Code examples show before/after correctly
- [ ] Links to documentation are valid
- [ ] Effort estimates are reasonable
- [ ] Categories are appropriate (mandatory/potential/optional)
- [ ] Labels include source and target frameworks

### Procedure 2: Pattern Accuracy Review

Verify patterns will match intended code:

**Java Provider Rules:**
- [ ] Fully qualified class names are correct
- [ ] Location types are appropriate (TYPE, METHOD_CALL, etc.)
- [ ] Wildcards use TYPE location
- [ ] Method signatures are complete

**Builtin Provider Rules:**
- [ ] Regex patterns are valid
- [ ] File patterns match target files
- [ ] Special characters are properly escaped
- [ ] Patterns aren't overly broad

### Procedure 3: Message Quality Review

Ensure violation messages help developers:

**Checklist:**
- [ ] Explains what is deprecated/changed
- [ ] Provides replacement recommendation
- [ ] Includes code example if helpful
- [ ] Links to official documentation
- [ ] Written in clear, professional language
- [ ] Free of grammatical errors

## Test Coverage Goals

### Code Coverage Targets

- **Unit Tests**: 80% coverage of core logic
  - Pattern extraction: 90%
  - Rule generation: 85%
  - OpenRewrite ingestion: 80%
  - Guide ingestion: 75%

- **Integration Tests**: Cover all major workflows
  - OpenRewrite → Rules
  - Migration Guide → Rules
  - Rules → Kantra validation

- **E2E Tests**: At least one complete workflow per framework
  - Java versions (11→17, 17→21)
  - Spring Boot (2.7→3.0, 3.x→4.0)
  - PatternFly (v5→v6)

### Validation Coverage Targets

- **Rule Validation**: 100% of generated rules tested with Kantra
- **Pattern Coverage**: At least one test case per pattern type
  - Package deprecations
  - Class renames
  - Method changes
  - Annotation updates
  - Configuration changes

## Best Practices

1. **Test Early and Often**
   - Write tests as you develop features
   - Run tests before committing
   - Validate rules immediately after generation

2. **Maintain Test Data**
   - Keep test applications minimal but complete
   - Document expected behavior clearly
   - Update tests when rules change

3. **Automate Where Possible**
   - Use CI/CD for regression testing
   - Script repetitive validation tasks
   - Generate test data when feasible

4. **Review Results Manually**
   - Don't rely solely on automated tests
   - Inspect generated rules visually
   - Verify Kantra output makes sense

5. **Document Failures**
   - Record bugs and edge cases
   - Create regression tests for fixed bugs
   - Share learnings with team

## Tools and Resources

### Testing Tools

- **pytest**: Python unit and integration testing
- **pytest-cov**: Code coverage measurement
- **pytest-mock**: Mocking for LLM and external dependencies
- **yamllint**: YAML syntax validation
- **Kantra**: Rule validation against real code

### Useful Commands

```bash
# Run all tests with coverage
pytest --cov=src/rule_generator --cov-report=html

# Run specific test file
pytest tests/unit/test_extraction.py -v

# Run tests matching pattern
pytest -k "openrewrite" -v

# Run with verbose output
pytest tests/ -vv

# Generate coverage report
pytest --cov=src/rule_generator --cov-report=term-missing

# Validate YAML syntax
yamllint examples/output/**/*.yaml
```

## Future Improvements

### Planned Enhancements

1. **Automated Test Data Generation**
   - Generate test code from rule patterns
   - Create comprehensive test suites automatically

2. **Performance Testing**
   - Measure rule generation time
   - Test with large migration guides
   - Optimize slow components

3. **Mutation Testing**
   - Verify tests catch actual bugs
   - Improve test quality

4. **Visual Regression Testing**
   - Compare generated rules visually
   - Detect unintended formatting changes

5. **Integration with Konveyor CI**
   - Submit generated rules to upstream CI
   - Validate against Konveyor test suite

## Summary

This testing strategy ensures high-quality Konveyor analyzer rules through:

- **Multi-level testing**: Unit, integration, E2E, and validation
- **Comprehensive workflows**: From generation to Kantra verification
- **Automated and manual testing**: Balance of automation and human review
- **Regression protection**: Prevent unintended changes
- **Continuous improvement**: Regular review and enhancement

By following this strategy, we can confidently generate rules that accurately detect migration patterns and provide value to developers.
