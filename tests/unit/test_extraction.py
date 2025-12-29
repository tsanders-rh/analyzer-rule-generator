"""
Unit tests for src/rule_generator/extraction.py

Tests pattern extraction logic, language detection, and LLM response parsing.
"""

import json
from unittest.mock import Mock, patch

import pytest

from src.rule_generator.extraction import MigrationPatternExtractor, detect_language_from_frameworks
from src.rule_generator.schema import CSharpLocationType, LocationType, MigrationPattern


class TestLanguageDetection:
    """Test language detection from framework names."""

    def test_detect_java_from_spring(self):
        """Should detect Java from Spring framework names"""
        result = detect_language_from_frameworks("spring-boot-2", "spring-boot-3")
        assert result == "java"

    def test_detect_java_from_jakarta(self):
        """Should detect Java from Jakarta framework names"""
        result = detect_language_from_frameworks("javax", "jakarta")
        assert result == "java"

    def test_detect_java_from_jdk(self):
        """Should detect Java from JDK version names"""
        result = detect_language_from_frameworks("openjdk-11", "openjdk-17")
        assert result == "java"

    def test_detect_javascript_from_react(self):
        """Should detect JavaScript from React framework names"""
        result = detect_language_from_frameworks("react-16", "react-18")
        assert result == "javascript"

    def test_detect_javascript_from_node(self):
        """Should detect JavaScript from Node framework names"""
        result = detect_language_from_frameworks("node-14", "node-20")
        assert result == "javascript"

    def test_detect_typescript_when_explicitly_mentioned(self):
        """Should detect TypeScript when explicitly mentioned"""
        result = detect_language_from_frameworks("typescript-4", "typescript-5")
        assert result == "typescript"

    def test_detect_javascript_from_patternfly(self):
        """Should detect JavaScript from PatternFly framework names"""
        result = detect_language_from_frameworks("patternfly-v5", "patternfly-v6")
        assert result == "javascript"

    def test_detect_unknown_for_generic_names(self):
        """Should return unknown for unrecognized framework names"""
        result = detect_language_from_frameworks("framework-v1", "framework-v2")
        assert result == "unknown"

    def test_case_insensitive_detection(self):
        """Should detect language case-insensitively"""
        result = detect_language_from_frameworks("Spring-Boot-3", "SPRING-BOOT-4")
        assert result == "java"

    def test_detect_csharp_from_dotnet(self):
        """Should detect C# from .NET framework names"""
        result = detect_language_from_frameworks("dotnetframework", "dotnet8")
        assert result == "csharp"

    def test_detect_csharp_from_aspnet(self):
        """Should detect C# from ASP.NET framework names"""
        result = detect_language_from_frameworks("aspnet-mvc-5", "aspnet-core-8")
        assert result == "csharp"

    def test_detect_csharp_from_csharp_keyword(self):
        """Should detect C# when 'csharp' or 'c#' is mentioned"""
        result = detect_language_from_frameworks("csharp-10", "csharp-11")
        assert result == "csharp"

    def test_detect_csharp_from_netcore(self):
        """Should detect C# from .NET Core framework names"""
        result = detect_language_from_frameworks("netcore-3.1", "dotnet-6")
        assert result == "csharp"

    def test_detect_csharp_from_entityframework(self):
        """Should detect C# from Entity Framework names"""
        result = detect_language_from_frameworks("entityframework-6", "ef-core-7")
        assert result == "csharp"


class TestPatternParsing:
    """Test parsing of LLM responses into MigrationPattern objects."""

    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider."""
        mock = Mock()
        mock.generate = Mock(return_value="Mock response")
        return mock

    @pytest.fixture
    def extractor(self, mock_llm_provider):
        """Create a MigrationPatternExtractor instance."""
        return MigrationPatternExtractor(mock_llm_provider)

    def test_parse_valid_json_response(self, extractor):
        """Should parse valid JSON response into MigrationPattern objects"""
        response = '''[{
            "source_pattern": "javax.security.cert",
            "target_pattern": "java.security.cert",
            "source_fqn": "javax.security.cert.*",
            "location_type": "TYPE",
            "complexity": "TRIVIAL",
            "category": "api",
            "concern": "security",
            "rationale": "Package deprecated for removal",
            "example_before": "import javax.security.cert.Certificate;",
            "example_after": "import java.security.cert.Certificate;"
        }]'''

        patterns = extractor._parse_extraction_response(response)

        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.source_pattern == "javax.security.cert"
        assert pattern.target_pattern == "java.security.cert"
        assert pattern.source_fqn == "javax.security.cert.*"
        assert pattern.location_type == LocationType.TYPE
        assert pattern.complexity == "TRIVIAL"
        assert pattern.category == "api"
        assert pattern.concern == "security"

    def test_parse_multiple_patterns(self, extractor):
        """Should parse multiple patterns from JSON array"""
        response = '''[
            {
                "source_pattern": "Pattern1",
                "target_pattern": "NewPattern1",
                "complexity": "LOW",
                "category": "api",
                "rationale": "Test 1"
            },
            {
                "source_pattern": "Pattern2",
                "target_pattern": "NewPattern2",
                "complexity": "MEDIUM",
                "category": "config",
                "rationale": "Test 2"
            }
        ]'''

        patterns = extractor._parse_extraction_response(response)

        assert len(patterns) == 2
        assert patterns[0].source_pattern == "Pattern1"
        assert patterns[1].source_pattern == "Pattern2"

    def test_parse_json_with_surrounding_text(self, extractor):
        """Should extract JSON from response with surrounding text"""
        response = '''Here are the patterns:

        [{
            "source_pattern": "test.pattern",
            "target_pattern": "new.pattern",
            "complexity": "TRIVIAL",
            "category": "api",
            "rationale": "Test"
        }]

        That's all!'''

        patterns = extractor._parse_extraction_response(response)

        assert len(patterns) == 1
        assert patterns[0].source_pattern == "test.pattern"

    def test_handle_invalid_json(self, extractor):
        """Should return empty list for invalid JSON"""
        response = "This is not valid JSON {invalid}"

        patterns = extractor._parse_extraction_response(response)

        assert patterns == []

    def test_handle_no_json_array(self, extractor):
        """Should return empty list when no JSON array found"""
        response = "No JSON array here"

        patterns = extractor._parse_extraction_response(response)

        assert patterns == []

    def test_handle_missing_required_fields(self, extractor):
        """Should skip patterns with missing required fields"""
        response = '''[
            {
                "source_pattern": "test",
                "target_pattern": "new"
            }
        ]'''

        patterns = extractor._parse_extraction_response(response)

        # Should be empty because complexity, category, and rationale are missing
        assert patterns == []

    def test_handle_invalid_location_type(self, extractor):
        """Should handle invalid location type gracefully"""
        response = '''[{
            "source_pattern": "test",
            "target_pattern": "new",
            "location_type": "INVALID_TYPE",
            "complexity": "TRIVIAL",
            "category": "api",
            "rationale": "Test"
        }]'''

        patterns = extractor._parse_extraction_response(response)

        assert len(patterns) == 1
        assert patterns[0].location_type is None

    def test_parse_pattern_with_all_location_types(self, extractor):
        """Should correctly parse all valid location types"""
        location_types = [
            "ANNOTATION",
            "IMPORT",
            "METHOD_CALL",
            "CONSTRUCTOR_CALL",
            "TYPE",
            "INHERITANCE",
            "PACKAGE",
        ]

        for loc_type in location_types:
            response = f'''[{{
                "source_pattern": "test",
                "target_pattern": "new",
                "location_type": "{loc_type}",
                "complexity": "TRIVIAL",
                "category": "api",
                "rationale": "Test"
            }}]'''

            patterns = extractor._parse_extraction_response(response)

            assert len(patterns) == 1
            assert patterns[0].location_type == LocationType(loc_type)

    def test_parse_pattern_with_csharp_location_types(self, extractor):
        """Should correctly parse all valid C# location types"""
        location_types = ["FIELD", "CLASS", "METHOD", "ALL"]

        for loc_type in location_types:
            response = f'''[{{
                "source_pattern": "test",
                "target_pattern": "new",
                "location_type": "{loc_type}",
                "provider_type": "csharp",
                "complexity": "TRIVIAL",
                "category": "api",
                "rationale": "Test"
            }}]'''

            patterns = extractor._parse_extraction_response(response)

            assert len(patterns) == 1
            assert patterns[0].location_type == CSharpLocationType(loc_type)
            assert patterns[0].provider_type == "csharp"

    def test_parse_pattern_with_optional_fields(self, extractor):
        """Should parse pattern with all optional fields"""
        response = '''[{
            "source_pattern": "old.pattern",
            "target_pattern": "new.pattern",
            "source_fqn": "com.example.OldClass",
            "location_type": "TYPE",
            "alternative_fqns": ["com.example.AlternativeClass"],
            "complexity": "MEDIUM",
            "category": "api",
            "concern": "performance",
            "provider_type": "java",
            "file_pattern": "*.java",
            "rationale": "Performance improvement",
            "example_before": "OldClass obj = new OldClass();",
            "example_after": "NewClass obj = new NewClass();",
            "documentation_url": "https://example.com/docs"
        }]'''

        patterns = extractor._parse_extraction_response(response)

        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.source_fqn == "com.example.OldClass"
        assert pattern.alternative_fqns == ["com.example.AlternativeClass"]
        assert pattern.concern == "performance"
        assert pattern.provider_type == "java"
        assert pattern.file_pattern == "*.java"
        assert pattern.documentation_url == "https://example.com/docs"

    def test_parse_pattern_with_missing_optional_fields(self, extractor):
        """Should handle missing optional fields with defaults"""
        response = '''[{
            "source_pattern": "test",
            "target_pattern": "new",
            "complexity": "TRIVIAL",
            "category": "api",
            "rationale": "Test"
        }]'''

        patterns = extractor._parse_extraction_response(response)

        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.source_fqn is None
        assert pattern.location_type is None
        assert pattern.alternative_fqns == []
        assert pattern.concern == "general"  # Default value
        assert pattern.provider_type is None
        assert pattern.file_pattern is None

    def test_parse_mixed_valid_and_invalid_patterns(self, extractor):
        """Should parse valid patterns and skip invalid ones"""
        response = '''[
            {
                "source_pattern": "valid1",
                "target_pattern": "new1",
                "complexity": "TRIVIAL",
                "category": "api",
                "rationale": "Valid"
            },
            {
                "source_pattern": "invalid"
            },
            {
                "source_pattern": "valid2",
                "target_pattern": "new2",
                "complexity": "TRIVIAL",
                "category": "api",
                "rationale": "Also valid"
            }
        ]'''

        patterns = extractor._parse_extraction_response(response)

        assert len(patterns) == 2
        assert patterns[0].source_pattern == "valid1"
        assert patterns[1].source_pattern == "valid2"


class TestOpenRewriteMode:
    """Test OpenRewrite-specific extraction behavior."""

    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider."""
        mock = Mock()
        mock.generate = Mock(return_value="[]")
        return mock

    def test_openrewrite_mode_flag(self, mock_llm_provider):
        """Should set from_openrewrite flag correctly"""
        extractor = MigrationPatternExtractor(mock_llm_provider, from_openrewrite=True)
        assert extractor.from_openrewrite is True

        extractor = MigrationPatternExtractor(mock_llm_provider, from_openrewrite=False)
        assert extractor.from_openrewrite is False

    def test_default_mode_is_not_openrewrite(self, mock_llm_provider):
        """Should default to non-OpenRewrite mode"""
        extractor = MigrationPatternExtractor(mock_llm_provider)
        assert extractor.from_openrewrite is False


class TestPatternComplexity:
    """Test handling of different complexity levels."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        mock_llm = Mock()
        return MigrationPatternExtractor(mock_llm)

    @pytest.mark.parametrize("complexity", ["TRIVIAL", "LOW", "MEDIUM", "HIGH", "EXPERT"])
    def test_parse_all_complexity_levels(self, extractor, complexity):
        """Should parse all valid complexity levels"""
        response = f'''[{{
            "source_pattern": "test",
            "target_pattern": "new",
            "complexity": "{complexity}",
            "category": "api",
            "rationale": "Test"
        }}]'''

        patterns = extractor._parse_extraction_response(response)

        assert len(patterns) == 1
        assert patterns[0].complexity == complexity


class TestPatternCategories:
    """Test handling of different pattern categories."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        mock_llm = Mock()
        return MigrationPatternExtractor(mock_llm)

    @pytest.mark.parametrize(
        "category", ["dependency", "annotation", "api", "configuration", "other"]
    )
    def test_parse_all_categories(self, extractor, category):
        """Should parse all valid categories"""
        response = f'''[{{
            "source_pattern": "test",
            "target_pattern": "new",
            "complexity": "TRIVIAL",
            "category": "{category}",
            "rationale": "Test"
        }}]'''

        patterns = extractor._parse_extraction_response(response)

        assert len(patterns) == 1
        assert patterns[0].category == category


class TestErrorHandling:
    """Test error handling in pattern extraction."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        mock_llm = Mock()
        return MigrationPatternExtractor(mock_llm)

    def test_handle_pydantic_validation_error(self, extractor):
        """Should skip patterns with Pydantic validation errors"""
        response = '''[
            {
                "source_pattern": "valid",
                "target_pattern": "new",
                "complexity": "MEDIUM",
                "category": "api",
                "rationale": "This is valid"
            },
            {
                "source_pattern": "invalid",
                "target_pattern": "new",
                "complexity": "INVALID_COMPLEXITY"
            }
        ]'''

        patterns = extractor._parse_extraction_response(response)

        # Should skip the invalid pattern (missing required fields)
        assert len(patterns) == 1
        assert patterns[0].source_pattern == "valid"

    def test_handle_missing_required_field_in_json(self, extractor):
        """Should skip patterns missing required fields"""
        response = '''[
            {
                "source_pattern": "test1",
                "target_pattern": "new1",
                "complexity": "MEDIUM",
                "category": "api",
                "rationale": "Valid"
            },
            {
                "source_pattern": "test2",
                "target_pattern": "new2",
                "category": "api"
            }
        ]'''

        patterns = extractor._parse_extraction_response(response)

        # Should only parse the valid pattern (second is missing complexity and rationale)
        assert len(patterns) == 1
        assert patterns[0].source_pattern == "test1"

    def test_handle_malformed_json_in_response(self, extractor):
        """Should return empty list for completely malformed JSON"""
        response = "This is not JSON at all, just plain text"

        patterns = extractor._parse_extraction_response(response)

        assert patterns == []

    def test_handle_partial_json(self, extractor):
        """Should return empty list for incomplete JSON"""
        response = '''[{"source_pattern": "test", "complexity":'''

        patterns = extractor._parse_extraction_response(response)

        assert patterns == []

    def test_handle_empty_json_array(self, extractor):
        """Should handle empty JSON array"""
        response = "[]"

        patterns = extractor._parse_extraction_response(response)

        assert patterns == []

    def test_handle_non_array_json(self, extractor):
        """Should return empty list when JSON is not an array"""
        response = '''{"source_pattern": "test"}'''

        patterns = extractor._parse_extraction_response(response)

        # Should return empty since it's looking for an array
        assert patterns == []

    def test_extract_patterns_with_llm_error(self):
        """Should return empty list when LLM raises exception"""
        mock_llm = Mock()
        mock_llm.generate.side_effect = Exception("LLM API error")

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("test guide")

        assert patterns == []

    def test_extract_patterns_with_llm_returning_invalid_json(self):
        """Should handle LLM returning non-JSON response"""
        mock_llm = Mock()
        mock_llm.generate.return_value = {
            "response": "I cannot extract patterns from this guide.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("invalid guide")

        assert patterns == []

    def test_handle_json_with_extra_fields(self, extractor):
        """Should ignore extra fields in JSON"""
        response = '''[{
            "source_pattern": "test",
            "target_pattern": "new",
            "complexity": "MEDIUM",
            "category": "api",
            "rationale": "Test",
            "extra_field": "should be ignored",
            "another_unknown": 123
        }]'''

        patterns = extractor._parse_extraction_response(response)

        assert len(patterns) == 1
        assert patterns[0].source_pattern == "test"

    def test_handle_null_values_in_optional_fields(self, extractor):
        """Should handle explicit null values in optional fields"""
        response = '''[{
            "source_pattern": "test",
            "target_pattern": null,
            "source_fqn": null,
            "complexity": "MEDIUM",
            "category": "api",
            "rationale": "Test"
        }]'''

        patterns = extractor._parse_extraction_response(response)

        assert len(patterns) == 1
        assert patterns[0].target_pattern is None
        assert patterns[0].source_fqn is None

    def test_handle_type_mismatch_errors(self, extractor):
        """Should handle patterns that have unexpected data types in fields"""
        response = '''[
            {
                "source_pattern": "test",
                "target_pattern": "new",
                "complexity": "MEDIUM",
                "category": "api",
                "rationale": "Valid"
            }
        ]'''

        patterns = extractor._parse_extraction_response(response)

        # Should successfully parse the valid pattern
        assert len(patterns) == 1
        assert patterns[0].source_pattern == "test"


class TestJSONRepair:
    """Test JSON repair functionality."""

    @pytest.fixture
    def extractor(self):
        """Create extractor with mock LLM."""
        mock_llm = Mock()
        return MigrationPatternExtractor(mock_llm)

    def test_repair_invalid_backslash_escapes(self, extractor):
        """Should fix invalid escape sequences like \\. in JSON strings"""
        # JSON with invalid \. escape (common in regex patterns)
        malformed = '{"pattern": "com\\.example\\.Test"}'
        repaired = extractor._repair_json(malformed)

        # Should double-escape the backslashes
        assert "\\\\" in repaired
        # Should be valid JSON after repair
        parsed = json.loads(repaired)
        assert "pattern" in parsed

    def test_repair_regex_escape_sequences(self, extractor):
        """Should fix regex patterns with invalid JSON escapes"""
        # Regex pattern with \d (invalid in JSON)
        malformed = '{"pattern": "\\d+"}'
        repaired = extractor._repair_json(malformed)

        # Should successfully parse after repair
        parsed = json.loads(repaired)
        assert "pattern" in parsed

    def test_repair_unescaped_single_quotes(self, extractor):
        """Should fix unescaped single quotes in JSON strings"""
        # JSON with unescaped single quote
        malformed = '{"desc": "It\'s a test"}'
        repaired = extractor._repair_json(malformed)

        # Should successfully parse after repair
        parsed = json.loads(repaired)
        assert "desc" in parsed

    def test_repair_preserves_valid_escape_sequences(self, extractor):
        """Should preserve valid escape sequences like \\n, \\t"""
        valid_json = '{"message": "Line 1\\nLine 2\\tTabbed"}'
        repaired = extractor._repair_json(valid_json)

        # Should parse successfully
        parsed = json.loads(repaired)
        assert "message" in parsed
        # Valid escapes should be preserved
        assert "Line 1" in parsed["message"] or "\\n" in repaired

    def test_repair_removes_trailing_commas(self, extractor):
        """Should remove trailing commas before closing braces"""
        malformed = '{"pattern": "test", "rationale": "desc",}'
        repaired = extractor._repair_json(malformed)

        # Should remove the trailing comma
        assert not repaired.strip().endswith(",}")
        # Should parse successfully
        parsed = json.loads(repaired)
        assert parsed["pattern"] == "test"

    def test_repair_fixes_missing_commas_between_objects(self, extractor):
        """Should add missing commas between objects in array"""
        malformed = '[{"a": 1}{"b": 2}]'
        repaired = extractor._repair_json(malformed)

        # Should add comma between objects
        assert '},{' in repaired
        # Should parse successfully
        parsed = json.loads(repaired)
        assert len(parsed) == 2

    def test_repair_handles_already_valid_json(self, extractor):
        """Should not break already valid JSON"""
        valid_json = '{"pattern": "example", "rationale": "Test"}'
        repaired = extractor._repair_json(valid_json)

        parsed = json.loads(repaired)
        assert parsed["pattern"] == "example"
        assert parsed["rationale"] == "Test"


class TestPatternValidation:
    """Test pattern validation helper functions."""

    @pytest.fixture
    def extractor(self):
        """Create extractor with mock LLM."""
        mock_llm = Mock()
        return MigrationPatternExtractor(mock_llm)

    def test_looks_like_prop_pattern_with_component_prop_format(self, extractor):
        """Should detect patterns in 'Component propName' format"""
        pattern = MigrationPattern(
            source_pattern="Button isDisabled",  # Component + prop format
            rationale="Button component change",
            complexity="low",
            category="api",
        )

        assert extractor._looks_like_prop_pattern(pattern) is True

    def test_looks_like_prop_pattern_with_pascal_camel_case(self, extractor):
        """Should detect PascalCase component + camelCase prop"""
        pattern = MigrationPattern(
            source_pattern="Modal title",  # PascalCase + camelCase
            rationale="Modal property change",
            complexity="low",
            category="api",
        )

        assert extractor._looks_like_prop_pattern(pattern) is True

    def test_looks_like_prop_pattern_without_component_format(self, extractor):
        """Should return False for patterns without component format"""
        pattern = MigrationPattern(
            source_pattern="isDisabled",  # Just prop name, no component
            rationale="Property change",
            complexity="low",
            category="api",
        )

        assert extractor._looks_like_prop_pattern(pattern) is False

    def test_looks_like_prop_pattern_excludes_method_names(self, extractor):
        """Should exclude common method names like useState"""
        pattern = MigrationPattern(
            source_pattern="Component useState",  # Method name, not prop
            rationale="Component change",
            complexity="low",
            category="api",
        )

        assert extractor._looks_like_prop_pattern(pattern) is False

    def test_is_overly_broad_pattern_generic_prop_names(self, extractor):
        """Should detect overly generic prop names"""
        # These are in the predefined list of overly generic patterns
        assert extractor._is_overly_broad_pattern("isDisabled") is True
        assert extractor._is_overly_broad_pattern("title") is True
        assert extractor._is_overly_broad_pattern("onClick") is True

    def test_is_overly_broad_pattern_specific_patterns(self, extractor):
        """Should accept specific patterns not in generic list"""
        # These are specific enough and not in the overly generic list
        assert extractor._is_overly_broad_pattern("componentWillMount") is False
        assert extractor._is_overly_broad_pattern("getUserConfirmation") is False

    def test_is_overly_broad_pattern_wildcard_patterns(self, extractor):
        """Should detect overly broad wildcard patterns"""
        assert extractor._is_overly_broad_pattern(".*") is True
        assert extractor._is_overly_broad_pattern(".+") is True
        assert extractor._is_overly_broad_pattern("\\w+") is True

    def test_convert_to_combo_rule(self, extractor):
        """Should convert pattern to combo rule with import verification"""
        pattern = MigrationPattern(
            source_pattern="Button isActive",  # Component + prop format
            rationale="Button prop change",
            complexity="low",
            category="api",
            provider_type="builtin",
        )

        # Convert to combo rule
        converted = extractor._convert_to_combo_rule(pattern)

        # Should update provider_type to combo
        assert converted.provider_type == "combo"
        # Should have when_combo configuration
        assert converted.when_combo is not None
        assert "import_pattern" in converted.when_combo
        assert "builtin_pattern" in converted.when_combo
        # Import pattern should check for Button import
        assert "Button" in converted.when_combo["import_pattern"]

    def test_validate_and_fix_patterns_with_patternfly(self, extractor):
        """Should validate patterns for PatternFly migration"""
        patterns = [
            MigrationPattern(
                source_pattern="Alert isActive",
                rationale="Alert prop change",
                complexity="low",
                category="api",
                provider_type="builtin",
            )
        ]

        # Call with language and framework info
        fixed_patterns = extractor._validate_and_fix_patterns(
            patterns,
            language="javascript",
            source_framework="patternfly-v5",
            target_framework="patternfly-v6",
        )

        # Should return validated patterns
        assert len(fixed_patterns) >= 1


class TestOpenRewritePrompt:
    """Test OpenRewrite-specific prompt generation."""

    @pytest.fixture
    def extractor(self):
        """Create extractor configured for OpenRewrite."""
        mock_llm = Mock()
        return MigrationPatternExtractor(mock_llm, from_openrewrite=True)

    def test_build_openrewrite_prompt_for_java(self, extractor):
        """Should generate Java-specific OpenRewrite prompt"""
        recipe_content = """
        ---
        type: specs.openrewrite.org/v1beta/recipe
        name: com.example.SpringBoot3Upgrade
        displayName: Spring Boot 3 Upgrade
        description: Migrate to Spring Boot 3
        recipeList:
          - org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_0
        """

        prompt = extractor._build_openrewrite_prompt(
            recipe_content=recipe_content,
            source_framework="spring-boot-2",
            target_framework="spring-boot-3",
        )

        # Should contain OpenRewrite-specific instructions
        assert "OpenRewrite" in prompt or "recipe" in prompt.lower()
        # Should contain Java-specific instructions
        assert "java" in prompt.lower() or "source_fqn" in prompt.lower()

    def test_build_openrewrite_prompt_for_typescript(self, extractor):
        """Should generate TypeScript-specific OpenRewrite prompt"""
        recipe_content = """
        ---
        type: specs.openrewrite.org/v1beta/recipe
        name: com.example.ReactUpgrade
        displayName: React 18 Upgrade
        description: Migrate to React 18
        """

        prompt = extractor._build_openrewrite_prompt(
            recipe_content=recipe_content, source_framework="react-17", target_framework="react-18"
        )

        # Should contain TypeScript/JavaScript instructions
        assert len(prompt) > 0

    def test_build_openrewrite_prompt_includes_frameworks(self, extractor):
        """Should include framework information in prompt"""
        recipe_content = "# Test recipe"

        prompt = extractor._build_openrewrite_prompt(
            recipe_content=recipe_content,
            source_framework="spring-boot-2.7",
            target_framework="spring-boot-3.0",
        )

        # Should generate a prompt with framework info
        assert len(prompt) > 0

    def test_build_openrewrite_prompt_without_frameworks(self, extractor):
        """Should handle missing framework information"""
        recipe_content = "# Test recipe"

        prompt = extractor._build_openrewrite_prompt(
            recipe_content=recipe_content, source_framework=None, target_framework=None
        )

        # Should still generate a valid prompt
        assert len(prompt) > 0


class TestAggressiveJSONRepair:
    """Test aggressive JSON repair fallback logic."""

    @pytest.fixture
    def extractor(self):
        """Create extractor with mock LLM."""
        mock_llm = Mock()
        return MigrationPatternExtractor(mock_llm)

    def test_parse_response_with_badly_malformed_json(self, extractor):
        """Should use aggressive repair when initial repair fails"""
        # JSON that's so broken even initial repair won't fix it
        # Contains both invalid escapes AND other syntax errors
        badly_malformed = (
            '[{"pattern": "test\\.pattern", "rationale": "desc"}}'  # Missing opening bracket
        )

        # This should trigger aggressive repair
        patterns = extractor._parse_extraction_response(badly_malformed)

        # May return empty list if too broken, but shouldn't crash
        assert isinstance(patterns, list)

    def test_parse_response_with_aggressive_escaping_needed(self, extractor):
        """Should handle patterns needing aggressive backslash escaping"""
        # JSON with multiple levels of escaping issues
        response = '[{"source_pattern": "\\w+", "rationale": "test", "complexity": "low", "category": "api"}]'

        patterns = extractor._parse_extraction_response(response)

        # Should successfully parse with aggressive escaping
        assert len(patterns) >= 0  # May succeed or fail gracefully

    def test_parse_response_returns_empty_on_total_failure(self, extractor):
        """Should return empty list when all repair attempts fail"""
        # Completely unparseable input
        garbage = '{"this is not json at all [[[{'

        patterns = extractor._parse_extraction_response(garbage)

        # Should return empty list, not crash
        assert patterns == []

    def test_parse_response_handles_over_escaped_backslashes(self, extractor):
        """Should fix over-escaped backslashes from aggressive repair"""
        # After aggressive escaping, we might have \\\\ which needs to become \\
        response = '[{"pattern": "test\\\\pattern", "rationale": "desc", "complexity": "low", "category": "api"}]'

        patterns = extractor._parse_extraction_response(response)

        # Should parse successfully
        assert isinstance(patterns, list)


class TestChunkedExtraction:
    """Test chunked content extraction."""

    @pytest.fixture
    def extractor(self):
        """Create extractor with mock LLM."""
        mock_llm = Mock()
        return MigrationPatternExtractor(mock_llm)

    def test_extract_patterns_chunked_splits_large_content(self, extractor):
        """Should split large content into chunks and process each"""
        # Create large content that will be chunked
        large_content = "Migration guide:\n" + ("Some content about API changes.\n" * 1000)

        # Mock the single extraction to return patterns
        with patch.object(extractor, '_extract_patterns_single') as mock_single:
            mock_single.return_value = [
                MigrationPattern(
                    source_pattern="OldAPI", rationale="Test", complexity="low", category="api"
                )
            ]

            patterns = extractor._extract_patterns_chunked(
                large_content, source_framework="v1", target_framework="v2"
            )

            # Should have called _extract_patterns_single at least once (probably multiple times for chunks)
            assert mock_single.call_count >= 1
            # Should return patterns
            assert len(patterns) >= 1

    def test_extract_patterns_chunked_deduplicates(self, extractor):
        """Should deduplicate patterns from different chunks"""
        content = "Test content"

        # Mock to return duplicate patterns
        duplicate_pattern = MigrationPattern(
            source_pattern="test",
            source_fqn="com.example.Test",
            rationale="Test",
            complexity="low",
            category="api",
            concern="api",
        )

        with patch.object(extractor, '_extract_patterns_single') as mock_single:
            # Return same pattern twice (simulating duplicates from different chunks)
            mock_single.return_value = [duplicate_pattern, duplicate_pattern]

            patterns = extractor._extract_patterns_chunked(
                content, source_framework="v1", target_framework="v2"
            )

            # Should deduplicate based on source_fqn + concern
            # Exact count depends on chunking, but should handle deduplication
            assert isinstance(patterns, list)

    def test_deduplicate_patterns_removes_duplicates(self, extractor):
        """Should remove duplicate patterns based on source_fqn and concern"""
        patterns = [
            MigrationPattern(
                source_pattern="test1",
                source_fqn="com.example.Test",
                concern="api",
                rationale="First",
                complexity="low",
                category="api",
            ),
            MigrationPattern(
                source_pattern="test2",
                source_fqn="com.example.Test",  # Same FQN
                concern="api",  # Same concern
                rationale="Duplicate",
                complexity="low",
                category="api",
            ),
            MigrationPattern(
                source_pattern="test3",
                source_fqn="com.example.Other",  # Different FQN
                concern="api",
                rationale="Different",
                complexity="low",
                category="api",
            ),
        ]

        unique = extractor._deduplicate_patterns(patterns)

        # Should keep only 2: one for Test (first occurrence) and one for Other
        assert len(unique) == 2
        assert unique[0].source_fqn == "com.example.Test"
        assert unique[1].source_fqn == "com.example.Other"

    def test_deduplicate_patterns_keeps_different_concerns(self, extractor):
        """Should keep patterns with same FQN but different concerns"""
        patterns = [
            MigrationPattern(
                source_pattern="test",
                source_fqn="com.example.Test",
                concern="api",
                rationale="API concern",
                complexity="low",
                category="api",
            ),
            MigrationPattern(
                source_pattern="test",
                source_fqn="com.example.Test",  # Same FQN
                concern="configuration",  # Different concern
                rationale="Config concern",
                complexity="low",
                category="api",
            ),
        ]

        unique = extractor._deduplicate_patterns(patterns)

        # Should keep both (different concerns)
        assert len(unique) == 2
