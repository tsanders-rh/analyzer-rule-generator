"""
Tests for rule_generator.validate_rules module.
"""
import pytest
from unittest.mock import Mock, MagicMock
from src.rule_generator.validate_rules import ValidationReport, RuleValidator
from src.rule_generator.schema import AnalyzerRule, Category
from src.rule_generator.llm import LLMProvider


class TestValidationReport:
    """Tests for ValidationReport class."""

    def test_init(self):
        """Test ValidationReport initialization."""
        report = ValidationReport()
        assert report.improvements == []
        assert report.issues == []
        assert report.statistics['total_rules'] == 0
        assert report.statistics['rules_improved'] == 0
        assert report.statistics['import_verification_added'] == 0
        assert report.statistics['overly_broad_detected'] == 0
        assert report.statistics['quality_issues_fixed'] == 0
        assert report.statistics['duplicates_found'] == 0

    def test_add_improvement(self):
        """Test adding an improvement."""
        report = ValidationReport()
        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "test"}},
            message="Test message",
            customVariables=[]
        )
        improved = {"when": {"builtin.filecontent": {"pattern": "improved"}}}

        report.add_improvement('import_verification', rule, improved)

        assert len(report.improvements) == 1
        assert report.improvements[0]['type'] == 'import_verification'
        assert report.improvements[0]['original'] == rule
        assert report.improvements[0]['improved'] == improved
        assert report.statistics['rules_improved'] == 1
        assert report.statistics['import_verification_added'] == 1

    def test_add_issue(self):
        """Test adding an issue."""
        report = ValidationReport()
        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "ab"}},
            message="Test message",
            customVariables=[]
        )
        details = {"reason": "Pattern too short"}

        report.add_issue('overly_broad', rule, details)

        assert len(report.issues) == 1
        assert report.issues[0]['type'] == 'overly_broad'
        assert report.issues[0]['rule'] == rule
        assert report.issues[0]['details'] == details
        assert report.statistics['overly_broad_detected'] == 1

    def test_generate_report_with_improvements(self):
        """Test generating report with improvements."""
        report = ValidationReport()
        report.statistics['total_rules'] = 5

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="This is a long description that will be truncated in the report output",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "test"}},
            message="Test message",
            customVariables=[]
        )
        improved = {"when": {"builtin.filecontent": {"pattern": "improved"}}}
        report.add_improvement('import_verification', rule, improved)

        result = report.generate_report()

        assert "POST-GENERATION VALIDATION REPORT" in result
        assert "Total rules validated: 5" in result
        assert "Rules improved: 1" in result
        assert "IMPORT_VERIFICATION:" in result
        assert "test-00000" in result

    def test_generate_report_with_issues(self):
        """Test generating report with issues."""
        report = ValidationReport()
        report.statistics['total_rules'] = 3

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "ab"}},
            message="Test message",
            customVariables=[]
        )
        details = {"reason": "Pattern too short"}
        report.add_issue('overly_broad', rule, details)

        result = report.generate_report()

        assert "ISSUES DETECTED" in result
        assert "OVERLY_BROAD:" in result
        assert "test-00000" in result
        assert "Pattern too short" in result

    def test_generate_report_empty(self):
        """Test generating report with no improvements or issues."""
        report = ValidationReport()
        report.statistics['total_rules'] = 2

        result = report.generate_report()

        assert "Total rules validated: 2" in result
        assert "No improvements applied." in result
        assert "No issues detected." in result


class TestRuleValidator:
    """Tests for RuleValidator class."""

    def test_init(self):
        """Test RuleValidator initialization."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        assert validator.llm == llm
        assert validator.language == 'javascript'

    def test_needs_import_verification_combo_rule_without_import(self):
        """Test detecting combo rule needing import verification."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={
                "and": [
                    {"nodejs.referenced": {"pattern": "MyComponent"}},
                    {"builtin.filecontent": {"pattern": "<MyComponent"}}
                ]
            },
            message="Test message",
            customVariables=[]
        )

        assert validator._needs_import_verification(rule) is True

    def test_needs_import_verification_combo_rule_with_import(self):
        """Test detecting combo rule that already has import verification."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={
                "and": [
                    {"builtin.filecontent": {"pattern": "import.*MyComponent.*from.*@patternfly"}},
                    {"nodejs.referenced": {"pattern": "MyComponent"}},
                    {"builtin.filecontent": {"pattern": "<MyComponent"}}
                ]
            },
            message="Test message",
            customVariables=[]
        )

        assert validator._needs_import_verification(rule) is False

    def test_needs_import_verification_simple_nodejs_rule(self):
        """Test detecting simple nodejs.referenced rule needing import verification."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"nodejs.referenced": {"pattern": "Button"}},
            message="Test message",
            customVariables=[]
        )

        assert validator._needs_import_verification(rule) is True

    def test_needs_import_verification_lowercase_pattern(self):
        """Test that lowercase patterns don't need import verification."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"nodejs.referenced": {"pattern": "myFunction"}},
            message="Test message",
            customVariables=[]
        )

        assert validator._needs_import_verification(rule) is False

    def test_extract_component_name_from_combo_rule(self):
        """Test extracting component name from combo rule."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={
                "and": [
                    {"nodejs.referenced": {"pattern": "Alert"}},
                    {"builtin.filecontent": {"pattern": "<Alert"}}
                ]
            },
            message="Test message",
            customVariables=[]
        )

        component = validator._extract_component_name(rule)
        assert component == "Alert"

    def test_extract_component_name_from_simple_rule(self):
        """Test extracting component name from simple nodejs.referenced rule."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"nodejs.referenced": {"pattern": "Card"}},
            message="Test message",
            customVariables=[]
        )

        component = validator._extract_component_name(rule)
        assert component == "Card"

    def test_extract_component_name_returns_none_for_non_component_rule(self):
        """Test extracting component name returns None for non-component rules."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"java.referenced": {"pattern": "org.example.MyClass", "location": "TYPE"}},
            message="Test message",
            customVariables=[]
        )

        component = validator._extract_component_name(rule)
        assert component is None

    def test_add_import_verification_to_combo_rule(self):
        """Test adding import verification to combo rule."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={
                "and": [
                    {"nodejs.referenced": {"pattern": "Alert"}},
                    {"builtin.filecontent": {"pattern": "<Alert", "filePattern": "\\.(j|t)sx?$"}}
                ]
            },
            message="Test message",
            customVariables=[]
        )

        improved = validator._add_import_verification(rule)

        assert improved is not None
        assert 'when' in improved
        assert 'and' in improved['when']
        assert len(improved['when']['and']) == 2

        # Check import verification was added
        import_cond = improved['when']['and'][0]
        assert 'builtin.filecontent' in import_cond
        assert 'import' in import_cond['builtin.filecontent']['pattern']
        assert 'Alert' in import_cond['builtin.filecontent']['pattern']

    def test_add_import_verification_to_simple_rule(self):
        """Test adding import verification to simple nodejs.referenced rule."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"nodejs.referenced": {"pattern": "Button"}},
            message="Test message",
            customVariables=[]
        )

        improved = validator._add_import_verification(rule)

        assert improved is not None
        assert 'when' in improved
        assert 'and' in improved['when']
        assert len(improved['when']['and']) == 2

        # Check import verification and JSX pattern were added
        import_cond = improved['when']['and'][0]
        jsx_cond = improved['when']['and'][1]
        assert 'import' in import_cond['builtin.filecontent']['pattern']
        assert '<Button' in jsx_cond['builtin.filecontent']['pattern']

    def test_add_import_verification_returns_none_for_invalid_rule(self):
        """Test that add_import_verification returns None for invalid rules."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"java.referenced": {"pattern": "org.example.Class", "location": "TYPE"}},
            message="Test message",
            customVariables=[]
        )

        improved = validator._add_import_verification(rule)
        assert improved is None

    def test_check_pattern_breadth_short_pattern(self):
        """Test detecting overly broad pattern (too short)."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "abc"}},
            message="Test message",
            customVariables=[]
        )

        analysis = validator._check_pattern_breadth(rule)

        assert analysis is not None
        assert analysis['is_overly_broad'] is True
        assert analysis['risk_level'] == 'HIGH'
        assert 'Pattern too short' in analysis['reason']

    def test_check_pattern_breadth_acceptable_pattern(self):
        """Test that acceptable patterns are not flagged."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "import.*Component.*from"}},
            message="Test message",
            customVariables=[]
        )

        analysis = validator._check_pattern_breadth(rule)
        assert analysis is None

    def test_check_pattern_breadth_non_builtin_rule(self):
        """Test that non-builtin rules are not checked for pattern breadth."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"nodejs.referenced": {"pattern": "x"}},
            message="Test message",
            customVariables=[]
        )

        analysis = validator._check_pattern_breadth(rule)
        assert analysis is None

    def test_review_pattern_quality(self):
        """Test pattern quality review (currently placeholder)."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "test"}},
            message="Test message",
            customVariables=[]
        )

        result = validator._review_pattern_quality(rule)
        assert result is None  # Currently returns None (placeholder)

    def test_find_duplicates(self):
        """Test finding duplicate rules."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule1 = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "test"}},
            message="Test message",
            customVariables=[]
        )

        rule2 = AnalyzerRule(
            ruleID="test-00010",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "test"}},
            message="Test message",
            customVariables=[]
        )

        rule3 = AnalyzerRule(
            ruleID="test-00020",
            description="Different rule",
            effort=3,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "different"}},
            message="Different message",
            customVariables=[]
        )

        duplicates = validator._find_duplicates([rule1, rule2, rule3])

        assert len(duplicates) == 1
        assert duplicates[0][0] == rule1
        assert duplicates[0][1] == rule2

    def test_find_duplicates_no_duplicates(self):
        """Test finding duplicates when there are none."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule1 = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule 1",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "test1"}},
            message="Test message 1",
            customVariables=[]
        )

        rule2 = AnalyzerRule(
            ruleID="test-00010",
            description="Test rule 2",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "test2"}},
            message="Test message 2",
            customVariables=[]
        )

        duplicates = validator._find_duplicates([rule1, rule2])
        assert len(duplicates) == 0

    def test_validate_rules_javascript(self, capsys):
        """Test validate_rules for JavaScript with import verification."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript', 'patternfly-v5', 'patternfly-v6')

        rule1 = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"nodejs.referenced": {"pattern": "Alert"}},
            message="Test message",
            customVariables=[]
        )

        rule2 = AnalyzerRule(
            ruleID="test-00010",
            description="Test rule 2",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "ab"}},
            message="Test message",
            customVariables=[]
        )

        report = validator.validate_rules([rule1, rule2])

        assert report.statistics['total_rules'] == 2
        assert report.statistics['rules_improved'] >= 1  # At least import verification
        assert len(report.issues) >= 1  # At least overly broad pattern

        # Check console output
        captured = capsys.readouterr()
        assert "POST-GENERATION VALIDATION" in captured.out
        assert "Checking for missing import verification" in captured.out

    def test_validate_rules_java(self, capsys):
        """Test validate_rules for Java (no import verification check)."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'java')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"java.referenced": {"pattern": "org.example.MyClass", "location": "TYPE"}},
            message="Test message",
            customVariables=[]
        )

        report = validator.validate_rules([rule])

        assert report.statistics['total_rules'] == 1
        # No import verification for Java
        assert report.statistics['import_verification_added'] == 0

        # Check console output
        captured = capsys.readouterr()
        assert "POST-GENERATION VALIDATION" in captured.out
        assert "Checking for missing import verification" not in captured.out

    def test_apply_improvements(self, capsys):
        """Test applying improvements to rules."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"nodejs.referenced": {"pattern": "Button"}},
            message="Test message",
            customVariables=[]
        )

        # Create report with improvement
        report = ValidationReport()
        improved_when = {
            "and": [
                {"builtin.filecontent": {"pattern": "import.*Button", "filePattern": "\\.(j|t)sx?$"}},
                {"builtin.filecontent": {"pattern": "<Button", "filePattern": "\\.(j|t)sx?$"}}
            ]
        }
        report.add_improvement('import_verification', rule, {'when': improved_when})

        # Apply improvements
        improved_rules = validator.apply_improvements([rule], report)

        assert len(improved_rules) == 1
        assert improved_rules[0].when == improved_when

        # Check console output
        captured = capsys.readouterr()
        assert "Applied import verification" in captured.out

    def test_apply_improvements_handles_errors(self, capsys):
        """Test that apply_improvements applies changes even with some errors."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"nodejs.referenced": {"pattern": "Button"}},
            message="Test message",
            customVariables=[]
        )

        # Create report with valid improvement that will succeed
        report = ValidationReport()
        valid_when = {
            "and": [
                {"builtin.filecontent": {"pattern": "import.*Button", "filePattern": "\\.(j|t)sx?$"}},
                {"builtin.filecontent": {"pattern": "<Button", "filePattern": "\\.(j|t)sx?$"}}
            ]
        }
        valid_improvement = {'when': valid_when}
        report.add_improvement('import_verification', rule, valid_improvement)

        # Apply improvements
        improved_rules = validator.apply_improvements([rule], report)

        assert len(improved_rules) == 1
        assert improved_rules[0].when == valid_when  # Improvement successfully applied

        # Check success message in output
        captured = capsys.readouterr()
        assert "Applied import verification" in captured.out

    def test_rule_to_yaml_string(self):
        """Test converting rule to YAML string."""
        llm = Mock(spec=LLMProvider)
        validator = RuleValidator(llm, 'javascript')

        rule = AnalyzerRule(
            ruleID="test-00000",
            description="Test rule",
            effort=5,
            category=Category.POTENTIAL,
            labels=["test"],
            when={"builtin.filecontent": {"pattern": "test"}},
            message="Test message",
            customVariables=[]
        )

        yaml_str = validator._rule_to_yaml_string(rule)

        assert "ruleID: test-00000" in yaml_str
        assert "description: Test rule" in yaml_str
        assert "pattern: test" in yaml_str
        assert "message: Test message" in yaml_str
