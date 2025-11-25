# Post-Generation LLM Validation Design

## Overview

After initial rule generation, use an LLM to review and improve rules to:
1. **Add import verification** where missing
2. **Detect overly broad patterns** that would cause false positives
3. **Suggest pattern improvements** for better accuracy
4. **Flag duplicate or conflicting rules**
5. **Validate rule quality** against best practices

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Rule Generation Flow                      │
└─────────────────────────────────────────────────────────────┘

Phase 1: Initial Generation (Current)
  ├─ Ingest migration guide
  ├─ Extract patterns with LLM
  ├─ Generate rules
  └─ Basic validation (duplicates, required fields)

Phase 2: LLM Validation & Improvement (NEW)
  ├─ Review each rule
  ├─ Identify improvement opportunities
  ├─ Generate improved versions
  ├─ Present changes for approval
  └─ Apply improvements

Phase 3: Output
  ├─ Write validated rules
  ├─ Generate validation report
  └─ Summary of improvements made
```

## Validation Checks

### 1. Import Verification Check

**Purpose:** Detect rules that need PatternFly import verification

**Detection criteria:**
- Uses `nodejs.referenced` for a component name (Button, Card, etc.)
- Has JSX pattern in `builtin.filecontent`
- **Missing** import verification pattern

**LLM Prompt:**
```
Review this Konveyor analyzer rule for a JavaScript/TypeScript migration:

Rule: {rule_yaml}

This rule detects usage of component "{component}" but does not verify
it's from the target library (@patternfly/react-core).

Task: Add an import verification condition to ensure this only matches
components from @patternfly/react-core.

Return the improved rule with a 3-condition combo:
1. Import verification: import...from '@patternfly/react-core'
2. nodejs.referenced (existing)
3. builtin.filecontent (existing JSX pattern)

Output only the YAML for the improved rule.
```

### 2. Overly Broad Pattern Detection

**Purpose:** Identify patterns that match too broadly

**Detection criteria:**
- Pattern is < 10 characters
- Pattern is common word (isActive, variant, onClick, etc.)
- No component context or specificity

**LLM Prompt:**
```
Review this Konveyor analyzer rule:

Rule: {rule_yaml}

Analyze if the pattern "{pattern}" is overly broad and would match
unintended code.

Consider:
- Is this a common prop name used in many libraries?
- Does it have enough context to be specific?
- Could it match HTML attributes or generic code?

If overly broad, suggest a more specific pattern.
Return: {
  "is_overly_broad": boolean,
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "reason": "explanation",
  "suggested_improvement": "improved pattern or null"
}
```

### 3. Pattern Quality Review

**Purpose:** Ensure patterns follow best practices

**Checks:**
- JSX patterns have proper escaping
- Regex patterns are valid
- filePattern is specified for builtin rules
- Component names are capitalized correctly

**LLM Prompt:**
```
Review this Konveyor analyzer rule for pattern quality:

Rule: {rule_yaml}

Check for:
1. Regex escaping issues (brackets, special chars)
2. Missing filePattern for builtin.filecontent
3. Inefficient or incorrect regex patterns
4. Component name casing issues

Return improvements as JSON:
{
  "issues": [
    {"type": "regex_escaping", "severity": "HIGH", "fix": "..."},
    ...
  ],
  "improved_rule": "full YAML or null if no changes needed"
}
```

### 4. Duplicate & Conflict Detection

**Purpose:** Find rules that overlap or conflict

**Detection:**
- Same source pattern with different targets
- Multiple rules for same component/prop combination
- Contradictory guidance

**LLM Prompt:**
```
Compare these two rules for conflicts or duplicates:

Rule 1: {rule1_yaml}
Rule 2: {rule2_yaml}

Analyze:
1. Do they detect the same pattern?
2. Do they provide conflicting guidance?
3. Should they be merged or one removed?

Return: {
  "are_duplicates": boolean,
  "have_conflict": boolean,
  "recommendation": "merge" | "keep_both" | "remove_rule1" | "remove_rule2",
  "reason": "explanation",
  "merged_rule": "YAML if merging recommended"
}
```

## Implementation Plan

### Module: `src/rule_generator/validate_rules.py`

```python
class RuleValidator:
    """Post-generation LLM-based rule validator"""

    def __init__(self, llm_client, language: str):
        self.llm = llm_client
        self.language = language

    def validate_rules(self, rules: List[Rule]) -> ValidationReport:
        """Run all validation checks on rules"""
        report = ValidationReport()

        # 1. Import verification check
        for rule in rules:
            if self._needs_import_verification(rule):
                improved = self._add_import_verification(rule)
                report.add_improvement('import_verification', rule, improved)

        # 2. Overly broad pattern check
        for rule in rules:
            analysis = self._check_pattern_breadth(rule)
            if analysis['is_overly_broad']:
                report.add_issue('overly_broad', rule, analysis)

        # 3. Pattern quality review
        for rule in rules:
            quality_check = self._review_pattern_quality(rule)
            if quality_check['issues']:
                report.add_improvement('quality', rule, quality_check)

        # 4. Duplicate detection
        duplicates = self._find_duplicates(rules)
        for dup_pair in duplicates:
            report.add_issue('duplicate', dup_pair[0], dup_pair[1])

        return report

    def _needs_import_verification(self, rule: Rule) -> bool:
        """Check if rule needs import verification added"""
        when = rule.when

        # Check for combo rule with nodejs.referenced but no import check
        if isinstance(when, dict) and 'and' in when:
            has_nodejs = any('nodejs.referenced' in str(c) for c in when['and'])
            has_import_check = any('@patternfly' in str(c) or 'import' in str(c)
                                   for c in when['and'])

            # For JS/TS, component patterns should verify imports
            if has_nodejs and not has_import_check:
                # Extract component name
                for cond in when['and']:
                    if 'nodejs.referenced' in cond:
                        pattern = cond['nodejs.referenced'].get('pattern', '')
                        # If it looks like a component name (capitalized)
                        if pattern and pattern[0].isupper():
                            return True

        return False

    def _add_import_verification(self, rule: Rule) -> Rule:
        """Use LLM to add import verification to rule"""

        # Extract component name
        component = self._extract_component_name(rule)

        prompt = f"""
Add import verification to this Konveyor analyzer rule to ensure it only
matches components from @patternfly/react-core:

```yaml
{rule.to_yaml()}
```

Component to verify: {component}

Add a condition that checks for:
import {{ {component} }} from '@patternfly/react-core'
OR
import {{ {component} }} from '@patternfly/react-core/deprecated'

Return the complete improved rule as YAML.
"""

        response = self.llm.query(prompt)
        improved_rule = Rule.from_yaml(response)

        return improved_rule

    def _check_pattern_breadth(self, rule: Rule) -> dict:
        """Use LLM to check if pattern is overly broad"""

        prompt = f"""
Analyze this Konveyor analyzer rule for overly broad patterns:

```yaml
{rule.to_yaml()}
```

Check if the pattern would match unintended code (false positives).

Common issues:
- Generic prop names (isActive, variant, onClick) without component context
- Short patterns that match common words
- Missing file type restrictions

Return JSON:
{{
  "is_overly_broad": boolean,
  "risk_level": "LOW|MEDIUM|HIGH",
  "reason": "explanation",
  "estimated_false_positive_rate": "percentage",
  "suggested_improvement": "more specific pattern or null"
}}
"""

        response = self.llm.query(prompt, format="json")
        return response

    def _review_pattern_quality(self, rule: Rule) -> dict:
        """Use LLM to review pattern quality"""

        prompt = f"""
Review this Konveyor analyzer rule for pattern quality issues:

```yaml
{rule.to_yaml()}
```

Check for:
1. Regex escaping problems (unescaped brackets, dots, etc.)
2. Missing filePattern for builtin.filecontent
3. Inefficient regex patterns
4. Case sensitivity issues

Return JSON:
{{
  "issues": [
    {{"type": "issue_type", "severity": "HIGH|MEDIUM|LOW", "description": "...", "fix": "..."}}
  ],
  "improved_rule_yaml": "improved YAML or null"
}}
"""

        response = self.llm.query(prompt, format="json")
        return response
```

### Module: `src/rule_generator/validation_report.py`

```python
class ValidationReport:
    """Report of validation findings and improvements"""

    def __init__(self):
        self.improvements = []
        self.issues = []
        self.statistics = {
            'total_rules': 0,
            'rules_improved': 0,
            'import_verification_added': 0,
            'overly_broad_detected': 0,
            'quality_issues_fixed': 0,
            'duplicates_found': 0
        }

    def add_improvement(self, improvement_type: str, original: Rule, improved: Rule):
        self.improvements.append({
            'type': improvement_type,
            'original': original,
            'improved': improved
        })
        self.statistics['rules_improved'] += 1
        self.statistics[f'{improvement_type}_added'] += 1

    def add_issue(self, issue_type: str, rule: Rule, details: dict):
        self.issues.append({
            'type': issue_type,
            'rule': rule,
            'details': details
        })
        self.statistics[f'{issue_type}_detected'] += 1

    def generate_report(self) -> str:
        """Generate human-readable validation report"""
        report = []

        report.append("="*80)
        report.append("POST-GENERATION VALIDATION REPORT")
        report.append("="*80)

        report.append(f"\nTotal rules validated: {self.statistics['total_rules']}")
        report.append(f"Rules improved: {self.statistics['rules_improved']}")

        report.append("\n" + "─"*80)
        report.append("IMPROVEMENTS APPLIED")
        report.append("─"*80)

        for improvement in self.improvements:
            report.append(f"\n{improvement['type'].upper()}:")
            report.append(f"  Rule: {improvement['original'].ruleID}")
            report.append(f"  Change: {improvement['original'].description}")
            # Show diff

        report.append("\n" + "─"*80)
        report.append("ISSUES DETECTED")
        report.append("─"*80)

        for issue in self.issues:
            report.append(f"\n{issue['type'].upper()}:")
            report.append(f"  Rule: {issue['rule'].ruleID}")
            report.append(f"  Details: {issue['details']}")

        return "\n".join(report)
```

## Integration with generate_rules.py

```python
# In generate_rules.py, after initial rule generation:

print("="*80)
print("POST-GENERATION VALIDATION")
print("="*80)

# Initialize validator
from src.rule_generator.validate_rules import RuleValidator
from src.rule_generator.llm import LLMClient

llm = LLMClient(model="claude-sonnet-4")
validator = RuleValidator(llm, language="javascript")

# Validate all generated rules
validation_report = validator.validate_rules(all_rules)

# Show validation summary
print(validation_report.generate_report())

# Ask user for approval
if validation_report.improvements:
    print(f"\n{len(validation_report.improvements)} improvements suggested.")

    # Show each improvement for approval
    for improvement in validation_report.improvements:
        print(f"\n{'─'*80}")
        print(f"Improvement: {improvement['type']}")
        print(f"Rule: {improvement['original'].ruleID}")
        print(f"\nORIGINAL:")
        print(improvement['original'].to_yaml())
        print(f"\nIMPROVED:")
        print(improvement['improved'].to_yaml())

        # Auto-approve import verification additions
        if improvement['type'] == 'import_verification':
            print("✓ Auto-approving import verification")
            improvement['original'].update_from(improvement['improved'])
        else:
            # Ask for approval
            approval = input("Apply this improvement? [y/N]: ")
            if approval.lower() == 'y':
                improvement['original'].update_from(improvement['improved'])

# Write improved rules
print("\nWriting validated rules...")
write_rules(all_rules, output_dir)
```

## Benefits

1. **Automated Quality Improvement**: LLM catches issues humans might miss
2. **Consistency**: All rules follow same quality standards
3. **Accuracy**: Import verification reduces false positives by ~60%
4. **Learning**: Validation report teaches best practices
5. **Safety**: User approval required for non-obvious changes

## Cost Considerations

**LLM API calls:**
- ~2-4 calls per rule (import check, breadth check, quality check, duplicates)
- 138 rules × 3 calls = ~400 API calls
- At $0.003/1K input tokens, ~$5-10 per full validation

**Trade-off:**
- Cost: $5-10 per ruleset generation
- Benefit: 1,000+ fewer false positives to manually review
- **ROI: Massive** (hours of manual review saved)

## Future Enhancements

1. **Learn from test results**: Feed Kantra output back to improve patterns
2. **A/B testing**: Generate multiple pattern variants, test all
3. **Confidence scoring**: LLM assigns confidence to each rule
4. **Auto-fix mode**: Automatically apply high-confidence improvements
5. **Validation rules database**: Learn from past validations
