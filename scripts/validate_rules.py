#!/usr/bin/env python3
"""
Validate Konveyor analyzer rules for common issues.

This script performs both syntactic and semantic validation of generated rules
to catch issues like description/pattern mismatches, overly broad patterns, etc.

Usage:
    # Validate a single ruleset
    python scripts/validate_rules.py --rules examples/output/spring-boot/rules.yaml

    # Validate with LLM-based semantic checking (costs API calls)
    python scripts/validate_rules.py --rules examples/output/spring-boot/rules.yaml --semantic

    # Validate all rules in a directory
    python scripts/validate_rules.py --rules examples/output/patternfly-v6/ --semantic
"""

import sys
import yaml
import argparse
from pathlib import Path
from typing import List, Dict, Any
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_generator.llm import LLMProvider, get_llm_provider


class RuleValidator:
    """Validates Konveyor analyzer rules for common issues."""

    def __init__(self, use_semantic: bool = False, llm_provider: str = "anthropic"):
        """
        Initialize validator.

        Args:
            use_semantic: Enable LLM-based semantic validation (costs API calls)
            llm_provider: LLM provider to use for semantic validation
        """
        self.use_semantic = use_semantic
        self.llm = None

        if use_semantic:
            self.llm = get_llm_provider(llm_provider)

        self.issues = []
        self.warnings = []

    def validate_ruleset(self, ruleset_path: Path) -> Dict[str, Any]:
        """
        Validate all rules in a ruleset file.

        Args:
            ruleset_path: Path to ruleset YAML file

        Returns:
            Validation results with issues and warnings
        """
        print(f"\nValidating: {ruleset_path}")
        print("=" * 80)

        with open(ruleset_path, 'r') as f:
            data = yaml.safe_load(f)

        # Handle both list and dict formats
        if isinstance(data, list):
            rules = data
        elif isinstance(data, dict) and 'rules' in data:
            rules = data['rules']
        else:
            return {
                'valid': False,
                'issues': ['Unrecognized ruleset format']
            }

        # Reset counters
        self.issues = []
        self.warnings = []

        # Validate each rule
        for i, rule in enumerate(rules):
            rule_id = rule.get('ruleID', f'rule_{i}')
            print(f"\n  Checking {rule_id}...")

            # Syntactic validations
            self._validate_required_fields(rule, rule_id)
            self._validate_when_condition(rule, rule_id)
            self._validate_effort_score(rule, rule_id)
            self._validate_pattern_broadness(rule, rule_id)

            # Semantic validation (optional, uses LLM)
            if self.use_semantic:
                self._validate_description_pattern_alignment(rule, rule_id)

        # Print summary
        print("\n" + "=" * 80)
        print(f"Validation Summary:")
        print(f"  Issues:   {len(self.issues)}")
        print(f"  Warnings: {len(self.warnings)}")

        if self.issues:
            print(f"\n❌ Issues found:")
            for issue in self.issues:
                print(f"  - {issue}")

        if self.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.issues and not self.warnings:
            print(f"\n✅ All rules validated successfully!")

        return {
            'valid': len(self.issues) == 0,
            'issues': self.issues,
            'warnings': self.warnings
        }

    def _validate_required_fields(self, rule: Dict, rule_id: str):
        """Check that all required fields are present."""
        required = ['ruleID', 'description', 'effort', 'when', 'message']

        for field in required:
            if field not in rule:
                self.issues.append(f"{rule_id}: Missing required field '{field}'")

    def _validate_when_condition(self, rule: Dict, rule_id: str):
        """Validate the when condition structure."""
        when = rule.get('when', {})

        if not when:
            self.issues.append(f"{rule_id}: Empty 'when' condition")
            return

        # Check for common issues
        if isinstance(when, dict):
            # Check for empty providers
            for provider in ['java.referenced', 'nodejs.referenced', 'builtin.filecontent']:
                if provider in when:
                    if not when[provider].get('pattern'):
                        self.issues.append(f"{rule_id}: Empty pattern in {provider}")

            # Check for overly simple patterns
            if 'builtin.filecontent' in when:
                pattern = when['builtin.filecontent'].get('pattern', '')
                if len(pattern) < 3:
                    self.warnings.append(f"{rule_id}: Very short pattern '{pattern}' may cause false positives")

    def _validate_effort_score(self, rule: Dict, rule_id: str):
        """Validate effort score is in valid range."""
        effort = rule.get('effort')

        if effort is not None:
            if not isinstance(effort, int):
                self.issues.append(f"{rule_id}: Effort must be an integer, got {type(effort)}")
            elif effort < 1 or effort > 10:
                self.issues.append(f"{rule_id}: Effort must be 1-10, got {effort}")

    def _validate_pattern_broadness(self, rule: Dict, rule_id: str):
        """Check for overly broad patterns that might cause false positives."""
        when = rule.get('when', {})
        description = rule.get('description', '')

        # Check for patterns that are too generic
        if 'builtin.filecontent' in when:
            pattern = when['builtin.filecontent'].get('pattern', '')

            # Warn about very short patterns
            if len(pattern) < 5 and not pattern.startswith('^'):
                self.warnings.append(
                    f"{rule_id}: Short unanchored pattern '{pattern}' may match unintended code"
                )

            # Warn if description mentions specific component but pattern is generic
            if 'EmptyStateHeader' in description:
                if 'EmptyStateHeader' not in pattern:
                    self.warnings.append(
                        f"{rule_id}: Description mentions EmptyStateHeader but pattern doesn't check for it"
                    )

        # Check combo rules
        if 'and' in when:
            conditions = when['and']
            has_import = False
            has_usage = False

            for cond in conditions:
                if 'builtin.filecontent' in cond:
                    pattern = cond['builtin.filecontent'].get('pattern', '')
                    if 'import' in pattern.lower():
                        has_import = True
                    elif '<' in pattern:  # JSX usage
                        has_usage = True

            # Warn if checking imports without usage (might be intentional)
            if has_import and not has_usage:
                self.warnings.append(
                    f"{rule_id}: Checks imports but not usage - may flag unused imports"
                )

    def _validate_description_pattern_alignment(self, rule: Dict, rule_id: str):
        """Use LLM to check if description matches what the pattern actually detects."""
        if not self.llm:
            return

        description = rule.get('description', '')
        when = rule.get('when', {})
        message = rule.get('message', '')

        prompt = f"""You are validating a Konveyor analyzer rule for consistency.

Rule ID: {rule_id}
Description: {description}
Message: {message[:200]}...
When Condition: {yaml.dump(when, default_flow_style=False)}

Does the 'description' accurately describe what the 'when' condition will actually detect?

Common mismatches to check for:
1. Description says "import path change" but when condition checks for component usage
2. Description mentions specific component but when condition is too broad
3. Description is generic but when condition is very specific
4. Description and when condition target different things entirely

Respond with EXACTLY this format:
ALIGNED: yes/no
REASON: <brief explanation>
SUGGESTION: <suggested fix if not aligned, or 'none' if aligned>

Example responses:
ALIGNED: no
REASON: Description says "import path change" but when condition detects EmptyStateHeader component usage
SUGGESTION: Change description to "EmptyStateHeader component usage" or change when condition to detect import paths

ALIGNED: yes
REASON: Description accurately describes the button prop change that the pattern detects
SUGGESTION: none
"""

        try:
            result = self.llm.generate(prompt)
            response = result.get("response", "")

            # Parse response
            aligned = 'yes' in response.split('\n')[0].lower()
            reason_match = re.search(r'REASON:\s*(.+)', response, re.IGNORECASE)
            suggestion_match = re.search(r'SUGGESTION:\s*(.+)', response, re.IGNORECASE | re.DOTALL)

            reason = reason_match.group(1).strip() if reason_match else "Unknown"
            suggestion = suggestion_match.group(1).strip() if suggestion_match else ""

            if not aligned:
                self.issues.append(
                    f"{rule_id}: Description/pattern mismatch - {reason}\n"
                    f"    Suggestion: {suggestion}"
                )
            else:
                print(f"    ✓ Description aligns with pattern")

        except Exception as e:
            self.warnings.append(f"{rule_id}: Semantic validation failed: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate Konveyor analyzer rules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic syntactic validation (fast, free)
  python scripts/validate_rules.py --rules examples/output/spring-boot/rules.yaml

  # Deep semantic validation (slower, costs API calls)
  python scripts/validate_rules.py --rules examples/output/spring-boot/rules.yaml --semantic

  # Validate all rulesets in a directory
  python scripts/validate_rules.py --rules examples/output/patternfly-v6/ --semantic
        """
    )

    parser.add_argument(
        '--rules',
        type=Path,
        required=True,
        help='Path to rule YAML file or directory containing rule files'
    )

    parser.add_argument(
        '--semantic',
        action='store_true',
        help='Enable LLM-based semantic validation (costs API calls)'
    )

    parser.add_argument(
        '--provider',
        default='anthropic',
        choices=['openai', 'anthropic', 'google'],
        help='LLM provider for semantic validation (default: anthropic)'
    )

    args = parser.parse_args()

    # Find rule files
    rules_path = args.rules
    if rules_path.is_file():
        rule_files = [rules_path]
    elif rules_path.is_dir():
        rule_files = list(rules_path.glob('*.yaml'))
    else:
        print(f"Error: {rules_path} not found")
        return 1

    # Create validator
    validator = RuleValidator(
        use_semantic=args.semantic,
        llm_provider=args.provider
    )

    # Validate all files
    all_valid = True
    for rule_file in rule_files:
        result = validator.validate_ruleset(rule_file)
        if not result['valid']:
            all_valid = False

    # Exit code
    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
