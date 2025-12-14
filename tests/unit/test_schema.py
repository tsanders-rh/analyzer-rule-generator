"""
Unit tests for schema module.

Tests cover:
- Pydantic model validation
- Required vs optional fields
- Field constraints and validation
- Enum values
- Default values
- Serialization/deserialization
- Edge cases and boundary conditions
"""
import pytest
from pydantic import ValidationError

from src.rule_generator.schema import (
    Category,
    LocationType,
    JavaReferenced,
    JavaDependency,
    NodejsReferenced,
    BuiltinFileContent,
    BuiltinFile,
    BuiltinXML,
    Link,
    AnalyzerRule,
    AnalyzerRuleset,
    MigrationPattern,
)


class TestCategoryEnum:
    """Test Category enum values."""

    def test_category_mandatory(self):
        """Should have MANDATORY category"""
        assert Category.MANDATORY == "mandatory"
        assert Category.MANDATORY.value == "mandatory"

    def test_category_potential(self):
        """Should have POTENTIAL category"""
        assert Category.POTENTIAL == "potential"
        assert Category.POTENTIAL.value == "potential"

    def test_category_optional(self):
        """Should have OPTIONAL category"""
        assert Category.OPTIONAL == "optional"
        assert Category.OPTIONAL.value == "optional"

    def test_category_from_string(self):
        """Should create Category from string"""
        assert Category("mandatory") == Category.MANDATORY
        assert Category("potential") == Category.POTENTIAL
        assert Category("optional") == Category.OPTIONAL

    def test_invalid_category_raises_error(self):
        """Should raise ValueError for invalid category"""
        with pytest.raises(ValueError):
            Category("invalid")


class TestLocationTypeEnum:
    """Test LocationType enum values."""

    def test_location_type_import(self):
        """Should have IMPORT location type"""
        assert LocationType.IMPORT == "IMPORT"

    def test_location_type_package(self):
        """Should have PACKAGE location type"""
        assert LocationType.PACKAGE == "PACKAGE"

    def test_location_type_constructor_call(self):
        """Should have CONSTRUCTOR_CALL location type"""
        assert LocationType.CONSTRUCTOR_CALL == "CONSTRUCTOR_CALL"

    def test_location_type_method_call(self):
        """Should have METHOD_CALL location type"""
        assert LocationType.METHOD_CALL == "METHOD_CALL"

    def test_location_type_type(self):
        """Should have TYPE location type"""
        assert LocationType.TYPE == "TYPE"

    def test_location_type_inheritance(self):
        """Should have INHERITANCE location type"""
        assert LocationType.INHERITANCE == "INHERITANCE"

    def test_location_type_annotation(self):
        """Should have ANNOTATION location type"""
        assert LocationType.ANNOTATION == "ANNOTATION"

    def test_invalid_location_type_raises_error(self):
        """Should raise ValueError for invalid location type"""
        with pytest.raises(ValueError):
            LocationType("INVALID_TYPE")


class TestJavaReferenced:
    """Test JavaReferenced model."""

    def test_create_with_pattern_only(self):
        """Should create with pattern only"""
        ref = JavaReferenced(pattern="com.example.*")
        assert ref.pattern == "com.example.*"
        assert ref.location is None

    def test_create_with_pattern_and_location(self):
        """Should create with pattern and location"""
        ref = JavaReferenced(pattern="com.example.MyClass", location=LocationType.TYPE)
        assert ref.pattern == "com.example.MyClass"
        assert ref.location == LocationType.TYPE

    def test_missing_pattern_raises_error(self):
        """Should raise ValidationError when pattern missing"""
        with pytest.raises(ValidationError) as exc_info:
            JavaReferenced()

        assert "pattern" in str(exc_info.value)

    def test_location_type_validation(self):
        """Should validate location type"""
        # Valid location type
        ref = JavaReferenced(pattern="test", location="TYPE")
        assert ref.location == LocationType.TYPE

        # Invalid location type should raise error
        with pytest.raises(ValidationError):
            JavaReferenced(pattern="test", location="INVALID")


class TestJavaDependency:
    """Test JavaDependency model."""

    def test_create_with_name_only(self):
        """Should create with name only"""
        dep = JavaDependency(name="junit.junit")
        assert dep.name == "junit.junit"
        assert dep.upperbound is None
        assert dep.lowerbound is None

    def test_create_with_version_bounds(self):
        """Should create with version bounds"""
        dep = JavaDependency(
            name="junit.junit",
            lowerbound="4.0.0",
            upperbound="5.0.0"
        )
        assert dep.name == "junit.junit"
        assert dep.lowerbound == "4.0.0"
        assert dep.upperbound == "5.0.0"

    def test_missing_name_raises_error(self):
        """Should raise ValidationError when name missing"""
        with pytest.raises(ValidationError) as exc_info:
            JavaDependency()

        assert "name" in str(exc_info.value)


class TestNodejsReferenced:
    """Test NodejsReferenced model."""

    def test_create_with_pattern(self):
        """Should create with pattern"""
        ref = NodejsReferenced(pattern="OldComponent")
        assert ref.pattern == "OldComponent"

    def test_missing_pattern_raises_error(self):
        """Should raise ValidationError when pattern missing"""
        with pytest.raises(ValidationError) as exc_info:
            NodejsReferenced()

        assert "pattern" in str(exc_info.value)


class TestBuiltinFileContent:
    """Test BuiltinFileContent model."""

    def test_create_with_pattern_only(self):
        """Should create with pattern only"""
        content = BuiltinFileContent(pattern="isDisabled\\s*=")
        assert content.pattern == "isDisabled\\s*="
        assert content.filePattern is None

    def test_create_with_file_pattern(self):
        """Should create with file pattern"""
        content = BuiltinFileContent(
            pattern="test",
            filePattern="*.{tsx,jsx}"
        )
        assert content.pattern == "test"
        assert content.filePattern == "*.{tsx,jsx}"

    def test_missing_pattern_raises_error(self):
        """Should raise ValidationError when pattern missing"""
        with pytest.raises(ValidationError) as exc_info:
            BuiltinFileContent()

        assert "pattern" in str(exc_info.value)


class TestBuiltinFile:
    """Test BuiltinFile model."""

    def test_create_with_pattern(self):
        """Should create with pattern"""
        file = BuiltinFile(pattern="*.xml")
        assert file.pattern == "*.xml"

    def test_missing_pattern_raises_error(self):
        """Should raise ValidationError when pattern missing"""
        with pytest.raises(ValidationError) as exc_info:
            BuiltinFile()

        assert "pattern" in str(exc_info.value)


class TestBuiltinXML:
    """Test BuiltinXML model."""

    def test_create_with_xpath_only(self):
        """Should create with xpath only"""
        xml = BuiltinXML(xpath="//configuration")
        assert xml.xpath == "//configuration"
        assert xml.filepaths is None

    def test_create_with_filepaths(self):
        """Should create with filepaths"""
        xml = BuiltinXML(
            xpath="//configuration",
            filepaths=["pom.xml", "web.xml"]
        )
        assert xml.xpath == "//configuration"
        assert xml.filepaths == ["pom.xml", "web.xml"]

    def test_missing_xpath_raises_error(self):
        """Should raise ValidationError when xpath missing"""
        with pytest.raises(ValidationError) as exc_info:
            BuiltinXML()

        assert "xpath" in str(exc_info.value)


class TestLink:
    """Test Link model."""

    def test_create_link(self):
        """Should create link with url and title"""
        link = Link(
            url="https://example.com/docs",
            title="Migration Guide"
        )
        assert link.url == "https://example.com/docs"
        assert link.title == "Migration Guide"

    def test_missing_url_raises_error(self):
        """Should raise ValidationError when url missing"""
        with pytest.raises(ValidationError) as exc_info:
            Link(title="Test")

        assert "url" in str(exc_info.value)

    def test_missing_title_raises_error(self):
        """Should raise ValidationError when title missing"""
        with pytest.raises(ValidationError) as exc_info:
            Link(url="https://example.com")

        assert "title" in str(exc_info.value)


class TestAnalyzerRule:
    """Test AnalyzerRule model."""

    def test_create_minimal_rule(self):
        """Should create rule with minimal required fields"""
        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            when={"java.referenced": {"pattern": "test"}},
            message="Test message"
        )
        assert rule.ruleID == "test-00000"
        assert rule.description == "Test rule"
        assert rule.effort == 5
        assert rule.category == Category.POTENTIAL  # Default
        assert rule.labels == []  # Default
        assert rule.message == "Test message"
        assert rule.links is None

    def test_create_complete_rule(self):
        """Should create rule with all fields"""
        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=7,
            category=Category.MANDATORY,
            labels=["konveyor.io/source=java-ee"],
            when={"java.referenced": {"pattern": "test"}},
            message="Test message",
            links=[Link(url="https://example.com", title="Docs")],
            customVariables=[{"name": "var1", "value": "val1"}],
            tag=["migration", "security"]
        )
        assert rule.ruleID == "test-00000"
        assert rule.category == Category.MANDATORY
        assert len(rule.labels) == 1
        assert len(rule.links) == 1
        assert len(rule.customVariables) == 1
        assert len(rule.tag) == 2

    def test_effort_must_be_in_range(self):
        """Should validate effort is between 1 and 10"""
        # Valid efforts
        for effort in [1, 5, 10]:
            rule = AnalyzerRule(
                ruleID="test",
                description="Test",
                effort=effort,
                when={},
                message="Test"
            )
            assert rule.effort == effort

        # Invalid efforts
        for effort in [0, 11, -1, 100]:
            with pytest.raises(ValidationError):
                AnalyzerRule(
                    ruleID="test",
                    description="Test",
                    effort=effort,
                    when={},
                    message="Test"
                )

    def test_missing_required_fields_raises_error(self):
        """Should raise ValidationError when required fields missing"""
        # Missing ruleID
        with pytest.raises(ValidationError) as exc_info:
            AnalyzerRule(
                description="Test",
                effort=5,
                when={},
                message="Test"
            )
        assert "ruleID" in str(exc_info.value)

        # Missing description
        with pytest.raises(ValidationError) as exc_info:
            AnalyzerRule(
                ruleID="test",
                effort=5,
                when={},
                message="Test"
            )
        assert "description" in str(exc_info.value)

        # Missing effort
        with pytest.raises(ValidationError) as exc_info:
            AnalyzerRule(
                ruleID="test",
                description="Test",
                when={},
                message="Test"
            )
        assert "effort" in str(exc_info.value)

        # Missing when
        with pytest.raises(ValidationError) as exc_info:
            AnalyzerRule(
                ruleID="test",
                description="Test",
                effort=5,
                message="Test"
            )
        assert "when" in str(exc_info.value)

        # Missing message
        with pytest.raises(ValidationError) as exc_info:
            AnalyzerRule(
                ruleID="test",
                description="Test",
                effort=5,
                when={}
            )
        assert "message" in str(exc_info.value)

    def test_serialization(self):
        """Should serialize to dict"""
        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            when={"java.referenced": {"pattern": "test"}},
            message="Test message"
        )
        data = rule.model_dump()

        assert data["ruleID"] == "test-00000"
        assert data["effort"] == 5
        assert data["category"] == "potential"

    def test_deserialization(self):
        """Should deserialize from dict"""
        data = {
            "ruleID": "test-00000",
            "description": "Test rule",
            "effort": 5,
            "category": "mandatory",
            "when": {"java.referenced": {"pattern": "test"}},
            "message": "Test message"
        }
        rule = AnalyzerRule(**data)

        assert rule.ruleID == "test-00000"
        assert rule.category == Category.MANDATORY

    def test_migration_complexity_optional_field(self):
        """Should allow migration_complexity as optional field"""
        # Without migration_complexity (should default to None)
        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            when={"java.referenced": {"pattern": "test"}},
            message="Test message"
        )
        assert rule.migration_complexity is None

        # With migration_complexity
        rule = AnalyzerRule(
            ruleID="test-00001",
            description="Test rule",
            effort=5,
            when={"java.referenced": {"pattern": "test"}},
            message="Test message",
            migration_complexity="medium"
        )
        assert rule.migration_complexity == "medium"

    def test_migration_complexity_all_valid_values(self):
        """Should accept all valid complexity values"""
        valid_complexities = ["trivial", "low", "medium", "high", "expert"]

        for complexity in valid_complexities:
            rule = AnalyzerRule(
                ruleID=f"test-{complexity}",
                description="Test rule",
                effort=5,
                when={"java.referenced": {"pattern": "test"}},
                message="Test message",
                migration_complexity=complexity
            )
            assert rule.migration_complexity == complexity

    def test_migration_complexity_serialization(self):
        """Should serialize migration_complexity field"""
        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            when={"java.referenced": {"pattern": "test"}},
            message="Test message",
            migration_complexity="high"
        )
        data = rule.model_dump()

        assert data["migration_complexity"] == "high"

    def test_migration_complexity_deserialization(self):
        """Should deserialize migration_complexity field"""
        data = {
            "ruleID": "test-00000",
            "description": "Test rule",
            "effort": 5,
            "when": {"java.referenced": {"pattern": "test"}},
            "message": "Test message",
            "migration_complexity": "expert"
        }
        rule = AnalyzerRule(**data)

        assert rule.migration_complexity == "expert"

    def test_migration_complexity_exclude_none(self):
        """Should exclude migration_complexity from dict if None"""
        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            when={"java.referenced": {"pattern": "test"}},
            message="Test message"
        )
        data = rule.model_dump(exclude_none=True)

        assert "migration_complexity" not in data


class TestAnalyzerRuleset:
    """Test AnalyzerRuleset model."""

    def test_create_empty_ruleset(self):
        """Should create empty ruleset"""
        ruleset = AnalyzerRuleset()
        assert ruleset.rules == []

    def test_create_ruleset_with_rules(self):
        """Should create ruleset with rules"""
        rules = [
            AnalyzerRule(
                ruleID="test-00000",
                description="Test 1",
                effort=5,
                when={},
                message="Test"
            ),
            AnalyzerRule(
                ruleID="test-00010",
                description="Test 2",
                effort=7,
                when={},
                message="Test"
            )
        ]
        ruleset = AnalyzerRuleset(rules=rules)
        assert len(ruleset.rules) == 2

    def test_add_rules_after_creation(self):
        """Should be able to add rules after creation"""
        ruleset = AnalyzerRuleset()
        ruleset.rules.append(
            AnalyzerRule(
                ruleID="test-00000",
                description="Test",
                effort=5,
                when={},
                message="Test"
            )
        )
        assert len(ruleset.rules) == 1


class TestMigrationPattern:
    """Test MigrationPattern model."""

    def test_create_minimal_pattern(self):
        """Should create pattern with minimal required fields"""
        pattern = MigrationPattern(
            source_pattern="OldClass",
            complexity="MEDIUM",
            category="api",
            rationale="Class renamed"
        )
        assert pattern.source_pattern == "OldClass"
        assert pattern.complexity == "MEDIUM"
        assert pattern.category == "api"
        assert pattern.rationale == "Class renamed"
        assert pattern.target_pattern is None
        assert pattern.concern == "general"  # Default

    def test_create_complete_pattern(self):
        """Should create pattern with all fields"""
        pattern = MigrationPattern(
            source_pattern="OldClass",
            target_pattern="NewClass",
            source_fqn="com.example.OldClass",
            location_type=LocationType.TYPE,
            alternative_fqns=["org.example.OldClass"],
            complexity="HIGH",
            category="api",
            concern="security",
            provider_type="java",
            file_pattern="*.java",
            rationale="Security improvement",
            example_before="OldClass obj = new OldClass();",
            example_after="NewClass obj = new NewClass();",
            documentation_url="https://example.com/docs"
        )
        assert pattern.source_pattern == "OldClass"
        assert pattern.target_pattern == "NewClass"
        assert pattern.source_fqn == "com.example.OldClass"
        assert pattern.location_type == LocationType.TYPE
        assert pattern.alternative_fqns == ["org.example.OldClass"]
        assert pattern.complexity == "HIGH"
        assert pattern.concern == "security"
        assert pattern.provider_type == "java"
        assert pattern.documentation_url == "https://example.com/docs"

    def test_missing_required_fields_raises_error(self):
        """Should raise ValidationError when required fields missing"""
        # Missing source_pattern
        with pytest.raises(ValidationError) as exc_info:
            MigrationPattern(
                complexity="MEDIUM",
                category="api",
                rationale="Test"
            )
        assert "source_pattern" in str(exc_info.value)

        # Missing complexity
        with pytest.raises(ValidationError) as exc_info:
            MigrationPattern(
                source_pattern="test",
                category="api",
                rationale="Test"
            )
        assert "complexity" in str(exc_info.value)

        # Missing category
        with pytest.raises(ValidationError) as exc_info:
            MigrationPattern(
                source_pattern="test",
                complexity="MEDIUM",
                rationale="Test"
            )
        assert "category" in str(exc_info.value)

        # Missing rationale
        with pytest.raises(ValidationError) as exc_info:
            MigrationPattern(
                source_pattern="test",
                complexity="MEDIUM",
                category="api"
            )
        assert "rationale" in str(exc_info.value)

    def test_default_concern(self):
        """Should default concern to 'general'"""
        pattern = MigrationPattern(
            source_pattern="test",
            complexity="MEDIUM",
            category="api",
            rationale="Test"
        )
        assert pattern.concern == "general"

    def test_empty_alternative_fqns_default(self):
        """Should default alternative_fqns to empty list"""
        pattern = MigrationPattern(
            source_pattern="test",
            complexity="MEDIUM",
            category="api",
            rationale="Test"
        )
        assert pattern.alternative_fqns == []

    def test_serialization(self):
        """Should serialize to dict"""
        pattern = MigrationPattern(
            source_pattern="OldClass",
            target_pattern="NewClass",
            complexity="HIGH",
            category="api",
            rationale="Test"
        )
        data = pattern.model_dump()

        assert data["source_pattern"] == "OldClass"
        assert data["target_pattern"] == "NewClass"
        assert data["complexity"] == "HIGH"

    def test_deserialization(self):
        """Should deserialize from dict"""
        data = {
            "source_pattern": "OldClass",
            "complexity": "MEDIUM",
            "category": "api",
            "rationale": "Test"
        }
        pattern = MigrationPattern(**data)

        assert pattern.source_pattern == "OldClass"
        assert pattern.complexity == "MEDIUM"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_pattern(self):
        """Should allow empty string pattern (validation done elsewhere)"""
        # Pydantic allows empty strings unless explicitly forbidden
        pattern = MigrationPattern(
            source_pattern="",
            complexity="MEDIUM",
            category="api",
            rationale="Test"
        )
        assert pattern.source_pattern == ""

    def test_unicode_in_patterns(self):
        """Should handle Unicode characters"""
        pattern = MigrationPattern(
            source_pattern="测试类",  # Chinese characters
            target_pattern="TestClass",
            complexity="MEDIUM",
            category="api",
            rationale="Internationalization"
        )
        assert pattern.source_pattern == "测试类"

    def test_special_characters_in_regex_pattern(self):
        """Should handle regex special characters"""
        content = BuiltinFileContent(pattern="\\w+\\.test\\(\\)")
        assert content.pattern == "\\w+\\.test\\(\\)"

    def test_very_long_strings(self):
        """Should handle very long strings"""
        long_string = "x" * 10000
        pattern = MigrationPattern(
            source_pattern=long_string,
            complexity="MEDIUM",
            category="api",
            rationale="Test"
        )
        assert len(pattern.source_pattern) == 10000

    def test_effort_boundary_values(self):
        """Should accept boundary values for effort"""
        # Minimum
        rule = AnalyzerRule(
            ruleID="test",
            description="Test",
            effort=1,
            when={},
            message="Test"
        )
        assert rule.effort == 1

        # Maximum
        rule = AnalyzerRule(
            ruleID="test",
            description="Test",
            effort=10,
            when={},
            message="Test"
        )
        assert rule.effort == 10

    def test_empty_lists_as_defaults(self):
        """Should handle empty lists correctly"""
        rule = AnalyzerRule(
            ruleID="test",
            description="Test",
            effort=5,
            when={},
            message="Test"
        )
        assert rule.labels == []
        assert rule.customVariables == []

    def test_none_vs_empty_string(self):
        """Should distinguish None from empty string"""
        pattern = MigrationPattern(
            source_pattern="test",
            target_pattern="",  # Empty string, not None
            complexity="MEDIUM",
            category="api",
            rationale="Test"
        )
        assert pattern.target_pattern == ""
        assert pattern.source_fqn is None  # Actually None
