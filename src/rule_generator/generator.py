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

from .schema import AnalyzerRule, MigrationPattern, Category, Link, LocationType, CSharpLocationType


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

        # Build custom variables (for import capture, etc.)
        custom_variables = self._build_custom_variables(pattern)

        # Build message
        message = self._build_message(pattern, has_custom_variables=len(custom_variables) > 0)

        # Build links
        links = self._build_links(pattern)

        # Create description
        description = self._build_description(pattern, has_custom_variables=len(custom_variables) > 0)

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
            customVariables=custom_variables if custom_variables else [],
            tag=None,
            migration_complexity=pattern.complexity
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
        # Check provider type first
        provider = pattern.provider_type or "java"  # Default to java for backward compatibility

        # Handle combo rules (nodejs + builtin OR import + builtin)
        if provider == "combo":
            if not pattern.when_combo:
                print(f"Warning: Combo provider specified but no when_combo config: {pattern.rationale}")
                return None

            # Build combo condition with AND logic
            import_pattern = pattern.when_combo.get("import_pattern")
            nodejs_pattern = pattern.when_combo.get("nodejs_pattern")
            builtin_pattern = pattern.when_combo.get("builtin_pattern")
            file_pattern = pattern.when_combo.get("file_pattern")

            # Validate: Must have builtin_pattern and either import_pattern OR nodejs_pattern
            if not builtin_pattern:
                print(f"Warning: Combo rule missing builtin_pattern: {pattern.rationale}")
                return None

            if not import_pattern and not nodejs_pattern:
                print(f"Warning: Combo rule missing both import_pattern and nodejs_pattern: {pattern.rationale}")
                return None

            conditions = []

            # Add import verification condition if present (preferred over nodejs.referenced)
            if import_pattern:
                import_condition = {
                    "builtin.filecontent": {
                        "pattern": import_pattern
                    }
                }
                if file_pattern:
                    import_condition["builtin.filecontent"]["filePattern"] = file_pattern
                conditions.append(import_condition)

            # Add nodejs.referenced condition if present and no import pattern
            # (for backward compatibility with existing combo rules)
            elif nodejs_pattern:
                conditions.append({
                    "nodejs.referenced": {
                        "pattern": nodejs_pattern
                    }
                })

            # Add main builtin.filecontent condition for JSX pattern
            jsx_condition = {
                "builtin.filecontent": {
                    "pattern": builtin_pattern
                }
            }
            if file_pattern:
                jsx_condition["builtin.filecontent"]["filePattern"] = file_pattern
            conditions.append(jsx_condition)

            return {"and": conditions}

        # Nodejs and csharp providers can use source_pattern as fallback
        # Other providers require source_fqn
        if provider not in ["nodejs", "csharp"] and not pattern.source_fqn:
            # If no FQN, we can't create a proper when condition for static analysis
            return None

        if provider == "builtin":
            # Build builtin.filecontent condition
            regex_pattern = pattern.source_fqn  # For builtin, source_fqn contains regex

            # For import patterns, ensure pattern ends with $ anchor for precise matching
            if self._is_import_pattern(pattern) and not regex_pattern.endswith('$'):
                # Add $ anchor to match end of import statement
                # This prevents false positives from partial matches
                regex_pattern = regex_pattern + '$'

            condition = {
                "builtin.filecontent": {
                    "pattern": regex_pattern
                }
            }

            # Add file pattern if specified
            if pattern.file_pattern:
                condition["builtin.filecontent"]["filePattern"] = pattern.file_pattern

            return condition

        elif provider == "nodejs":
            # Use nodejs.referenced for semantic symbol analysis in JavaScript/TypeScript
            # Note: nodejs.referenced finds symbol references in TypeScript/JavaScript code
            # (functions, classes, variables, types, interfaces, etc.)
            #
            # The nodejs provider now uses import-based search with multiline import support,
            # so we no longer need the builtin.filecontent workaround for React components.

            # Build nodejs.referenced condition
            condition = {
                "nodejs.referenced": {
                    "pattern": pattern.source_fqn or pattern.source_pattern
                }
            }

            return condition

        elif provider == "csharp":
            # Use c-sharp.referenced for semantic symbol analysis in C# code
            # The c-sharp provider finds references to types, methods, fields, etc.

            # Build c-sharp.referenced condition
            condition = {
                "c-sharp.referenced": {
                    "pattern": pattern.source_fqn or pattern.source_pattern
                }
            }

            # Add location if specified (FIELD, CLASS, METHOD, ALL)
            # Note: If location is not specified, defaults to ALL
            if pattern.location_type:
                # Convert enum to string if necessary
                location_str = pattern.location_type.value if hasattr(pattern.location_type, 'value') else str(pattern.location_type)
                condition["c-sharp.referenced"]["location"] = location_str

            return condition

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

    def _is_import_pattern(self, pattern: MigrationPattern) -> bool:
        """
        Determine if pattern is for import statement migration.

        Args:
            pattern: Migration pattern

        Returns:
            True if pattern is for import statements
        """
        # Check if this is a builtin provider pattern (likely imports)
        if pattern.provider_type != "builtin":
            return False

        # Check if source_fqn or source_pattern contains import keywords
        source = pattern.source_fqn or pattern.source_pattern or ""

        # Look for import statement patterns
        if "import" in source.lower():
            return True

        # Check rationale for import-related keywords
        rationale = (pattern.rationale or "").lower()
        if any(keyword in rationale for keyword in ["import", "import statement", "imported from"]):
            return True

        # Check examples for import statements
        if pattern.example_before and "import" in pattern.example_before.lower():
            return True

        return False

    def _build_custom_variables(self, pattern: MigrationPattern) -> List[Dict[str, str]]:
        """
        Build custom variables for pattern matching.

        Currently supports import capture for import statement migrations.

        Args:
            pattern: Migration pattern

        Returns:
            List of custom variable definitions
        """
        custom_vars = []

        # Check if this is an import pattern
        if self._is_import_pattern(pattern):
            # Add variable to capture imported components
            custom_vars.append({
                "pattern": "import {(?P<imports>[A-Za-z,\\s]+)}",
                "name": "component",
                "nameOfCaptureGroup": "imports",
                "defaultValue": "Component"
            })

        return custom_vars

    def _build_description(self, pattern: MigrationPattern, has_custom_variables: bool = False) -> str:
        """
        Build rule description.

        Args:
            pattern: Migration pattern
            has_custom_variables: Whether the rule uses custom variables

        Returns:
            Description text
        """
        # For import patterns with custom variables, use generic description
        if has_custom_variables and self._is_import_pattern(pattern):
            if pattern.target_pattern:
                # Extract package name from patterns
                # e.g., "import { Area } from '@patternfly/react-charts'" -> "@patternfly/react-charts"
                source_pkg = self._extract_package_name(pattern.source_pattern)
                target_pkg = self._extract_package_name(pattern.target_pattern)

                if source_pkg and target_pkg:
                    return f"imports  from '{source_pkg}'; should be replaced with imports from '{target_pkg}';"
                else:
                    return f"{pattern.source_pattern} should be replaced with {pattern.target_pattern}"
            else:
                return f"{pattern.source_pattern} usage detected (removed API)"

        # Default description
        if pattern.target_pattern:
            description = f"{pattern.source_pattern} should be replaced with {pattern.target_pattern}"
        else:
            description = f"{pattern.source_pattern} usage detected (removed API)"

        return description

    def _extract_package_name(self, import_statement: Optional[str]) -> Optional[str]:
        """
        Extract package name from import statement.

        Args:
            import_statement: Import statement string

        Returns:
            Package name or None
        """
        if not import_statement:
            return None

        import re
        # Match pattern: from 'package' or from "package"
        match = re.search(r"from\s+['\"]([^'\"]+)['\"]", import_statement)
        if match:
            return match.group(1)

        return None

    def _build_message(self, pattern: MigrationPattern, has_custom_variables: bool = False) -> str:
        """
        Build migration guidance message.

        Args:
            pattern: Migration pattern
            has_custom_variables: Whether the rule uses custom variables

        Returns:
            Message text
        """
        message = f"{pattern.rationale}\n\n"

        # Use custom variables in message if available
        if has_custom_variables and self._is_import_pattern(pattern):
            if pattern.target_pattern:
                message += f"Replace `{pattern.source_pattern.replace(pattern.source_pattern.split('{')[1].split('}')[0], '{{ component }}')}` with `{pattern.target_pattern.replace(pattern.target_pattern.split('{')[1].split('}')[0], '{{ component }}')}`."\
                    if '{' in pattern.source_pattern and '}' in pattern.source_pattern else \
                    f"Replace `import {{ {{{{ component }}}} }} from '{self._extract_package_name(pattern.source_pattern) or pattern.source_pattern}'` with `import {{ {{{{ component }}}} }} from '{self._extract_package_name(pattern.target_pattern) or pattern.target_pattern}'`."
            else:
                message += f"Remove usage of `{pattern.source_pattern}` (API has been removed)."

            # Update examples to use variables
            if pattern.example_before and pattern.example_after:
                # Replace specific component names with {{ component }} in examples
                example_before = self._replace_component_with_variable(pattern.example_before)
                example_after = self._replace_component_with_variable(pattern.example_after)

                message += f"\n\nBefore:\n```\n{example_before}\n```\n\n"
                message += f"After:\n```\n{example_after}\n```"
        else:
            # Default message without variables
            if pattern.target_pattern:
                message += f"Replace `{pattern.source_pattern}` with `{pattern.target_pattern}`."
            else:
                message += f"Remove usage of `{pattern.source_pattern}` (API has been removed)."

            # Add code examples if available
            if pattern.example_before and pattern.example_after:
                # Detect language from examples for syntax highlighting
                language_hint = self._detect_code_language(pattern.example_before)

                message += f"\n\nBefore:\n```{language_hint}\n{pattern.example_before}\n```\n\n"
                message += f"After:\n```{language_hint}\n{pattern.example_after}\n```"

        return message

    def _detect_code_language(self, code: str) -> str:
        """
        Detect programming language from code for syntax highlighting.

        Args:
            code: Code string

        Returns:
            Language identifier for markdown code blocks
        """
        code_lower = code.lower()

        # TypeScript indicators
        if any(indicator in code_lower for indicator in ['interface', 'type ', ': string', ': number', ': boolean', 'constructor(']):
            return 'typescript'

        # JavaScript/JSX indicators
        if any(indicator in code for indicator in ['import ', 'export ', 'const ', 'let ', 'function', '=>']):
            return ''  # No language hint for generic JS (could be JS or TS)

        return ''

    def _replace_component_with_variable(self, code: str) -> str:
        """
        Replace specific component names with {{ component }} variable in code examples.

        Args:
            code: Code string

        Returns:
            Code with component names replaced by variable
        """
        import re

        # Match import statements and replace component names with {{ component }}
        # Pattern: import { ComponentName } from 'package'
        pattern = r"import\s*\{\s*([A-Z][A-Za-z0-9_]*)\s*\}\s*from"
        replacement = r"import { {{ component }} } from"

        return re.sub(pattern, replacement, code)

    def _requires_semantic_analysis(self, pattern: MigrationPattern) -> bool:
        """
        Determine if pattern needs Node.js (TypeScript/JavaScript) language server semantic analysis.

        Use nodejs.referenced when you need to find actual symbol references (functions, classes,
        variables, types, interfaces) in the code. Use builtin.filecontent for simple text/regex matching.

        Args:
            pattern: Migration pattern

        Returns:
            True if semantic analysis is required (nodejs.referenced), False for text matching (builtin.filecontent)
        """
        semantic_keywords = [
            'function',
            'class',
            'type',
            'interface',
            'variable',
            'const',
            'import',
            'export',
            'component',
            'hook',
            'generic',
            'inheritance',
            'extends',
            'implements'
        ]

        description = (pattern.rationale or "").lower()
        return any(keyword in description for keyword in semantic_keywords)


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
