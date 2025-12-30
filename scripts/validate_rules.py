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

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_generator.llm import get_llm_provider
from rule_generator.security import is_safe_path


class RuleValidator:
    """Validates Konveyor analyzer rules for common issues."""

    def __init__(
        self, use_semantic: bool = False, llm_provider: str = "anthropic", auto_fix: bool = False
    ):
        """
        Initialize validator.

        Args:
            use_semantic: Enable LLM-based semantic validation (costs API calls)
            llm_provider: LLM provider to use for semantic validation
            auto_fix: Automatically fix validation errors when possible
        """
        self.use_semantic = use_semantic
        self.auto_fix = auto_fix
        self.llm = None

        if use_semantic:
            self.llm = get_llm_provider(llm_provider)

        self.issues = []
        self.warnings = []
        self.fixes_applied = []

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
            return {'valid': False, 'issues': ['Unrecognized ruleset format']}

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
            self._validate_pattern_matches_example(rule, rule_id)

            # Semantic validation (optional, uses LLM)
            if self.use_semantic:
                self._validate_description_pattern_alignment(rule, rule_id)

        # Print summary
        print("\n" + "=" * 80)
        print("Validation Summary:")
        print(f"  Fixes:    {len(self.fixes_applied)}")
        print(f"  Issues:   {len(self.issues)}")
        print(f"  Warnings: {len(self.warnings)}")

        if self.fixes_applied:
            print("\n✅ Fixes applied:")
            for fix in self.fixes_applied:
                print(f"  - {fix}")

        if self.issues:
            print("\n❌ Issues found:")
            for issue in self.issues:
                print(f"  - {issue}")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.issues and not self.warnings and not self.fixes_applied:
            print("\n✅ All rules validated successfully!")

        # Save fixed rules if auto-fix is enabled and fixes were applied
        if self.auto_fix and self.fixes_applied:
            self._save_fixed_rules(ruleset_path, data)
            print(f"\n💾 Saved {len(self.fixes_applied)} fixes to {ruleset_path}")

        return {
            'valid': len(self.issues) == 0,
            'issues': self.issues,
            'warnings': self.warnings,
            'fixes': self.fixes_applied,
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
                    self.warnings.append(
                        f"{rule_id}: Very short pattern '{pattern}' may cause false positives"
                    )

    def _validate_effort_score(self, rule: Dict, rule_id: str):
        """Validate effort score is in valid range."""
        effort = rule.get('effort')

        if effort is not None:
            if not isinstance(effort, int):
                self.issues.append(f"{rule_id}: Effort must be an integer, got {type(effort)}")
            elif effort < 1 or effort > 10:
                self.issues.append(f"{rule_id}: Effort must be 1 - 10, got {effort}")

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
                        f"{rule_id}: Description mentions EmptyStateHeader "
                        "but pattern doesn't check for it"
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

    def _validate_pattern_matches_example(self, rule: Dict, rule_id: str):
        """Check if pattern actually matches example code from 'Before:' section in message."""
        when = rule.get('when', {})
        message = rule.get('message', '')

        # Only validate builtin.filecontent patterns
        if 'builtin.filecontent' not in when:
            return

        pattern = when['builtin.filecontent'].get('pattern', '')
        if not pattern:
            return

        # Extract code from "Before:" section
        # Handle both actual newlines and literal \n in messages
        before_match = re.search(
            r'Before:(?:\\n|\n)```(?:\w*)?(?:\\n|\n)(.*?)(?:\\n|\n)```', message, re.DOTALL
        )
        if not before_match:
            return  # No example code found, skip validation

        example_code = before_match.group(1).strip()

        # Replace literal \n with actual newlines if present
        if '\\n' in example_code:
            example_code = example_code.replace('\\n', '\n')

        # Test if pattern matches the example code
        try:
            # Test line-by-line since builtin.filecontent matches per line
            matches = False
            for line in example_code.split('\n'):
                if re.search(pattern, line):
                    matches = True
                    break

            if not matches:
                # Pattern doesn't match - try to auto-fix if enabled
                if self.auto_fix:
                    fixed_pattern = self._auto_fix_pattern(rule, rule_id, pattern, example_code)
                    if fixed_pattern:
                        # Update the rule with the fixed pattern
                        when['builtin.filecontent']['pattern'] = fixed_pattern
                        self.fixes_applied.append(
                            f"{rule_id}: Fixed pattern from '{pattern}' to '{fixed_pattern}'"
                        )
                        return  # Skip adding to issues since we fixed it

                # Not fixed or auto-fix disabled - report issue
                self.issues.append(
                    f"{rule_id}: Pattern '{pattern}' does NOT match example code "
                    "from 'Before:' section"
                )
                # Show first line of example for context
                first_line = example_code.split('\n')[0][:80]
                self.issues.append(f"  Example starts with: {first_line}...")
        except re.error as e:
            self.warnings.append(f"{rule_id}: Invalid regex pattern '{pattern}': {e}")

    def _auto_fix_pattern(
        self, rule: Dict, rule_id: str, original_pattern: str, example_code: str
    ) -> str:
        """
        Attempt to automatically fix a pattern that doesn't match its example.

        Args:
            rule: The rule being validated
            rule_id: Rule identifier
            original_pattern: The pattern that doesn't match
            example_code: The example code it should match

        Returns:
            Fixed pattern string, or None if unable to fix
        """
        description = rule.get('description', '').lower()

        # Strategy 1: Extract key identifier from description
        # Look for patterns like "ReactDOM.render", "interface", "hydrate", etc.
        key_terms = []

        # Common patterns to look for
        if 'reactdom.render' in description or 'render(' in description:
            key_terms.append('render\\(')
        if 'interface' in description:
            key_terms.append('interface\\s+\\w+')
        if 'hydrate' in description:
            key_terms.append('hydrate\\(')
        if 'unmount' in description:
            key_terms.append('unmount')

        # Strategy 2: Extract from example code
        # Find the most distinctive line (longest, or contains keywords)
        lines = example_code.split('\n')
        distinctive_lines = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('/*'):
                continue  # Skip comments
            if len(line) > 10:  # Skip very short lines
                distinctive_lines.append(line)

        # Try key terms first
        for term in key_terms:
            try:
                # Test if this term matches any line
                for line in lines:
                    if re.search(term, line):
                        # Found a match! Use this as the pattern
                        return term
            except re.error:
                continue

        # Strategy 3: Find the actual content mentioned in description
        # Extract words from description that might be code identifiers
        code_words = re.findall(r'\b[A-Z][a-zA-Z]+\b|\b\w+\(\)', description)
        for word in code_words:
            # Escape special regex chars and try as pattern
            escaped = re.escape(word)
            try:
                for line in lines:
                    if re.search(escaped, line):
                        return escaped
            except re.error:
                continue

        # Strategy 4: Use the first distinctive line as a simple substring match
        if distinctive_lines:
            first_distinctive = distinctive_lines[0]
            # Extract the main identifier (function call, class name, etc.)
            # Match: word followed by ( or word at start of line
            match = re.search(r'\b(\w+)\s*\(', first_distinctive)
            if match:
                identifier = match.group(1)
                pattern = f'{identifier}\\('
                try:
                    for line in lines:
                        if re.search(pattern, line):
                            return pattern
                except re.error:
                    pass

        # Strategy 5: Fix overly strict patterns (missing optional semicolons, etc.)
        # If the pattern ends with $ (end-of-line) but example has trailing punctuation
        if original_pattern.endswith('$'):
            # Check if example code has trailing semicolons
            has_semicolons = any(line.rstrip().endswith(';') for line in lines if line.strip())

            if has_semicolons:
                # Try adding optional semicolon before $
                # First, check what comes before the $
                pattern_without_anchor = original_pattern[:-1]  # Remove $

                # If pattern ends with a quote (like ['"] or ['"]), add optional semicolon
                if pattern_without_anchor.endswith(r"['\"]") or pattern_without_anchor.endswith(
                    r'["\']'
                ):
                    fixed_pattern = pattern_without_anchor + ';?$'
                elif pattern_without_anchor.endswith('"') or pattern_without_anchor.endswith("'"):
                    fixed_pattern = pattern_without_anchor + ';?$'
                else:
                    # Generic: just add optional semicolon
                    fixed_pattern = pattern_without_anchor + ';?$'

                # Test if this fixed pattern matches
                try:
                    for line in lines:
                        if re.search(fixed_pattern, line):
                            return fixed_pattern
                except re.error:
                    pass

        # Strategy 6: Fix import statement patterns
        # Import statements commonly have variations that should be handled
        if 'import' in original_pattern:
            # If pattern is for imports, try variations
            for line in lines:
                line = line.strip()
                if not line.startswith('import'):
                    continue

                # Try to match the line with a more flexible pattern
                # Extract what's being imported and from where
                import_match = re.search(
                    r'import\s+(?:{?\s*)?(\w+)(?:\s*}?)?\s+from\s+[\'"]([^\'"]+)[\'"]', line
                )
                if import_match:
                    imported = import_match.group(1)
                    source = import_match.group(2)

                    # Check if this matches what the description mentions
                    if imported.lower() in description or source.lower() in description:
                        # Build a flexible import pattern
                        # Allow optional braces, whitespace, and semicolon
                        flexible_pattern = (
                            r'import\s+[{\s]*[\w\s,]*'
                            + re.escape(imported)
                            + r'[\w\s,]*[}\s]*\s+from\s+[\'"]{}'
                            + r'[\'"];?$'
                        ).format(re.escape(source))

                        try:
                            if re.search(flexible_pattern, line):
                                return flexible_pattern
                        except re.error:
                            pass

        # Strategy 7: Try relaxing strict whitespace requirements
        # If pattern has \s+ or \s*, try making them more flexible
        if r'\s' in original_pattern and original_pattern.endswith('$'):
            # Remove the $ anchor and add optional trailing content
            pattern_without_anchor = original_pattern[:-1]
            relaxed_pattern = pattern_without_anchor + r'\s*;?\s*$'

            try:
                for line in lines:
                    if re.search(relaxed_pattern, line):
                        return relaxed_pattern
            except re.error:
                pass

        # Unable to auto-fix
        return None

    def _save_fixed_rules(self, ruleset_path: Path, data: Any):
        """Save the fixed rules back to the YAML file."""
        try:
            with open(ruleset_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        except Exception as e:
            print(f"⚠️  Warning: Could not save fixes: {e}")

    def _validate_description_pattern_alignment(self, rule: Dict, rule_id: str):
        """Use LLM to check if description matches what the pattern actually detects."""
        if not self.llm:
            return

        description = rule.get('description', '')
        when = rule.get('when', {})
        message = rule.get('message', '')

        prompt = """You are validating a Konveyor analyzer rule for consistency.

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
REASON: Description says "import path change" but when condition detects EmptyStateHeader
        component usage
SUGGESTION: Change description to "EmptyStateHeader component usage" or change when
            condition to detect import paths

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
                print("    ✓ Description aligns with pattern")

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
        """,
    )

    parser.add_argument(
        '--rules',
        type=Path,
        required=True,
        help='Path to rule YAML file or directory containing rule files',
    )

    parser.add_argument(
        '--semantic',
        action='store_true',
        help='Enable LLM-based semantic validation (costs API calls)',
    )

    parser.add_argument(
        '--provider',
        default='anthropic',
        choices=['openai', 'anthropic', 'google'],
        help='LLM provider for semantic validation (default: anthropic)',
    )

    parser.add_argument(
        '--auto-fix',
        action='store_true',
        help='Automatically fix validation errors when possible (modifies rule files)',
    )

    args = parser.parse_args()

    # Validate path for security (check for path traversal attacks)
    if not is_safe_path(args.rules):
        print(f"Error: Rules path '{args.rules}' contains suspicious patterns", file=sys.stderr)
        return 1

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
        use_semantic=args.semantic, llm_provider=args.provider, auto_fix=args.auto_fix
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
