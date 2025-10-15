"""
Generate Konveyor rules for Java API removals.

This module provides a simplified interface for generating rules to detect
removed/deprecated Java APIs, such as those removed in JDK upgrades.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

from .schema import AnalyzerRule, Category, Link, LocationType


class RemovedJavaAPI(BaseModel):
    """
    Specification for a removed Java API.

    Examples:
        - Class removal: java.applet.Applet
        - Method removal: java.lang.Thread.stop()
        - Package removal: javax.xml.bind.*
    """
    fqn: str = Field(..., description="Fully qualified name (e.g., 'java.applet.Applet')")
    api_type: str = Field(..., description="Type of API: 'class', 'interface', 'method', 'package'")
    category: Category = Field(default=Category.MANDATORY, description="Rule category")
    effort: int = Field(default=5, ge=1, le=13, description="Migration effort (1-13)")
    message: str = Field(..., description="Migration guidance message")


class JavaRemovalRuleGenerator:
    """Generate Konveyor rules for removed Java APIs."""

    def __init__(
        self,
        migration_name: str,
        source_version: str,
        target_version: str,
        guide_url: Optional[str] = None
    ):
        """
        Initialize generator for Java API removal rules.

        Args:
            migration_name: Name of migration (e.g., "JDK 21 Applet Removal")
            source_version: Source version (e.g., "openjdk17")
            target_version: Target version (e.g., "openjdk21")
            guide_url: URL to migration guide
        """
        self.migration_name = migration_name
        self.source_version = source_version
        self.target_version = target_version
        self.guide_url = guide_url
        self._rule_counter = 0

    def generate_rules(self, removals: List[RemovedJavaAPI]) -> List[AnalyzerRule]:
        """
        Generate analyzer rules for removed APIs.

        For each removed API, generates a rule with multiple detection patterns:
        - Import detection
        - Type reference detection
        - Inheritance detection (for classes/interfaces)
        - Constructor call detection (for classes)

        Args:
            removals: List of removed API specifications

        Returns:
            List of AnalyzerRule objects
        """
        rules = []

        for removal in removals:
            rule = self._create_removal_rule(removal)
            rules.append(rule)

        return rules

    def _create_removal_rule(self, removal: RemovedJavaAPI) -> AnalyzerRule:
        """
        Create a single rule for a removed API.

        Args:
            removal: Removed API specification

        Returns:
            AnalyzerRule object
        """
        self._rule_counter += 1

        # Generate rule ID
        rule_id = self._generate_rule_id(removal)

        # Build when condition with multiple location types
        when_condition = self._build_when_condition(removal)

        # Build labels
        labels = [
            f"konveyor.io/source={self.source_version}",
            f"konveyor.io/target={self.target_version}+"
        ]

        # Build links
        links = None
        if self.guide_url:
            links = [Link(
                url=self.guide_url,
                title=self.migration_name
            )]

        # Create description
        description = f"{removal.fqn} usage detected"

        return AnalyzerRule(
            ruleID=rule_id,
            description=description,
            message=removal.message,
            category=removal.category,
            effort=removal.effort,
            labels=labels,
            when=when_condition,
            links=links,
            customVariables=[],
            tag=None
        )

    def _generate_rule_id(self, removal: RemovedJavaAPI) -> str:
        """
        Generate unique rule ID based on the API being removed.

        Args:
            removal: Removed API specification

        Returns:
            Rule ID string
        """
        # Create a slug from the migration name
        slug = self.migration_name.lower().replace(" ", "-")

        return f"{slug}-{self._rule_counter:05d}"

    def _build_when_condition(self, removal: RemovedJavaAPI) -> dict:
        """
        Build when condition with multiple detection patterns.

        Args:
            removal: Removed API specification

        Returns:
            When condition dictionary
        """
        conditions = []

        # Always detect imports
        conditions.append({
            "java.referenced": {
                "pattern": removal.fqn,
                "location": LocationType.IMPORT.value
            }
        })

        # Always detect type references
        conditions.append({
            "java.referenced": {
                "pattern": removal.fqn,
                "location": LocationType.TYPE.value
            }
        })

        # For classes and interfaces, detect inheritance
        if removal.api_type in ['class', 'interface']:
            conditions.append({
                "java.referenced": {
                    "pattern": removal.fqn,
                    "location": LocationType.INHERITANCE.value
                }
            })

        # For classes, detect constructor calls
        if removal.api_type == 'class':
            conditions.append({
                "java.referenced": {
                    "pattern": removal.fqn,
                    "location": LocationType.CONSTRUCTOR_CALL.value
                }
            })

        # For methods, detect method calls
        if removal.api_type == 'method':
            conditions.append({
                "java.referenced": {
                    "pattern": removal.fqn,
                    "location": LocationType.METHOD_CALL.value
                }
            })

        # Combine all conditions with OR
        if len(conditions) == 1:
            return conditions[0]
        else:
            return {"or": conditions}
