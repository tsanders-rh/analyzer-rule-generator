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
from typing import List, Optional

from .schema import MigrationPattern, LocationType
from .llm import LLMProvider


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
        'react', 'angular', 'vue', 'node', 'npm', 'typescript', 'javascript',
        'patternfly', 'next', 'nuxt', 'svelte', 'ember', 'webpack', 'vite',
        'express', 'nestjs', 'gatsby', 'redux'
    ]

    # Java frameworks
    java_keywords = [
        'spring', 'jakarta', 'javax', 'jboss', 'wildfly', 'tomcat',
        'hibernate', 'jpa', 'ejb', 'servlet', 'jdk', 'openjdk',
        'quarkus', 'micronaut', 'maven', 'gradle'
    ]

    # Check for JS/TS patterns
    if any(keyword in frameworks for keyword in js_ts_keywords):
        # If TypeScript is explicitly mentioned, return typescript
        if 'typescript' in frameworks:
            return 'typescript'
        return 'javascript'

    # Check for Java patterns
    if any(keyword in frameworks for keyword in java_keywords):
        return 'java'

    return 'unknown'


class MigrationPatternExtractor:
    """Extract migration patterns from guide content using LLM."""

    def __init__(self, model: LLMProvider):
        """
        Initialize pattern extractor with LLM model.

        Args:
            model: LLM provider instance
        """
        self.model = model

    def extract_patterns(
        self,
        guide_content: str,
        source_framework: Optional[str] = None,
        target_framework: Optional[str] = None
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
        # Build prompt
        prompt = self._build_extraction_prompt(
            guide_content,
            source_framework,
            target_framework
        )

        # Generate with LLM
        try:
            result = self.model.generate(prompt)

            # Extract text response
            response_text = result.get("response", "")

            # Parse response
            patterns = self._parse_extraction_response(response_text)

            return patterns

        except Exception as e:
            print(f"Error extracting patterns: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _build_extraction_prompt(
        self,
        guide_content: str,
        source_framework: Optional[str],
        target_framework: Optional[str]
    ) -> str:
        """Build LLM prompt for pattern extraction."""

        # Detect language for language-specific instructions
        language = "unknown"
        if source_framework and target_framework:
            language = detect_language_from_frameworks(source_framework, target_framework)

        frameworks = ""
        if source_framework and target_framework:
            frameworks = f"Migration: {source_framework} → {target_framework}\n"
            frameworks += f"Detected Language: {language}\n\n"

        # Language-specific instructions
        lang_instructions = ""
        if language in ["javascript", "typescript"]:
            lang_instructions = """
**IMPORTANT - JavaScript/TypeScript Detection Instructions:**

For JavaScript/TypeScript patterns, choose the appropriate provider:

**Option 1: TypeScript Provider (for semantic analysis)**
Use when you need to find top-level symbol declarations and their references:
- Functions: `function MyComponent() {}`
- Classes: `class MyComponent {}`
- Variables/Constants: `const MyComponent = () => {}`
- Exported symbols

Fields:
- **provider_type**: Set to "typescript"
- **source_fqn**: Symbol name to find (e.g., "MyComponent", "useEffect", "useState")
- **file_pattern**: File extension pattern (e.g., "*.tsx", "*.ts", or "*.{tsx,jsx}" for brace expansion)
- **location_type**: Can be null

Example for React component usage:
```json
{
  "source_pattern": "MyComponent",
  "target_pattern": "NewComponent",
  "source_fqn": "MyComponent",
  "provider_type": "typescript",
  "file_pattern": "*.tsx",
  "location_type": null
}
```

**Option 2: Builtin Provider (for text/regex matching)**
Use for patterns that TypeScript provider CANNOT find:
- Methods inside classes (e.g., `componentWillMount`)
- Properties (e.g., `propTypes`, `defaultProps`)
- Type annotations (e.g., `React.FC`, `React.Component`)
- Imported types from libraries
- Any complex code patterns

Fields:
- **provider_type**: Set to "builtin"
- **source_fqn**: SIMPLE regex pattern. Use `.*` for wildcards, avoid complex escapes like \\s, \\{, \\} (e.g., "componentWillMount")
- **file_pattern**: File extension pattern (e.g., "*.tsx" or "*.{tsx,jsx}" for multiple extensions)
- **location_type**: null

Example for deprecated lifecycle method:
```json
{
  "source_pattern": "componentWillMount",
  "target_pattern": "componentDidMount",
  "source_fqn": "componentWillMount",
  "provider_type": "builtin",
  "file_pattern": "*.tsx",
  "location_type": null
}
```

Example for React.FC type usage:
```json
{
  "source_pattern": "React.FC",
  "target_pattern": "function component with explicit props",
  "source_fqn": "React\\\\.FC",
  "provider_type": "builtin",
  "file_pattern": "*.tsx",
  "location_type": null
}
```

**IMPORTANT: TypeScript Provider Limitations**
- ✅ CAN find: Top-level functions, classes, variables, exports
- ❌ CANNOT find: Methods, properties, type annotations, imported types
- When in doubt, use builtin provider with simple regex

**File Pattern Support:**
- Brace expansion is supported: "*.{ts,tsx,js,jsx}"
- Multiple extensions: "*.{css,scss}" or "*.{html,js,jsx,ts,tsx}"

"""
        else:
            lang_instructions = """
**Java Detection Instructions:**
For Java code patterns (classes, annotations, imports), use these fields:
- **provider_type**: Set to "java" (or leave null for auto-detection)
- **source_fqn**: Fully qualified class name (e.g., "javax.ejb.Stateless")
- **location_type**: One of ANNOTATION, IMPORT, METHOD_CALL, TYPE, INHERITANCE, PACKAGE
- **file_pattern**: Can be null

**Configuration File Detection Instructions:**
For property/configuration file patterns (application.properties, application.yaml), use these fields:
- **provider_type**: Set to "builtin"
- **source_fqn**: SIMPLE regex pattern to match the property. Use `.*` for wildcards and escape dots with \\\\ (e.g., "spring\\.data\\.mongodb\\.host")
- **file_pattern**: Regex pattern to match configuration files (e.g., ".*\\.(properties|yaml|yml)")
- **location_type**: null (not needed for builtin provider)
- **category**: "configuration"

Example for Spring Boot property migration:
```json
{
  "source_pattern": "spring.data.mongodb.host",
  "target_pattern": "spring.mongodb.host",
  "source_fqn": "spring\\\\.data\\\\.mongodb\\\\.host",
  "provider_type": "builtin",
  "file_pattern": ".*\\\\.(properties|yaml|yml)",
  "location_type": null,
  "category": "configuration"
}
```

"""

        prompt = f"""Analyze this migration guide and extract specific code migration patterns for static analysis rule generation.

{frameworks}{lang_instructions}For each pattern you find, identify:

1. **Source Pattern**: The old code/annotation/configuration (e.g., "@Stateless")
2. **Target Pattern**: The new replacement (e.g., "@ApplicationScoped")
3. **Source FQN**: Fully qualified name for detection (e.g., "javax.ejb.Stateless")
4. **Location Type**: Where to detect it. Choose from:
   - ANNOTATION: For annotations like @Stateless, @Autowired
   - IMPORT: For import statements
   - METHOD_CALL: For method invocations
   - TYPE: For class/interface usage
   - INHERITANCE: For extends/implements
   - PACKAGE: For package references
5. **Alternative FQNs**: List any alternative fully qualified names (e.g., ["jakarta.ejb.Stateless"] for javax→jakarta migration)
6. **Category**: One of: dependency, annotation, api, configuration, other
7. **Concern**: The specific migration concern/topic this pattern addresses (e.g., "mongodb", "security", "web", "testing", "applet-removal"). This will be used to group related patterns into separate files. Use lowercase-with-hyphens format.
8. **Complexity**: One of:
   - TRIVIAL: Mechanical find-replace (e.g., package rename, removing unused imports)
   - LOW: Straightforward 1:1 API replacement with minimal code changes
   - MEDIUM: API changes requiring minor refactoring or logic updates
   - HIGH: Removed APIs requiring significant code restructuring (e.g., replacing framework components)
   - EXPERT: Architectural changes or patterns requiring deep redesign and human expertise

   Consider these factors:
   - Removing an unused import = TRIVIAL
   - Renaming a class/method = LOW
   - Changing API calls with similar alternatives = MEDIUM
   - Replacing core component types (e.g., Applet → JFrame) = HIGH
   - Migrating entire frameworks or patterns = EXPERT
9. **Rationale**: Brief explanation of why this change is needed
10. **Documentation URL**: Link to relevant documentation (if available in guide)
11. **Example Before/After**: Code examples if present

---
MIGRATION GUIDE CONTENT:

{guide_content}

---

Return your findings as a JSON array. Each pattern should be an object with these fields:

{{
  "source_pattern": "string",
  "target_pattern": "string",
  "source_fqn": "string or null",
  "location_type": "ANNOTATION|IMPORT|METHOD_CALL|TYPE|INHERITANCE|PACKAGE or null",
  "alternative_fqns": ["string"] or [],
  "complexity": "TRIVIAL|LOW|MEDIUM|HIGH|EXPERT",
  "category": "string",
  "concern": "string",
  "provider_type": "java|typescript|builtin or null",
  "file_pattern": "string or null",
  "rationale": "string",
  "example_before": "string or null",
  "example_after": "string or null",
  "documentation_url": "string or null"
}}

Focus on patterns that can be detected via static analysis. Skip general advice or manual migration steps.

**IMPORTANT REGEX PATTERN RULES:**
- For builtin provider: Use SIMPLE regex patterns with `.*` wildcards
- Avoid complex regex escapes like \\s, \\(, \\) (but \\{{ and \\}} are OK in non-file-pattern contexts)
- Example: Use "import.*Component.*from.*library" NOT "import\\s*\\{{\\s*Component\\s*\\}}"

**FILE PATTERN RULES:**
- Brace expansion IS supported: Use "*.{ts,tsx}" for multiple extensions
- Prefer brace expansion over separate rules when patterns match multiple file types
- Examples: "*.{js,jsx,ts,tsx}", "*.{css,scss}", "*.{html,htm}"

Return ONLY the JSON array, no additional commentary."""

        return prompt

    def _parse_extraction_response(self, response: str) -> List[MigrationPattern]:
        """
        Parse LLM response into MigrationPattern objects.

        Args:
            response: LLM response text

        Returns:
            List of MigrationPattern objects
        """
        # Try to extract JSON from response
        json_match = re.search(r'\[.*\]', response, re.DOTALL)

        if not json_match:
            print("Warning: No JSON array found in response")
            return []

        try:
            patterns_data = json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response: {response[:500]}")
            return []

        # Convert to MigrationPattern objects
        patterns = []
        for data in patterns_data:
            try:
                # Map location_type string to enum
                location_type = None
                if data.get("location_type"):
                    try:
                        location_type = LocationType(data["location_type"])
                    except ValueError:
                        print(f"Warning: Unknown location type: {data.get('location_type')}")

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
                    rationale=data["rationale"],
                    example_before=data.get("example_before"),
                    example_after=data.get("example_after"),
                    documentation_url=data.get("documentation_url")
                )
                patterns.append(pattern)
            except (KeyError, TypeError) as e:
                print(f"Warning: Skipping invalid pattern: {e}")
                print(f"Data: {data}")
                continue

        return patterns
