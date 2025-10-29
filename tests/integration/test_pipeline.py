"""
Integration tests for complete pipeline workflows.
"""
import pytest
from unittest.mock import patch

from src.rule_generator.ingestion import GuideIngester
from src.rule_generator.extraction import MigrationPatternExtractor
from src.rule_generator.generator import AnalyzerRuleGenerator


@pytest.mark.integration
class TestFullPipeline:
    """Test complete end-to-end workflows."""

    def test_java_guide_to_rules(self, mock_llm_provider):
        """Should convert Java migration guide to analyzer rules."""
        # Sample guide
        guide = """# Spring Boot Migration
        
## Package Changes
The javax.servlet package has been renamed to jakarta.servlet.
"""

        # Setup components
        ingester = GuideIngester()
        extractor = MigrationPatternExtractor(mock_llm_provider)
        generator = AnalyzerRuleGenerator(
            source_framework="spring-boot-3",
            target_framework="spring-boot-4"
        )

        # Step 1: Ingest guide
        guide_content = ingester.ingest(guide)
        assert guide_content is not None
        assert "javax.servlet" in guide_content

        # Step 2: Extract patterns
        patterns = extractor.extract_patterns(guide_content)
        assert len(patterns) == 1
        assert patterns[0].source_pattern == "javax.servlet"
        assert patterns[0].target_pattern == "jakarta.servlet"

        # Step 3: Generate rules
        rules = generator.generate_rules(patterns)
        assert len(rules) == 1
        assert rules[0].ruleID == "spring-boot-3-to-spring-boot-4-00000"
        assert "java.referenced" in rules[0].when

    def test_pipeline_with_file_input(self, mock_llm_provider, tmp_path):
        """Should process migration guide from file."""
        # Write guide to file
        guide_file = tmp_path / "guide.md"
        guide_file.write_text("# Guide\njavax.servlet -> jakarta.servlet")

        # Setup
        ingester = GuideIngester()
        extractor = MigrationPatternExtractor(mock_llm_provider)
        generator = AnalyzerRuleGenerator()

        # Process file
        guide_content = ingester.ingest(str(guide_file))
        patterns = extractor.extract_patterns(guide_content)
        rules = generator.generate_rules(patterns)

        # Verify
        assert guide_content is not None
        assert len(patterns) > 0
        assert len(rules) > 0

    @patch('src.rule_generator.ingestion.requests.get')
    def test_pipeline_with_url_input(self, mock_get, mock_llm_provider):
        """Should process migration guide from URL."""
        from unittest.mock import Mock
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.content = b"<html><body>javax.servlet migration</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Setup
        ingester = GuideIngester()
        extractor = MigrationPatternExtractor(mock_llm_provider)

        # Process URL
        guide_content = ingester.ingest("https://example.com/guide")
        patterns = extractor.extract_patterns(guide_content)

        # Verify
        assert guide_content is not None
        assert len(patterns) > 0

    def test_llm_error_handling(self):
        """Should handle LLM errors gracefully."""
        from unittest.mock import Mock
        
        # Mock LLM that raises error
        mock_llm = Mock()
        mock_llm.generate = Mock(side_effect=Exception("API error"))

        extractor = MigrationPatternExtractor(mock_llm)
        patterns = extractor.extract_patterns("test guide")

        # Should return empty instead of crashing
        assert patterns == []
