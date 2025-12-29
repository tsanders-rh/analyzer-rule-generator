"""
Pattern extraction - Use LLM to extract migration patterns from guides.

Extracts patterns with enough detail to generate Konveyor analyzer rules including:
- Source pattern (old code/annotation/config)
- Target pattern (new replacement)
- Fully qualified names for detection
- Location types (ANNOTATION, IMPORT, etc.)
- Rationale and complexity
"""

import json
import re
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import config
from .llm import LLMAPIError, LLMAuthenticationError, LLMProvider, LLMRateLimitError
from .schema import CSharpLocationType, LocationType, MigrationPattern

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
        Language identifier: 'java', 'javascript', 'typescript', or 'unknown'
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
        # Check if content needs chunking (>40KB)
        if guide_content and len(guide_content) > config.MAX_CONTENT_SIZE:
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

            # Parse response
            patterns = self._parse_extraction_response(response_text)

            # Validate and fix patterns
            language = detect_language_from_frameworks(
                source_framework or "", target_framework or ""
            )
            patterns = self._validate_and_fix_patterns(
                patterns, language, source_framework, target_framework
            )

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

        # Fix invalid escape sequences in string values FIRST
        # JSON only allows: \" \\ \/ \b \f \n \r \t \uXXXX
        # Regex patterns often have: \. \d \w \s etc. which are invalid in JSON
        def fix_invalid_escapes(match):
            value = match.group(1)
            # Double-escape backslashes that aren't followed by valid JSON escape chars
            # Valid JSON escapes: " \ / b f n r t u
            # Replace \X (where X is not a valid escape) with \\X
            fixed = INVALID_ESCAPE_PATTERN.sub(r'\\\\\1', value)
            return f'"{fixed}"'

        # Match string values and fix invalid escapes
        # This pattern matches: "..." string values
        json_str = STRING_VALUE_PATTERN.sub(fix_invalid_escapes, json_str)

        # Remove trailing commas before closing brackets/braces
        # e.g., {"key": "value",} -> {"key": "value"}
        json_str = TRAILING_COMMA_PATTERN.sub(r'\1', json_str)

        # Fix missing commas between objects in arrays
        # e.g., }{"key" -> },{"key"
        json_str = OBJECT_SEPARATOR_PATTERN.sub(r'},\1{', json_str)

        # Fix missing commas between array items
        # e.g., ]["key" -> ],["key"
        json_str = ARRAY_SEPARATOR_PATTERN.sub(r'],\1[', json_str)

        # Fix unescaped quotes in string values (basic heuristic)
        # This is tricky - only fix obvious cases like: "description": "It's a test"
        # Convert to: "description": "It\'s a test"
        # But skip already escaped quotes
        def fix_unescaped_quotes(match):
            key = match.group(1)
            value = match.group(2)
            # Escape single quotes that aren't already escaped
            value = UNESCAPED_QUOTE_PATTERN.sub(r"\'", value)
            return f'"{key}": "{value}"'

        # Match "key": "value" pairs and fix unescaped quotes in values
        # This pattern is conservative to avoid breaking valid JSON
        json_str = KEY_VALUE_PATTERN.sub(fix_unescaped_quotes, json_str)

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

            # Try to repair the JSON
            repaired_json = self._repair_json(json_str)

            try:
                patterns_data = json.loads(repaired_json)
                print("[Extraction] Info: Successfully repaired JSON")
            except json.JSONDecodeError as e2:
                print(f"[Extraction] Warning: JSON repair failed: {e2} (trying aggressive repair)")
                # Try one more aggressive repair: escape all single backslashes
                try:
                    # Replace single backslash with double backslash in string values
                    aggressive_json = repaired_json
                    # This is a last resort - may break some patterns but better than nothing
                    aggressive_json = aggressive_json.replace('\\', '\\\\')
                    # But we may have over-escaped, so fix double-double backslashes
                    aggressive_json = aggressive_json.replace('\\\\\\\\', '\\\\')
                    patterns_data = json.loads(aggressive_json)
                    print("[Extraction] Info: Successfully repaired JSON with aggressive escaping")
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

                pattern = MigrationPattern(
                    source_pattern=data["source_pattern"],
                    target_pattern=data["target_pattern"],
                    source_fqn=data.get("source_fqn"),
                    location_type=location_type,
                    alternative_fqns=data.get("alternative_fqns", []),
                    complexity=data["complexity"],
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
            language: Detected language (javascript, typescript, java, csharp)
            source_framework: Source framework name (e.g., "patternfly-v5", "react-17")
            target_framework: Target framework name (e.g., "patternfly-v6", "react-18")

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
                    print(
                        f"[Extraction] Info: Auto-converting to combo rule: "
                        f"{pattern.source_pattern}"
                    )
                    pattern = self._convert_to_combo_rule(pattern)

            # RULE 2: Reject overly generic builtin patterns
            if pattern.provider_type == "builtin" and pattern.source_fqn:
                if self._is_overly_broad_pattern(pattern.source_fqn):
                    print(
                        f"[Extraction] Warning: Rejecting overly broad pattern: "
                        f"{pattern.source_fqn}"
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
                # Exclude common method names that look like props but aren't
                # These are method calls, not component props
                method_names = [
                    "render",
                    "mount",
                    "unmount",
                    "update",
                    "setState",
                    "useState",
                    "useEffect",
                ]
                if parts[1] in method_names:
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

            # Create import verification pattern for PatternFly
            # This matches: import { Component } from '@patternfly/react-core'
            # or: import { Component } from '@patternfly/react-core/deprecated'
            import_pattern = (
                f"import.*\\{{{{[^}}}}]*\\\\b{component}\\\\b[^}}}}]*\\}}}}"
                f".*from ['\"]@patternfly/react-"
            )

            # Use 2-condition combo rule (import verification + JSX pattern)
            # This is simpler and more effective than 3-condition with nodejs.referenced
            pattern.when_combo = {
                "import_pattern": import_pattern,
                "builtin_pattern": f"<{component}[^>]*\\\\b{prop}\\\\b",
                "file_pattern": "\\\\.(j|t)sx?$",
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
