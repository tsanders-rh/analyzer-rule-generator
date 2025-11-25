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

from .schema import MigrationPattern, LocationType, CSharpLocationType
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

    # C# / .NET frameworks
    csharp_keywords = [
        'dotnet', '.net', 'csharp', 'c#', 'asp.net', 'aspnet', 'entityframework',
        'ef', 'mvc', 'webapi', 'blazor', 'xamarin', 'maui', 'nuget',
        'dotnetcore', 'netcore', 'netframework'
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
        # Check if content needs chunking (>40KB)
        max_content_size = 40000  # ~10K tokens

        if guide_content and len(guide_content) > max_content_size:
            print(f"  → Content is large ({len(guide_content):,} chars), using chunked extraction")
            return self._extract_patterns_chunked(
                guide_content,
                source_framework,
                target_framework
            )

        # Single extraction for smaller content
        return self._extract_patterns_single(
            guide_content,
            source_framework,
            target_framework
        )

    def _extract_patterns_single(
        self,
        guide_content: str,
        source_framework: Optional[str] = None,
        target_framework: Optional[str] = None
    ) -> List[MigrationPattern]:
        """Extract patterns from a single piece of content."""
        # Build prompt (use OpenRewrite-specific prompt if needed)
        if self.from_openrewrite:
            prompt = self._build_openrewrite_prompt(
                guide_content,
                source_framework,
                target_framework
            )
        else:
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

            # Validate and fix patterns
            language = detect_language_from_frameworks(source_framework or "", target_framework or "")
            patterns = self._validate_and_fix_patterns(patterns, language)

            return patterns

        except Exception as e:
            print(f"Error extracting patterns: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_patterns_chunked(
        self,
        guide_content: str,
        source_framework: Optional[str] = None,
        target_framework: Optional[str] = None
    ) -> List[MigrationPattern]:
        """Extract patterns from large content by chunking."""
        from .ingestion import GuideIngester

        # Chunk the content
        ingester = GuideIngester()
        chunks = ingester.chunk_content(guide_content, max_tokens=8000)

        print(f"  → Split into {len(chunks)} chunks")

        all_patterns = []
        for i, chunk in enumerate(chunks, 1):
            print(f"  → Processing chunk {i}/{len(chunks)} ({len(chunk):,} chars)")

            # Extract from this chunk
            patterns = self._extract_patterns_single(
                chunk,
                source_framework,
                target_framework
            )

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

**Option 1: Node.js Provider (for semantic analysis)**
Use when you need to find symbol references in JavaScript/TypeScript:
- Functions: `function MyComponent() {}`
- Classes: `class MyComponent {}`
- Variables/Constants: `const MyComponent = () => {}`
- Types and interfaces
- Exported symbols

Fields:
- **provider_type**: Set to "nodejs"
- **source_fqn**: Symbol name to find (e.g., "MyComponent", "useEffect", "useState")
- **file_pattern**: Must be null (nodejs provider doesn't support file filtering)
- **location_type**: Must be null

Example for React component usage:
```json
{{
  "source_pattern": "MyComponent",
  "target_pattern": "NewComponent",
  "source_fqn": "MyComponent",
  "provider_type": "nodejs",
  "file_pattern": null,
  "location_type": null
}}
```

**Option 2: Builtin Provider (for file-specific text/regex matching)**
Use for patterns that require file filtering or that nodejs provider cannot find:
- File-specific imports (e.g., `import React` in .tsx files only)
- Type annotations in specific file types (e.g., `React.FC` in .tsx files)
- CSS patterns in style files (e.g., `--pf-` in .css/.scss files)
- Any complex code patterns requiring file type filtering

Fields:
- **provider_type**: Set to "builtin"
- **source_fqn**: SIMPLE regex pattern. Use `.*` for wildcards, avoid complex escapes like \\s, \\{{, \\}} (e.g., "componentWillMount")
- **file_pattern**: REGEX pattern for file matching (e.g., "\\.tsx$" for .tsx files, "\\.(j|t)sx?$" for .js/.jsx/.ts/.tsx)
- **location_type**: null

Example for pattern in .tsx files only:
```json
{{
  "source_pattern": "React.FC",
  "target_pattern": "function component with explicit props",
  "source_fqn": "React.FC",
  "provider_type": "builtin",
  "file_pattern": "\\\\.tsx$",
  "location_type": null
}}
```

Example for CSS pattern in .css or .scss files:
```json
{{
  "source_pattern": "--pf-v5-global",
  "target_pattern": "--pf-v6-global",
  "source_fqn": "--pf-v5-global",
  "provider_type": "builtin",
  "file_pattern": "\\\\.(css|scss)$",
  "location_type": null
}}
```

IMPORTANT: In JSON, backslashes must be escaped. Use \\\\ for regex backslashes.

**IMPORTANT: Node.js Provider vs Builtin Provider**
- ✅ Use nodejs provider: Symbol references across ALL JS/TS files (no file filtering)
- ✅ Use builtin provider: Patterns that need file type filtering using regex filePattern
- When in doubt about file filtering, use builtin provider with filePattern

**CRITICAL: Component Prop Changes - Use COMBO RULES (nodejs + builtin)**

When a migration involves changing a prop on a SPECIFIC component (e.g., Button's isActive → isPressed), you MUST use a COMBO RULE that combines BOTH nodejs.referenced (for the component) AND builtin.filecontent (for the prop pattern).

**IMPORTANT: Use "when_combo" field for combining conditions**

✅ CORRECT - Combo rule for component-specific prop change:
```json
{{
  "source_pattern": "Button isActive",
  "target_pattern": "Button isPressed",
  "source_fqn": "Button",
  "provider_type": "combo",
  "when_combo": {{
    "nodejs_pattern": "Button",
    "builtin_pattern": "<Button[^>]*\\\\bisActive\\\\b",
    "file_pattern": "\\\\.(j|t)sx?$"
  }},
  "rationale": "Button's isActive prop has been renamed to isPressed",
  "complexity": "MEDIUM"
}}
```

This creates a rule with:
```yaml
when:
  and:
  - nodejs.referenced:
      pattern: Button
  - builtin.filecontent:
      pattern: <Button[^>]*\\bisActive\\b
      filePattern: \\.(j|t)sx?$
```

**Benefits of Combo Rules:**
- ✅ Only matches when BOTH conditions are true
- ✅ nodejs.referenced ensures the component exists in the file
- ✅ builtin.filecontent ensures the specific prop usage exists
- ✅ No false positives from other components with same prop
- ✅ No false positives from variables with same name

**Pattern Guidelines for Combo Rules:**

1. **nodejs_pattern**: Component name (e.g., "Button", "AccordionContent")

2. **builtin_pattern**: Component + prop regex pattern
   - Use `<ComponentName[^>]*\\bisActive\\b` format
   - `[^>]*` matches any content until closing `>`
   - `\\b` creates word boundaries to avoid partial matches
   - Escape special regex characters properly

3. **file_pattern**: "\\\\.(j|t)sx?$" for JSX/TSX files

**Examples:**

Example 1 - Button isActive → isPressed:
```json
{{
  "source_pattern": "Button isActive",
  "target_pattern": "Button isPressed",
  "source_fqn": "Button",
  "provider_type": "combo",
  "when_combo": {{
    "nodejs_pattern": "Button",
    "builtin_pattern": "<Button[^>]*\\\\bisActive\\\\b",
    "file_pattern": "\\\\.(j|t)sx?$"
  }},
  "rationale": "Button's isActive prop renamed to isPressed"
}}
```

Example 2 - AccordionContent isHidden (removed):
```json
{{
  "source_pattern": "AccordionContent isHidden",
  "target_pattern": "AccordionContent",
  "source_fqn": "AccordionContent",
  "provider_type": "combo",
  "when_combo": {{
    "nodejs_pattern": "AccordionContent",
    "builtin_pattern": "<AccordionContent[^>]*\\\\bisHidden\\\\b",
    "file_pattern": "\\\\.(j|t)sx?$"
  }},
  "rationale": "isHidden prop removed, visibility now automatic"
}}
```

❌ WRONG - Using single provider for component-specific props:
```json
{{
  "source_fqn": "isActive",
  "provider_type": "builtin"
}}
```
This matches isActive on ALL components and ALL variables!

❌ WRONG - Using nodejs.referenced for common prop names:
```json
{{
  "source_fqn": "title",
  "provider_type": "nodejs"
}}
```
This matches every occurrence of "title" as an identifier!

**When to Use Combo Rules:**

✅ ALWAYS use combo rules for component-specific prop changes:
- Button's isActive → isPressed
- AccordionToggle's isExpanded → move to AccordionItem
- Modal's title → titleText
- Any prop change on a specific component

❌ Use single provider for:
- Component renames (nodejs.referenced for old component name)
- Import path changes (builtin.filecontent for import statements)
- CSS variable changes (builtin.filecontent for CSS files)
- Unique props that only exist on one component (but combo is still safer!)

"""
        elif language == "csharp":
            lang_instructions = """
**IMPORTANT - C# / .NET Detection Instructions:**

For C# code patterns, use the C# provider for semantic analysis:

**C# Provider (for semantic analysis)**
Use when you need to find type/method/field references in C# code:
- Classes: `public class MyController`
- Methods: `public void MyMethod()`
- Fields: `private string _field`
- Namespaces: `System.Web.Mvc`
- Types and interfaces

Fields:
- **provider_type**: Set to "csharp"
- **source_fqn**: Fully qualified name or regex pattern (e.g., "System.Web.Http", "System.*.Http", "*.Web.Mvc")
- **location_type**: Optional - MUST be one of: FIELD, CLASS, METHOD, or ALL (defaults to ALL if not specified)
  - **FIELD**: Use for field/property references
  - **CLASS**: Use for class/type references (including attributes/annotations)
  - **METHOD**: Use for method invocations
  - **ALL**: Use for any reference type (default)
- **file_pattern**: Must be null (csharp provider doesn't support file filtering)

**CRITICAL: C# Location Type Restrictions**
- ❌ DO NOT use Java location types: ANNOTATION, METHOD_CALL, TYPE, IMPORT, INHERITANCE, PACKAGE
- ✅ ONLY use C# location types: FIELD, CLASS, METHOD, ALL
- For attributes/annotations → use "CLASS"
- For method calls → use "METHOD" (not METHOD_CALL)
- For type references → use "CLASS" (not TYPE)
- For fields/properties → use "FIELD"
- When unsure → use "ALL"

Example for method invocation:
```json
{{
  "source_pattern": "SignedCms.ComputeSignature",
  "target_pattern": "SignedCms.ComputeSignature with updated behavior",
  "source_fqn": "System.Security.Cryptography.Pkcs.SignedCms.ComputeSignature",
  "provider_type": "csharp",
  "location_type": "METHOD",
  "file_pattern": null
}}
```

Example for attribute/annotation:
```json
{{
  "source_pattern": "HandleProcessCorruptedStateExceptionsAttribute",
  "target_pattern": null,
  "source_fqn": "System.Runtime.ExceptionServices.HandleProcessCorruptedStateExceptionsAttribute",
  "provider_type": "csharp",
  "location_type": "CLASS",
  "file_pattern": null
}}
```

Example for field/property:
```json
{{
  "source_pattern": "FileSystemInfo.Attributes",
  "target_pattern": "FileSystemInfo.Attributes with updated behavior",
  "source_fqn": "System.IO.FileSystemInfo.Attributes",
  "provider_type": "csharp",
  "location_type": "FIELD",
  "file_pattern": null
}}
```

Example with wildcard pattern:
```json
{{
  "source_pattern": "System.Web.Http",
  "target_pattern": "Microsoft.AspNetCore.Mvc",
  "source_fqn": "System.Web.Http.*",
  "provider_type": "csharp",
  "location_type": "ALL",
  "file_pattern": null
}}
```

**Configuration File Detection:**
For configuration file patterns (appsettings.json, web.config), use builtin provider:
- **provider_type**: Set to "builtin"
- **source_fqn**: SIMPLE regex pattern (e.g., "connectionStrings")
- **file_pattern**: Regex pattern for config files (e.g., "appsettings.*\\.json$" or "web\\.config$")
- **location_type**: null

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

**CRITICAL WARNING - Component Prop Detection Strategy:**

For component-specific prop changes (e.g., "Button's isActive → isPressed"):

**REQUIRED: Use COMBO RULES (provider_type: "combo")**
- Set provider_type to "combo"
- Include when_combo object with nodejs_pattern, builtin_pattern, and file_pattern
- This combines nodejs.referenced (for component) + builtin.filecontent (for prop)
- See the JavaScript/TypeScript instructions above for detailed examples

**NEVER use generic prop detection:**
- ❌ DON'T set provider_type to "nodejs" and source_fqn to a common prop name
- ❌ DON'T set provider_type to "builtin" and source_fqn to a common prop name
- ✅ DO use combo rules for ALL component-specific prop changes

---
MIGRATION GUIDE CONTENT:

{guide_content}

---

**CRITICAL REMINDER - Component Prop Changes:**

For JavaScript/TypeScript migrations where a prop changes on a SPECIFIC component:
- ✅ ALWAYS use `"provider_type": "combo"`
- ✅ ALWAYS include `"when_combo"` with nodejs_pattern (component name), builtin_pattern (component + prop), and file_pattern
- ❌ NEVER use `"provider_type": "builtin"` with just a prop name
- ❌ NEVER use `"provider_type": "nodejs"` with just a prop name

Example - Button's isActive → isPressed:
```json
{{
  "source_pattern": "Button isActive",
  "source_fqn": "Button",
  "provider_type": "combo",
  "when_combo": {{
    "nodejs_pattern": "Button",
    "builtin_pattern": "<Button[^>]*\\\\bisActive\\\\b",
    "file_pattern": "\\\\.(j|t)sx?$"
  }}
}}
```

**AUTOMATIC VALIDATION - RULES WILL BE ENFORCED:**

Your patterns will be automatically validated. Patterns violating these rules will be REJECTED or AUTO-FIXED:

1. ✅ AUTO-FIX: Component-specific prop changes (e.g., "Button isActive") will be converted to combo rules
2. ❌ REJECT: Generic prop names as standalone patterns (isActive, title, onClick, alignLeft, etc.)
3. ❌ REJECT: Source and target must be different (source: "^5", target: "^5" → INVALID)
4. ❌ REJECT: Overly broad patterns (wildcards like ".*", ".+", etc.)

Return your findings as a JSON array. Each pattern should be an object with these fields:

{{
  "source_pattern": "string",
  "target_pattern": "string",
  "source_fqn": "string or null",
  "location_type": "ANNOTATION|IMPORT|METHOD_CALL|TYPE|INHERITANCE|PACKAGE|FIELD|CLASS|METHOD|ALL or null",
  "alternative_fqns": ["string"] or [],
  "complexity": "TRIVIAL|LOW|MEDIUM|HIGH|EXPERT",
  "category": "string",
  "concern": "string",
  "provider_type": "java|nodejs|csharp|builtin|combo or null",
  "file_pattern": "string or null",
  "when_combo": {{
    "nodejs_pattern": "string",
    "builtin_pattern": "string",
    "file_pattern": "string"
  }} or null,
  "rationale": "string",
  "example_before": "string or null",
  "example_after": "string or null",
  "documentation_url": "string or null"
}}

Note: when_combo is REQUIRED when provider_type is "combo", otherwise it should be null.

Focus on patterns that can be detected via static analysis. Skip general advice or manual migration steps.

**CRITICAL: Pattern Granularity Rules**

When a migration involves MULTIPLE specific value replacements, you MUST create SEPARATE patterns for EACH value pair:

1. ✅ DO: Create individual patterns for each specific value
   - Example: For pixel→rem conversions, create separate rules:
     * "576px" → "36rem" (one pattern)
     * "768px" → "48rem" (another pattern)
     * "992px" → "62rem" (another pattern)
   - Example: For enum renames, create separate rules:
     * "alignLeft" → "alignStart" (one pattern)
     * "alignRight" → "alignEnd" (another pattern)

2. ❌ DON'T: Create generic catch-all patterns
   - DON'T: "breakpoint pixel values" → "breakpoint rem values"
   - DON'T: "alignment values" → "updated alignment values"

3. When you see multiple related changes in the guide, treat each as a separate pattern with:
   - Exact source value in source_pattern
   - Exact target value in target_pattern
   - Specific description (see below)

**Description Format Rules:**

- Use SPECIFIC values, not generic descriptions
- Format: "{{exact_source}} should be replaced with {{exact_target}}"
- ✅ GOOD: "576px should be replaced with 36rem"
- ✅ GOOD: "alignLeft should be replaced with alignStart"
- ✅ GOOD: "variant='button-group' should be replaced with variant='action-group'"
- ❌ BAD: "pixel values should be replaced with rem values"
- ❌ BAD: "alignment values should be updated"
- ❌ BAD: "variant values have changed"

**Example Code Guidelines:**

- Keep examples MINIMAL - show only the code being changed
- DO NOT include import statements unless the import path itself is changing
- DO NOT include export/function wrappers
- ✅ GOOD: "<Button isActive />"
- ❌ BAD: "import {{{{ Button }}}} from '@patternfly/react-core'; export const MyButton = () => <Button isActive />"

**IMPORTANT REGEX PATTERN RULES:**
- For builtin provider: Use SIMPLE regex patterns with `.*` wildcards
- Avoid complex regex escapes like \\s, \\(, \\) (but \\{{ and \\}} are OK in non-file-pattern contexts)
- Example: Use "import.*Component.*from.*library" NOT "import\\s*\\{{\\s*Component\\s*\\}}"

**FILE PATTERN RULES:**
- For builtin.filecontent provider: Use REGEX patterns for filePattern field
- Examples: "\\\\.tsx$" for .tsx files, "\\\\.(j|t)sx?$" for .js/.jsx/.ts/.tsx files
- Remember: In JSON, backslashes must be escaped with \\\\
- For nodejs provider: Do NOT use filePattern (matches all JS/TS files)

Return ONLY the JSON array, no additional commentary."""

        return prompt

    def _build_openrewrite_prompt(
        self,
        recipe_content: str,
        source_framework: Optional[str],
        target_framework: Optional[str]
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
  - **TYPE**: For package changes with wildcards (e.g., "com.sun.net.ssl.*") - PREFERRED for ChangePackage
  - **IMPORT**: For specific class imports only (no wildcards, exact FQN required)
  - **METHOD_CALL**: For method invocations
  - **ANNOTATION**: For annotation usage
  - **INHERITANCE**: For class inheritance
  - **PACKAGE**: Do not use - TYPE is preferred
- **file_pattern**: Can be null

**Configuration File Detection Instructions:**
For property/configuration file patterns (application.properties, application.yaml), use these fields:
- **provider_type**: Set to "builtin"
- **source_fqn**: SIMPLE regex pattern to match the property. Use `.*` for wildcards and escape dots with \\\\ (e.g., "spring\\.data\\.mongodb\\.host")
- **file_pattern**: Regex pattern to match configuration files (e.g., ".*\\.(properties|yaml|yml)")
- **location_type**: null (not needed for builtin provider)
- **category**: "configuration"

"""

        prompt = f"""You are converting OpenRewrite recipes into Konveyor analyzer detection patterns.

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
- **TYPE**: For package-level changes with wildcards (e.g., "javax.security.cert.*") - USE THIS FOR ChangePackage
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
5. For composite recipes with sub-recipes, expand and extract patterns from each meaningful transformation

Return your findings as a JSON array with these fields:

{{
  "source_pattern": "string",
  "target_pattern": "string",
  "source_fqn": "string or null",
  "location_type": "ANNOTATION|IMPORT|METHOD_CALL|TYPE|INHERITANCE|PACKAGE|FIELD|CLASS|METHOD|ALL or null",
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
                    when_combo=data.get("when_combo"),
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

    def _validate_and_fix_patterns(self, patterns: List[MigrationPattern], language: str) -> List[MigrationPattern]:
        """
        Validate patterns and auto-fix common issues.

        Args:
            patterns: List of patterns to validate
            language: Detected language (javascript, typescript, java, csharp)

        Returns:
            List of validated/fixed patterns
        """
        validated = []

        for pattern in patterns:
            # RULE 1: Component-specific prop changes MUST use combo rules
            if language in ["javascript", "typescript"]:
                # Detect if this is a prop change pattern
                is_prop_pattern = self._looks_like_prop_pattern(pattern)

                if is_prop_pattern and pattern.provider_type != "combo":
                    print(f"  ! Auto-converting to combo rule: {pattern.source_pattern}")
                    pattern = self._convert_to_combo_rule(pattern)

            # RULE 2: Reject overly generic builtin patterns
            if pattern.provider_type == "builtin" and pattern.source_fqn:
                if self._is_overly_broad_pattern(pattern.source_fqn):
                    print(f"  ! Rejecting overly broad pattern: {pattern.source_fqn}")
                    continue

            # RULE 3: Ensure source != target
            if pattern.source_pattern and pattern.target_pattern:
                if pattern.source_pattern.strip() == pattern.target_pattern.strip():
                    print(f"  ! Rejecting pattern with identical source/target: {pattern.source_pattern}")
                    continue

            validated.append(pattern)

        return validated

    def _looks_like_prop_pattern(self, pattern: MigrationPattern) -> bool:
        """Check if pattern appears to be a component prop change."""
        # Look for patterns like "Button isActive" or "Modal title"
        if not pattern.source_pattern:
            return False

        parts = pattern.source_pattern.split()
        if len(parts) >= 2:
            # First part looks like component name (PascalCase)
            # Second part looks like prop name (camelCase)
            if parts[0] and parts[0][0].isupper() and parts[1] and parts[1][0].islower():
                return True

        return False

    def _convert_to_combo_rule(self, pattern: MigrationPattern) -> MigrationPattern:
        """
        Convert a simple pattern to combo rule with import verification.

        For JavaScript/TypeScript component patterns, this adds import verification
        to ensure the component is from the target library (e.g., @patternfly/react-core).
        This prevents false positives from components with the same name in other libraries.
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
            import_pattern = f"import.*\\{{{{[^}}}}]*\\\\b{component}\\\\b[^}}}}]*\\}}}}.*from ['\"]@patternfly/react-"

            # Use 2-condition combo rule (import verification + JSX pattern)
            # This is simpler and more effective than 3-condition with nodejs.referenced
            pattern.when_combo = {
                "import_pattern": import_pattern,
                "builtin_pattern": f"<{component}[^>]*\\\\b{prop}\\\\b",
                "file_pattern": "\\\\.(j|t)sx?$"
            }

        return pattern

    def _is_overly_broad_pattern(self, pattern: str) -> bool:
        """Check if builtin pattern is too broad."""
        # Common prop names that should never be standalone patterns
        overly_generic = [
            "isActive", "isDisabled", "isOpen", "isClosed", "isExpanded",
            "title", "name", "id", "className", "style",
            "onClick", "onChange", "onSubmit", "onClose",
            "alignLeft", "alignRight", "alignCenter",
            "variant", "size", "color", "type"
        ]

        # If pattern is just one of these words, it's too broad
        if pattern.strip() in overly_generic:
            return True

        # Patterns that are just wildcards are too broad
        if pattern.strip() in [".*", ".+", "\\w+", "[a-zA-Z]+", ".*Icon"]:
            return True

        return False
