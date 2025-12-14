# Migration Complexity Classification Guide

This guide explains how migration complexity classification works in the analyzer-rule-generator and how to use it effectively.

## Overview

Migration complexity classification helps teams understand and prioritize migration work by automatically categorizing rules based on their difficulty level. This enables:

- **AI-assisted migration planning**: Route simple changes to automated tools, complex ones to human review
- **Resource allocation**: Prioritize effort where it's most needed
- **Realistic estimation**: Set expectations based on actual complexity
- **Integration with evaluation frameworks**: Powers konveyor-iq evaluation and benchmarking

## Complexity Levels

### Trivial (95%+ AI Success Rate)

**Characteristics:**
- Simple namespace or package changes (e.g., `javax.*` → `jakarta.*`)
- Mechanical find/replace operations
- No context understanding required
- No logic changes

**Examples:**
```yaml
- ruleID: javax-to-jakarta-00000
  description: Replace javax.servlet imports with jakarta.servlet
  migration_complexity: trivial
  effort: 1
```

**Automation:** These can be handled by simple find/replace tools or AI with minimal risk.

### Low (80%+ AI Success Rate)

**Characteristics:**
- Simple annotation swaps (e.g., `@Stateless` → `@ApplicationScoped`)
- Straightforward API equivalents
- One-to-one replacements with similar semantics
- Minimal code restructuring

**Examples:**
```yaml
- ruleID: ejb-to-cdi-00000
  description: Replace @Stateless with @ApplicationScoped
  migration_complexity: low
  effort: 2-3
```

**Automation:** AI can handle most cases with high confidence; human review for edge cases.

### Medium (60%+ AI Success Rate)

**Characteristics:**
- Requires understanding of surrounding context
- Pattern changes with semantic implications
- Configuration migrations
- Moderate API differences
- Message queue or reactive patterns

**Examples:**
```yaml
- ruleID: jms-to-reactive-00000
  description: Migrate JMS MessageListener to Reactive Messaging
  migration_complexity: medium
  effort: 4-6
```

**Automation:** AI can assist but requires human verification; some cases need manual implementation.

### High (30-50% AI Success Rate)

**Characteristics:**
- Architectural changes
- Security implementations
- Complex API migrations
- Multi-step transformations
- Framework-specific patterns

**Examples:**
```yaml
- ruleID: spring-security-migration-00000
  description: Update Spring Security configuration for new architecture
  migration_complexity: high
  effort: 7-9
```

**Automation:** AI provides guidance and suggestions; significant human oversight required.

### Expert (<30% AI Success Rate)

**Characteristics:**
- Custom implementations
- Deep framework internals
- Performance-critical code
- Distributed transactions
- Legacy integration patterns

**Examples:**
```yaml
- ruleID: custom-realm-migration-00000
  description: Migrate custom security realm implementation
  migration_complexity: expert
  effort: 10
```

**Automation:** AI-generated code likely needs significant rework; primarily human-driven with AI assistance.

## How Classification Works

### Automatic Classification During Generation

When generating rules from migration guides, the LLM automatically extracts complexity:

```bash
python scripts/generate_rules.py \
  --guide https://example.com/migration-guide \
  --source framework-v1 \
  --target framework-v2 \
  --output rules.yaml
```

Generated rules include `migration_complexity` field:

```yaml
- ruleID: example-00000
  description: Update deprecated API
  effort: 5
  migration_complexity: medium  # ← Automatically added
```

### Classification Algorithm

The classifier uses multiple signals:

1. **Pattern Matching**
   - Scans rule description, message, and ruleID for complexity indicators
   - Keywords like "security", "custom", "architectural" → higher complexity
   - Keywords like "rename", "replace", "javax" → lower complexity

2. **Effort Score Analysis**
   - `effort >= 7` → high
   - `effort >= 4` → medium
   - `effort <= 2` → low

3. **When Condition Complexity**
   - Logical operators (`and`, `or`, `not`) → medium
   - Multiple providers (combo rules) → medium
   - XPath expressions → high
   - Complex regex (lookaheads/lookbehinds) → high

4. **Simple Replacement Detection**
   - `javax` → `jakarta` patterns → trivial
   - Import statement changes → trivial
   - Excludes security/config/transaction changes

### Classification Decision Tree

```
IF expert_patterns match:
  → expert
ELSE IF high_patterns match OR effort >= 7 OR when_complexity == high:
  → high
ELSE IF medium_patterns match > 1 OR effort >= 4:
  → medium
ELSE IF low_patterns match OR effort <= 2:
  → low
ELSE IF trivial_patterns match AND simple_replacement:
  → trivial
ELSE:
  → low (conservative default)
```

## Using the Classifier

### Classify Existing Rulesets

The `classify_existing_rules.py` script adds complexity to existing rules without regenerating them.

#### Basic Usage

```bash
# Dry run (preview classifications)
python scripts/classify_existing_rules.py \
  --ruleset examples/output/spring-boot/migration-rules.yaml \
  --dry-run

# Apply classifications
python scripts/classify_existing_rules.py \
  --ruleset examples/output/spring-boot/migration-rules.yaml

# Verbose output (show reasoning)
python scripts/classify_existing_rules.py \
  --ruleset examples/output/spring-boot/migration-rules.yaml \
  --dry-run \
  --verbose
```

#### Output Example

```
Classifying ruleset: migration-rules.yaml
================================================================================

✓ spring-boot-3-to-spring-boot-4-00000: medium
✓ spring-boot-3-to-spring-boot-4-00010: low
✓ spring-boot-3-to-spring-boot-4-00020: high

================================================================================
Classification Summary:
  TRIVIAL:   2 rules (95%+ AI success - namespace changes, mechanical fixes)
  LOW:      15 rules (80%+ AI success - simple API equivalents)
  MEDIUM:   10 rules (60%+ AI success - requires context understanding)
  HIGH:      5 rules (30-50% AI success - architectural changes)
  EXPERT:    1 rules (<30% AI success - likely needs human review)

Total rules: 33
Total changes: 33

✓ Updated migration-rules.yaml
```

### Batch Processing

Process multiple rulesets at once:

```bash
# Dry run on multiple files
bash scripts/batch_classify_rulesets.sh /path/to/rulesets true

# Apply to all rulesets
bash scripts/batch_classify_rulesets.sh /path/to/rulesets false
```

### Supported Ruleset Formats

Both list and dict formats are supported:

**List format:**
```yaml
- ruleID: test-00000
  description: Test rule
  # ... rest of rule
```

**Dict format:**
```yaml
name: my-ruleset
rules:
  - ruleID: test-00000
    description: Test rule
    # ... rest of rule
```

## Integration with konveyor-iq

Migration complexity enables complexity-aware evaluation and reporting in konveyor-iq:

```bash
# Generate test suite from classified rules
cd /path/to/konveyor-iq
python scripts/generate_tests.py \
  --ruleset /path/to/classified-ruleset.yaml

# Evaluate with complexity filtering
python evaluate.py \
  --benchmark benchmarks/test_cases/generated/spring-boot.yaml \
  --filter-complexity trivial,low

# Reports automatically include complexity breakdown
```

Benefits:
- Compare AI performance across complexity levels
- Identify where human review is most needed
- Track improvement in handling complex migrations
- Set realistic expectations for automation success rates

## Customizing Classification Patterns

You can modify the classifier patterns to match your domain:

**Edit `scripts/classify_existing_rules.py`:**

```python
# Add your own patterns
TRIVIAL_PATTERNS = [
    r'javax\.',
    r'your-custom-pattern',  # Add here
]

EXPERT_PATTERNS = [
    r'custom.*realm',
    r'your-expert-indicator',  # Add here
]
```

### Pattern Matching Tips

- Use lowercase patterns (matching is case-insensitive)
- Use `.*` for wildcards
- Test with `--verbose` to see which patterns match
- Be specific to avoid false positives

## Best Practices

### For Rule Generation

1. **Review LLM-assigned complexity**: The LLM extracts complexity during generation, but verify it matches your expectations
2. **Calibrate with examples**: Provide example rules with known complexity to guide the LLM
3. **Be consistent**: Use the same complexity criteria across your organization

### For Existing Rulesets

1. **Start with dry run**: Always preview classifications before applying
2. **Use verbose mode**: Understand why rules were classified a certain way
3. **Validate high/expert rules**: Manually review critical classifications
4. **Update patterns**: Customize patterns for your specific domain

### For Migration Planning

1. **Prioritize by impact**: Focus on high-complexity rules that affect many files
2. **Automate trivial/low**: Use AI or automated tools for simple changes
3. **Human review for medium+**: All medium and above should have human oversight
4. **Expert → human-first**: Start with human implementation, use AI for assistance

## Troubleshooting

### Classifications Seem Wrong

**Problem:** Rules are classified incorrectly

**Solution:**
```bash
# Run with verbose to see reasoning
python scripts/classify_existing_rules.py \
  --ruleset problematic-rules.yaml \
  --dry-run \
  --verbose

# Review pattern matches and scores
# Adjust classifier patterns if needed
```

### Different Results for Similar Rules

**Problem:** Similar rules get different complexity

**Solution:** The classifier looks at multiple signals. Check:
- Effort scores (different effort → different complexity)
- Keywords in description/message
- When condition structure

Consider standardizing rule descriptions for consistent classification.

### YAML Formatting Changes

**Problem:** File formatting changes after classification

**Solution:** The classifier preserves YAML structure but may reformat spacing. To see content-only changes:

```bash
# Compare semantic differences only
diff <(yq -P 'sort_keys(..)' original.yaml) \
     <(yq -P 'sort_keys(..)' classified.yaml)
```

## Schema Reference

### AnalyzerRule.migration_complexity

```python
migration_complexity: Optional[str] = Field(
    default=None,
    description="Migration complexity level (trivial, low, medium, high, expert)"
)
```

**Type:** Optional string
**Valid values:** `"trivial"`, `"low"`, `"medium"`, `"high"`, `"expert"`
**Default:** `None` (backward compatible)

## Examples

### Example 1: Classifying Java EE to Quarkus Rules

```bash
python scripts/classify_existing_rules.py \
  --ruleset examples/output/java-ee-to-quarkus/migration-rules.yaml
```

Typical distribution:
- TRIVIAL: 10-15% (javax → jakarta)
- LOW: 40-45% (@Stateless → @ApplicationScoped)
- MEDIUM: 30-35% (JMS → Reactive)
- HIGH: 8-10% (Security configurations)
- EXPERT: 2-5% (Custom realms, performance tuning)

### Example 2: Classifying React Migration Rules

```bash
python scripts/classify_existing_rules.py \
  --ruleset examples/output/react-v17-to-v18/migration-rules.yaml
```

Typical distribution:
- TRIVIAL: 5-10% (Simple renames)
- LOW: 50-60% (Hook replacements)
- MEDIUM: 25-30% (Concurrent features)
- HIGH: 5-10% (Suspense changes)
- EXPERT: <5% (Custom concurrent implementations)

## Related Documentation

- [Konveyor Rule Schema](../reference/java-rule-schema.md)
- [Rule Generation Guide](../reference/generate-rules.md)
- [konveyor-iq Integration](https://github.com/konveyor/konveyor-iq)

## Contributing

To improve classification accuracy:

1. Run classifier on your rulesets
2. Note any misclassifications
3. Propose pattern updates via pull request
4. Include examples demonstrating the improvement

We welcome contributions that make classification more accurate and domain-aware!
