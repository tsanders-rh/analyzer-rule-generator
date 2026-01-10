"""
Tests for security utilities module.

Tests path validation, filename sanitization, and input validation
to prevent security vulnerabilities.
"""

import os
import tempfile
from pathlib import Path

import pytest

from rule_generator.security import (
    is_safe_path,
    sanitize_filename,
    validate_complexity,
    validate_framework_name,
    validate_llm_response,
    validate_path,
    validate_rule_id,
)


class TestValidatePath:
    """Tests for path validation and traversal prevention."""

    def test_valid_relative_path(self, tmp_path):
        """Should accept valid relative paths within base directory."""
        base_dir = tmp_path
        test_path = base_dir / "subdir" / "file.txt"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.touch()

        result = validate_path(test_path, base_dir)
        assert result.is_absolute()
        assert result.is_relative_to(base_dir)

    def test_valid_absolute_path(self, tmp_path):
        """Should accept valid absolute paths within base directory."""
        base_dir = tmp_path
        test_path = base_dir / "file.txt"
        test_path.touch()

        result = validate_path(test_path.absolute(), base_dir)
        assert result == test_path.resolve()

    def test_parent_directory_traversal(self, tmp_path):
        """Should reject parent directory traversal attempts."""
        base_dir = tmp_path / "safe"
        base_dir.mkdir()

        malicious_paths = [
            "../../../etc/passwd",
            "../../etc/passwd",
            "../outside.txt",
            "subdir/../../outside.txt",
        ]

        for malicious in malicious_paths:
            with pytest.raises(ValueError, match="outside allowed directory"):
                validate_path(Path(malicious), base_dir)

    def test_windows_parent_traversal(self, tmp_path):
        """Should reject Windows-style parent directory traversal."""
        base_dir = tmp_path / "safe"
        base_dir.mkdir()

        malicious_paths = [
            "..\\..\\..\\windows\\system32",
            "..\\outside.txt",
        ]

        for malicious in malicious_paths:
            with pytest.raises(ValueError, match="outside allowed directory"):
                validate_path(Path(malicious), base_dir)

    def test_absolute_path_outside_base(self, tmp_path):
        """Should reject absolute paths outside base directory."""
        base_dir = tmp_path / "safe"
        base_dir.mkdir()

        malicious_paths = [
            "/etc/passwd",
            "/tmp/malicious.txt",
        ]

        for malicious in malicious_paths:
            with pytest.raises(ValueError, match="outside allowed directory"):
                validate_path(Path(malicious), base_dir)

    def test_symlink_outside_base(self, tmp_path):
        """Should reject symlinks pointing outside base directory."""
        base_dir = tmp_path / "safe"
        base_dir.mkdir()

        # Create a file outside base
        outside_file = tmp_path / "outside.txt"
        outside_file.touch()

        # Create symlink inside base pointing outside
        symlink = base_dir / "link.txt"
        try:
            symlink.symlink_to(outside_file)
        except OSError:
            pytest.skip("Cannot create symlinks (Windows/permissions)")

        with pytest.raises(ValueError, match="outside allowed directory"):
            validate_path(symlink, base_dir)

    def test_nonexistent_path(self, tmp_path):
        """Should handle nonexistent paths appropriately."""
        base_dir = tmp_path
        nonexistent = base_dir / "nonexistent" / "file.txt"

        # Should not raise for nonexistent paths within base
        result = validate_path(nonexistent, base_dir)
        assert result.is_relative_to(base_dir)

    def test_invalid_path(self, tmp_path):
        """Should handle invalid/inaccessible paths."""
        base_dir = tmp_path

        # Null bytes in path
        with pytest.raises(ValueError):
            validate_path(Path("file\x00.txt"), base_dir)


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_valid_filename(self):
        """Should accept valid filenames unchanged."""
        valid_names = [
            "rules.yaml",
            "migration-guide.md",
            "test_file_123.txt",
            "output.yaml",
        ]

        for name in valid_names:
            assert sanitize_filename(name) == name

    def test_remove_path_separators(self):
        """Should remove path separators from filenames."""
        assert sanitize_filename("path/to/file.txt") == "pathtofile.txt"
        assert sanitize_filename("path\\to\\file.txt") == "pathtofile.txt"

    def test_remove_parent_references(self):
        """Should remove parent directory references."""
        assert sanitize_filename("../../../etc/passwd") == "etcpasswd"
        assert sanitize_filename("..\\..\\windows\\system32") == "windowssystem32"

    def test_remove_dangerous_characters(self):
        """Should remove dangerous characters."""
        dangerous = "file|<>:\"?*\n\r.txt"
        sanitized = sanitize_filename(dangerous)
        assert "|" not in sanitized
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized
        assert '"' not in sanitized
        assert "?" not in sanitized
        assert "*" not in sanitized
        assert "\n" not in sanitized
        assert "\r" not in sanitized

    def test_remove_null_bytes(self):
        """Should remove null bytes."""
        assert sanitize_filename("file\x00.txt") == "file.txt"

    def test_strip_leading_trailing(self):
        """Should strip leading/trailing dots and spaces."""
        assert sanitize_filename("  file.txt  ") == "file.txt"
        assert sanitize_filename("...file.txt...") == "file.txt"
        assert sanitize_filename(". . file.txt . .") == "file.txt"

    def test_allow_path_mode(self):
        """Should allow path separators when allow_path=True."""
        result = sanitize_filename("output/rules.yaml", allow_path=True)
        assert result == "output/rules.yaml"
        assert "/" in result

    def test_empty_filename_error(self):
        """Should reject empty filenames."""
        with pytest.raises(ValueError, match="cannot be empty"):
            sanitize_filename("")

    def test_invalid_after_sanitization(self):
        """Should reject filenames that become empty after sanitization."""
        with pytest.raises(ValueError, match="invalid after sanitization"):
            sanitize_filename("...")
        with pytest.raises(ValueError, match="invalid after sanitization"):
            sanitize_filename("   ")


class TestIsSafePath:
    """Tests for safe path heuristic checks."""

    def test_safe_relative_paths(self):
        """Should accept safe relative paths."""
        safe_paths = [
            "output/rules.yaml",
            "subdir/file.txt",
            "migration-guide.md",
        ]

        for path in safe_paths:
            assert is_safe_path(path) is True

    def test_safe_absolute_paths(self):
        """Should accept safe absolute paths."""
        safe_paths = [
            "/home/user/project/output.yaml",
            "/tmp/test.txt",
        ]

        # Note: /etc, /root, etc. are considered unsafe
        for path in safe_paths:
            assert is_safe_path(path) is True

    def test_reject_parent_traversal(self):
        """Should reject parent directory traversal."""
        unsafe_paths = [
            "../../../etc/passwd",
            "../../outside.txt",
            "..\\..\\windows\\system32",
        ]

        for path in unsafe_paths:
            assert is_safe_path(path) is False

    def test_reject_null_bytes(self):
        """Should reject paths with null bytes."""
        assert is_safe_path("file\x00.txt") is False

    def test_reject_sensitive_directories(self):
        """Should reject paths to sensitive directories."""
        sensitive_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "/root/.ssh/id_rsa",
            "/var/log/secure",
            "/proc/self/environ",
            "/sys/class/net",
        ]

        for path in sensitive_paths:
            assert is_safe_path(path) is False


class TestValidateFrameworkName:
    """Tests for framework name validation."""

    def test_valid_framework_names(self):
        """Should accept valid framework names."""
        valid_names = [
            "spring-boot-3",
            "patternfly-v5",
            "react-18.2.0",
            "quarkus_2.0",
            "jakarta.ee.10",
        ]

        for name in valid_names:
            assert validate_framework_name(name) == name

    def test_strip_whitespace(self):
        """Should strip leading/trailing whitespace."""
        assert validate_framework_name("  spring-boot-3  ") == "spring-boot-3"

    def test_empty_name(self):
        """Should reject empty names."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_framework_name("")
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_framework_name("   ")

    def test_too_long(self):
        """Should reject names that are too long."""
        long_name = "a" * 101
        with pytest.raises(ValueError, match="too long"):
            validate_framework_name(long_name)

    def test_invalid_characters(self):
        """Should reject names with invalid characters."""
        invalid_names = [
            "spring/boot",
            "react@18",
            "framework name",  # space
            "test|invalid",
            "bad<name",
        ]

        for name in invalid_names:
            with pytest.raises(ValueError, match="Invalid framework name"):
                validate_framework_name(name)


class TestValidateComplexity:
    """Tests for complexity value validation."""

    def test_valid_complexity_values(self):
        """Should accept valid complexity values."""
        valid_values = ["TRIVIAL", "LOW", "MEDIUM", "HIGH", "EXPERT"]

        for value in valid_values:
            assert validate_complexity(value) == value

    def test_case_insensitive(self):
        """Should accept lowercase and normalize to uppercase."""
        assert validate_complexity("low") == "LOW"
        assert validate_complexity("Medium") == "MEDIUM"
        assert validate_complexity("trivial") == "TRIVIAL"

    def test_strip_whitespace(self):
        """Should strip whitespace."""
        assert validate_complexity("  LOW  ") == "LOW"

    def test_empty_value(self):
        """Should reject empty values."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_complexity("")

    def test_invalid_value(self):
        """Should reject invalid complexity values."""
        invalid_values = ["SUPER_HIGH", "NONE", "EASY", "HARD"]

        for value in invalid_values:
            with pytest.raises(ValueError, match="Invalid complexity"):
                validate_complexity(value)


class TestValidateRuleId:
    """Tests for rule ID format validation."""

    def test_valid_rule_ids(self):
        """Should accept valid rule IDs."""
        valid_ids = [
            "spring-boot-to-quarkus-00000",
            "patternfly-v5-to-patternfly-v6-00010",
            "migration-12345",
            "test-rule-99990",
        ]

        for rule_id in valid_ids:
            assert validate_rule_id(rule_id) == rule_id

    def test_strip_whitespace(self):
        """Should strip whitespace."""
        assert validate_rule_id("  migration-00000  ") == "migration-00000"

    def test_empty_rule_id(self):
        """Should reject empty rule IDs."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_rule_id("")
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_rule_id("   ")

    def test_invalid_format(self):
        """Should reject invalid formats."""
        invalid_ids = [
            "no-number",
            "123-only-three-digits",
            "missingdash00000",  # No dash before number
            "00000",  # No prefix
            "prefix_00000",  # Underscore instead of dash
        ]

        for rule_id in invalid_ids:
            with pytest.raises(ValueError, match="Invalid rule ID format"):
                validate_rule_id(rule_id)

    def test_source_target_validation(self):
        """Should validate source/target in rule ID when provided."""
        rule_id = "spring-boot-to-quarkus-00000"

        # Should pass with correct source/target
        result = validate_rule_id(rule_id, source="spring-boot", target="quarkus")
        assert result == rule_id

        # Should fail with wrong source/target
        with pytest.raises(ValueError, match="does not match expected prefix"):
            validate_rule_id(rule_id, source="wrong", target="framework")


class TestValidateLLMResponse:
    """Tests for LLM response validation."""

    def test_valid_json_array(self):
        """Should accept valid JSON arrays."""
        valid_responses = [
            '[{"key": "value"}]',
            '[]',
            '[1, 2, 3]',
            '[{"a": 1}, {"b": 2}]',
        ]

        for response in valid_responses:
            result = validate_llm_response(response, expected_format="json_array")
            assert result == response

    def test_strips_markdown_code_blocks(self):
        """Should strip markdown code blocks from LLM responses."""
        # Test with ```json ... ```
        markdown_response = '```json\n[{"key": "value"}]\n```'
        result = validate_llm_response(markdown_response, expected_format="json_array")
        assert result == '[{"key": "value"}]'

        # Test with ```javascript ... ```
        markdown_response = '```javascript\n{"key": "value"}\n```'
        result = validate_llm_response(markdown_response, expected_format="json_object")
        assert result == '{"key": "value"}'

        # Test with ``` ... ``` (no language specified)
        markdown_response = '```\n[1, 2, 3]\n```'
        result = validate_llm_response(markdown_response, expected_format="json_array")
        assert result == '[1, 2, 3]'

    def test_valid_json_object(self):
        """Should accept valid JSON objects."""
        valid_responses = [
            '{"key": "value"}',
            '{}',
            '{"nested": {"key": "value"}}',
        ]

        for response in valid_responses:
            result = validate_llm_response(response, expected_format="json_object")
            assert result == response

    def test_empty_response(self):
        """Should reject empty responses."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_llm_response("", expected_format="json_array")
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_llm_response("   ", expected_format="json_array")

    def test_too_short(self):
        """Should reject responses that are too short."""
        with pytest.raises(ValueError, match="too short"):
            validate_llm_response("[", expected_format="json_array")

    def test_json_array_invalid_start(self):
        """Should reject responses that don't contain [ and ]."""
        with pytest.raises(ValueError, match="does not contain"):
            validate_llm_response('{"key": "value"}', expected_format="json_array")

    def test_json_array_invalid_end(self):
        """Should reject responses with malformed array structure."""
        with pytest.raises(ValueError, match="malformed JSON array structure"):
            validate_llm_response(']{"key": "value"}[', expected_format="json_array")

    def test_json_object_invalid_start(self):
        """Should reject JSON objects that don't start with {."""
        with pytest.raises(ValueError, match="does not start with"):
            validate_llm_response('[1, 2, 3]', expected_format="json_object")

    def test_json_object_invalid_end(self):
        """Should reject JSON objects that don't end with }."""
        with pytest.raises(ValueError, match="does not end with"):
            validate_llm_response('{"key": "value"', expected_format="json_object")

    def test_yaml_format(self):
        """Should accept YAML format (not pure JSON)."""
        yaml_response = """rules:
  - id: 1
    name: test"""
        result = validate_llm_response(yaml_response, expected_format="yaml")
        assert result == yaml_response

    def test_yaml_rejects_json(self):
        """Should reject JSON when expecting YAML."""
        with pytest.raises(ValueError, match="looks like JSON"):
            validate_llm_response('[1, 2, 3]', expected_format="yaml")
        with pytest.raises(ValueError, match="looks like JSON"):
            validate_llm_response('{"key": "value"}', expected_format="yaml")
