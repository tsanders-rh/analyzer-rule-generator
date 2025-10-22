"""
Rule generation - Convert migration patterns to Konveyor analyzer rule format.

Generates analyzer rules with:
- Rule ID (auto-generated)
- When conditions (pattern matching)
- Effort scoring
- Messages with migration guidance
- Links to documentation
- Multiple file output grouped by concern
"""
from typing import List, Optional, Dict, Any
from collections import defaultdict

from .schema import AnalyzerRule, MigrationPattern, Category, Link, LocationType


class AnalyzerRuleGenerator:
    """Generate Konveyor analyzer rules from migration patterns."""

    def __init__(
        self,
        source_framework: Optional[str] = None,
        target_framework: Optional[str] = None,
        rule_file_name: Optional[str] = None
    ):
        """
        Initialize rule generator.

        Args:
            source_framework: Source framework name (e.g., "spring-boot")
            target_framework: Target framework name (e.g., "quarkus")
            rule_file_name: Base name of the rule file (without .yaml extension)
        """
        self.source_framework = source_framework
        self.target_framework = target_framework
        self.rule_file_name = rule_file_name
        self._rule_counter = 0

    def generate_rules(self, patterns: List[MigrationPattern]) -> List[AnalyzerRule]:
        """
        Generate analyzer rules from extracted patterns.

        Args:
            patterns: List of migration patterns

        Returns:
            List of AnalyzerRule objects
        """
        rules = []
        for pattern in patterns:
            rule = self._pattern_to_rule(pattern)
            if rule:
                rules.append(rule)

        return rules

    def generate_rules_by_concern(self, patterns: List[MigrationPattern]) -> Dict[str, List[AnalyzerRule]]:
        """
        Generate analyzer rules grouped by concern.

        Args:
            patterns: List of migration patterns

        Returns:
            Dictionary mapping concern names to lists of AnalyzerRule objects
        """
        # Group patterns by concern
        patterns_by_concern = defaultdict(list)
        for pattern in patterns:
            concern = pattern.concern or "general"
            patterns_by_concern[concern].append(pattern)

        # Generate rules for each concern
        rules_by_concern = {}
        for concern, concern_patterns in patterns_by_concern.items():
            # Reset rule counter for each concern
            self._rule_counter = 0

            rules = []
            for pattern in concern_patterns:
                rule = self._pattern_to_rule(pattern)
                if rule:
                    rules.append(rule)

            if rules:
                rules_by_concern[concern] = rules

        return rules_by_concern

    def _pattern_to_rule(self, pattern: MigrationPattern) -> Optional[AnalyzerRule]:
        """
        Convert a migration pattern to an analyzer rule.

        Args:
            pattern: Migration pattern

        Returns:
            AnalyzerRule object or None if pattern cannot be converted
        """
        # Skip if we don't have enough info to create a when condition
        if not pattern.source_fqn and not pattern.source_pattern:
            print(f"Warning: Skipping pattern without FQN or pattern: {pattern.rationale}")
            return None

        # Generate rule ID
        rule_id = self._create_rule_id()

        # Build when condition
        when_condition = self._build_when_condition(pattern)

        if not when_condition:
            print(f"Warning: Could not build when condition for: {pattern.rationale}")
            return None

        # Map complexity to effort (1-10 scale)
        effort = self._map_complexity_to_effort(pattern.complexity)

        # Determine category
        category = self._determine_category(pattern)

        # Build labels
        labels = self._build_labels()

        # Build message
        message = self._build_message(pattern)

        # Build links
        links = self._build_links(pattern)

        # Create description
        if pattern.target_pattern:
            description = f"{pattern.source_pattern} should be replaced with {pattern.target_pattern}"
        else:
            description = f"{pattern.source_pattern} usage detected (removed API)"

        # Create rule
        rule = AnalyzerRule(
            ruleID=rule_id,
            description=description,
            effort=effort,
            category=category,
            labels=labels,
            when=when_condition,
            message=message,
            links=links if links else None,
            customVariables=[],
            tag=None
        )

        return rule

    def _create_rule_id(self, concern: Optional[str] = None) -> str:
        """
        Generate unique rule ID following Konveyor convention.

        Convention from https://github.com/konveyor/rulesets/blob/main/CONTRIBUTING.md:
        - Must contain the rule file name
        - Use 5-digit numbers
        - Increment by 10 each time

        Args:
            concern: Optional concern/topic for multi-file output (will be used in rule ID)

        Returns:
            Rule ID (e.g., "patternfly-v5-to-patternfly-v6-00000")
        """
        # Increment counter by 10 following Konveyor convention
        rule_number = self._rule_counter * 10
        self._rule_counter += 1

        if self.rule_file_name:
            prefix = self.rule_file_name
        elif self.source_framework and self.target_framework:
            prefix = f"{self.source_framework}-to-{self.target_framework}"
        else:
            prefix = "migration"

        # Add concern suffix if provided (for multi-file output)
        # Note: When using multi-file output, the concern is already in the filename,
        # so we don't include it in the rule ID to avoid duplication
        # The rule ID will match the filename without concern

        # Format: prefix-00000 (5 digits, incrementing by 10)
        rule_id = f"{prefix}-{rule_number:05d}"

        return rule_id

    def _build_when_condition(self, pattern: MigrationPattern) -> Optional[Dict[str, Any]]:
        """
        Build when condition for pattern matching.

        Args:
            pattern: Migration pattern

        Returns:
            When condition dict or None if cannot be built
        """
        if not pattern.source_fqn:
            # If no FQN, we can't create a proper when condition for static analysis
            return None

        # Check provider type
        provider = pattern.provider_type or "java"  # Default to java for backward compatibility

        if provider == "builtin":
            # Build builtin.filecontent condition
            condition = {
                "builtin.filecontent": {
                    "pattern": pattern.source_fqn  # For builtin, source_fqn contains regex
                }
            }

            # Add file pattern if specified
            if pattern.file_pattern:
                condition["builtin.filecontent"]["filePattern"] = pattern.file_pattern

            return condition

        elif provider == "typescript":
            # Check if pattern requires semantic analysis
            if self._requires_semantic_analysis(pattern):
                # Use typescript.referenced for semantic analysis
                return {
                    "typescript.referenced": {
                        "pattern": pattern.source_fqn or pattern.source_pattern,
                        "location": self._infer_location_context(pattern)
                    }
                }
            else:
                # Fall back to file content matching for simple text patterns
                return {
                    "builtin.filecontent": {
                        "pattern": pattern.source_fqn or pattern.source_pattern,
                        "filePattern": pattern.file_pattern or self._get_file_pattern(pattern)
                    }
                }

        else:  # Java provider
            # Determine location (default to TYPE if not specified)
            location = pattern.location_type or LocationType.TYPE

            # Build java.referenced condition
            java_referenced = {
                "pattern": pattern.source_fqn,
                "location": location.value
            }

            # If there are alternative FQNs (e.g., javax vs jakarta), use OR condition
            if pattern.alternative_fqns and len(pattern.alternative_fqns) > 0:
                conditions = [
                    {"java.referenced": {
                        "pattern": pattern.source_fqn,
                        "location": location.value
                    }}
                ]

                for alt_fqn in pattern.alternative_fqns:
                    conditions.append({
                        "java.referenced": {
                            "pattern": alt_fqn,
                            "location": location.value
                        }
                    })

                return {"or": conditions}
            else:
                return {"java.referenced": java_referenced}

    def _map_complexity_to_effort(self, complexity: str) -> int:
        """
        Map migration complexity to effort score (1-10).

        Args:
            complexity: Complexity level (TRIVIAL, LOW, MEDIUM, HIGH, EXPERT)

        Returns:
            Effort score (1-10)
        """
        complexity = complexity.upper()

        mapping = {
            'TRIVIAL': 1,
            'LOW': 3,
            'MEDIUM': 5,
            'HIGH': 7,
            'EXPERT': 10
        }

        return mapping.get(complexity, 5)

    def _determine_category(self, pattern: MigrationPattern) -> Category:
        """
        Determine rule category based on complexity and pattern info.

        Args:
            pattern: Migration pattern

        Returns:
            Category enum value
        """
        complexity = pattern.complexity.upper()

        # High complexity changes are usually mandatory (require action)
        if complexity in ['HIGH', 'EXPERT']:
            return Category.MANDATORY

        # Trivial changes are usually mandatory (easy wins)
        if complexity == 'TRIVIAL':
            return Category.MANDATORY

        # API removals should be mandatory regardless of complexity
        # Look for keywords in rationale that indicate removal/deprecation
        rationale_lower = pattern.rationale.lower()
        removal_keywords = ['removed', 'removal', 'deprecated for removal', 'no longer available', 'deleted']
        if any(keyword in rationale_lower for keyword in removal_keywords):
            return Category.MANDATORY

        # Property/configuration renames and updates should be mandatory (mechanical changes)
        # Look for patterns that indicate simple property migrations
        property_keywords = [
            'properties have been updated',
            'properties have been renamed',
            'property has been renamed',
            'property has been updated',
            'should be replaced with',
            'now use',
            'instead of'
        ]
        if any(keyword in rationale_lower for keyword in property_keywords):
            # Check if this looks like a simple property rename (similar structure)
            if pattern.target_pattern and pattern.source_pattern:
                source_parts = pattern.source_pattern.split('.')
                target_parts = pattern.target_pattern.split('.')
                # If both are dotted properties with similar depth, likely a simple rename
                if len(source_parts) >= 3 and len(target_parts) >= 3:
                    return Category.MANDATORY

        # Everything else is potential (needs evaluation)
        return Category.POTENTIAL

    def _build_labels(self) -> List[str]:
        """
        Build labels for rule.

        Returns:
            List of labels
        """
        labels = []

        if self.source_framework:
            labels.append(f"konveyor.io/source={self.source_framework}")

        if self.target_framework:
            labels.append(f"konveyor.io/target={self.target_framework}")

        return labels

    def _build_message(self, pattern: MigrationPattern) -> str:
        """
        Build migration guidance message.

        Args:
            pattern: Migration pattern

        Returns:
            Message text
        """
        message = f"{pattern.rationale}\n\n"

        if pattern.target_pattern:
            message += f"Replace `{pattern.source_pattern}` with `{pattern.target_pattern}`."
        else:
            message += f"Remove usage of `{pattern.source_pattern}` (API has been removed)."

        if pattern.example_before and pattern.example_after:
            message += f"\n\nBefore:\n```\n{pattern.example_before}\n```\n\n"
            message += f"After:\n```\n{pattern.example_after}\n```"

        return message

    def _requires_semantic_analysis(self, pattern: MigrationPattern) -> bool:
        """
        Determine if pattern needs TypeScript language server semantic analysis.

        Args:
            pattern: Migration pattern

        Returns:
            True if semantic analysis is required, False for simple text matching
        """
        semantic_keywords = [
            'function component',
            'class component',
            'type definition',
            'interface',
            'generic type',
            'implicit return',
            'method',
            'class',
            'inheritance',
            'extends',
            'implements'
        ]

        description = (pattern.rationale or "").lower()
        return any(keyword in description for keyword in semantic_keywords)

    def _infer_location_context(self, pattern: MigrationPattern) -> str:
        """
        Infer AST location context from pattern description for TypeScript provider.

        Args:
            pattern: Migration pattern

        Returns:
            Location context string (e.g., 'FUNCTION_DECLARATION', 'CLASS_DECLARATION')
        """
        description = (pattern.rationale or "").lower()

        context_map = {
            'function': 'FUNCTION_DECLARATION',
            'class': 'CLASS_DECLARATION',
            'method': 'METHOD_DECLARATION',
            'import': 'IMPORT_DECLARATION',
            'variable': 'VARIABLE_DECLARATION',
            'interface': 'INTERFACE_DECLARATION',
            'type': 'TYPE_ALIAS_DECLARATION'
        }

        for keyword, location in context_map.items():
            if keyword in description:
                return location

        return "ANY"

    def _get_file_pattern(self, pattern: MigrationPattern) -> str:
        """
        Get file pattern based on pattern metadata.

        Args:
            pattern: Migration pattern

        Returns:
            File pattern string (e.g., '*.{ts,tsx,js,jsx}')
        """
        # If pattern already has a file_pattern, use it
        if pattern.file_pattern:
            return pattern.file_pattern

        # Default TypeScript/JavaScript file pattern
        return "*.{ts,tsx,js,jsx}"

    def _build_links(self, pattern: MigrationPattern) -> Optional[List[Link]]:
        """
        Build documentation links.

        Args:
            pattern: Migration pattern

        Returns:
            List of Link objects or None
        """
        if not pattern.documentation_url:
            return None

        return [Link(
            url=pattern.documentation_url,
            title=f"{self.target_framework or 'Migration'} Documentation"
        )]
