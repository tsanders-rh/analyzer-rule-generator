"""
Unit tests for src/rule_generator/extraction.py

Tests pattern extraction logic, language detection, and LLM response parsing.
"""
import json
import pytest
from unittest.mock import Mock, patch

from src.rule_generator.extraction import (
    MigrationPatternExtractor,
    detect_language_from_frameworks
)
from src.rule_generator.schema import MigrationPattern, LocationType


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
            "PACKAGE"
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

    @pytest.mark.parametrize("complexity", [
        "TRIVIAL",
        "LOW",
        "MEDIUM",
        "HIGH",
        "EXPERT"
    ])
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

    @pytest.mark.parametrize("category", [
        "dependency",
        "annotation",
        "api",
        "configuration",
        "other"
    ])
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
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
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
        """Should skip patterns with type mismatches"""
        response = '''[
            {
                "source_pattern": "test",
                "target_pattern": "new",
                "complexity": "MEDIUM",
                "category": "api",
                "rationale": "Valid"
            },
            {
                "source_pattern": 123,
                "target_pattern": "new",
                "complexity": "MEDIUM",
                "category": "api",
                "rationale": "Invalid - source_pattern should be string"
            }
        ]'''

        patterns = extractor._parse_extraction_response(response)

        # Should only get the valid pattern
        assert len(patterns) == 1
        assert patterns[0].source_pattern == "test"
