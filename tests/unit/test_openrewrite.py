"""
Unit tests for src/rule_generator/openrewrite.py

Tests OpenRewrite recipe ingestion, parsing, and formatting.
"""

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from src.rule_generator.openrewrite import OpenRewriteRecipeIngester


class TestURLDetection:
    """Test URL vs file path detection."""

    @pytest.fixture
    def ingester(self):
        """Create OpenRewriteRecipeIngester instance."""
        return OpenRewriteRecipeIngester()

    def test_detect_http_url(self, ingester):
        """Should recognize HTTP URLs"""
        assert ingester._is_url("http://example.com/recipe.yml") is True

    def test_detect_https_url(self, ingester):
        """Should recognize HTTPS URLs"""
        assert ingester._is_url("https://github.com/org/repo/recipe.yml") is True

    def test_detect_file_path_as_not_url(self, ingester):
        """Should recognize file paths as not URLs"""
        assert ingester._is_url("/path/to/recipe.yml") is False
        assert ingester._is_url("./recipe.yml") is False
        assert ingester._is_url("recipe.yml") is False

    def test_detect_relative_path_as_not_url(self, ingester):
        """Should recognize relative paths as not URLs"""
        assert ingester._is_url("../recipe.yml") is False


class TestRecipeFetching:
    """Test fetching recipes from various sources."""

    @pytest.fixture
    def ingester(self):
        """Create OpenRewriteRecipeIngester instance."""
        return OpenRewriteRecipeIngester()

    @patch('src.rule_generator.openrewrite.requests.get')
    def test_fetch_from_url_success(self, mock_get, ingester):
        """Should fetch recipe from URL successfully"""
        mock_response = Mock()
        mock_response.text = """
type: specs.openrewrite.org/v1beta/recipe
name: TestRecipe
displayName: Test Recipe
"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        recipe = ingester._fetch_recipe("https://example.com/recipe.yml")

        assert recipe is not None
        assert recipe['type'] == 'specs.openrewrite.org/v1beta/recipe'
        assert recipe['name'] == 'TestRecipe'
        mock_get.assert_called_once_with("https://example.com/recipe.yml", timeout=30)

    @patch('src.rule_generator.openrewrite.requests.get')
    def test_fetch_from_url_network_error(self, mock_get, ingester):
        """Should handle network errors gracefully"""
        mock_get.side_effect = Exception("Network error")

        recipe = ingester._fetch_recipe("https://example.com/recipe.yml")

        assert recipe is None

    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data="""
type: specs.openrewrite.org/v1beta/recipe
name: LocalRecipe
""",
    )
    @patch('pathlib.Path.exists', return_value=True)
    def test_fetch_from_local_file(self, mock_exists, mock_file, ingester):
        """Should fetch recipe from local file"""
        recipe = ingester._fetch_recipe("./local-recipe.yml")

        assert recipe is not None
        assert recipe['name'] == 'LocalRecipe'

    @patch('pathlib.Path.exists', return_value=False)
    def test_fetch_from_nonexistent_file(self, mock_exists, ingester):
        """Should return None for nonexistent file"""
        recipe = ingester._fetch_recipe("./nonexistent.yml")

        assert recipe is None

    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data="""
---
type: specs.openrewrite.org/v1beta/recipe
name: Recipe1
---
type: specs.openrewrite.org/v1beta/recipe
name: Recipe2
""",
    )
    @patch('pathlib.Path.exists', return_value=True)
    def test_fetch_multiple_recipes(self, mock_exists, mock_file, ingester):
        """Should handle multiple YAML documents"""
        recipe = ingester._fetch_recipe("./multi-recipe.yml")

        assert recipe is not None
        assert "multiple_recipes" in recipe
        assert len(recipe["multiple_recipes"]) == 2
        assert recipe["multiple_recipes"][0]['name'] == 'Recipe1'
        assert recipe["multiple_recipes"][1]['name'] == 'Recipe2'

    @patch('builtins.open', new_callable=mock_open, read_data="invalid: yaml: content:")
    @patch('pathlib.Path.exists', return_value=True)
    def test_fetch_invalid_yaml(self, mock_exists, mock_file, ingester):
        """Should handle invalid YAML gracefully"""
        recipe = ingester._fetch_recipe("./invalid.yml")

        assert recipe is None


class TestRecipeFormatting:
    """Test formatting recipes for LLM consumption."""

    @pytest.fixture
    def ingester(self):
        """Create OpenRewriteRecipeIngester instance."""
        return OpenRewriteRecipeIngester()

    def test_format_simple_recipe(self, ingester):
        """Should format simple recipe correctly"""
        recipe_data = {
            "type": "specs.openrewrite.org/v1beta/recipe",
            "name": "TestRecipe",
            "displayName": "Test Recipe",
            "description": "A test recipe",
        }

        formatted = ingester._format_recipe_for_llm(recipe_data)

        assert "# OpenRewrite Recipe" in formatted
        assert "TestRecipe" in formatted
        assert "Test Recipe" in formatted
        assert "A test recipe" in formatted

    def test_format_recipe_with_transformations(self, ingester):
        """Should format recipe with transformation list"""
        recipe_data = {
            "name": "MigrationRecipe",
            "recipeList": [
                "org.openrewrite.java.ChangePackage",
                {
                    "org.openrewrite.java.ChangeType": {
                        "oldFullyQualifiedTypeName": "old.Class",
                        "newFullyQualifiedTypeName": "new.Class",
                    }
                },
            ],
        }

        formatted = ingester._format_recipe_for_llm(recipe_data)

        assert "## Transformations" in formatted
        assert "org.openrewrite.java.ChangePackage" in formatted
        assert "org.openrewrite.java.ChangeType" in formatted
        assert "oldFullyQualifiedTypeName" in formatted
        assert "old.Class" in formatted

    def test_format_recipe_with_preconditions(self, ingester):
        """Should format recipe with preconditions"""
        recipe_data = {
            "name": "ConditionalRecipe",
            "preconditions": ["org.openrewrite.java.search.FindTypes"],
        }

        formatted = ingester._format_recipe_for_llm(recipe_data)

        assert "## Preconditions" in formatted
        assert "org.openrewrite.java.search.FindTypes" in formatted

    def test_format_multiple_recipes(self, ingester):
        """Should format multiple recipes with separators"""
        recipe_data = {
            "multiple_recipes": [
                {"name": "Recipe1", "displayName": "First Recipe"},
                {"name": "Recipe2", "displayName": "Second Recipe"},
            ]
        }

        formatted = ingester._format_recipe_for_llm(recipe_data)

        assert "Recipe1" in formatted
        assert "Recipe2" in formatted
        assert "---" in formatted  # Separator between recipes

    def test_format_recipe_with_tags(self, ingester):
        """Should include tags in formatted output"""
        recipe_data = {"name": "TaggedRecipe", "tags": ["java", "migration", "security"]}

        formatted = ingester._format_recipe_for_llm(recipe_data)

        assert "Tags" in formatted
        assert "java" in formatted
        assert "migration" in formatted
        assert "security" in formatted

    def test_format_recipe_item_string(self, ingester):
        """Should format string recipe items"""
        item = "org.openrewrite.java.ChangePackage"
        formatted = ingester._format_recipe_item(item)

        assert "org.openrewrite.java.ChangePackage" in formatted
        assert "`" in formatted  # Should be wrapped in backticks

    def test_format_recipe_item_dict(self, ingester):
        """Should format dict recipe items with parameters"""
        item = {
            "org.openrewrite.java.ChangeType": {
                "oldFullyQualifiedTypeName": "javax.security.cert.X509Certificate",
                "newFullyQualifiedTypeName": "java.security.cert.X509Certificate",
            }
        }
        formatted = ingester._format_recipe_item(item)

        assert "org.openrewrite.java.ChangeType" in formatted
        assert "oldFullyQualifiedTypeName" in formatted
        assert "javax.security.cert.X509Certificate" in formatted

    def test_format_empty_recipe(self, ingester):
        """Should handle empty recipe gracefully"""
        recipe_data = {}
        formatted = ingester._format_recipe_for_llm(recipe_data)

        assert "# OpenRewrite Recipe" in formatted
        assert len(formatted) > 0


class TestIngestionCaching:
    """Test caching of ingested recipes."""

    @pytest.fixture
    def ingester(self):
        """Create OpenReWriteRecipeIngester instance."""
        return OpenRewriteRecipeIngester()

    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data="""
type: specs.openrewrite.org/v1beta/recipe
name: CachedRecipe
""",
    )
    @patch('pathlib.Path.exists', return_value=True)
    def test_caching_works(self, mock_exists, mock_file, ingester):
        """Should cache ingested recipes"""
        source = "./recipe.yml"

        # First call - should fetch and cache
        result1 = ingester.ingest(source)
        call_count_1 = mock_file.call_count

        # Second call - should use cache
        result2 = ingester.ingest(source)
        call_count_2 = mock_file.call_count

        assert result1 == result2
        assert call_count_1 == call_count_2  # File not read again

    def test_cache_different_sources(self, ingester):
        """Should cache different sources separately"""
        with patch('builtins.open', new_callable=mock_open, read_data="name: Recipe1"):
            with patch('pathlib.Path.exists', return_value=True):
                result1 = ingester.ingest("./recipe1.yml")

        with patch('builtins.open', new_callable=mock_open, read_data="name: Recipe2"):
            with patch('pathlib.Path.exists', return_value=True):
                result2 = ingester.ingest("./recipe2.yml")

        assert result1 != result2
        assert "Recipe1" in result1
        assert "Recipe2" in result2


class TestFullIngestionWorkflow:
    """Test complete ingestion workflow."""

    @pytest.fixture
    def ingester(self):
        """Create OpenRewriteRecipeIngester instance."""
        return OpenRewriteRecipeIngester()

    @patch('src.rule_generator.openrewrite.requests.get')
    def test_ingest_from_url_complete(self, mock_get, ingester):
        """Should complete full ingestion from URL"""
        mock_response = Mock()
        mock_response.text = """
type: specs.openrewrite.org/v1beta/recipe
name: UpgradeToJava17
displayName: Upgrade to Java 17
description: Migrates Java 11 applications to Java 17
recipeList:
  - org.openrewrite.java.migrate.JavaVersion17
"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        content = ingester.ingest("https://example.com/java17.yml")

        assert content is not None
        assert "UpgradeToJava17" in content
        assert "Upgrade to Java 17" in content
        assert "JavaVersion17" in content

    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data="""
type: specs.openrewrite.org/v1beta/recipe
name: LocalTestRecipe
""",
    )
    @patch('pathlib.Path.exists', return_value=True)
    def test_ingest_from_file_complete(self, mock_exists, mock_file, ingester):
        """Should complete full ingestion from file"""
        content = ingester.ingest("./local.yml")

        assert content is not None
        assert "LocalTestRecipe" in content

    def test_ingest_returns_none_on_failure(self, ingester):
        """Should return None when ingestion fails"""
        with patch.object(ingester, '_fetch_recipe', return_value=None):
            content = ingester.ingest("https://example.com/nonexistent.yml")

            assert content is None


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def ingester(self):
        """Create OpenRewriteRecipeIngester instance."""
        return OpenRewriteRecipeIngester()

    def test_handle_none_recipe_data(self, ingester):
        """Should handle None recipe data"""
        formatted = ingester._format_single_recipe({})
        assert formatted is not None
        assert len(formatted) > 0

    def test_handle_complex_nested_recipe(self, ingester):
        """Should handle deeply nested recipe structures"""
        recipe_data = {
            "name": "ComplexRecipe",
            "recipeList": [
                {
                    "org.openrewrite.Composite": {
                        "recipeList": [
                            "org.openrewrite.java.ChangePackage",
                            "org.openrewrite.java.ChangeType",
                        ]
                    }
                }
            ],
        }

        formatted = ingester._format_recipe_for_llm(recipe_data)
        assert formatted is not None
        assert "ComplexRecipe" in formatted

    @patch('builtins.open', new_callable=mock_open, read_data="")
    @patch('pathlib.Path.exists', return_value=True)
    def test_handle_empty_yaml_file(self, mock_exists, mock_file, ingester):
        """Should handle empty YAML file"""
        recipe = ingester._fetch_recipe("./empty.yml")
        # Empty YAML returns a list with one None element, which becomes multiple_recipes with empty list
        assert recipe is None or recipe == {} or recipe == {'multiple_recipes': []}

    def test_format_recipe_with_none_values(self, ingester):
        """Should handle None values in recipe data"""
        recipe_data = {"name": "TestRecipe", "displayName": None, "description": None, "tags": None}

        formatted = ingester._format_recipe_for_llm(recipe_data)
        assert formatted is not None
        assert "TestRecipe" in formatted
