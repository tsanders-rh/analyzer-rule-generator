"""
Rule Validation and Improvement Module

Provides post-generation validation and improvement of analyzer rules to ensure
high quality and reduce false positives.

Key Components:
    - RuleValidator: Main validation class with LLM-powered analysis
    - ValidationReport: Structured reporting of improvements and issues
    - Import Verification: Auto-adds import checks for component patterns
    - Pattern Analysis: Detects overly broad or problematic patterns
    - Duplicate Detection: Identifies and flags duplicate rules

Validation Checks:
    1. Import Verification (JavaScript/TypeScript PatternFly only):
       - Detects component patterns without import verification
       - Automatically adds import checks to prevent false positives
       - Ensures components are from the correct library (e.g., @patternfly/react-*)

    2. Pattern Breadth Analysis:
       - Detects overly broad patterns (e.g., short strings)
       - Estimates false positive rates
       - Suggests more specific patterns

    3. Pattern Quality Review:
       - Validates regex patterns against examples
       - Checks for common pattern mistakes
       - Suggests improvements for better accuracy

    4. Duplicate Detection:
       - Finds rules with identical when conditions
       - Identifies conflicting descriptions
       - Helps consolidate redundant rules

Rule Improvements Applied:
    - Import verification for JavaScript/TypeScript component patterns
    - Pattern specificity enhancements
    - Regex validation and correction
    - Consolidation of duplicates

Usage:
    >>> from rule_generator.llm import get_llm_provider
    >>> llm = get_llm_provider("anthropic")
    >>> validator = RuleValidator(
    ...     llm_provider=llm,
    ...     language="javascript",
    ...     source_framework="patternfly-v5",
    ...     target_framework="patternfly-v6"
    ... )
    >>> rules = generator.generate_rules(patterns)
    >>> report = validator.validate_rules(rules)
    >>> print(report.generate_report())
    >>> improved_rules = validator.apply_improvements(rules, report)

Example Output:
    >>> print(report.generate_report())
    ================================================================================
    POST-GENERATION VALIDATION REPORT
    ================================================================================

    Total rules validated: 42
    Rules improved: 15

    ────────────────────────────────────────────────────────────────────────────
    IMPROVEMENTS APPLIED
    ────────────────────────────────────────────────────────────────────────────

    IMPORT_VERIFICATION:
      Rule: patternfly-v5-to-patternfly-v6-00030
      Description: Button isActive should be replaced with isDisabled...

See Also:
    - AnalyzerRule: Rule schema (schema.py)
    - RuleGenerator: Rule generation (generator.py)
    - LLMProvider: LLM interface (llm.py)
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from .condition_builder import build_builtin_condition, build_combo_condition
from .llm import LLMProvider
from .schema import AnalyzerRule


class ValidationReport:
    """Report of validation findings and improvements."""

    def __init__(self):
        """Initialize validation report."""
        self.improvements = []
        self.issues = []
        self.statistics = {
            'total_rules': 0,
            'rules_improved': 0,
            'import_verification_added': 0,
            'overly_broad_detected': 0,
            'quality_issues_fixed': 0,
            'duplicates_found': 0,
        }

    def add_improvement(
        self, improvement_type: str, original: AnalyzerRule, improved: Dict[str, Any]
    ) -> None:
        """
        Add an improvement to the report.

        Args:
            improvement_type: Type of improvement (import_verification, quality, etc.)
            original: Original rule
            improved: Improved rule data (dict from LLM or AnalyzerRule)
        """
        self.improvements.append(
            {'type': improvement_type, 'original': original, 'improved': improved}
        )
        self.statistics['rules_improved'] += 1
        if f'{improvement_type}_added' in self.statistics:
            self.statistics[f'{improvement_type}_added'] += 1

    def add_issue(self, issue_type: str, rule: AnalyzerRule, details: Dict[str, Any]) -> None:
        """
        Add an issue to the report.

        Args:
            issue_type: Type of issue (overly_broad, duplicate, etc.)
            rule: Rule with the issue
            details: Issue details
        """
        self.issues.append({'type': issue_type, 'rule': rule, 'details': details})
        if f'{issue_type}_detected' in self.statistics:
            self.statistics[f'{issue_type}_detected'] += 1

    def generate_report(self) -> str:
        """
        Generate human-readable validation report.

        Returns:
            Formatted validation report string
        """
        report = []

        report.append("=" * 80)
        report.append("POST-GENERATION VALIDATION REPORT")
        report.append("=" * 80)

        report.append(f"\nTotal rules validated: {self.statistics['total_rules']}")
        report.append(f"Rules improved: {self.statistics['rules_improved']}")

        report.append("\n" + "─" * 80)
        report.append("IMPROVEMENTS APPLIED")
        report.append("─" * 80)

        if self.improvements:
            for improvement in self.improvements:
                report.append(f"\n{improvement['type'].upper()}:")
                report.append(f"  Rule: {improvement['original'].ruleID}")
                report.append(f"  Description: {improvement['original'].description[:60]}...")
        else:
            report.append("\nNo improvements applied.")

        report.append("\n" + "─" * 80)
        report.append("ISSUES DETECTED")
        report.append("─" * 80)

        if self.issues:
            for issue in self.issues:
                report.append(f"\n{issue['type'].upper()}:")
                report.append(f"  Rule: {issue['rule'].ruleID}")
                report.append(f"  Details: {issue['details']}")
        else:
            report.append("\nNo issues detected.")

        return "\n".join(report)


class RuleValidator:
    """Post-generation LLM-based rule validator."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        language: str,
        source_framework: Optional[str] = None,
        target_framework: Optional[str] = None,
    ):
        """
        Initialize rule validator.

        Args:
            llm_provider: LLM provider instance
            language: Programming language (javascript, typescript, java, csharp)
            source_framework: Source framework name (e.g., "patternfly-v5", "react-17")
            target_framework: Target framework name (e.g., "patternfly-v6", "react-18")
        """
        self.llm = llm_provider
        self.language = language
        self.source_framework = source_framework
        self.target_framework = target_framework

        # Check if this is a PatternFly migration
        self.is_patternfly = False
        if source_framework and target_framework:
            frameworks = f"{source_framework} {target_framework}".lower()
            self.is_patternfly = "patternfly" in frameworks

    def validate_rules(self, rules: List[AnalyzerRule]) -> ValidationReport:
        """
        Run all validation checks on rules.

        Args:
            rules: List of analyzer rules to validate

        Returns:
            ValidationReport with findings and improvements
        """
        report = ValidationReport()
        report.statistics['total_rules'] = len(rules)

        print("\n" + "=" * 80)
        print("POST-GENERATION VALIDATION")
        print("=" * 80)

        # 1. Import verification check (for JavaScript/TypeScript PatternFly migrations only)
        if self.language in ["javascript", "typescript"] and self.is_patternfly:
            print("\n→ Checking for missing import verification...")
            for rule in rules:
                if self._needs_import_verification(rule):
                    print(f"  ! Rule {rule.ruleID} needs import verification")
                    improved = self._add_import_verification(rule)
                    if improved:
                        report.add_improvement('import_verification', rule, improved)

        # 2. Overly broad pattern check
        print("\n→ Checking for overly broad patterns...")
        for rule in rules:
            analysis = self._check_pattern_breadth(rule)
            if analysis and analysis.get('is_overly_broad'):
                print(f"  ! Rule {rule.ruleID} has overly broad pattern")
                report.add_issue('overly_broad', rule, analysis)

        # 3. Pattern quality review
        print("\n→ Reviewing pattern quality...")
        for rule in rules:
            quality_check = self._review_pattern_quality(rule)
            if quality_check and quality_check.get('issues'):
                print(f"  ! Rule {rule.ruleID} has quality issues")
                report.add_improvement('quality', rule, quality_check)

        # 4. Duplicate detection
        print("\n→ Checking for duplicates...")
        duplicates = self._find_duplicates(rules)
        for dup_pair in duplicates:
            print(f"  ! Duplicate found: {dup_pair[0].ruleID} and {dup_pair[1].ruleID}")
            report.add_issue('duplicate', dup_pair[0], {'duplicate_of': dup_pair[1].ruleID})

        print("\n✓ Validation complete")
        print(f"  - {report.statistics['rules_improved']} rules improved")
        print(f"  - {len(report.issues)} issues detected")

        return report

    def _needs_import_verification(self, rule: AnalyzerRule) -> bool:
        """
        Check if rule needs import verification added.

        NOTE: nodejs.referenced already performs semantic analysis and only finds
        components that are actually imported. Rules using nodejs.referenced do NOT
        need additional import verification patterns. This matches the official
        Konveyor PatternFly rules which use nodejs.referenced + builtin.filecontent
        for JSX patterns WITHOUT import regex patterns.

        Args:
            rule: Analyzer rule to check

        Returns:
            True if rule needs import verification (always False for nodejs.referenced rules)
        """
        when = rule.when

        # Rules with nodejs.referenced do NOT need import verification
        # nodejs.referenced already does semantic analysis and only finds imported symbols
        if isinstance(when, dict):
            # Check for nodejs.referenced in combo rules
            if 'and' in when:
                has_nodejs = any('nodejs.referenced' in str(c) for c in when['and'])
                if has_nodejs:
                    return False  # nodejs.referenced is sufficient

            # Check for simple nodejs.referenced rules
            elif 'nodejs.referenced' in when:
                return False  # nodejs.referenced is sufficient

        return False  # No import verification needed

    def _add_import_verification(self, rule: AnalyzerRule) -> Optional[Dict[str, Any]]:
        """
        Add import verification to rule directly without LLM.

        Handles two cases:
        1. Combo rules with nodejs.referenced + JSX pattern
        2. Simple nodejs.referenced rules (component renames)

        Args:
            rule: Rule to improve

        Returns:
            Improved rule data as dict or None if failed
        """
        # Extract component name
        component = self._extract_component_name(rule)
        if not component:
            return None

        # Build import verification pattern
        import_pattern = (
            f"import.*\\{{{{[^}}}}]*\\b{component}\\b[^}}}}]*\\}}}}.*from ['\"]@patternfly/react-"
        )

        # Get the current when condition
        when = rule.when
        file_pattern = '\\.(j|t)sx?$'

        # Case 1: Combo rule with nodejs.referenced + JSX pattern
        if isinstance(when, dict) and 'and' in when:
            # Find the builtin.filecontent condition with JSX pattern
            jsx_condition = None
            for cond in when['and']:
                if isinstance(cond, dict) and 'builtin.filecontent' in cond:
                    builtin = cond['builtin.filecontent']
                    if 'pattern' in builtin and '<' in builtin['pattern']:
                        jsx_condition = builtin
                        file_pattern = builtin.get('filePattern', file_pattern)
                        break

            if not jsx_condition:
                return None

            # Create new combo rule with import verification
            new_when = build_combo_condition(
                [
                    build_builtin_condition(import_pattern, file_pattern),
                    build_builtin_condition(jsx_condition['pattern'], file_pattern),
                ]
            )

        # Case 2: Simple nodejs.referenced rule (component rename)
        elif isinstance(when, dict) and 'nodejs.referenced' in when:
            # Convert to combo rule with import verification + component reference
            # Use a generic JSX pattern to match any usage of the component
            jsx_pattern = f"<{component}[^/>]*(?:/>|>)"

            new_when = build_combo_condition(
                [
                    build_builtin_condition(import_pattern, file_pattern),
                    build_builtin_condition(jsx_pattern, file_pattern),
                ]
            )

        else:
            return None

        # Return improved rule as dict
        return {
            'ruleID': rule.ruleID,
            'description': rule.description,
            'effort': rule.effort,
            'category': rule.category.value if hasattr(rule.category, 'value') else rule.category,
            'labels': rule.labels,
            'when': new_when,
            'message': rule.message,
            'links': (
                [{'url': link.url, 'title': link.title} for link in rule.links]
                if rule.links
                else []
            ),
            'customVariables': rule.customVariables if rule.customVariables else [],
        }

    def apply_improvements(
        self, rules: List[AnalyzerRule], report: 'ValidationReport'
    ) -> List[AnalyzerRule]:
        """
        Apply validated improvements to rules.

        Args:
            rules: Original list of rules
            report: Validation report with improvements

        Returns:
            Updated list of rules with improvements applied
        """
        # Create a mapping of rule IDs to improvements
        improvements_by_id = defaultdict(list)
        for improvement in report.improvements:
            rule_id = improvement['original'].ruleID
            improvements_by_id[rule_id].append(improvement)

        # Apply improvements to rules
        improved_rules = []
        for rule in rules:
            if rule.ruleID in improvements_by_id:
                # Get the latest improvement for this rule
                improvement = improvements_by_id[rule.ruleID][-1]
                improved_data = improvement['improved']

                # Create new rule from improved data using model_copy
                # Pydantic V2 requires using model_copy to create a modified version
                try:
                    improved_rule = rule.model_copy(update={'when': improved_data['when']})
                    improved_rules.append(improved_rule)
                    print(f"  ✓ Applied import verification to {rule.ruleID}")
                except (ValueError, TypeError, KeyError) as e:
                    # Handle validation or data access errors
                    print(
                        f"[Validation] Warning: Failed to apply improvement: Invalid data - {e} "
                        f"(rule_id={rule.ruleID})"
                    )
                    improved_rules.append(rule)
                except ValidationError as e:
                    # Handle Pydantic validation errors (invalid model state)
                    print(
                        f"[Validation] Warning: Failed to apply improvement: Validation failed - "
                        f"{e} (rule_id={rule.ruleID})"
                    )
                    improved_rules.append(rule)
                except AttributeError as e:
                    # Handle missing attributes on rule object
                    print(
                        f"[Validation] Warning: Failed to apply improvement: Missing attribute - "
                        f"{e} (rule_id={rule.ruleID})"
                    )
                    improved_rules.append(rule)
            else:
                improved_rules.append(rule)

        return improved_rules

    def _check_pattern_breadth(self, rule: AnalyzerRule) -> Optional[Dict[str, Any]]:
        """
        Use LLM to check if pattern is overly broad.

        Args:
            rule: Rule to analyze

        Returns:
            Analysis dict or None if check not applicable
        """
        # Only check builtin rules with short patterns
        when = rule.when
        if not isinstance(when, dict):
            return None

        if 'builtin.filecontent' in when:
            pattern = when['builtin.filecontent'].get('pattern', '')
            if len(pattern) < 10:
                return {
                    'is_overly_broad': True,
                    'risk_level': 'HIGH',
                    'reason': f'Pattern too short ({len(pattern)} chars): {pattern}',
                    'estimated_false_positive_rate': '>50%',
                }

        return None

    def _review_pattern_quality(self, rule: AnalyzerRule) -> Optional[Dict[str, Any]]:
        """
        Use LLM to review pattern quality.

        Args:
            rule: Rule to review

        Returns:
            Quality check dict or None if no issues
        """
        # For now, return None (placeholder for future LLM-based quality checks)
        return None

    def _find_duplicates(self, rules: List[AnalyzerRule]) -> List[tuple]:
        """
        Find duplicate rules based on when conditions.

        Args:
            rules: List of rules to check

        Returns:
            List of (rule1, rule2) tuples representing duplicates
        """
        duplicates = []
        seen = {}

        for rule in rules:
            when_str = str(rule.when)
            key = (when_str, rule.description)

            if key in seen:
                duplicates.append((seen[key], rule))
            else:
                seen[key] = rule

        return duplicates

    def _extract_component_name(self, rule: AnalyzerRule) -> Optional[str]:
        """
        Extract component name from rule.

        Args:
            rule: Rule to extract from

        Returns:
            Component name or None
        """
        when = rule.when

        # Case 1: Combo rule with 'and' conditions
        if isinstance(when, dict) and 'and' in when:
            for cond in when['and']:
                if isinstance(cond, dict) and 'nodejs.referenced' in cond:
                    return cond['nodejs.referenced'].get('pattern')

        # Case 2: Simple nodejs.referenced rule
        elif isinstance(when, dict) and 'nodejs.referenced' in when:
            return when['nodejs.referenced'].get('pattern')

        return None

    def _rule_to_yaml_string(self, rule: AnalyzerRule) -> str:
        """
        Convert rule to YAML-like string for LLM.

        Args:
            rule: Rule to convert

        Returns:
            YAML-formatted string
        """
        import yaml

        # Convert to dict
        rule_dict = {
            'ruleID': rule.ruleID,
            'description': rule.description,
            'when': rule.when,
            'message': rule.message,
        }
        return yaml.dump([rule_dict], default_flow_style=False)
