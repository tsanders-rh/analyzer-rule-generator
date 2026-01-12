"""
Unit tests for Claude Code skill configuration.

Tests cover:
- YAML frontmatter validation
- Required fields presence
- File structure validation
- Documentation completeness
- Markdown link validation
"""

from pathlib import Path

import pytest
import yaml


class TestSkillStructure:
    """Test Claude Code skill file structure."""

    @pytest.fixture
    def skill_dir(self):
        """Path to the skill directory."""
        return Path(__file__).parent.parent.parent / ".claude" / "skills" / "konveyor-rules"

    @pytest.fixture
    def skill_file(self, skill_dir):
        """Path to SKILL.md file."""
        return skill_dir / "SKILL.md"

    def test_skill_directory_exists(self, skill_dir):
        """Skill directory should exist."""
        assert skill_dir.exists(), "Skill directory not found"
        assert skill_dir.is_dir(), "Skill path is not a directory"

    def test_skill_md_exists(self, skill_file):
        """SKILL.md file should exist."""
        assert skill_file.exists(), "SKILL.md not found"
        assert skill_file.is_file(), "SKILL.md is not a file"

    def test_readme_exists(self, skill_dir):
        """README.md should exist."""
        readme = skill_dir / "README.md"
        assert readme.exists(), "README.md not found"

    def test_demo_files_exist(self, skill_dir):
        """Demo documentation files should exist."""
        demo_files = ["DEMO.md", "QUICK-DEMO.md", "examples.md"]
        for filename in demo_files:
            filepath = skill_dir / filename
            assert filepath.exists(), f"{filename} not found"


class TestSkillFrontmatter:
    """Test YAML frontmatter in SKILL.md."""

    @pytest.fixture
    def skill_content(self):
        """Read SKILL.md content."""
        skill_file = (
            Path(__file__).parent.parent.parent
            / ".claude"
            / "skills"
            / "konveyor-rules"
            / "SKILL.md"
        )
        return skill_file.read_text()

    @pytest.fixture
    def frontmatter(self, skill_content):
        """Extract and parse YAML frontmatter."""
        # YAML frontmatter is between --- markers
        if not skill_content.startswith("---\n"):
            pytest.fail("SKILL.md does not start with YAML frontmatter")

        # Find the closing ---
        parts = skill_content.split("---\n", 2)
        if len(parts) < 3:
            pytest.fail("SKILL.md frontmatter not properly closed")

        frontmatter_text = parts[1]
        return yaml.safe_load(frontmatter_text)

    def test_frontmatter_exists(self, skill_content):
        """SKILL.md should have YAML frontmatter."""
        assert skill_content.startswith("---\n"), "Missing YAML frontmatter"

    def test_frontmatter_valid_yaml(self, frontmatter):
        """Frontmatter should be valid YAML."""
        assert isinstance(frontmatter, dict), "Frontmatter is not a dictionary"

    def test_frontmatter_has_name(self, frontmatter):
        """Frontmatter should have 'name' field."""
        assert "name" in frontmatter, "Missing 'name' field in frontmatter"
        assert frontmatter["name"], "Name field is empty"
        assert isinstance(frontmatter["name"], str), "Name should be a string"

    def test_frontmatter_has_description(self, frontmatter):
        """Frontmatter should have 'description' field."""
        assert "description" in frontmatter, "Missing 'description' field in frontmatter"
        assert frontmatter["description"], "Description field is empty"
        assert isinstance(frontmatter["description"], str), "Description should be a string"

    def test_name_value(self, frontmatter):
        """Name should be 'konveyor-rules'."""
        assert frontmatter["name"] == "konveyor-rules"

    def test_description_not_too_short(self, frontmatter):
        """Description should be descriptive (at least 20 characters)."""
        assert len(frontmatter["description"]) >= 20, "Description is too short"


class TestSkillContent:
    """Test content of SKILL.md."""

    @pytest.fixture
    def skill_content(self):
        """Read SKILL.md content."""
        skill_file = (
            Path(__file__).parent.parent.parent
            / ".claude"
            / "skills"
            / "konveyor-rules"
            / "SKILL.md"
        )
        return skill_file.read_text()

    @pytest.fixture
    def markdown_content(self, skill_content):
        """Extract markdown content after frontmatter."""
        parts = skill_content.split("---\n", 2)
        return parts[2] if len(parts) >= 3 else ""

    def test_has_markdown_content(self, markdown_content):
        """Should have content after frontmatter."""
        assert markdown_content.strip(), "No content after frontmatter"

    def test_mentions_guide_parameter(self, markdown_content):
        """Should mention --guide parameter."""
        assert "--guide" in markdown_content, "Missing --guide parameter documentation"

    def test_mentions_source_target(self, markdown_content):
        """Should mention source and target frameworks."""
        assert "--source" in markdown_content or "source framework" in markdown_content.lower()
        assert "--target" in markdown_content or "target framework" in markdown_content.lower()

    def test_mentions_providers(self, markdown_content):
        """Should mention LLM providers."""
        content_lower = markdown_content.lower()
        assert "openai" in content_lower, "Missing OpenAI provider"
        assert "anthropic" in content_lower, "Missing Anthropic provider"
        assert "google" in content_lower, "Missing Google provider"

    def test_has_examples(self, markdown_content):
        """Should have usage examples."""
        assert "```" in markdown_content, "Missing code examples"
        assert (
            "python scripts/generate_rules.py" in markdown_content
        ), "Missing script usage example"


class TestDocumentationLinks:
    """Test internal links in documentation."""

    @pytest.fixture
    def skill_dir(self):
        """Path to the skill directory."""
        return Path(__file__).parent.parent.parent / ".claude" / "skills" / "konveyor-rules"

    @pytest.fixture
    def readme_content(self, skill_dir):
        """Read README.md content."""
        return (skill_dir / "README.md").read_text()

    def test_readme_links_to_demo_files(self, readme_content, skill_dir):
        """README should link to demo files and they should exist."""
        # Check for markdown links to demo files
        demo_links = {
            "DEMO.md": "DEMO.md",
            "QUICK-DEMO.md": "QUICK-DEMO.md",
            "examples.md": "examples.md",
        }

        for link_text, filename in demo_links.items():
            assert (
                link_text in readme_content or filename in readme_content
            ), f"README does not link to {filename}"

            # Verify file exists
            filepath = skill_dir / filename
            assert filepath.exists(), f"Linked file {filename} does not exist"


class TestSkillNaming:
    """Test skill directory naming conventions."""

    @pytest.fixture
    def skill_dir(self):
        """Path to the skill directory."""
        return Path(__file__).parent.parent.parent / ".claude" / "skills" / "konveyor-rules"

    def test_directory_name_lowercase(self, skill_dir):
        """Skill directory name should be lowercase with hyphens."""
        dir_name = skill_dir.name
        assert dir_name == dir_name.lower(), "Directory name should be lowercase"
        assert " " not in dir_name, "Directory name should not contain spaces"

    def test_directory_name_length(self, skill_dir):
        """Skill directory name should be reasonable length (<=64 chars)."""
        dir_name = skill_dir.name
        assert len(dir_name) <= 64, "Directory name exceeds 64 characters"


class TestDocumentationCompleteness:
    """Test that documentation is complete and helpful."""

    @pytest.fixture
    def skill_dir(self):
        """Path to the skill directory."""
        return Path(__file__).parent.parent.parent / ".claude" / "skills" / "konveyor-rules"

    def test_readme_has_prerequisites(self, skill_dir):
        """README should document prerequisites."""
        readme = (skill_dir / "README.md").read_text()
        content_lower = readme.lower()
        assert (
            "prerequisite" in content_lower or "requirement" in content_lower
        ), "README should document prerequisites"

    def test_readme_has_usage_instructions(self, skill_dir):
        """README should have usage instructions."""
        readme = (skill_dir / "README.md").read_text()
        assert "konveyor-rules" in readme, "README should show how to invoke the skill"

    def test_readme_has_examples(self, skill_dir):
        """README should have examples."""
        readme = (skill_dir / "README.md").read_text()
        assert "example" in readme.lower(), "README should have examples"

    def test_quick_demo_has_timing(self, skill_dir):
        """QUICK-DEMO.md should include timing information."""
        quick_demo = (skill_dir / "QUICK-DEMO.md").read_text()
        content_lower = quick_demo.lower()
        # Should mention minutes or seconds
        assert (
            "minute" in content_lower or "second" in content_lower
        ), "Quick demo should include timing information"

    def test_examples_has_conversations(self, skill_dir):
        """examples.md should have example conversations."""
        examples = (skill_dir / "examples.md").read_text()
        # Should have user/claude conversation markers
        assert "User:" in examples or "**User:**" in examples, "examples.md should show user input"
        assert (
            "Claude:" in examples or "**Claude:**" in examples
        ), "examples.md should show Claude responses"


class TestAPIKeyDocumentation:
    """Test that API key setup is properly documented."""

    @pytest.fixture
    def skill_dir(self):
        """Path to the skill directory."""
        return Path(__file__).parent.parent.parent / ".claude" / "skills" / "konveyor-rules"

    def test_readme_documents_api_keys(self, skill_dir):
        """README should document API key requirements."""
        readme = (skill_dir / "README.md").read_text()
        assert "OPENAI_API_KEY" in readme, "Should document OPENAI_API_KEY"
        assert "ANTHROPIC_API_KEY" in readme, "Should document ANTHROPIC_API_KEY"
        assert "GOOGLE_API_KEY" in readme, "Should document GOOGLE_API_KEY"

    def test_skill_md_mentions_api_keys(self, skill_dir):
        """SKILL.md should mention API key requirements."""
        skill_md = (skill_dir / "SKILL.md").read_text()
        content_lower = skill_md.lower()
        assert "api" in content_lower and "key" in content_lower, "SKILL.md should mention API keys"
