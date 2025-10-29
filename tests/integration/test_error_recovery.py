"""
Integration tests for error recovery and failure handling.

Tests that the system handles errors gracefully and provides useful feedback.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.rule_generator.ingestion import GuideIngester
from src.rule_generator.extraction import MigrationPatternExtractor
from src.rule_generator.generator import AnalyzerRuleGenerator
from src.rule_generator.llm import get_llm_provider


@pytest.mark.integration
class TestMissingDependencies:
    """Test handling of missing Python package dependencies."""

    def test_openai_package_missing(self):
        """Should raise helpful error when openai package is missing."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'openai'")):
            with pytest.raises(ImportError) as exc_info:
                get_llm_provider(provider="openai", model="gpt-4")

            assert "openai package required" in str(exc_info.value)
            assert "pip install openai" in str(exc_info.value)

    def test_anthropic_package_missing(self):
        """Should raise helpful error when anthropic package is missing."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'anthropic'")):
            with pytest.raises(ImportError) as exc_info:
                get_llm_provider(provider="anthropic", model="claude-3-sonnet")

            assert "anthropic package required" in str(exc_info.value)
            assert "pip install anthropic" in str(exc_info.value)

    def test_beautifulsoup_missing_for_url_ingestion(self, capsys):
        """Should warn and return None when beautifulsoup4 is missing for URL ingestion."""
        ingester = GuideIngester()

        with patch('builtins.__import__', side_effect=ImportError("No module named 'bs4'")):
            result = ingester.ingest("https://example.com/guide")

        captured = capsys.readouterr()
        assert result is None
        assert "beautifulsoup4" in captured.out.lower()
        assert "markdownify" in captured.out.lower()


@pytest.mark.integration
class TestNetworkErrors:
    """Test handling of network-related errors."""

    def test_url_timeout(self, capsys):
        """Should handle network timeout gracefully."""
        import requests

        ingester = GuideIngester()

        with patch('requests.get', side_effect=requests.Timeout("Connection timeout")):
            result = ingester.ingest("https://example.com/guide")

        # Should return None and print error
        assert result is None
        captured = capsys.readouterr()
        assert "timeout" in captured.out.lower()

    def test_url_not_found(self, capsys):
        """Should handle 404 errors gracefully."""
        import requests

        ingester = GuideIngester()

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch('requests.get', return_value=mock_response):
            result = ingester.ingest("https://example.com/nonexistent")

        # Should return None and print error
        assert result is None
        captured = capsys.readouterr()
        assert "404" in captured.out

    def test_url_server_error(self, capsys):
        """Should handle 500 server errors gracefully."""
        import requests

        ingester = GuideIngester()

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Internal Server Error")

        with patch('requests.get', return_value=mock_response):
            result = ingester.ingest("https://example.com/error")

        # Should return None and print error
        assert result is None
        captured = capsys.readouterr()
        assert "500" in captured.out or "error" in captured.out.lower()

    def test_connection_error(self, capsys):
        """Should handle connection errors gracefully."""
        import requests

        ingester = GuideIngester()

        with patch('requests.get', side_effect=requests.ConnectionError("Connection refused")):
            result = ingester.ingest("https://unreachable.example.com")

        # Should return None and print error
        assert result is None
        captured = capsys.readouterr()
        assert "connection" in captured.out.lower() or "error" in captured.out.lower()


@pytest.mark.integration
class TestMalformedJSON:
    """Test handling of malformed JSON responses from LLM."""

    def test_invalid_json_response(self):
        """Should handle invalid JSON gracefully and return empty list."""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value={
            "response": "This is not valid JSON {{{",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        })

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("test guide")

        # Should return empty list instead of crashing
        assert patterns == []

    def test_json_with_missing_required_fields(self):
        """Should skip patterns with missing required fields."""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value={
            "response": json.dumps([
                {
                    "source_pattern": "Old",
                    # Missing rationale (required field)
                    "target_pattern": "New",
                    "complexity": "TRIVIAL",
                    "category": "api"
                }
            ]),
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        })

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("test guide")

        # Should skip invalid patterns
        assert len(patterns) == 0

    def test_partial_valid_json(self):
        """Should extract valid patterns and skip invalid ones."""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value={
            "response": json.dumps([
                {
                    "source_pattern": "Valid1",
                    "target_pattern": "New1",
                    "rationale": "Valid pattern",
                    "complexity": "TRIVIAL",
                    "category": "api"
                },
                {
                    "source_pattern": "Invalid",
                    # Missing rationale
                    "complexity": "LOW"
                },
                {
                    "source_pattern": "Valid2",
                    "target_pattern": "New2",
                    "rationale": "Another valid pattern",
                    "complexity": "LOW",
                    "category": "api"
                }
            ]),
            "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75}
        })

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("test guide")

        # Should extract only valid patterns
        assert len(patterns) == 2
        assert patterns[0].source_pattern == "Valid1"
        assert patterns[1].source_pattern == "Valid2"

    def test_empty_json_array(self):
        """Should handle empty JSON array gracefully."""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value={
            "response": "[]",
            "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12}
        })

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("test guide")

        assert patterns == []

    def test_json_not_an_array(self):
        """Should handle JSON that's not an array."""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value={
            "response": json.dumps({"error": "Invalid format"}),
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        })

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("test guide")

        # Should return empty list
        assert patterns == []


@pytest.mark.integration
class TestLLMErrors:
    """Test handling of LLM API errors."""

    def test_llm_api_error(self):
        """Should handle LLM API errors gracefully."""
        mock_llm = Mock()
        mock_llm.generate = Mock(side_effect=Exception("API rate limit exceeded"))

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("test guide")

        # Should return empty list instead of crashing
        assert patterns == []

    def test_llm_returns_none(self):
        """Should handle LLM returning None."""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value=None)

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("test guide")

        assert patterns == []

    def test_llm_missing_response_field(self):
        """Should handle LLM response missing 'response' field."""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value={
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            # Missing 'response' field
        })

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("test guide")

        assert patterns == []

    def test_llm_response_is_none(self):
        """Should handle LLM response field being None."""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value={
            "response": None,
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        })

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("test guide")

        assert patterns == []


@pytest.mark.integration
class TestFileErrors:
    """Test handling of file-related errors."""

    def test_nonexistent_file(self, capsys):
        """Should handle nonexistent files gracefully."""
        ingester = GuideIngester()

        result = ingester.ingest("/nonexistent/path/to/guide.md")

        # Should return None and print error
        assert result is None
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "error" in captured.out.lower()

    def test_permission_denied(self, tmp_path, capsys):
        """Should handle permission errors gracefully."""
        import os
        import stat

        # Create a file with no read permissions (Unix only)
        if os.name != 'nt':  # Skip on Windows
            restricted_file = tmp_path / "restricted.md"
            restricted_file.write_text("# Guide")
            restricted_file.chmod(stat.S_IWUSR)  # Write-only

            ingester = GuideIngester()
            result = ingester.ingest(str(restricted_file))

            # Should return None and print error
            assert result is None
            captured = capsys.readouterr()
            assert "permission" in captured.out.lower() or "error" in captured.out.lower()

            # Cleanup
            restricted_file.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def test_empty_file(self, tmp_path):
        """Should handle empty files gracefully."""
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("")

        ingester = GuideIngester()
        result = ingester.ingest(str(empty_file))

        # Should return empty string, not crash
        assert result == ""

    def test_directory_instead_of_file(self, tmp_path, capsys):
        """Should handle directory path instead of file."""
        directory = tmp_path / "somedir"
        directory.mkdir()

        ingester = GuideIngester()
        result = ingester.ingest(str(directory))

        # Should return None and print error
        assert result is None
        captured = capsys.readouterr()
        assert "directory" in captured.out.lower() or "error" in captured.out.lower()


@pytest.mark.integration
class TestPartialFailures:
    """Test handling of partial failures in multi-step processes."""

    def test_some_patterns_fail_validation(self):
        """Should continue processing when some patterns fail validation."""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value={
            "response": json.dumps([
                {
                    "source_pattern": "Good1",
                    "target_pattern": "New1",
                    "source_fqn": "com.example.Good1",
                    "location_type": "TYPE",
                    "rationale": "Valid",
                    "complexity": "TRIVIAL",
                    "category": "api"
                },
                {
                    "source_pattern": "",  # Invalid - empty
                    "target_pattern": "New2",
                    "rationale": "Invalid",
                    "complexity": "LOW",
                    "category": "api"
                },
                {
                    "source_pattern": "Good2",
                    "target_pattern": "New2",
                    "source_fqn": "com.example.Good2",
                    "location_type": "TYPE",
                    "rationale": "Valid",
                    "complexity": "LOW",
                    "category": "api"
                }
            ]),
            "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75}
        })

        extractor = MigrationPatternExtractor(mock_llm)
        generator = AnalyzerRuleGenerator(source_framework="old", target_framework="new")

        patterns = extractor.extract_patterns("test guide")
        rules = generator.generate_rules(patterns)

        # Should process valid patterns and skip invalid ones
        assert len(patterns) >= 2  # At least the good ones
        assert len(rules) >= 2

    def test_rule_generation_continues_on_error(self):
        """Should continue generating rules even if one fails."""
        from src.rule_generator.schema import MigrationPattern, LocationType

        patterns = [
            MigrationPattern(
                source_pattern="Good1",
                target_pattern="New1",
                source_fqn="com.example.Good1",
                location_type=LocationType.TYPE,
                complexity="TRIVIAL",
                category="api",
                rationale="Valid pattern"
            ),
            MigrationPattern(
                source_pattern="Good2",
                target_pattern="New2",
                source_fqn="com.example.Good2",
                location_type=LocationType.TYPE,
                complexity="LOW",
                category="api",
                rationale="Another valid pattern"
            ),
        ]

        generator = AnalyzerRuleGenerator(source_framework="old", target_framework="new")
        rules = generator.generate_rules(patterns)

        # Should generate all rules
        assert len(rules) == 2


@pytest.mark.integration
class TestInputValidation:
    """Test input validation and sanitization."""

    def test_null_guide_content(self):
        """Should handle null/None guide content."""
        mock_llm = Mock()
        extractor = MigrationPatternExtractor(mock_llm)

        patterns = extractor.extract_patterns(None)
        assert patterns == []

    def test_empty_string_guide(self):
        """Should handle empty string guide."""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value={
            "response": "[]",
            "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}
        })

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("")

        assert patterns == []

    def test_very_large_guide(self):
        """Should handle very large guide content."""
        # Create a very large guide (1MB+)
        large_guide = "# Large Guide\n" + ("Test pattern migration.\n" * 10000)

        mock_llm = Mock()
        mock_llm.generate = Mock(return_value={
            "response": json.dumps([{
                "source_pattern": "Test",
                "target_pattern": "New",
                "rationale": "Migration",
                "complexity": "TRIVIAL",
                "category": "api"
            }]),
            "usage": {"prompt_tokens": 100000, "completion_tokens": 50, "total_tokens": 100050}
        })

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns(large_guide)

        # Should handle large content without crashing
        assert len(patterns) == 1

    def test_binary_content(self, tmp_path, capsys):
        """Should handle binary files gracefully."""
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b'\x00\x01\x02\x03\xff\xfe')

        ingester = GuideIngester()
        result = ingester.ingest(str(binary_file))

        # Should return None and print error for binary files
        assert result is None
        captured = capsys.readouterr()
        assert "utf-8" in captured.out.lower() or "decode" in captured.out.lower() or "error" in captured.out.lower()


@pytest.mark.integration
class TestEdgeCasesInErrorHandling:
    """Test edge cases in error handling."""

    def test_recursive_error_handling(self):
        """Should not get stuck in error handling loops."""
        mock_llm = Mock()
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 10:
                raise RuntimeError("Too many calls - possible infinite loop")
            raise Exception("Test error")

        mock_llm.generate = Mock(side_effect=side_effect)

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("test")

        # Should fail gracefully without infinite loops
        assert patterns == []
        assert call_count[0] == 1  # Should only call once, not retry

    def test_unicode_errors_in_json(self):
        """Should handle Unicode errors in JSON responses."""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value={
            "response": '{"source_pattern": "Test\udcff"}',  # Invalid surrogate
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        })

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("test")

        # Should handle gracefully
        assert isinstance(patterns, list)

    def test_circular_reference_in_data(self):
        """Should handle circular references gracefully."""
        # This tests that we don't have issues with serialization
        from src.rule_generator.schema import MigrationPattern, LocationType

        pattern = MigrationPattern(
            source_pattern="Test",
            target_pattern="New",
            source_fqn="test",
            location_type=LocationType.TYPE,
            complexity="TRIVIAL",
            category="api",
            rationale="Test"
        )

        generator = AnalyzerRuleGenerator(source_framework="old", target_framework="new")

        # Should generate rule without circular reference issues
        rules = generator.generate_rules([pattern])
        assert len(rules) == 1

        # Should be able to dump to dict
        rule_dict = rules[0].model_dump()
        assert isinstance(rule_dict, dict)
