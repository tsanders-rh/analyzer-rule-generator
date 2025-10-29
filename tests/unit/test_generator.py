"""
Unit tests for rule generation module.

Tests cover:
- Rule ID generation
- Pattern to rule conversion
- When condition building (Java, Builtin, Node.js providers)
- Complexity to effort mapping
- Category determination
- Label and message building
- Rules by concern grouping
"""
import pytest
from src.rule_generator.generator import AnalyzerRuleGenerator
from src.rule_generator.schema import (
    MigrationPattern,
    Category,
    LocationType,
    AnalyzerRule
)


class TestRuleIDGeneration:
    """Test rule ID generation logic."""

    def test_generate_sequential_rule_ids(self):
        """Should generate sequential rule IDs incrementing by 10"""
        generator = AnalyzerRuleGenerator(
            source_framework="spring-boot-3",
            target_framework="spring-boot-4"
        )

        id1 = generator._create_rule_id()
        id2 = generator._create_rule_id()
        id3 = generator._create_rule_id()

        assert id1 == "spring-boot-3-to-spring-boot-4-00000"
        assert id2 == "spring-boot-3-to-spring-boot-4-00010"
        assert id3 == "spring-boot-3-to-spring-boot-4-00020"

    def test_generate_rule_id_with_rule_file_name(self):
        """Should use rule_file_name if provided"""
        generator = AnalyzerRuleGenerator(rule_file_name="custom-rules")

        rule_id = generator._create_rule_id()

        assert rule_id == "custom-rules-00000"

    def test_generate_rule_id_without_frameworks(self):
        """Should use default prefix without frameworks"""
        generator = AnalyzerRuleGenerator()

        rule_id = generator._create_rule_id()

        assert rule_id == "migration-00000"

    def test_rule_id_has_five_digits(self):
        """Should always use 5-digit numbering"""
        generator = AnalyzerRuleGenerator(
            source_framework="a",
            target_framework="b"
        )

        # Generate many IDs to test padding
        for i in range(15):
            rule_id = generator._create_rule_id()

        # Last ID should still have 5 digits
        assert rule_id.endswith("-00140")


class TestComplexityToEffortMapping:
    """Test complexity to effort score mapping."""

    def test_map_trivial_to_effort_1(self):
        """Should map TRIVIAL to effort 1"""
        generator = AnalyzerRuleGenerator()
        effort = generator._map_complexity_to_effort("TRIVIAL")
        assert effort == 1

    def test_map_low_to_effort_3(self):
        """Should map LOW to effort 3"""
        generator = AnalyzerRuleGenerator()
        effort = generator._map_complexity_to_effort("LOW")
        assert effort == 3

    def test_map_medium_to_effort_5(self):
        """Should map MEDIUM to effort 5"""
        generator = AnalyzerRuleGenerator()
        effort = generator._map_complexity_to_effort("MEDIUM")
        assert effort == 5

    def test_map_high_to_effort_7(self):
        """Should map HIGH to effort 7"""
        generator = AnalyzerRuleGenerator()
        effort = generator._map_complexity_to_effort("HIGH")
        assert effort == 7

    def test_map_expert_to_effort_10(self):
        """Should map EXPERT to effort 10"""
        generator = AnalyzerRuleGenerator()
        effort = generator._map_complexity_to_effort("EXPERT")
        assert effort == 10

    def test_map_unknown_to_default_5(self):
        """Should default to effort 5 for unknown complexity"""
        generator = AnalyzerRuleGenerator()
        effort = generator._map_complexity_to_effort("UNKNOWN")
        assert effort == 5

    def test_map_case_insensitive(self):
        """Should handle lowercase complexity values"""
        generator = AnalyzerRuleGenerator()
        effort = generator._map_complexity_to_effort("trivial")
        assert effort == 1


class TestCategoryDetermination:
    """Test category determination logic."""

    def test_high_complexity_is_mandatory(self):
        """Should categorize HIGH complexity as mandatory"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="test",
            complexity="HIGH",
            rationale="Test change"
        )

        category = generator._determine_category(pattern)
        assert category == Category.MANDATORY

    def test_expert_complexity_is_mandatory(self):
        """Should categorize EXPERT complexity as mandatory"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="test",
            complexity="EXPERT",
            rationale="Complex migration"
        )

        category = generator._determine_category(pattern)
        assert category == Category.MANDATORY

    def test_trivial_complexity_is_mandatory(self):
        """Should categorize TRIVIAL complexity as mandatory (easy wins)"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="test",
            complexity="TRIVIAL",
            rationale="Simple rename"
        )

        category = generator._determine_category(pattern)
        assert category == Category.MANDATORY

    def test_removed_api_is_mandatory(self):
        """Should categorize removed APIs as mandatory"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="test",
            complexity="MEDIUM",
            rationale="API has been removed in version 2"
        )

        category = generator._determine_category(pattern)
        assert category == Category.MANDATORY

    def test_deprecated_for_removal_is_mandatory(self):
        """Should categorize deprecated for removal as mandatory"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="test",
            complexity="MEDIUM",
            rationale="Deprecated for removal in next release"
        )

        category = generator._determine_category(pattern)
        assert category == Category.MANDATORY

    def test_property_rename_is_mandatory(self):
        """Should categorize property renames as mandatory"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="app.config.oldProperty",
            target_pattern="app.config.newProperty",
            complexity="MEDIUM",
            rationale="Property has been renamed"
        )

        category = generator._determine_category(pattern)
        assert category == Category.MANDATORY

    def test_medium_complexity_default_is_potential(self):
        """Should categorize MEDIUM complexity as potential by default"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="test",
            complexity="MEDIUM",
            rationale="General change"
        )

        category = generator._determine_category(pattern)
        assert category == Category.POTENTIAL

    def test_low_complexity_is_potential(self):
        """Should categorize LOW complexity as potential"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="test",
            complexity="LOW",
            rationale="Optional improvement"
        )

        category = generator._determine_category(pattern)
        assert category == Category.POTENTIAL


class TestWhenConditionBuilding:
    """Test when condition building for different providers."""

    def test_build_java_referenced_condition(self):
        """Should build java.referenced condition"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_fqn="com.example.OldClass",
            location_type=LocationType.TYPE,
            complexity="MEDIUM",
            rationale="Test"
        )

        condition = generator._build_when_condition(pattern)

        assert "java.referenced" in condition
        assert condition["java.referenced"]["pattern"] == "com.example.OldClass"
        assert condition["java.referenced"]["location"] == "TYPE"

    def test_build_java_condition_with_default_location(self):
        """Should default to TYPE location if not specified"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_fqn="com.example.OldClass",
            complexity="MEDIUM",
            rationale="Test"
        )

        condition = generator._build_when_condition(pattern)

        assert condition["java.referenced"]["location"] == "TYPE"

    def test_build_java_condition_with_alternatives(self):
        """Should build OR condition with alternative FQNs"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_fqn="javax.security.cert.*",
            alternative_fqns=["java.security.cert.*"],
            location_type=LocationType.TYPE,
            complexity="MEDIUM",
            rationale="Package migration"
        )

        condition = generator._build_when_condition(pattern)

        assert "or" in condition
        assert len(condition["or"]) == 2
        assert condition["or"][0]["java.referenced"]["pattern"] == "javax.security.cert.*"
        assert condition["or"][1]["java.referenced"]["pattern"] == "java.security.cert.*"

    def test_build_builtin_filecontent_condition(self):
        """Should build builtin.filecontent condition"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_fqn="isDisabled\\s*=",  # regex pattern
            file_pattern="*.{tsx,jsx}",
            provider_type="builtin",
            complexity="MEDIUM",
            rationale="Property rename"
        )

        condition = generator._build_when_condition(pattern)

        assert "builtin.filecontent" in condition
        assert condition["builtin.filecontent"]["pattern"] == "isDisabled\\s*="
        assert condition["builtin.filecontent"]["filePattern"] == "*.{tsx,jsx}"

    def test_build_builtin_condition_without_file_pattern(self):
        """Should build builtin condition without filePattern if not specified"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_fqn="oldPattern",
            provider_type="builtin",
            complexity="MEDIUM",
            rationale="Test"
        )

        condition = generator._build_when_condition(pattern)

        assert "builtin.filecontent" in condition
        assert "filePattern" not in condition["builtin.filecontent"]

    def test_build_nodejs_referenced_condition(self):
        """Should build nodejs.referenced condition"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_fqn="OldComponent",
            provider_type="nodejs",
            complexity="MEDIUM",
            rationale="Component renamed"
        )

        condition = generator._build_when_condition(pattern)

        assert "nodejs.referenced" in condition
        assert condition["nodejs.referenced"]["pattern"] == "OldComponent"

    def test_build_nodejs_condition_uses_source_pattern_fallback(self):
        """Should use source_pattern if source_fqn not available"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="oldFunction",
            provider_type="nodejs",
            complexity="MEDIUM",
            rationale="Function renamed"
        )

        condition = generator._build_when_condition(pattern)

        assert condition["nodejs.referenced"]["pattern"] == "oldFunction"

    def test_build_condition_returns_none_without_fqn(self):
        """Should return None if no source_fqn or pattern"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            complexity="MEDIUM",
            rationale="No pattern specified"
        )

        condition = generator._build_when_condition(pattern)

        assert condition is None


class TestLabelBuilding:
    """Test label generation."""

    def test_build_labels_with_both_frameworks(self):
        """Should build labels with source and target"""
        generator = AnalyzerRuleGenerator(
            source_framework="spring-boot-3",
            target_framework="spring-boot-4"
        )

        labels = generator._build_labels()

        assert "konveyor.io/source=spring-boot-3" in labels
        assert "konveyor.io/target=spring-boot-4" in labels

    def test_build_labels_with_only_source(self):
        """Should build label with only source"""
        generator = AnalyzerRuleGenerator(source_framework="jakarta-ee-8")

        labels = generator._build_labels()

        assert "konveyor.io/source=jakarta-ee-8" in labels
        assert len([l for l in labels if "target" in l]) == 0

    def test_build_labels_with_only_target(self):
        """Should build label with only target"""
        generator = AnalyzerRuleGenerator(target_framework="jakarta-ee-10")

        labels = generator._build_labels()

        assert "konveyor.io/target=jakarta-ee-10" in labels
        assert len([l for l in labels if "source" in l]) == 0

    def test_build_empty_labels(self):
        """Should build empty labels list without frameworks"""
        generator = AnalyzerRuleGenerator()

        labels = generator._build_labels()

        assert labels == []


class TestMessageBuilding:
    """Test migration message generation."""

    def test_build_message_with_replacement(self):
        """Should build message with replacement guidance"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="OldClass",
            target_pattern="NewClass",
            complexity="MEDIUM",
            rationale="Class has been renamed for clarity"
        )

        message = generator._build_message(pattern)

        assert "Class has been renamed for clarity" in message
        assert "Replace `OldClass` with `NewClass`" in message

    def test_build_message_for_removed_api(self):
        """Should build message for removed API without replacement"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="RemovedAPI",
            complexity="HIGH",
            rationale="API has been removed"
        )

        message = generator._build_message(pattern)

        assert "API has been removed" in message
        assert "Remove usage of `RemovedAPI`" in message
        assert "API has been removed" in message

    def test_build_message_with_examples(self):
        """Should include before/after examples in message"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="oldMethod()",
            target_pattern="newMethod()",
            complexity="MEDIUM",
            rationale="Method renamed",
            example_before="obj.oldMethod();",
            example_after="obj.newMethod();"
        )

        message = generator._build_message(pattern)

        assert "Before:" in message
        assert "obj.oldMethod();" in message
        assert "After:" in message
        assert "obj.newMethod();" in message

    def test_build_message_without_examples(self):
        """Should build message without examples if not provided"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="OldClass",
            target_pattern="NewClass",
            complexity="MEDIUM",
            rationale="Class renamed"
        )

        message = generator._build_message(pattern)

        assert "Before:" not in message
        assert "After:" not in message


class TestLinksBuilding:
    """Test documentation links generation."""

    def test_build_links_with_documentation_url(self):
        """Should build links when documentation URL provided"""
        generator = AnalyzerRuleGenerator(target_framework="spring-boot-4")
        pattern = MigrationPattern(
            source_pattern="test",
            complexity="MEDIUM",
            rationale="Test",
            documentation_url="https://docs.spring.io/migration"
        )

        links = generator._build_links(pattern)

        assert links is not None
        assert len(links) == 1
        assert links[0].url == "https://docs.spring.io/migration"
        assert "spring-boot-4" in links[0].title

    def test_build_links_without_documentation_url(self):
        """Should return None when no documentation URL"""
        generator = AnalyzerRuleGenerator()
        pattern = MigrationPattern(
            source_pattern="test",
            complexity="MEDIUM",
            rationale="Test"
        )

        links = generator._build_links(pattern)

        assert links is None


class TestPatternToRule:
    """Test complete pattern to rule conversion."""

    def test_convert_valid_pattern_to_rule(self):
        """Should convert valid pattern to rule successfully"""
        generator = AnalyzerRuleGenerator(
            source_framework="spring-boot-3",
            target_framework="spring-boot-4"
        )

        pattern = MigrationPattern(
            source_pattern="OldClass",
            target_pattern="NewClass",
            source_fqn="com.example.OldClass",
            location_type=LocationType.TYPE,
            complexity="MEDIUM",
            category="api",
            concern="core",
            rationale="Class renamed for clarity",
            documentation_url="https://example.com/docs"
        )

        rule = generator._pattern_to_rule(pattern)

        assert rule is not None
        assert isinstance(rule, AnalyzerRule)
        assert rule.ruleID == "spring-boot-3-to-spring-boot-4-00000"
        assert rule.effort == 5
        assert rule.category == Category.POTENTIAL
        assert "konveyor.io/source=spring-boot-3" in rule.labels
        assert "konveyor.io/target=spring-boot-4" in rule.labels
        assert rule.when is not None
        assert "Class renamed for clarity" in rule.message
        assert rule.links is not None

    def test_skip_pattern_without_fqn_or_pattern(self):
        """Should return None for pattern without FQN or source_pattern"""
        generator = AnalyzerRuleGenerator()

        pattern = MigrationPattern(
            complexity="MEDIUM",
            rationale="Missing pattern info"
        )

        rule = generator._pattern_to_rule(pattern)

        assert rule is None

    def test_skip_pattern_with_unbuildable_condition(self):
        """Should return None if when condition cannot be built"""
        generator = AnalyzerRuleGenerator()

        # Pattern with source_pattern but no source_fqn for Java provider
        pattern = MigrationPattern(
            source_pattern="test",
            complexity="MEDIUM",
            rationale="Test"
        )

        rule = generator._pattern_to_rule(pattern)

        # Will be None because java provider needs source_fqn
        assert rule is None


class TestGenerateRules:
    """Test bulk rule generation."""

    def test_generate_rules_from_multiple_patterns(self):
        """Should generate multiple rules from patterns"""
        generator = AnalyzerRuleGenerator(
            source_framework="a",
            target_framework="b"
        )

        patterns = [
            MigrationPattern(
                source_fqn="com.example.Class1",
                complexity="MEDIUM",
                rationale="Test 1"
            ),
            MigrationPattern(
                source_fqn="com.example.Class2",
                complexity="HIGH",
                rationale="Test 2"
            )
        ]

        rules = generator.generate_rules(patterns)

        assert len(rules) == 2
        assert rules[0].ruleID.endswith("-00000")
        assert rules[1].ruleID.endswith("-00010")

    def test_generate_rules_skips_invalid_patterns(self):
        """Should skip patterns that cannot be converted"""
        generator = AnalyzerRuleGenerator()

        patterns = [
            MigrationPattern(
                source_fqn="com.example.Valid",
                complexity="MEDIUM",
                rationale="Valid"
            ),
            MigrationPattern(
                complexity="MEDIUM",
                rationale="Invalid - no FQN"
            )
        ]

        rules = generator.generate_rules(patterns)

        assert len(rules) == 1
        assert "Valid" in rules[0].message


class TestGenerateRulesByConcern:
    """Test rules generation grouped by concern."""

    def test_group_rules_by_concern(self):
        """Should group rules by concern"""
        generator = AnalyzerRuleGenerator()

        patterns = [
            MigrationPattern(
                source_fqn="com.example.Security1",
                complexity="MEDIUM",
                concern="security",
                rationale="Security change 1"
            ),
            MigrationPattern(
                source_fqn="com.example.Security2",
                complexity="MEDIUM",
                concern="security",
                rationale="Security change 2"
            ),
            MigrationPattern(
                source_fqn="com.example.Config1",
                complexity="MEDIUM",
                concern="configuration",
                rationale="Config change"
            )
        ]

        rules_by_concern = generator.generate_rules_by_concern(patterns)

        assert "security" in rules_by_concern
        assert "configuration" in rules_by_concern
        assert len(rules_by_concern["security"]) == 2
        assert len(rules_by_concern["configuration"]) == 1

    def test_use_general_for_no_concern(self):
        """Should use 'general' for patterns without concern"""
        generator = AnalyzerRuleGenerator()

        patterns = [
            MigrationPattern(
                source_fqn="com.example.Test",
                complexity="MEDIUM",
                rationale="No concern specified"
            )
        ]

        rules_by_concern = generator.generate_rules_by_concern(patterns)

        assert "general" in rules_by_concern
        assert len(rules_by_concern["general"]) == 1

    def test_reset_rule_counter_per_concern(self):
        """Should reset rule counter for each concern"""
        generator = AnalyzerRuleGenerator(
            source_framework="a",
            target_framework="b"
        )

        patterns = [
            MigrationPattern(
                source_fqn="com.example.Test1",
                complexity="MEDIUM",
                concern="concern-a",
                rationale="Test"
            ),
            MigrationPattern(
                source_fqn="com.example.Test2",
                complexity="MEDIUM",
                concern="concern-a",
                rationale="Test"
            ),
            MigrationPattern(
                source_fqn="com.example.Test3",
                complexity="MEDIUM",
                concern="concern-b",
                rationale="Test"
            )
        ]

        rules_by_concern = generator.generate_rules_by_concern(patterns)

        # First concern should have rules 00000 and 00010
        concern_a_rules = rules_by_concern["concern-a"]
        assert concern_a_rules[0].ruleID.endswith("-00000")
        assert concern_a_rules[1].ruleID.endswith("-00010")

        # Second concern should reset and start at 00000
        concern_b_rules = rules_by_concern["concern-b"]
        assert concern_b_rules[0].ruleID.endswith("-00000")


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_handle_empty_pattern_list(self):
        """Should handle empty pattern list gracefully"""
        generator = AnalyzerRuleGenerator()

        rules = generator.generate_rules([])

        assert rules == []

    def test_handle_all_invalid_patterns(self):
        """Should handle case where all patterns are invalid"""
        generator = AnalyzerRuleGenerator()

        patterns = [
            MigrationPattern(complexity="MEDIUM", rationale="No FQN"),
            MigrationPattern(complexity="HIGH", rationale="Also no FQN")
        ]

        rules = generator.generate_rules(patterns)

        assert rules == []

    def test_generate_description_with_target(self):
        """Should generate description with replacement"""
        generator = AnalyzerRuleGenerator()

        pattern = MigrationPattern(
            source_pattern="Old",
            target_pattern="New",
            source_fqn="com.example.Old",
            complexity="MEDIUM",
            rationale="Test"
        )

        rule = generator._pattern_to_rule(pattern)

        assert "should be replaced with" in rule.description

    def test_generate_description_without_target(self):
        """Should generate description for removed API"""
        generator = AnalyzerRuleGenerator()

        pattern = MigrationPattern(
            source_pattern="Removed",
            source_fqn="com.example.Removed",
            complexity="MEDIUM",
            rationale="Test"
        )

        rule = generator._pattern_to_rule(pattern)

        assert "removed API" in rule.description.lower()
