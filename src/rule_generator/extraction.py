"""
Pattern Extraction Module

Uses Large Language Models (LLMs) to extract migration patterns from documentation
and migration guides, converting unstructured text into structured patterns for
rule generation.

Key Components:
    - MigrationPatternExtractor: Main class for LLM-based extraction
    - Prompt Building: Language-specific Jinja2 templates for LLM prompts
    - JSON Repair: Automatic fixing of malformed LLM responses
    - Pattern Validation: Auto-detection and fixing of common pattern issues
    - Chunking Support: Handles large documents via automatic chunking

Extracted Pattern Data:
    - Source pattern (old code/annotation/config to find)
    - Target pattern (new replacement to suggest)
    - Fully qualified names (FQNs) for semantic detection
    - Location types (ANNOTATION, IMPORT, TYPE, METHOD_CALL, etc.)
    - Provider types (java, nodejs, builtin, csharp, combo)
    - Rationale and migration complexity (TRIVIAL to EXPERT)
    - Code examples (before/after)
    - Documentation links

Language Support:
    - Java: Detects packages, classes, annotations, dependencies
    - JavaScript/TypeScript: Components, hooks, imports, JSX patterns
    - C#: Classes, methods, fields, namespaces
    - Configuration: Properties, YAML, XML patterns

Pattern Auto-Fixing:
    For JavaScript/TypeScript PatternFly migrations:
    - Detects component prop changes (e.g., "Button isActive")
    - Automatically converts to combo rules with import verification
    - Prevents false positives from identically-named components
    - Rejects overly broad patterns (common prop names)

Usage:
    >>> from rule_generator.llm import get_llm_provider
    >>> llm = get_llm_provider("anthropic", model="claude-3-7-sonnet-latest")
    >>> extractor = MigrationPatternExtractor(llm)
    >>> patterns = extractor.extract_patterns(
    ...     guide_content="Migration guide text...",
    ...     source_framework="patternfly-v5",
    ...     target_framework="patternfly-v6"
    ... )
    >>> print(f"Extracted {len(patterns)} patterns")

Large Document Handling:
    >>> # Documents > 40KB are automatically chunked
    >>> large_guide = load_large_migration_guide()
    >>> patterns = extractor.extract_patterns(large_guide, "v1", "v2")
    >>> # Patterns are automatically deduplicated across chunks

See Also:
    - MigrationPattern: Schema for extracted patterns (schema.py)
    - llm: LLM provider interface (llm.py)
    - Template files: templates/extraction/*.j2
"""

import json
import re
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import config
from .llm import LLMAPIError, LLMAuthenticationError, LLMProvider, LLMRateLimitError
from .logging_setup import PerformanceTimer, get_logger, log_decision
from .schema import CSharpLocationType, LocationType, MigrationPattern
from .security import validate_complexity, validate_llm_response

# Get module logger
logger = get_logger(__name__)

# Set up Jinja2 template environment
TEMPLATE_DIR = Path(__file__).parent.parent.parent / 'templates' / 'extraction'
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)

# Compiled regex patterns for performance (used in JSON repair and parsing)
JSON_ARRAY_PATTERN = re.compile(r'\[.*\]', re.DOTALL)
INVALID_ESCAPE_PATTERN = re.compile(r'\\([^"\\/bfnrtu])')
TRIPLE_BACKSLASH_PATTERN = re.compile(r'\\\\\\([^"\\/bfnrtu])')  # Matches \\\X where X is invalid
STRING_VALUE_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')
TRAILING_COMMA_PATTERN = re.compile(r',(\s*[}\]])')
OBJECT_SEPARATOR_PATTERN = re.compile(r'\}(\s*)\{')
ARRAY_SEPARATOR_PATTERN = re.compile(r'\](\s*)\[')
UNESCAPED_QUOTE_PATTERN = re.compile(r"(?<!\\)'")
KEY_VALUE_PATTERN = re.compile(r'"([^"]+)":\s*"([^"]*[^\\]"[^"]*)"')


def detect_language_from_frameworks(source: str, target: str) -> str:
    """
    Detect programming language based on framework names.

    Args:
        source: Source framework name
        target: Target framework name

    Returns:
        Language identifier: 'java', 'javascript', 'typescript', 'go', 'csharp', or 'unknown'
    """
    # Combine source and target for analysis
    frameworks = f"{source} {target}".lower()

    # JavaScript/TypeScript frameworks
    js_ts_keywords = [
        'react',
        'angular',
        'vue',
        'node',
        'npm',
        'typescript',
        'javascript',
        'patternfly',
        'next',
        'nuxt',
        'svelte',
        'ember',
        'webpack',
        'vite',
        'express',
        'nestjs',
        'gatsby',
        'redux',
    ]

    # Java frameworks
    java_keywords = [
        'spring',
        'jakarta',
        'javax',
        'jboss',
        'wildfly',
        'tomcat',
        'hibernate',
        'jpa',
        'ejb',
        'servlet',
        'jdk',
        'openjdk',
        'quarkus',
        'micronaut',
        'maven',
        'gradle',
    ]

    # C# / .NET frameworks
    csharp_keywords = [
        'dotnet',
        '.net',
        'csharp',
        'c#',
        'asp.net',
        'aspnet',
        'entityframework',
        'ef',
        'mvc',
        'webapi',
        'blazor',
        'xamarin',
        'maui',
        'nuget',
        'dotnetcore',
        'netcore',
        'netframework',
    ]

    # Go frameworks and version identifiers
    go_keywords = [
        'go',
        'golang',
        'go-1.',  # Matches go-1.17, go-1.18, go-1.19, etc.
        'go1.',  # Matches go1.17, go1.18, go1.19, etc.
    ]

    # Check for Go patterns (check first as "go" is short and might appear in other contexts)
    # Only match if it's clearly a Go version or "golang"
    if any(keyword in frameworks for keyword in go_keywords):
        # Additional validation: ensure it's not a false positive
        # (e.g., "go" appearing in "django" or other frameworks)
        if (
            'golang' in frameworks
            or 'go-1.' in frameworks
            or 'go1.' in frameworks
            or frameworks.startswith('go ')
            or frameworks.endswith(' go')
            or frameworks == 'go'
        ):
            return 'go'

    # Check for JS/TS patterns
    if any(keyword in frameworks for keyword in js_ts_keywords):
        # If TypeScript is explicitly mentioned, return typescript
        if 'typescript' in frameworks:
            return 'typescript'
        return 'javascript'

    # Check for C# / .NET patterns
    if any(keyword in frameworks for keyword in csharp_keywords):
        return 'csharp'

    # Check for Java patterns
    if any(keyword in frameworks for keyword in java_keywords):
        return 'java'

    return 'unknown'


class MigrationPatternExtractor:
    """Extract migration patterns from guide content using LLM."""

    def __init__(self, model: LLMProvider, from_openrewrite: bool = False):
        """
        Initialize pattern extractor with LLM model.

        Args:
            model: LLM provider instance
            from_openrewrite: If True, use OpenRewrite-specific prompting
        """
        self.model = model
        self.from_openrewrite = from_openrewrite

    def extract_patterns(
        self,
        guide_content: str,
        source_framework: Optional[str] = None,
        target_framework: Optional[str] = None,
    ) -> List[MigrationPattern]:
        """
        Extract migration patterns from guide content.

        Args:
            guide_content: Clean text content from guide
            source_framework: Source framework name (e.g., "spring-boot")
            target_framework: Target framework name (e.g., "quarkus")

        Returns:
            List of extracted migration patterns
        """
        # Handle None or empty content
        if not guide_content:
            return []

        # Check if content needs chunking (>40KB)
        if len(guide_content) > config.MAX_CONTENT_SIZE:
            print(
                f"  → Content is large ({len(guide_content):,} chars), " f"using chunked extraction"
            )
            return self._extract_patterns_chunked(guide_content, source_framework, target_framework)

        # Single extraction for smaller content
        return self._extract_patterns_single(guide_content, source_framework, target_framework)

    def _extract_patterns_single(
        self,
        guide_content: str,
        source_framework: Optional[str] = None,
        target_framework: Optional[str] = None,
    ) -> List[MigrationPattern]:
        """Extract patterns from a single piece of content."""
        with PerformanceTimer(logger, f"pattern extraction from {len(guide_content)} chars"):
            # Build prompt (use OpenRewrite-specific prompt if needed)
            if self.from_openrewrite:
                prompt = self._build_openrewrite_prompt(
                    guide_content, source_framework, target_framework
                )
            else:
                prompt = self._build_extraction_prompt(
                    guide_content, source_framework, target_framework
                )

            # Generate with LLM
            try:
                result = self.model.generate(prompt)

                # Extract text response
                response_text = result.get("response", "")

                # Validate LLM response structure before parsing
                try:
                    response_text = validate_llm_response(
                        response_text, expected_format="json_array"
                    )
                except ValueError as e:
                    logger.warning(f"Invalid LLM response structure: {e}")
                    return []

                # Parse response
                patterns = self._parse_extraction_response(response_text)

                # Validate and fix patterns
                language = detect_language_from_frameworks(
                    source_framework or "", target_framework or ""
                )
                patterns = self._validate_and_fix_patterns(
                    patterns, language, source_framework, target_framework
                )

                logger.info(f"Extracted {len(patterns)} valid patterns from content")
                return patterns

            except (ValueError, TypeError, KeyError) as e:
                # Handle validation or parsing errors gracefully
                print(f"[Extraction] Error: Failed to parse LLM response: {e}")
                return []
            except (ConnectionError, TimeoutError, OSError) as e:
                # Handle network-related errors
                print(f"[Extraction] Warning: Network error, skipping chunk: {e}")
                return []
            except LLMRateLimitError as e:
                # Rate limit exceeded - expected error, just log and continue
                print(f"[Extraction] Warning: Rate limit exceeded, skipping chunk: {e}")
                return []
            except LLMAuthenticationError as e:
                # Authentication failed - fatal error, raise it
                print(f"[Extraction] Error: Authentication failed: {e}")
                raise
            except LLMAPIError as e:
                # API error (5xx, temporary failures) - log and continue
                print(f"[Extraction] Warning: API temporarily unavailable, skipping chunk: {e}")
                return []
            except Exception as e:
                # Fallback for any other exceptions (e.g., from custom providers or during testing)
                # Check if error message indicates specific error types
                error_message = str(e).lower()
                if "rate" in error_message or "429" in error_message:
                    print(f"[Extraction] Warning: Rate limit exceeded, skipping chunk: {e}")
                elif "api" in error_message or "500" in error_message:
                    print(f"[Extraction] Warning: API error, skipping chunk: {e}")
                else:
                    print(f"[Extraction] Warning: Pattern extraction failed, skipping chunk: {e}")
                return []

    def _extract_patterns_chunked(
        self,
        guide_content: str,
        source_framework: Optional[str] = None,
        target_framework: Optional[str] = None,
    ) -> List[MigrationPattern]:
        """Extract patterns from large content by chunking."""
        from .ingestion import GuideIngester

        # Chunk the content
        ingester = GuideIngester()
        chunks = ingester.chunk_content(guide_content, max_tokens=config.EXTRACTION_MAX_TOKENS)

        print(f"  → Split into {len(chunks)} chunks")

        all_patterns = []
        for i, chunk in enumerate(chunks, 1):
            print(f"  → Processing chunk {i}/{len(chunks)} ({len(chunk):,} chars)")

            # Extract from this chunk
            patterns = self._extract_patterns_single(chunk, source_framework, target_framework)

            if patterns:
                print(f"    ✓ Extracted {len(patterns)} patterns from chunk {i}")
                all_patterns.extend(patterns)

        # Deduplicate patterns based on source_fqn
        deduplicated = self._deduplicate_patterns(all_patterns)

        print(f"  ✓ Total: {len(all_patterns)} patterns extracted, {len(deduplicated)} unique")

        return deduplicated

    def _deduplicate_patterns(self, patterns: List[MigrationPattern]) -> List[MigrationPattern]:
        """Remove duplicate patterns based on source_fqn."""
        seen = set()
        unique = []

        for pattern in patterns:
            # Create a key from source_fqn and concern
            key = (pattern.source_fqn, pattern.concern)

            if key not in seen:
                seen.add(key)
                unique.append(pattern)

        return unique

    def _build_extraction_prompt(
        self, guide_content: str, source_framework: Optional[str], target_framework: Optional[str]
    ) -> str:
        """Build LLM prompt for pattern extraction using templates."""

        # Detect language for language-specific instructions
        language = "unknown"
        if source_framework and target_framework:
            language = detect_language_from_frameworks(source_framework, target_framework)

        # Build frameworks context
        frameworks = ""
        if source_framework and target_framework:
            frameworks = f"Migration: {source_framework} → {target_framework}\n"
            frameworks += f"Detected Language: {language}\n\n"

        # Load language-specific instructions template
        lang_instructions = ""
        if language in ["javascript", "typescript"]:
            lang_template = jinja_env.get_template('lang/javascript.j2')
            lang_instructions = lang_template.render()
        elif language == "csharp":
            lang_template = jinja_env.get_template('lang/csharp.j2')
            lang_instructions = lang_template.render()
        elif language == "java":
            lang_template = jinja_env.get_template('lang/java.j2')
            lang_instructions = lang_instructions = lang_template.render()
        elif language == "go":
            lang_template = jinja_env.get_template('lang/go.j2')
            lang_instructions = lang_template.render()

        # Render main prompt template
        main_template = jinja_env.get_template('main.j2')
        prompt = main_template.render(
            frameworks=frameworks, lang_instructions=lang_instructions, guide_content=guide_content
        )

        return prompt

    def _build_openrewrite_prompt(
        self, recipe_content: str, source_framework: Optional[str], target_framework: Optional[str]
    ) -> str:
        """Build LLM prompt for OpenRewrite recipe conversion."""

        # Detect language for language-specific instructions
        language = "java"  # OpenRewrite is primarily Java
        if source_framework and target_framework:
            language = detect_language_from_frameworks(source_framework, target_framework)

        frameworks = ""
        if source_framework and target_framework:
            frameworks = f"Migration: {source_framework} → {target_framework}\n"
            frameworks += f"Detected Language: {language}\n\n"

        # Language-specific instructions (reuse from regular prompt)
        lang_instructions = ""
        if language == "java":
            lang_instructions = """
**Java Detection Instructions:**
For Java code patterns (classes, annotations, imports), use these fields:
- **provider_type**: Set to "java" (or leave null for auto-detection)
- **source_fqn**: Fully qualified class name (e.g., "javax.ejb.Stateless")
- **location_type**: Choose based on what you're detecting:
  - **TYPE**: For package changes with wildcards (e.g., "com.sun.net.ssl.*")
    - PREFERRED for ChangePackage
  - **IMPORT**: For specific class imports only (no wildcards, exact FQN required
    like "org.springframework.boot.actuate.trace.http.HttpTraceRepository")
  - **METHOD_CALL**: For method invocations
  - **ANNOTATION**: For annotation usage
  - **INHERITANCE**: For class inheritance
  - **PACKAGE**: Do not use - TYPE is preferred
- **file_pattern**: Can be null

**Maven Dependency Detection Instructions:**
For Maven dependency changes (pom.xml), use these fields:
- **provider_type**: Set to "java" (the java provider handles Maven dependencies)
- **category**: MUST set to "dependency"
- **source_fqn**: Maven coordinates in format "groupId:artifactId"
  (e.g., "mysql:mysql-connector-java" or "org.springframework.boot:spring-boot-starter-web")
- **alternative_fqns**: CRITICAL - Include Maven relocations!
  Many Maven artifacts have been relocated:
  * "mysql:mysql-connector-java" → "com.mysql:mysql-connector-j" (relocated in 8.0+)
  * If the migration guide mentions a dependency change, check if it's a Maven relocation
  * Include BOTH the old and relocated coordinates in alternative_fqns
    (e.g., ["com.mysql:mysql-connector-j"])
  * Maven automatically resolves relocations, so the analyzer will see the NEW coordinates
    even if pom.xml has OLD ones
- **location_type**: null (not needed for dependency detection)
- **file_pattern**: null

**Configuration File Detection Instructions:**
For property/configuration file patterns (application.properties, application.yaml),
use these fields:
- **provider_type**: Set to "builtin"
- **source_fqn**: SIMPLE regex pattern to match the property. Use `.*` for wildcards
  and escape dots with \\\\ (e.g., "spring\\.data\\.mongodb\\.host")
- **file_pattern**: Regex pattern to match configuration files (e.g., ".*\\.(properties|yaml|yml)")
- **location_type**: null (not needed for builtin provider)
- **category**: "configuration"

"""

        prompt = f"""You are converting OpenRewrite recipes into Konveyor analyzer
detection patterns.

{frameworks}**IMPORTANT: OpenRewrite vs Konveyor**

OpenRewrite recipes contain TRANSFORMATION logic (how to automatically rewrite code).
Konveyor rules contain DETECTION patterns (how to find code that needs review).

Your task: For each OpenRewrite transformation, extract the DETECTION pattern.

**Example Conversion:**

OpenRewrite Recipe:
```
- org.openrewrite.java.ChangePackage:
    oldPackageName: javax.security.cert
    newPackageName: java.security.cert
```

Konveyor Detection Pattern:
```json
{{
  "source_pattern": "javax.security.cert",
  "target_pattern": "java.security.cert",
  "source_fqn": "javax.security.cert.*",
  "location_type": "TYPE",
  "provider_type": "java",
  "complexity": "TRIVIAL",
  "category": "api",
  "concern": "security",
  "rationale": "javax.security.cert package is deprecated for removal",
  "example_before": "import javax.security.cert.Certificate;",
  "example_after": "import java.security.cert.Certificate;",
  "documentation_url": null
}}
```

**Common OpenRewrite Transformation Types:**

1. **ChangePackage** - Package renames
   - Extract: oldPackageName as source_pattern, newPackageName as target_pattern
   - **IMPORTANT**: Use location_type: TYPE for package-level detection with wildcards
   - Pattern format: "oldPackage.*" to match all classes in the package
   - Note: TYPE works with wildcards, IMPORT requires specific class names

2. **ChangeType** - Class renames
   - Extract: oldFullyQualifiedTypeName as source_fqn, newFullyQualifiedTypeName as target
   - location_type: TYPE (catches usage in any context)
   - Note: Use exact FQN, not wildcards (e.g., "com.example.OldClass")

3. **ChangeMethodName** - Method renames
   - Extract: methodPattern and newMethodName
   - location_type: METHOD_CALL

4. **AddDependency** / **ChangeDependency** - Dependency updates
   - Extract: groupId/artifactId changes
   - category: dependency

5. **Composite Recipes** - Multiple sub-recipes
   - Create separate patterns for each meaningful sub-recipe

**Location Type Selection:**
- **TYPE**: For package-level changes with wildcards (e.g., "javax.security.cert.*")
  - USE THIS FOR ChangePackage
- **IMPORT**: For specific class imports (requires exact FQN, no wildcards)
- **METHOD_CALL**: For detecting method invocations
- **ANNOTATION**: For detecting annotation usage
- **INHERITANCE**: For detecting class inheritance relationships
- **PACKAGE**: Do not use - TYPE is preferred for package-level detection

{lang_instructions}
---
OPENREWRITE RECIPE CONTENT:

{recipe_content}

---

**Instructions:**

1. Analyze each transformation in the recipe
2. For simple transformations (ChangePackage, ChangeType), directly map to detection patterns
3. For complex transformations, infer what code patterns are being changed
4. Skip recipe references that are too generic (e.g., "UpgradeToJava17" without parameters)
5. For composite recipes with sub-recipes, expand and extract patterns from each
   meaningful transformation

Return your findings as a JSON array with these fields:

{{
  "source_pattern": "string",
  "target_pattern": "string",
  "source_fqn": "string or null",
  "location_type": "ANNOTATION|IMPORT|METHOD_CALL|TYPE|INHERITANCE|PACKAGE|FIELD|
                    CLASS|METHOD|ALL or null",
  "alternative_fqns": ["string"] or [],
  "complexity": "TRIVIAL|LOW|MEDIUM|HIGH|EXPERT",
  "category": "dependency|annotation|api|configuration|other",
  "concern": "string",
  "provider_type": "java|builtin or null",
  "file_pattern": "string or null",
  "rationale": "string",
  "example_before": "string or null",
  "example_after": "string or null",
  "documentation_url": "string or null"
}}

**Complexity Guidelines:**
- TRIVIAL: Package renames, removing unused imports
- LOW: Simple 1:1 class/method renames
- MEDIUM: API changes with similar alternatives
- HIGH: Deprecated APIs requiring refactoring
- EXPERT: Architectural changes

Return ONLY the JSON array, no additional commentary."""

        return prompt

    def _repair_json(self, json_str: str) -> str:
        """
        Attempt to repair common JSON syntax errors.

        Args:
            json_str: Potentially malformed JSON string

        Returns:
            Repaired JSON string
        """

        # Fix triple-backslash + invalid escape (e.g., \\\s → \\\\s)
        # This happens when LLM over-escapes regex patterns
        # \\\s in JSON = \\ (one backslash) + \s (invalid!)
        # Should be \\\\s = \\ + \\ (two backslashes) for the regex \s
        matches = TRIPLE_BACKSLASH_PATTERN.findall(json_str)
        if matches:
            print(f"[Extraction] Debug: Found {len(matches)} triple-backslash patterns: {matches}")
        json_str = TRIPLE_BACKSLASH_PATTERN.sub(r'\\\\\\\\\1', json_str)
        if matches:
            print("[Extraction] Debug: Applied triple-backslash fix")

        # Fix invalid single-quote escapes in JSON strings
        # JSON doesn't allow \' (single quotes don't need escaping in double-quoted strings)
        # But LLM often generates JSX with \' which is valid in JS but not JSON
        # Example: "example_before": "<Avatar border={\'dark\'} />"
        # Should be: "example_before": "<Avatar border={'dark'} />"
        json_str = json_str.replace("\\'", "'")

        # Remove trailing commas before closing brackets/braces
        # e.g., {"key": "value",} -> {"key": "value"}
        json_str = TRAILING_COMMA_PATTERN.sub(r'\1', json_str)

        # Fix missing commas between objects in arrays
        # e.g., }{"key" -> },{"key"
        json_str = OBJECT_SEPARATOR_PATTERN.sub(r'},\1{', json_str)

        # Fix missing commas between array items
        # e.g., ]["key" -> ],["key"
        json_str = ARRAY_SEPARATOR_PATTERN.sub(r'],\1[', json_str)

        # DON'T escape single quotes - they don't need escaping in JSON double-quoted strings!
        # The fix_unescaped_quotes() was ADDING \' which is invalid JSON
        # Single quotes have no special meaning in JSON strings

        return json_str

    def _parse_extraction_response(self, response: str) -> List[MigrationPattern]:
        """
        Parse LLM response into MigrationPattern objects.

        Args:
            response: LLM response text

        Returns:
            List of MigrationPattern objects
        """
        # Try to extract JSON from response
        json_match = JSON_ARRAY_PATTERN.search(response)

        if not json_match:
            print("[Extraction] Warning: No JSON array found in LLM response")
            return []

        json_str = json_match.group(0)

        try:
            patterns_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"[Extraction] Warning: JSON parsing failed: {e} (attempting repair)")
            print("[Extraction] Info: Attempting to repair malformed JSON...")

            # Write ORIGINAL failed JSON before any repairs for debugging
            import tempfile

            try:
                with tempfile.NamedTemporaryFile(
                    mode='w', suffix='_original.json', delete=False, prefix='failed_json_'
                ) as f:
                    f.write(json_str)
                    print(f"[Extraction] Debug: Original failed JSON written to {f.name}")
            except Exception:
                pass

            # Try to repair the JSON
            repaired_json = self._repair_json(json_str)

            try:
                patterns_data = json.loads(repaired_json)
                print("[Extraction] Info: Successfully repaired JSON")
            except json.JSONDecodeError as e2:
                print(f"[Extraction] Warning: JSON repair failed: {e2}")

                # Write failed JSON to temp file for debugging
                import tempfile

                try:
                    with tempfile.NamedTemporaryFile(
                        mode='w', suffix='.json', delete=False, prefix='failed_json_'
                    ) as f:
                        f.write(repaired_json)
                        print(f"[Extraction] Debug: Failed JSON written to {f.name}")
                except Exception:
                    pass  # Don't fail if we can't write debug file

                # Try fixing missing commas between adjacent strings (common LLM error)
                # Pattern: "value""key" -> "value","key"
                try:
                    comma_fixed = re.sub(r'"\s*"([a-zA-Z_])', r'","\1', repaired_json)
                    patterns_data = json.loads(comma_fixed)
                    print("[Extraction] Info: Successfully repaired JSON (added missing commas)")
                except json.JSONDecodeError as e3:
                    print(f"[Extraction] Error: All JSON repair attempts failed: {e3}")
                    print(f"[Extraction] Debug: Response preview: {response[:500]}")
                    return []

        # Convert to MigrationPattern objects
        patterns = []
        for data in patterns_data:
            try:
                # Map location_type string to enum (try both Java and C# enums)
                location_type = None
                if data.get("location_type"):
                    try:
                        # Try Java LocationType first
                        location_type = LocationType(data["location_type"])
                    except ValueError:
                        try:
                            # Try C# CSharpLocationType
                            location_type = CSharpLocationType(data["location_type"])
                        except ValueError:
                            print(
                                f"[Extraction] Warning: Unknown location type, "
                                f"using None: {data.get('location_type')}"
                            )

                # Validate complexity value
                complexity = data["complexity"]
                try:
                    complexity = validate_complexity(complexity)
                except ValueError as e:
                    print(
                        f"[Extraction] Warning: Invalid complexity '{complexity}', "
                        f"defaulting to MEDIUM: {e}"
                    )
                    complexity = "MEDIUM"

                pattern = MigrationPattern(
                    source_pattern=data["source_pattern"],
                    target_pattern=data["target_pattern"],
                    source_fqn=data.get("source_fqn"),
                    location_type=location_type,
                    alternative_fqns=data.get("alternative_fqns", []),
                    complexity=complexity,
                    category=data["category"],
                    concern=data.get("concern", "general"),
                    provider_type=data.get("provider_type"),
                    file_pattern=data.get("file_pattern"),
                    when_combo=data.get("when_combo"),
                    rationale=data["rationale"],
                    example_before=data.get("example_before"),
                    example_after=data.get("example_after"),
                    documentation_url=data.get("documentation_url"),
                )
                patterns.append(pattern)
            except (KeyError, TypeError) as e:
                print(f"[Extraction] Warning: Skipping invalid pattern: {e}")
                print(f"[Extraction] Debug: Pattern data: {data}")
                continue

        return patterns

    def _validate_and_fix_patterns(
        self,
        patterns: List[MigrationPattern],
        language: str,
        source_framework: Optional[str] = None,
        target_framework: Optional[str] = None,
    ) -> List[MigrationPattern]:
        """
        Validate patterns and auto-fix common issues.

        Args:
            patterns: List of patterns to validate
            language: Detected language (javascript, typescript, java, csharp, go, unknown)
            source_framework: Source framework name (e.g., "patternfly-v5", "react-17", "go-1.17")
            target_framework: Target framework name (e.g., "patternfly-v6", "react-18", "go-1.18")

        Returns:
            List of validated/fixed patterns
        """
        validated = []

        # Check if this is a PatternFly migration (only auto-convert to combo rules for PatternFly)
        is_patternfly = False
        if source_framework and target_framework:
            frameworks = f"{source_framework} {target_framework}".lower()
            is_patternfly = "patternfly" in frameworks

        for pattern in patterns:
            # RULE 1: Component-specific prop changes MUST use combo rules (PatternFly only)
            if language in ["javascript", "typescript"] and is_patternfly:
                # Detect if this is a prop change pattern
                is_prop_pattern = self._looks_like_prop_pattern(pattern)

                if is_prop_pattern and pattern.provider_type != "combo":
                    log_decision(
                        logger,
                        "Auto-converting to combo rule",
                        "Component prop patterns require import verification to prevent "
                        "false positives",
                        pattern=pattern.source_pattern,
                        language=language,
                    )
                    pattern = self._convert_to_combo_rule(pattern)

            # RULE 2: Reject overly generic builtin patterns (PatternFly only)
            if language in ["javascript", "typescript"] and is_patternfly:
                if pattern.provider_type == "builtin" and pattern.source_fqn:
                    if self._is_overly_broad_pattern(pattern.source_fqn):
                        log_decision(
                            logger,
                            "Rejecting overly broad pattern",
                            "Pattern is too generic and would cause false positives",
                            pattern=pattern.source_fqn,
                            provider_type="builtin",
                        )
                        continue

            # RULE 3: Ensure source != target
            if pattern.source_pattern and pattern.target_pattern:
                if pattern.source_pattern.strip() == pattern.target_pattern.strip():
                    print(
                        f"[Extraction] Warning: Rejecting pattern with identical source/target: "
                        f"{pattern.source_pattern}"
                    )
                    continue

            # RULE 4: Validate and fix provider_type for detected language
            if pattern.provider_type:
                corrected_provider = self._validate_provider_for_language(
                    pattern.provider_type, language, pattern.source_pattern
                )
                if corrected_provider != pattern.provider_type:
                    log_decision(
                        logger,
                        "Auto-correcting provider type",
                        f"Provider '{pattern.provider_type}' is incorrect for {language} code",
                        pattern=pattern.source_pattern,
                        old_provider=pattern.provider_type,
                        new_provider=corrected_provider,
                    )
                    pattern.provider_type = corrected_provider

            validated.append(pattern)

        return validated

    def _looks_like_prop_pattern(self, pattern: MigrationPattern) -> bool:
        """
        Check if pattern appears to be a component prop change.

        Detects patterns following the format "ComponentName propName" where ComponentName
        starts with uppercase (PascalCase) and propName starts with lowercase (camelCase).
        Excludes common method names that match this pattern but aren't component props.

        Args:
            pattern: Migration pattern to analyze

        Returns:
            True if pattern looks like a component prop change (e.g., "Button isActive"),
            False otherwise (including method calls like "Component render")

        Examples:
            >>> pattern = MigrationPattern(source_pattern="Button isActive", ...)
            >>> self._looks_like_prop_pattern(pattern)
            True
            >>> pattern = MigrationPattern(source_pattern="Component render", ...)
            >>> self._looks_like_prop_pattern(pattern)  # render is a method
            False
        """
        # Look for patterns like "Button isActive" or "Modal title"
        if not pattern.source_pattern:
            return False

        parts = pattern.source_pattern.split()
        if len(parts) >= 2:
            # First part looks like component name (PascalCase)
            # Second part looks like prop name (camelCase)
            if parts[0] and parts[0][0].isupper() and parts[1] and parts[1][0].islower():
                # Exclude keywords that look like props but aren't
                # These are method calls, imports, exports, or other non-prop patterns
                excluded_keywords = [
                    # Method names
                    "render",
                    "mount",
                    "unmount",
                    "update",
                    "setState",
                    "useState",
                    "useEffect",
                    # Import/export related
                    "import",
                    "export",
                    "from",
                    "next",
                    "specifiers",
                    # Type/interface related
                    "interface",
                    "type",
                    # Generic descriptors
                    "component",
                    "class",
                    "function",
                    # CSS/styling related (exclude only clearly non-prop keywords)
                    "variable",  # CSS variables, not props
                    "property",  # CSS properties, not component props
                    "attribute",  # HTML attributes description
                    "selector",  # CSS selectors
                    # Note: "value" is NOT excluded - it's a common prop name
                    # (Input value, Select value, etc.)
                ]
                if parts[1] in excluded_keywords:
                    return False
                return True

        return False

    def _convert_to_combo_rule(self, pattern: MigrationPattern) -> MigrationPattern:
        """
        Convert a simple pattern to combo rule with import verification.

        For JavaScript/TypeScript component patterns, this adds import verification
        to ensure the component is from the target library (e.g., @patternfly/react-core).
        This prevents false positives from components with the same name in other libraries.

        Args:
            pattern: Migration pattern to convert (expects source_pattern like "Component propName")

        Returns:
            Modified pattern with provider_type set to "combo" and when_combo conditions added

        Example:
            >>> pattern = MigrationPattern(source_pattern="Button isActive", ...)
            >>> converted = self._convert_to_combo_rule(pattern)
            >>> converted.provider_type
            'combo'
            >>> 'import_pattern' in converted.when_combo
            True
        """
        parts = pattern.source_pattern.split()
        if len(parts) >= 2:
            component = parts[0]
            prop = parts[1]

            pattern.provider_type = "combo"
            pattern.source_fqn = component

            # Use nodejs.referenced for semantic component detection
            # This matches how official Konveyor PatternFly rules work:
            # - nodejs.referenced finds the component symbol (Button, Import, etc.)
            # - builtin.filecontent matches the JSX pattern with the prop
            #
            # Example official rule structure:
            # when:
            #   and:
            #   - nodejs.referenced:
            #       pattern: Button
            #   - builtin.filecontent:
            #       pattern: <Button[^>]*\bvariant=['"]plain['"][^>]*>
            #       filePattern: \.(j|t)sx?$
            pattern.when_combo = {
                "nodejs_pattern": component,
                "builtin_pattern": f"<{component}[^>]*\\\\b{prop}\\\\b",
                "file_pattern": "\\.(j|t)sx?$",
            }

        return pattern

    def _is_overly_broad_pattern(self, pattern: str) -> bool:
        """
        Check if builtin pattern is too broad and would cause false positives.

        Rejects patterns that are overly generic (common prop names, wildcard patterns)
        that would match too many unrelated code instances, leading to false positives.

        Args:
            pattern: Pattern string to check (typically from source_fqn)

        Returns:
            True if pattern is too broad and should be rejected, False if acceptable

        Examples:
            >>> self._is_overly_broad_pattern("isActive")  # Too generic
            True
            >>> self._is_overly_broad_pattern(".*")  # Pure wildcard
            True
            >>> self._is_overly_broad_pattern("Button")  # Specific component
            False
        """
        # Common prop names that should never be standalone patterns
        overly_generic = [
            "isActive",
            "isDisabled",
            "isOpen",
            "isClosed",
            "isExpanded",
            "title",
            "name",
            "id",
            "className",
            "style",
            "onClick",
            "onChange",
            "onSubmit",
            "onClose",
            "alignLeft",
            "alignRight",
            "alignCenter",
            "variant",
            "size",
            "color",
            "type",
        ]

        # If pattern is just one of these words, it's too broad
        if pattern.strip() in overly_generic:
            return True

        # Patterns that are just wildcards are too broad
        if pattern.strip() in [".*", ".+", "\\w+", "[a-zA-Z]+", ".*Icon"]:
            return True

        return False

    def _validate_provider_for_language(
        self, provider_type: str, language: str, pattern_text: Optional[str] = None
    ) -> str:
        """
        Validate that provider_type is appropriate for the detected language.

        Auto-corrects common mistakes where LLM chooses wrong provider for the language.
        For example, using 'nodejs.referenced' for Go code or 'java.referenced' for Go.

        Args:
            provider_type: Current provider type from pattern
            language: Detected language (go, java, javascript, typescript, csharp, unknown)
            pattern_text: Pattern text for logging/debugging

        Returns:
            Corrected provider_type (may be same as input if already correct)
        """
        # Valid provider combinations for each language
        # 'builtin' is valid for all languages (text/regex matching)
        valid_providers = {
            'go': {'go', 'builtin'},
            'java': {'java', 'builtin'},
            'javascript': {'nodejs', 'combo', 'builtin'},
            'typescript': {'nodejs', 'combo', 'builtin'},
            'csharp': {'csharp', 'builtin'},
        }

        # If language unknown or provider is already builtin/combo, keep as-is
        if language not in valid_providers or provider_type in {'builtin', 'combo'}:
            return provider_type

        # Check if provider is valid for this language
        if provider_type in valid_providers[language]:
            return provider_type

        # Provider is incorrect - auto-correct to the semantic provider for this language
        # Map: go -> go, java -> java, javascript/typescript -> nodejs, csharp -> csharp
        language_to_provider = {
            'go': 'go',
            'java': 'java',
            'javascript': 'nodejs',
            'typescript': 'nodejs',
            'csharp': 'csharp',
        }

        return language_to_provider.get(language, provider_type)
