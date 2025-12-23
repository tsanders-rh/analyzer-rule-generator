# Rule Validation Guide

The `validate_rules.py` script helps catch common issues in generated Konveyor analyzer rules before submission.

## Why Validate?

Even with improved prompts, LLMs can sometimes generate rules with issues like:

1. **Description/pattern mismatches**: Description says "import path change" but pattern detects component usage
2. **Overly broad patterns**: Short patterns that match unintended code
3. **Missing fields**: Required fields not populated
4. **Invalid effort scores**: Scores outside 1-10 range
5. **Semantic inconsistencies**: Rule behavior doesn't match intent

## Validation Modes

### Mode 1: Syntactic Validation (Fast, Free)

Performs fast, deterministic checks:
- Required fields present
- Valid effort scores (1-10)
- Non-empty when conditions
- Pattern broadness warnings

```bash
python scripts/validate_rules.py \
  --rules examples/output/spring-boot/rules.yaml
```

**Output:**
```
Validating: examples/output/spring-boot/rules.yaml
================================================================================

  Checking spring-boot-3-to-4-00000...
    ✓ All fields present
    ✓ Valid effort score
    ⚠️ Warning: Short pattern 'isActive' may match unintended code

  Checking spring-boot-3-to-4-00010...
    ✓ All fields present
    ✓ Valid effort score

================================================================================
Validation Summary:
  Issues:   0
  Warnings: 1

⚠️  Warnings:
  - spring-boot-3-to-4-00000: Short unanchored pattern 'isActive' may match unintended code
```

### Mode 2: Semantic Validation (Slower, Uses AI)

Uses LLM to check description/pattern alignment:

```bash
python scripts/validate_rules.py \
  --rules examples/output/patternfly-v6/rules.yaml \
  --semantic
```

**What it does:**
1. Sends rule description + when condition to LLM
2. LLM checks if description accurately describes what pattern detects
3. Provides suggestions if mismatch found

**Output:**
```
Validating: examples/output/patternfly-v6/rules.yaml
================================================================================

  Checking patternfly-v5-to-v6-00000...
    ✓ All fields present
    ✓ Valid effort score
    ✓ Description aligns with pattern

  Checking patternfly-v5-to-v6-00010...
    ✓ All fields present
    ✓ Valid effort score
    ❌ Description/pattern mismatch - Description says "import path change"
       but pattern detects EmptyStateHeader component usage
       Suggestion: Change description to "EmptyStateHeader component usage"
       or change when condition to detect import paths

================================================================================
Validation Summary:
  Issues:   1
  Warnings: 0

❌ Issues found:
  - patternfly-v5-to-v6-00010: Description/pattern mismatch
```

## Usage Patterns

### Validate Before Submission

```bash
# Quick check (free)
python scripts/validate_rules.py --rules my-rules.yaml

# Deep check (costs API calls)
python scripts/validate_rules.py --rules my-rules.yaml --semantic
```

### Validate Directory of Rules

```bash
# Validate all YAML files in directory
python scripts/validate_rules.py --rules examples/output/patternfly-v6/ --semantic
```

### Integrate with Demo Script

Add validation to step 4:

```bash
./scripts/demo.sh 1  # Generate rules
./scripts/demo.sh 2  # Generate tests

# Validate before submitting
python scripts/validate_rules.py --rules demo-output/rules/ --semantic

./scripts/demo.sh 4  # Show next steps
```

## Validation Checks

### Syntactic Checks (Always Performed)

| Check | Description | Severity |
|-------|-------------|----------|
| Required fields | ruleID, description, effort, when, message | Error |
| Valid effort | 1-10 range, integer | Error |
| Empty when | Detects empty when conditions | Error |
| Empty patterns | Checks for missing pattern values | Error |
| Short patterns | Warns about patterns < 5 chars | Warning |
| Generic patterns | Checks if description mentions specifics but pattern is generic | Warning |

### Semantic Checks (--semantic flag)

| Check | Description | Cost |
|-------|-------------|------|
| Description alignment | LLM verifies description matches pattern intent | ~$0.01 per rule |
| Pattern scope | LLM checks if pattern is too broad/narrow | ~$0.01 per rule |

## Common Issues Found

### Issue 1: Description/Pattern Mismatch

**Problem:**
```yaml
description: '@patternfly/react-core/v5 should be replaced with @patternfly/react-core'
when:
  and:
  - builtin.filecontent:
      pattern: import.*EmptyStateHeader.*from
  - builtin.filecontent:
      pattern: <EmptyStateHeader
```

**Validator Output:**
```
❌ Description says "import path change" but pattern detects EmptyStateHeader usage
   Suggestion: Change description to "EmptyStateHeader component usage"
```

**Fix:**
```yaml
description: 'EmptyStateHeader component usage detected'
# OR change the when condition to actually detect import paths
```

### Issue 2: Overly Broad Pattern

**Problem:**
```yaml
when:
  builtin.filecontent:
    pattern: isActive
```

**Validator Output:**
```
⚠️ Short unanchored pattern 'isActive' may match unintended code
```

**Fix:**
```yaml
when:
  and:
  - nodejs.referenced:
      pattern: Button
  - builtin.filecontent:
      pattern: <Button[^>]*\bisActive\b
```

### Issue 3: Missing Component Name

**Problem:**
```yaml
description: 'Button isActive prop should be replaced'
when:
  builtin.filecontent:
    pattern: \bisActive\b
```

**Validator Output:**
```
⚠️ Description mentions Button but pattern doesn't check for it
```

**Fix:**
Use combo rule to ensure Button component is present.

## Best Practices

1. **Always run syntactic validation** - It's fast and free
2. **Use semantic validation before submission** - Catches subtle issues
3. **Fix all errors, review all warnings** - Warnings often indicate real issues
4. **Re-validate after manual edits** - Ensure fixes didn't introduce new issues
5. **Keep validation in your workflow** - Part of the quality process

## Cost Considerations

**Syntactic validation**: Free, instant

**Semantic validation**:
- ~$0.01 per rule (using Anthropic Claude)
- For 50 rules: ~$0.50
- For 200 rules: ~$2.00

**Recommendation**: Use semantic validation for final pre-submission check, not during iterative development.

## Integration Examples

### CI/CD Integration

```bash
#!/bin/bash
# .github/workflows/validate-rules.yml

# Generate rules
python scripts/generate_rules.py --guide $GUIDE_URL --output rules.yaml

# Validate (fail build on errors)
python scripts/validate_rules.py --rules rules.yaml --semantic

# If validation passes, create PR
if [ $? -eq 0 ]; then
  gh pr create --title "Add migration rules" --body "Generated and validated"
fi
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Validate any changed rule files
changed_rules=$(git diff --cached --name-only | grep '\.yaml$')

if [ -n "$changed_rules" ]; then
  for rule_file in $changed_rules; do
    python scripts/validate_rules.py --rules "$rule_file"
    if [ $? -ne 0 ]; then
      echo "❌ Validation failed for $rule_file"
      echo "Fix issues before committing"
      exit 1
    fi
  done
fi
```

## Troubleshooting

### "No API key found"

For semantic validation, set your API key:
```bash
export ANTHROPIC_API_KEY="your-key"
# OR
export OPENAI_API_KEY="your-key"
```

### "Semantic validation failed"

If the LLM call fails:
- Check your API key is valid
- Verify network connectivity
- Check API rate limits
- Try again (may be transient error)

### "Too many warnings"

Warnings are suggestions, not blockers:
- Review each warning
- Decide if it's a real issue
- Some warnings may be false positives (use judgment)
- Fix obvious issues, document false positives

## Example: Full Validation Workflow

```bash
# 1. Generate rules
python scripts/generate_rules.py \
  --guide https://example.com/migration-guide \
  --source v1 \
  --target v2 \
  --output my-rules.yaml

# 2. Quick syntactic check
python scripts/validate_rules.py --rules my-rules.yaml

# 3. Fix any errors found
# ... edit my-rules.yaml ...

# 4. Deep semantic check before submission
python scripts/validate_rules.py --rules my-rules.yaml --semantic

# 5. Address any mismatches
# ... edit my-rules.yaml ...

# 6. Final validation
python scripts/validate_rules.py --rules my-rules.yaml --semantic

# 7. Submit if all clear
✅ All rules validated successfully!
```

## Future Enhancements

Potential additions to the validator:

- **Pattern testing**: Test patterns against sample code
- **Performance checking**: Warn about potentially slow regexes
- **Consistency checking**: Ensure similar rules use consistent patterns
- **Completeness checking**: Verify all guide patterns are covered
- **Auto-fix suggestions**: Generate corrected rules for common issues

## Related Documentation

- [Rule Generation Guide](generate-rules.md)
- [Konveyor Rule Schema](java-rule-schema.md)
- [Submission Guide](../guides/konveyor-submission-guide.md)
