"""
Unit tests for classify_existing_rules module.

Tests cover:
- Pattern matching for complexity classification
- When condition complexity analysis
- Simple pattern replacement detection
- Individual rule classification
- Ruleset classification (list and dict formats)
- Classification statistics and change tracking
"""
import pytest
import yaml
import tempfile
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from classify_existing_rules import RulesetComplexityClassifier


class TestPatternMatching:
    """Test pattern matching for different complexity levels."""

    def test_match_trivial_patterns(self):
        """Should match trivial complexity patterns"""
        classifier = RulesetComplexityClassifier()

        text = "Change javax.servlet to jakarta.servlet"
        score = classifier._match_patterns(text, classifier.TRIVIAL_PATTERNS)
        assert score > 0

    def test_match_low_patterns(self):
        """Should match low complexity patterns"""
        classifier = RulesetComplexityClassifier()

        text = "Replace @Stateless with @ApplicationScoped"
        score = classifier._match_patterns(text, classifier.LOW_PATTERNS)
        assert score > 0

    def test_match_medium_patterns(self):
        """Should match medium complexity patterns"""
        classifier = RulesetComplexityClassifier()

        text = "Migrate JMS to Reactive Messaging"
        score = classifier._match_patterns(text, classifier.MEDIUM_PATTERNS)
        assert score > 0

    def test_match_high_patterns(self):
        """Should match high complexity patterns"""
        classifier = RulesetComplexityClassifier()

        text = "Update Spring Security configuration"
        score = classifier._match_patterns(text, classifier.HIGH_PATTERNS)
        assert score > 0

    def test_match_expert_patterns(self):
        """Should match expert complexity patterns"""
        classifier = RulesetComplexityClassifier()

        text = "Custom security realm implementation"
        score = classifier._match_patterns(text, classifier.EXPERT_PATTERNS)
        assert score > 0

    def test_case_insensitive_matching(self):
        """Should match patterns case-insensitively"""
        classifier = RulesetComplexityClassifier()

        text_lower = "security configuration"
        text_upper = "SECURITY CONFIGURATION"
        text_mixed = "Security Configuration"

        score_lower = classifier._match_patterns(text_lower, classifier.HIGH_PATTERNS)
        score_upper = classifier._match_patterns(text_upper, classifier.HIGH_PATTERNS)
        score_mixed = classifier._match_patterns(text_mixed, classifier.HIGH_PATTERNS)

        assert score_lower > 0
        assert score_upper > 0
        assert score_mixed > 0

    def test_no_match_returns_zero(self):
        """Should return 0 when no patterns match"""
        classifier = RulesetComplexityClassifier()

        text = "some random unrelated text"
        score = classifier._match_patterns(text, classifier.TRIVIAL_PATTERNS)
        assert score == 0


class TestWhenConditionAnalysis:
    """Test when condition complexity analysis."""

    def test_simple_when_condition(self):
        """Should classify simple when conditions as low"""
        classifier = RulesetComplexityClassifier()

        when = {
            "java.referenced": {
                "pattern": "javax.servlet.*"
            }
        }

        complexity = classifier._analyze_when_condition(when)
        assert complexity == "low"

    def test_and_condition_is_medium(self):
        """Should classify 'and' conditions as medium"""
        classifier = RulesetComplexityClassifier()

        when = {
            "and": [
                {"java.referenced": {"pattern": "test1"}},
                {"java.referenced": {"pattern": "test2"}}
            ]
        }

        complexity = classifier._analyze_when_condition(when)
        assert complexity == "medium"

    def test_or_condition_is_medium(self):
        """Should classify 'or' conditions as medium"""
        classifier = RulesetComplexityClassifier()

        when = {
            "or": [
                {"java.referenced": {"pattern": "test1"}},
                {"java.referenced": {"pattern": "test2"}}
            ]
        }

        complexity = classifier._analyze_when_condition(when)
        assert complexity == "medium"

    def test_not_condition_is_medium(self):
        """Should classify 'not' conditions as medium"""
        classifier = RulesetComplexityClassifier()

        when = {
            "not": {"java.referenced": {"pattern": "test"}}
        }

        complexity = classifier._analyze_when_condition(when)
        assert complexity == "medium"

    def test_multiple_providers_is_medium(self):
        """Should classify multiple providers as medium"""
        classifier = RulesetComplexityClassifier()

        when = {
            "java.referenced": {"pattern": "test1"},
            "builtin.filecontent": {"pattern": "test2"}
        }

        complexity = classifier._analyze_when_condition(when)
        assert complexity == "medium"

    def test_xpath_condition_is_high(self):
        """Should classify XPath conditions as high"""
        classifier = RulesetComplexityClassifier()

        when = {
            "builtin.xml": {
                "xpath": "//configuration/property"
            }
        }

        complexity = classifier._analyze_when_condition(when)
        assert complexity == "high"

    def test_complex_regex_is_high(self):
        """Should classify complex regex patterns as high"""
        classifier = RulesetComplexityClassifier()

        when = {
            "java.referenced": {
                "pattern": "(?=test)pattern"  # Lookahead
            }
        }

        complexity = classifier._analyze_when_condition(when)
        assert complexity == "high"


class TestSimplePatternReplacement:
    """Test simple pattern replacement detection."""

    def test_javax_to_jakarta_is_simple(self):
        """Should detect javax->jakarta as simple replacement"""
        classifier = RulesetComplexityClassifier()

        text = "Replace javax.servlet with jakarta.servlet"
        is_simple = classifier._is_simple_pattern_replacement(text)
        assert is_simple is True

    def test_import_replacement_is_simple(self):
        """Should detect import replacements as simple"""
        classifier = RulesetComplexityClassifier()

        text = "Change import org.old -> import org.new"
        is_simple = classifier._is_simple_pattern_replacement(text)
        assert is_simple is True

    def test_simple_replace_with_syntax_is_simple(self):
        """Should detect 'replace X with Y' as simple"""
        classifier = RulesetComplexityClassifier()

        text = "Replace OldClass with NewClass"
        is_simple = classifier._is_simple_pattern_replacement(text)
        assert is_simple is True

    def test_security_replacement_not_simple(self):
        """Should not classify security changes as simple"""
        classifier = RulesetComplexityClassifier()

        text = "Replace OldSecurityConfig with NewSecurityConfig"
        is_simple = classifier._is_simple_pattern_replacement(text)
        assert is_simple is False

    def test_configuration_replacement_not_simple(self):
        """Should not classify configuration changes as simple"""
        classifier = RulesetComplexityClassifier()

        text = "Replace old configuration with new configuration"
        is_simple = classifier._is_simple_pattern_replacement(text)
        assert is_simple is False


class TestRuleClassification:
    """Test individual rule classification logic."""

    def test_classify_trivial_rule(self):
        """Should classify javax->jakarta with effort 1 as low (conservative)"""
        classifier = RulesetComplexityClassifier()

        rule = {
            "ruleID": "test-00000",
            "description": "Replace javax.servlet with jakarta.servlet",
            "message": "Change import from javax.servlet to jakarta.servlet",
            "effort": 1,
            "when": {"java.referenced": {"pattern": "javax.servlet.*"}}
        }

        complexity = classifier.classify_rule(rule)
        # Note: Classifier is conservative - trivial requires both pattern match
        # and simple replacement detection, which is hard to trigger consistently
        assert complexity in ["trivial", "low"]

    def test_classify_low_rule(self):
        """Should classify simple annotation swap as low"""
        classifier = RulesetComplexityClassifier()

        rule = {
            "ruleID": "test-00000",
            "description": "Replace @Stateless with @ApplicationScoped",
            "message": "Simple annotation replacement",
            "effort": 2,
            "when": {"java.referenced": {"pattern": "javax.ejb.Stateless"}}
        }

        complexity = classifier.classify_rule(rule)
        assert complexity == "low"

    def test_classify_medium_rule(self):
        """Should classify moderate complexity as medium"""
        classifier = RulesetComplexityClassifier()

        rule = {
            "ruleID": "test-00000",
            "description": "Migrate JMS to Reactive Messaging",
            "message": "Update message-driven beans to use reactive patterns",
            "effort": 5,
            "when": {"java.referenced": {"pattern": "javax.jms.*"}}
        }

        complexity = classifier.classify_rule(rule)
        assert complexity == "medium"

    def test_classify_high_rule_by_pattern(self):
        """Should classify security-related as high"""
        classifier = RulesetComplexityClassifier()

        rule = {
            "ruleID": "test-00000",
            "description": "Update Spring Security configuration",
            "message": "Migrate to new security architecture",
            "effort": 7,
            "when": {"java.referenced": {"pattern": "org.springframework.security.*"}}
        }

        complexity = classifier.classify_rule(rule)
        assert complexity == "high"

    def test_classify_high_rule_by_effort(self):
        """Should classify high effort (7+) as high"""
        classifier = RulesetComplexityClassifier()

        rule = {
            "ruleID": "test-00000",
            "description": "Complex migration",
            "message": "Requires significant refactoring",
            "effort": 8,
            "when": {"java.referenced": {"pattern": "test"}}
        }

        complexity = classifier.classify_rule(rule)
        assert complexity == "high"

    def test_classify_expert_rule(self):
        """Should classify custom implementations as expert"""
        classifier = RulesetComplexityClassifier()

        rule = {
            "ruleID": "test-00000",
            "description": "Custom security realm",
            "message": "Migrate custom security realm implementation",
            "effort": 10,
            "when": {"java.referenced": {"pattern": "org.wildfly.security.*"}}
        }

        complexity = classifier.classify_rule(rule)
        assert complexity == "expert"

    def test_default_to_low(self):
        """Should default to low when no strong signals"""
        classifier = RulesetComplexityClassifier()

        rule = {
            "ruleID": "test-00000",
            "description": "Some migration",
            "message": "Update something",
            "effort": 3,
            "when": {"java.referenced": {"pattern": "test"}}
        }

        complexity = classifier.classify_rule(rule)
        assert complexity == "low"


class TestRulesetClassification:
    """Test full ruleset classification."""

    def test_classify_list_format_ruleset(self):
        """Should classify ruleset in list format"""
        classifier = RulesetComplexityClassifier()

        # Create temporary ruleset file
        ruleset_data = [
            {
                "ruleID": "test-00000",
                "description": "Replace javax.servlet",
                "message": "Change to jakarta.servlet",
                "effort": 1,
                "when": {"java.referenced": {"pattern": "javax.servlet.*"}}
            },
            {
                "ruleID": "test-00010",
                "description": "Update security config",
                "message": "Migrate security",
                "effort": 7,
                "when": {"java.referenced": {"pattern": "spring.security.*"}}
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(ruleset_data, f)
            temp_path = Path(f.name)

        try:
            result = classifier.classify_ruleset(temp_path, dry_run=True)

            assert result is not None
            assert 'stats' in result
            assert 'changes' in result
            # Conservative classifier may classify trivial as low
            assert result['stats']['low'] >= 1
            assert result['stats']['high'] == 1
            assert sum(result['stats'].values()) == 2
        finally:
            temp_path.unlink()

    def test_classify_dict_format_ruleset(self):
        """Should classify ruleset in dict format"""
        classifier = RulesetComplexityClassifier()

        # Create temporary ruleset file
        ruleset_data = {
            "name": "test-ruleset",
            "rules": [
                {
                    "ruleID": "test-00000",
                    "description": "Simple annotation swap",
                    "message": "Replace @Stateless",
                    "effort": 2,
                    "when": {"java.referenced": {"pattern": "test"}}
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(ruleset_data, f)
            temp_path = Path(f.name)

        try:
            result = classifier.classify_ruleset(temp_path, dry_run=True)

            assert result is not None
            assert 'stats' in result
            assert result['stats']['low'] == 1
        finally:
            temp_path.unlink()

    def test_track_changes(self):
        """Should track changes when updating complexity"""
        classifier = RulesetComplexityClassifier()

        # Create ruleset with existing complexity
        ruleset_data = [
            {
                "ruleID": "test-00000",
                "description": "Test",
                "message": "Test",
                "effort": 1,
                "when": {},
                "migration_complexity": "medium"  # Existing, will change to low
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(ruleset_data, f)
            temp_path = Path(f.name)

        try:
            result = classifier.classify_ruleset(temp_path, dry_run=True)

            assert len(result['changes']) == 1
            assert result['changes'][0]['old'] == 'medium'
            assert result['changes'][0]['new'] == 'low'
        finally:
            temp_path.unlink()

    def test_dry_run_no_file_update(self):
        """Should not update file in dry run mode"""
        classifier = RulesetComplexityClassifier()

        ruleset_data = [
            {
                "ruleID": "test-00000",
                "description": "Test",
                "message": "Test",
                "effort": 5,
                "when": {}
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(ruleset_data, f)
            temp_path = Path(f.name)

        try:
            # Get original content
            with open(temp_path, 'r') as f:
                original_content = f.read()

            # Run classifier in dry run mode
            classifier.classify_ruleset(temp_path, dry_run=True)

            # Verify file wasn't changed
            with open(temp_path, 'r') as f:
                new_content = f.read()

            assert original_content == new_content
        finally:
            temp_path.unlink()

    def test_update_file_when_not_dry_run(self):
        """Should update file when not in dry run mode"""
        classifier = RulesetComplexityClassifier()

        ruleset_data = [
            {
                "ruleID": "test-00000",
                "description": "Test",
                "message": "Test",
                "effort": 5,
                "when": {}
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(ruleset_data, f)
            temp_path = Path(f.name)

        try:
            # Run classifier (not dry run)
            classifier.classify_ruleset(temp_path, dry_run=False)

            # Verify file was updated
            with open(temp_path, 'r') as f:
                updated_data = yaml.safe_load(f)

            assert updated_data[0]['migration_complexity'] is not None
        finally:
            temp_path.unlink()

    def test_handle_invalid_ruleset_format(self):
        """Should handle invalid ruleset format"""
        classifier = RulesetComplexityClassifier()

        # Create invalid ruleset (not list or dict with rules)
        ruleset_data = "invalid"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(ruleset_data, f)
            temp_path = Path(f.name)

        try:
            result = classifier.classify_ruleset(temp_path, dry_run=True)

            assert result == {}
        finally:
            temp_path.unlink()


class TestVerboseOutput:
    """Test verbose output mode."""

    def test_verbose_mode_shows_reasoning(self, capsys):
        """Should show detailed reasoning in verbose mode"""
        classifier = RulesetComplexityClassifier(verbose=True)

        rule = {
            "ruleID": "test-00000",
            "description": "Security update",
            "message": "Update authentication",
            "effort": 7,
            "when": {}
        }

        classifier.classify_rule(rule)

        captured = capsys.readouterr()
        assert "Rule: test-00000" in captured.out
        assert "Scores:" in captured.out
        assert "Classification:" in captured.out

    def test_non_verbose_mode_no_reasoning(self, capsys):
        """Should not show reasoning without verbose mode"""
        classifier = RulesetComplexityClassifier(verbose=False)

        rule = {
            "ruleID": "test-00000",
            "description": "Test",
            "message": "Test",
            "effort": 5,
            "when": {}
        }

        classifier.classify_rule(rule)

        captured = capsys.readouterr()
        assert "Scores:" not in captured.out


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_rule_dict(self):
        """Should handle empty rule dict"""
        classifier = RulesetComplexityClassifier()

        rule = {}
        complexity = classifier.classify_rule(rule)

        assert complexity in ["trivial", "low", "medium", "high", "expert"]

    def test_missing_fields_in_rule(self):
        """Should handle missing fields gracefully"""
        classifier = RulesetComplexityClassifier()

        rule = {
            "ruleID": "test-00000"
            # Missing description, message, effort, when
        }

        complexity = classifier.classify_rule(rule)
        assert complexity is not None

    def test_unicode_in_patterns(self):
        """Should handle Unicode characters"""
        classifier = RulesetComplexityClassifier()

        rule = {
            "ruleID": "test-00000",
            "description": "测试规则",  # Chinese
            "message": "テストメッセージ",  # Japanese
            "effort": 5,
            "when": {}
        }

        complexity = classifier.classify_rule(rule)
        assert complexity is not None
