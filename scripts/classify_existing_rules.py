#!/usr/bin/env python3
"""
Classify migration complexity for existing Konveyor analyzer rulesets.

This script analyzes existing Konveyor analyzer rules and adds migration_complexity
classifications based on pattern analysis of the rule's description, message, when
conditions, and effort scores.

Usage:
    # Dry run (preview classifications)
    python scripts/classify_existing_rules.py \
        --ruleset /path/to/ruleset.yaml \
        --dry-run

    # Apply classifications
    python scripts/classify_existing_rules.py \
        --ruleset /path/to/ruleset.yaml

    # Batch process multiple rulesets
    python scripts/classify_existing_rules.py \
        --ruleset /path/to/rulesets/quarkus/*.yaml

    # With verbose output
    python scripts/classify_existing_rules.py \
        --ruleset /path/to/ruleset.yaml \
        --verbose
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_generator.schema import AnalyzerRule


class RulesetComplexityClassifier:
    """Classify migration complexity of existing Konveyor analyzer rules."""

    # Complexity indicators based on pattern analysis
    # These patterns are matched against rule description, message, and when conditions

    TRIVIAL_PATTERNS = [
        r'javax\.',  # javax to jakarta namespace changes
        r'package.*rename',  # Simple package renaming
        r'namespace.*change',  # Namespace changes
        r'import.*replacement',  # Import statement replacements
        r'simple.*name.*change',  # Simple naming changes
    ]

    LOW_PATTERNS = [
        r'@Stateless.*@ApplicationScoped',  # Simple annotation swaps
        r'@Singleton',
        r'simple.*annotation',
        r'straightforward.*replacement',
        r'@Inject.*@Autowired',
        r'@WebServlet.*@Path',
        r'CDI.*bean',
    ]

    MEDIUM_PATTERNS = [
        r'@MessageDriven',  # JMS to Reactive Messaging
        r'reactive',
        r'@ConfigProperty',
        r'configuration.*migration',
        r'JMS.*Reactive',
        r'@Transactional',
        r'messaging.*pattern',
        r'context.*understanding',
    ]

    HIGH_PATTERNS = [
        r'security',  # Security-related changes
        r'authentication',
        r'authorization',
        r'architectural.*change',
        r'Spring Security.*Quarkus',
        r'@EnableWebSecurity',
        r'SecurityConfig',
        r'WebSecurityConfigurerAdapter',
        r'complex.*migration',
    ]

    EXPERT_PATTERNS = [
        r'custom.*realm',  # Custom security implementations
        r'SecurityDomain',
        r'performance.*critical',
        r'distributed.*transaction',
        r'expert.*review',
        r'cluster',
        r'custom.*implementation',
        r'internal.*API',
        r'advanced.*configuration',
    ]

    def __init__(self, verbose: bool = False):
        """
        Initialize classifier.

        Args:
            verbose: If True, print detailed classification reasoning
        """
        self.verbose = verbose

    def classify_rule(self, rule: Dict[str, Any]) -> str:
        """
        Classify a single rule's migration complexity.

        Algorithm:
        1. Gather all text from rule (description, message, when conditions)
        2. Count pattern matches for each complexity level
        3. Analyze when condition complexity (logical operators, multiple providers)
        4. Consider effort score as additional signal
        5. Return highest matching complexity level

        Args:
            rule: Rule dictionary from YAML

        Returns:
            Complexity level: trivial, low, medium, high, or expert
        """
        # Gather text to analyze
        text_parts = [
            rule.get('description', ''),
            rule.get('message', ''),
            str(rule.get('when', '')),
            rule.get('ruleID', ''),
        ]

        combined_text = '\n'.join(str(p) for p in text_parts)

        # Count pattern matches
        expert_score = self._match_patterns(combined_text, self.EXPERT_PATTERNS)
        high_score = self._match_patterns(combined_text, self.HIGH_PATTERNS)
        medium_score = self._match_patterns(combined_text, self.MEDIUM_PATTERNS)
        low_score = self._match_patterns(combined_text, self.LOW_PATTERNS)
        trivial_score = self._match_patterns(combined_text, self.TRIVIAL_PATTERNS)

        # Analyze when condition complexity
        when_complexity = self._analyze_when_condition(rule.get('when', {}))

        # Analyze effort score (1 - 10 scale)
        effort = rule.get('effort', 3)

        # Decision logic (cascading from highest to lowest complexity)
        if expert_score > 0:
            complexity = 'expert'
            reason = f"Expert patterns matched: {expert_score}"
        elif high_score > 0 or effort >= 7 or when_complexity == 'high':
            complexity = 'high'
            reason = f"High patterns: {high_score}, effort: {effort}, when: {when_complexity}"
        elif medium_score > 1 or effort >= 4:
            complexity = 'medium'
            reason = f"Medium patterns: {medium_score}, effort: {effort}"
        elif low_score > 0 or effort <= 2:
            complexity = 'low'
            reason = f"Low patterns: {low_score}, effort: {effort}"
        elif trivial_score > 0 and self._is_simple_pattern_replacement(combined_text):
            complexity = 'trivial'
            reason = f"Trivial patterns: {trivial_score}, simple replacement detected"
        else:
            # Conservative default
            complexity = 'low'
            reason = "Default (no strong signals)"

        if self.verbose:
            print(f"\n  Rule: {rule.get('ruleID', 'unknown')}")
            print(
                f"    Scores: Expert={expert_score}, High={high_score}, "
                f"Medium={medium_score}, Low={low_score}, Trivial={trivial_score}"
            )
            print(f"    Effort: {effort}, When complexity: {when_complexity}")
            print(f"    → Classification: {complexity} ({reason})")

        return complexity

    def _match_patterns(self, text: str, patterns: List[str]) -> int:
        """
        Count how many patterns match in the text.

        Args:
            text: Text to search
            patterns: List of regex patterns

        Returns:
            Number of matched patterns
        """
        count = 0
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                count += 1
        return count

    def _analyze_when_condition(self, when: Dict[str, Any]) -> str:
        """
        Analyze complexity of when condition structure.

        Complex when conditions indicate harder migrations:
        - Logical operators (and, or, not)
        - Multiple providers
        - XPath expressions
        - Advanced regex patterns

        Args:
            when: When condition dictionary

        Returns:
            Complexity level: low, medium, or high
        """
        # Check for complex logical operators
        if 'and' in when or 'or' in when or 'not' in when:
            return 'medium'

        # Check for multiple providers (combo rules)
        providers = [k for k in when.keys() if '.' in k]
        if len(providers) > 1:
            return 'medium'

        # Check for complex patterns (XPath, regex with lookaheads, etc.)
        when_str = str(when)
        if 'xpath' in when_str.lower():
            return 'high'

        # Check for advanced regex patterns
        if re.search(r'\(\?[=!<]', when_str):  # Lookaheads/lookbehinds
            return 'high'

        return 'low'

    def _is_simple_pattern_replacement(self, text: str) -> bool:
        """
        Check if this is a simple find/replace pattern.

        Indicators of trivial complexity:
        - javax -> jakarta patterns
        - Simple import/package changes
        - Direct string replacements

        Args:
            text: Text to analyze

        Returns:
            True if simple pattern replacement detected
        """
        # Look for javax -> jakarta patterns
        if 'javax' in text.lower() and 'jakarta' in text.lower():
            return True

        # Look for simple import/package changes
        if re.search(r'import.*->.*import', text, re.IGNORECASE):
            return True

        # Look for direct replacement language
        if re.search(r'replace\s+\S+\s+with\s+\S+', text, re.IGNORECASE):
            # Check if the before/after are simple tokens (not complex descriptions)
            if not re.search(
                r'(configuration|security|transaction|architecture)', text, re.IGNORECASE
            ):
                return True

        return False

    def classify_ruleset(self, ruleset_path: Path, dry_run: bool = False) -> Dict[str, Any]:
        """
        Classify all rules in a ruleset file.

        Args:
            ruleset_path: Path to Konveyor ruleset YAML file
            dry_run: If True, show classifications without writing changes

        Returns:
            Statistics dictionary with counts and changes
        """
        print(f"Classifying ruleset: {ruleset_path}")
        print(f"{'=' * 80}\n")

        # Load ruleset
        with open(ruleset_path, 'r') as f:
            data = yaml.safe_load(f)

        # Handle both formats:
        # 1. List of rules: [rule1, rule2, ...]
        # 2. Dict with 'rules' key: {name: "...", rules: [...]}
        if isinstance(data, list):
            rules = data
            is_list_format = True
        elif isinstance(data, dict) and 'rules' in data:
            rules = data['rules']
            is_list_format = False
        else:
            print("Error: Unrecognized ruleset format")
            print("Expected: list of rules OR dict with 'rules' key")
            return {}

        # Track statistics
        stats = {
            'trivial': 0,
            'low': 0,
            'medium': 0,
            'high': 0,
            'expert': 0,
        }

        changes = []

        # Classify each rule
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict):
                print(f"Warning: Skipping invalid rule at index {i}")
                continue

            complexity = self.classify_rule(rule)
            stats[complexity] += 1

            # Track change
            old_complexity = rule.get('migration_complexity')
            if old_complexity != complexity:
                changes.append(
                    {
                        'rule_id': rule.get('ruleID', f'rule_{i}'),
                        'old': old_complexity or 'None',
                        'new': complexity,
                    }
                )

                # Update in memory
                rule['migration_complexity'] = complexity
                print(f"✓ {rule.get('ruleID', f'rule_{i}')}: {complexity}")
            else:
                print(f"  {rule.get('ruleID', f'rule_{i}')}: {complexity} (unchanged)")

        # Print statistics
        print(f"\n{'=' * 80}")
        print("Classification Summary:")
        print(
            f"  TRIVIAL: {stats['trivial']:3d} rules "
            f"(95%+ AI success - namespace changes, mechanical fixes)"
        )
        print(f"  LOW:     {stats['low']:3d} rules (80%+ AI success - simple API equivalents)")
        print(
            f"  MEDIUM:  {stats['medium']:3d} rules "
            f"(60%+ AI success - requires context understanding)"
        )
        print(f"  HIGH:    {stats['high']:3d} rules (30 - 50% AI success - architectural changes)")
        print(
            f"  EXPERT:  {stats['expert']:3d} rules (<30% AI success - likely needs human review)"
        )
        print(f"\nTotal rules: {sum(stats.values())}")
        print(f"Total changes: {len(changes)}")

        if not dry_run and changes:
            # Write back to file
            print(f"\nUpdating {ruleset_path}...")
            with open(ruleset_path, 'w') as f:
                # Preserve format (list vs dict)
                output_data = data if not is_list_format else rules
                yaml.dump(
                    output_data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    width=120,
                )
            print(f"✓ Updated {ruleset_path}")
        elif dry_run:
            print("\n(Dry run - no changes written)")

        return {'stats': stats, 'changes': changes}


def main():
    parser = argparse.ArgumentParser(
        description="Classify migration complexity for existing Konveyor analyzer rulesets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview classifications (dry run)
  python scripts/classify_existing_rules.py \\
      --ruleset examples/output/spring-boot/migration-rules.yaml \\
      --dry-run

  # Apply classifications
  python scripts/classify_existing_rules.py \\
      --ruleset examples/output/spring-boot/migration-rules.yaml

  # Batch process with verbose output
  for file in /path/to/rulesets/**/*.yaml; do
    python scripts/classify_existing_rules.py --ruleset "$file" --verbose
  done
        """,
    )

    parser.add_argument(
        '--ruleset', type=Path, required=True, help='Path to Konveyor ruleset YAML file'
    )

    parser.add_argument(
        '--dry-run', action='store_true', help='Show classifications without updating file'
    )

    parser.add_argument(
        '--verbose', '-v', action='store_true', help='Show detailed classification reasoning'
    )

    args = parser.parse_args()

    if not args.ruleset.exists():
        print(f"Error: File not found: {args.ruleset}")
        sys.exit(1)

    classifier = RulesetComplexityClassifier(verbose=args.verbose)
    result = classifier.classify_ruleset(args.ruleset, dry_run=args.dry_run)

    # Exit with success if we processed rules
    if result and result.get('stats'):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
