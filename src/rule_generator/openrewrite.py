"""
OpenRewrite recipe ingestion - Fetch and parse OpenRewrite YAML recipes.

Supports:
- GitHub raw URLs
- Local YAML files
- Recursive recipe expansion
"""

from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests
import yaml


class OpenRewriteRecipeIngester:
    """Fetch and parse OpenRewrite recipes from YAML sources."""

    def __init__(self):
        """Initialize the recipe ingester with a cache."""
        self._cache = {}

    def ingest(self, source: str) -> Optional[str]:
        """
        Ingest an OpenRewrite recipe from any source.

        Args:
            source: URL or file path to OpenRewrite YAML recipe

        Returns:
            Formatted text content suitable for LLM processing, or None if ingestion fails
        """
        # Check cache first
        if source in self._cache:
            return self._cache[source]

        # Fetch the recipe YAML
        recipe_data = self._fetch_recipe(source)
        if not recipe_data:
            return None

        # Convert recipe to LLM-friendly format
        content = self._format_recipe_for_llm(recipe_data)

        if content:
            # Cache the result
            self._cache[source] = content

        return content

    def _fetch_recipe(self, source: str) -> Optional[Dict[str, Any]]:
        """
        Fetch OpenRewrite recipe YAML and parse it.

        Args:
            source: URL or file path

        Returns:
            Parsed recipe data or None if fetch fails
        """
        try:
            if self._is_url(source):
                # Fetch from URL
                response = requests.get(source, timeout=30)
                response.raise_for_status()
                content = response.text
            else:
                # Read from file
                path = Path(source)
                if not path.exists():
                    print(f"Error: Recipe file not found: {source}")
                    return None
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

            # Parse YAML (may contain multiple documents)
            recipes = list(yaml.safe_load_all(content))

            # If multiple recipes, return all of them as a list
            if len(recipes) == 1:
                return recipes[0]
            else:
                return {"multiple_recipes": recipes}

        except requests.RequestException as e:
            print(f"Error fetching recipe from {source}: {e}")
            return None
        except yaml.YAMLError as e:
            print(f"Error parsing YAML from {source}: {e}")
            return None
        except (IOError, OSError, UnicodeDecodeError) as e:
            print(f"Error reading file from {source}: {e}")
            return None
        except (ValueError, KeyError, TypeError) as e:
            print(f"Error processing recipe data from {source}: {e}")
            return None
        except Exception as e:
            # Catch any truly unexpected errors
            print(f"Unexpected error loading recipe from {source}: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _format_recipe_for_llm(self, recipe_data: Dict[str, Any]) -> str:
        """
        Format OpenRewrite recipe data into LLM-friendly text.

        Args:
            recipe_data: Parsed recipe YAML

        Returns:
            Formatted markdown text
        """
        # Handle multiple recipes in one file
        if "multiple_recipes" in recipe_data:
            recipes = recipe_data["multiple_recipes"]
            formatted_recipes = []
            for recipe in recipes:
                if recipe:  # Skip empty documents
                    formatted_recipes.append(self._format_single_recipe(recipe))
            return "\n\n---\n\n".join(formatted_recipes)
        else:
            return self._format_single_recipe(recipe_data)

    def _format_single_recipe(self, recipe: Dict[str, Any]) -> str:
        """Format a single recipe into markdown."""
        lines = []

        # Recipe metadata
        lines.append("# OpenRewrite Recipe")
        lines.append("")

        if recipe.get("type"):
            lines.append(f"**Type:** `{recipe['type']}`")
        if recipe.get("name"):
            lines.append(f"**Name:** `{recipe['name']}`")
        if recipe.get("displayName"):
            lines.append(f"**Display Name:** {recipe['displayName']}")
        if recipe.get("description"):
            lines.append(f"**Description:** {recipe['description']}")
        if recipe.get("tags"):
            lines.append(f"**Tags:** {', '.join(recipe['tags'])}")

        lines.append("")

        # Recipe list (transformations)
        if recipe.get("recipeList"):
            lines.append("## Transformations")
            lines.append("")
            lines.append("This recipe applies the following transformations:")
            lines.append("")

            for item in recipe["recipeList"]:
                lines.append(self._format_recipe_item(item))
                lines.append("")

        # Preconditions
        if recipe.get("preconditions"):
            lines.append("## Preconditions")
            lines.append("")
            lines.append("This recipe only applies when:")
            lines.append("")
            for precondition in recipe["preconditions"]:
                lines.append(self._format_recipe_item(precondition))
                lines.append("")

        return "\n".join(lines)

    def _format_recipe_item(self, item: Any, indent: int = 0) -> str:
        """
        Format a recipe list item (can be a string or dict with parameters).

        Args:
            item: Recipe item (string or dict)
            indent: Indentation level

        Returns:
            Formatted string
        """
        prefix = "  " * indent

        if isinstance(item, str):
            # Simple recipe reference
            return f"{prefix}- `{item}`"
        elif isinstance(item, dict):
            # Recipe with parameters
            lines = []
            for recipe_name, params in item.items():
                lines.append(f"{prefix}- `{recipe_name}`")
                if params and isinstance(params, dict):
                    for param_name, param_value in params.items():
                        lines.append(f"{prefix}  - **{param_name}:** `{param_value}`")
            return "\n".join(lines)
        else:
            return f"{prefix}- {str(item)}"

    def _is_url(self, source: str) -> bool:
        """Check if source is a URL."""
        try:
            result = urlparse(source)
            return all([result.scheme, result.netloc])
        except (ValueError, TypeError, AttributeError):
            return False
