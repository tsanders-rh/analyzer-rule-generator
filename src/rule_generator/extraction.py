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
            patterns = self._validate_and_fix_patterns(patterns, language, source_framework, target_framework)

            return patterns

        except Exception as e:
            error_message = str(e)

            # Check if it's a transient API error
            if "500" in error_message or "api_error" in error_message.lower():
                print(f"⚠ API temporarily unavailable, skipping this chunk (will continue with others)")
            elif "rate_limit" in error_message.lower() or "429" in error_message:
                print(f"⚠ Rate limit reached, skipping this chunk")
            else:
                # For unexpected errors, show more detail
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

**Option 1: Node.js Provider (for semantic analysis) - For symbol/identifier references**
Use when you need to find **symbol REFERENCES** (imports, identifiers, type usage) in JavaScript/TypeScript code:
- Classes and types (e.g., ComponentFactoryResolver, BrowserTransferStateModule, HttpClient)
- Function/method **imports** (e.g., `import { useEffect } from 'react'`)
- Function/method **names** as identifiers (e.g., `const x = useEffect`)
- Interfaces and types
- Variables/Constants: `const MyComponent = () => {}`
- Component names (e.g., Button, Modal, Accordion)

**CRITICAL: nodejs.referenced finds SYMBOL REFERENCES, NOT METHOD CALLS**
- ✅ Use for imports: `import { useEffect } from 'react'` → pattern: "useEffect"
- ✅ Use for identifier references: `const x = ComponentFactoryResolver` → pattern: "ComponentFactoryResolver"
- ✅ Use for type usage: `const c: MyComponent` → pattern: "MyComponent"
- ❌ DO NOT use for method calls: `ReactDOM.render()` (this is a method CALL, use builtin.filecontent)
- ❌ DO NOT use for function calls: `useEffect(() => {})` (this is a function CALL, use builtin.filecontent)

**When to use builtin vs nodejs:**
- For METHOD CALLS (e.g., `ReactDOM.render()`, `obj.method()`): Use builtin.filecontent with pattern `ReactDOM\\.render\\(`
- For SYMBOL REFERENCES (e.g., imports, type usage): Use nodejs.referenced
- When in doubt: If the pattern includes parentheses `()`, it's a call → use builtin

Fields:
- **provider_type**: Set to "nodejs"
- **source_fqn**: Symbol name to find (e.g., "ComponentFactoryResolver", "useEffect", "BrowserTransferStateModule")
- **file_pattern**: Must be null (nodejs provider doesn't support file filtering)
- **location_type**: Must be null

Example for Angular class reference:
```json
{{
  "source_pattern": "ComponentFactoryResolver",
  "target_pattern": "removed",
  "source_fqn": "ComponentFactoryResolver",
  "provider_type": "nodejs",
  "file_pattern": null,
  "location_type": null
}}
```

Example for React component reference (import/usage):
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

Example for React method CALL (use builtin, not nodejs):
```json
{{
  "source_pattern": "ReactDOM.render",
  "target_pattern": "createRoot",
  "source_fqn": "ReactDOM\\\\\\\\.render\\\\\\\\(",
  "provider_type": "builtin",
  "file_pattern": "\\\\\\\\.(j|t)sx?$",
  "location_type": null
}}
```

**Option 2: Builtin Provider (for text/regex matching) - For method calls, expressions, and file-specific patterns**
Use for patterns that require regex matching or file filtering:
- **METHOD CALLS**: `ReactDOM.render()`, `obj.method()`, function invocations
- **EXPRESSIONS**: Complex code patterns that aren't simple symbol references
- Import statement patterns with specific package paths (e.g., `import.*XhrFactory.*from.*@angular/common/http`)
- CSS patterns in style files (e.g., `--pf-` in .css/.scss files only)
- Configuration patterns in specific config files (e.g., .json, .xml files)
- Complex multi-line patterns that need regex matching

**CRITICAL: Use builtin for method calls, nodejs for symbol references**
- ✅ Use builtin for: `ReactDOM.render()` → pattern: `ReactDOM\\.render\\(`
- ✅ Use builtin for: `unmountComponentAtNode()` → pattern: `unmountComponentAtNode\\(`
- ✅ Use builtin for: `obj.method()` → pattern: `obj\\.method\\(`
- ✅ Use nodejs for: Symbol imports, type usage, identifier references
- When in doubt: If the code includes `()`, it's likely a call → use builtin

Fields:
- **provider_type**: Set to "builtin"
- **source_fqn**: SIMPLE regex pattern. Use `.*` for wildcards, avoid complex escapes like \\s, \\{{, \\}} (e.g., "componentWillMount")
  - **IMPORTANT - $  anchor usage**:
    - **Add $ anchor**: ONLY for COMPLETE import statement patterns (e.g., "import.*XhrFactory.*from.*@angular/common/http$")
    - **NO $ anchor**: For partial text/package name matching (e.g., "javax\\." to match javax.servlet, javax.persistence, etc.)
    - The $ anchor means "end of line" - only use it when you're matching a full line, not partial text
  - **IMPORTANT**: For symbol references (not imports), use the symbol name without anchors (e.g., "RouterEvent", "ComponentFactoryResolver")
- **file_pattern**: REGEX pattern for file matching (e.g., "\\.tsx$" for .tsx files, "\\.(j|t)sx?$" for .js/.jsx/.ts/.tsx, "\\.(j|t)s$" for .js/.ts)
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
- ✅ Use nodejs provider: Symbol references (classes, types, methods, components) - DEFAULT for Angular/TypeScript
- ✅ Use builtin provider: ONLY for import path patterns OR file-specific content filtering
- When in doubt for Angular migrations: Use nodejs provider (it's the default)

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
- **location_type**: One of:
  - **IMPORT**: For detecting import statements of specific classes (e.g., "import org.example.ClassName;")
  - **TYPE**: For detecting when a class is used as a type (field type, parameter type, return type, variable declaration)
    * Use this when the pattern is a CLASS that appears in code as a type reference
    * Example: "PathMatchConfigurer" used as parameter type in "void config(PathMatchConfigurer c)"
  - **METHOD_CALL**: For detecting specific METHOD NAME invocations (pattern should be method name, not class name)
    * Use this when the pattern is a METHOD that is being called
    * Example: pattern "getSomething" to find calls to "object.getSomething()"
    * DO NOT use for detecting usage of a class - use TYPE instead
  - **ANNOTATION**: For annotation usage (e.g., @Deprecated, @Stateless)
  - **INHERITANCE**: For detecting class inheritance (extends/implements)
  - **PACKAGE**: For detecting package references
- **file_pattern**: Can be null

**Maven Dependency Detection Instructions:**
For Maven dependency changes (pom.xml), use these fields:
- **provider_type**: Set to "java" (the java provider handles Maven dependencies)
- **category**: MUST set to "dependency"
- **source_fqn**: Maven coordinates in format "groupId:artifactId" (e.g., "mysql:mysql-connector-java" or "org.springframework.boot:spring-boot-starter-web")
- **alternative_fqns**: CRITICAL - Include Maven relocations! Many Maven artifacts have been relocated:
  * "mysql:mysql-connector-java" → "com.mysql:mysql-connector-j" (relocated in 8.0+)
  * If the migration guide mentions a dependency change, check if it's a Maven relocation
  * Include BOTH the old and relocated coordinates in alternative_fqns (e.g., ["com.mysql:mysql-connector-j"])
  * Maven automatically resolves relocations, so the analyzer will see the NEW coordinates even if pom.xml has OLD ones
- **location_type**: null (not needed for dependency detection)
- **file_pattern**: null

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

1. **Source Pattern**: The old code/annotation/configuration (e.g., "@Stateless", "Button isActive prop", "@patternfly/react-core/v5 import")
2. **Target Pattern**: The new replacement (e.g., "@ApplicationScoped", "Button isPressed prop", "@patternfly/react-core import")
3. **Source FQN**: Fully qualified name for detection (e.g., "javax.ejb.Stateless")

   **CRITICAL ALIGNMENT RULE**: Your source_pattern MUST accurately describe what the detection pattern will actually find:
   - If detecting an import path change: source_pattern should be the import path (e.g., "@patternfly/react-core/v5")
   - If detecting a component prop: source_pattern should mention the component AND prop (e.g., "Button isActive prop")
   - If detecting a class/annotation: source_pattern should be the class/annotation name
   - NEVER describe one thing (e.g., "import path") when actually detecting something else (e.g., "component usage")
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
9. **Rationale**: Clear, comprehensive explanation of why this change is needed. Expand on minimal guide text to provide full context. Include:
   - What changed and why
   - Any important behavioral differences
   - When applicable, explain the recommended approach
   **IMPORTANT**: Your rationale should be detailed enough to help a developer understand the migration without reading the full guide.
10. **Documentation URL**: Link to relevant documentation (if available in guide)
11. **Example Before/After**: High-quality, realistic code examples showing the migration.

   **CRITICAL - Example Quality Guidelines:**

   If the guide provides code examples, use them. If NOT, you MUST create realistic, complete examples that:
   - Show realistic usage in the target framework/language
   - Include necessary context (e.g., full method signatures, class constructors, realistic variable names)
   - Demonstrate the actual change clearly
   - Use proper language syntax (TypeScript for Angular, proper formatting)
   - Are complete enough to be actionable (not just fragments)

   **Example Quality Checklist:**
   - ✅ GOOD: Complete TypeScript method with constructor showing before/after DI patterns
   - ✅ GOOD: Full import statement showing package change
   - ✅ GOOD: Realistic component code with props showing migration
   - ❌ BAD: Generic placeholder code like "router.createComponent(ComponentFactoryResolver)"
   - ❌ BAD: Incomplete fragments without context
   - ❌ BAD: Abstract examples that don't show real usage

   For Angular/TypeScript migrations, examples should:
   - Use TypeScript syntax (types, interfaces, classes)
   - Show realistic Angular patterns (dependency injection, decorators, component structure)
   - Include full method signatures or constructors when showing API changes
   - Use realistic variable names (not "foo", "bar")

   For import path changes:
   - Show complete import statement
   - Use realistic imported symbols (not just "Component")
   - Show actual package paths

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

**FINAL CHECKLIST - Angular/TypeScript Migrations:**

Before returning your JSON, verify each pattern:

1. **Provider Selection:**
   - ✅ Classes/Types (ComponentFactoryResolver, BrowserTransferStateModule) → nodejs provider
   - ✅ Methods/Functions → nodejs provider
   - ✅ Component/Service names → nodejs provider
   - ✅ Import path changes (import X from 'old-package') → builtin provider with import pattern
   - ❌ Don't use builtin for simple class/type names

2. **Example Quality:**
   - ✅ TypeScript syntax with types and interfaces
   - ✅ Realistic Angular patterns (constructors, dependency injection, decorators)
   - ✅ Full code context (not just fragments)
   - ✅ Realistic variable names (MyComponent, not foo/bar)
   - ❌ Don't create generic placeholders like "router.createComponent(OldClass)"

3. **Rationale Quality:**
   - ✅ Explain WHY the change is needed
   - ✅ Explain the recommended approach
   - ✅ Provide context beyond the minimal guide text

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

**CRITICAL JSON FORMATTING RULES:**
- You are generating JSON - ALL backslashes in string values MUST be escaped
- In JSON: `\\.` is INVALID, `\\\\.` is CORRECT (escaped backslash + escaped dot)
- For regex dot: write `\\\\.` not `\\.`
- For file patterns: `".*\\\\.properties"` not `".*\\.properties"`
- ALWAYS double your backslashes in JSON strings!

**IMPORTANT REGEX PATTERN RULES:**
- For builtin provider: Use SIMPLE regex patterns with `.*` wildcards
- Avoid complex regex escapes like \\s, \\(, \\) (but \\{{ and \\}} are OK in non-file-pattern contexts)
- Example: Use "import.*Component.*from.*library" NOT "import\\s*\\{{\\s*Component\\s*\\}}"
- Remember: Escape your backslashes for JSON!

**FILE PATTERN RULES:**
- For builtin.filecontent provider: Use REGEX patterns for filePattern field
- Examples: "\\\\.tsx$" for .tsx files, "\\\\.(j|t)sx?$" for .js/.jsx/.ts/.tsx files
- CRITICAL: In JSON, write `\\\\.` for a literal dot in regex (four backslashes become two in the string, one in the actual regex)
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
  - **IMPORT**: For specific class imports only (no wildcards, exact FQN required like "org.springframework.boot.actuate.trace.http.HttpTraceRepository")
  - **METHOD_CALL**: For method invocations
  - **ANNOTATION**: For annotation usage
  - **INHERITANCE**: For class inheritance
  - **PACKAGE**: Do not use - TYPE is preferred
- **file_pattern**: Can be null

**Maven Dependency Detection Instructions:**
For Maven dependency changes (pom.xml), use these fields:
- **provider_type**: Set to "java" (the java provider handles Maven dependencies)
- **category**: MUST set to "dependency"
- **source_fqn**: Maven coordinates in format "groupId:artifactId" (e.g., "mysql:mysql-connector-java" or "org.springframework.boot:spring-boot-starter-web")
- **alternative_fqns**: CRITICAL - Include Maven relocations! Many Maven artifacts have been relocated:
  * "mysql:mysql-connector-java" → "com.mysql:mysql-connector-j" (relocated in 8.0+)
  * If the migration guide mentions a dependency change, check if it's a Maven relocation
  * Include BOTH the old and relocated coordinates in alternative_fqns (e.g., ["com.mysql:mysql-connector-j"])
  * Maven automatically resolves relocations, so the analyzer will see the NEW coordinates even if pom.xml has OLD ones
- **location_type**: null (not needed for dependency detection)
- **file_pattern**: null

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
            fixed = re.sub(r'\\([^"\\/bfnrtu])', r'\\\\\1', value)
            return f'"{fixed}"'

        # Match string values and fix invalid escapes
        # This pattern matches: "..." string values
        json_str = re.sub(r'"((?:[^"\\]|\\.)*)"', fix_invalid_escapes, json_str)

        # Remove trailing commas before closing brackets/braces
        # e.g., {"key": "value",} -> {"key": "value"}
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        # Fix missing commas between objects in arrays
        # e.g., }{"key" -> },{"key"
        json_str = re.sub(r'\}(\s*)\{', r'},\1{', json_str)

        # Fix missing commas between array items
        # e.g., ]["key" -> ],["key"
        json_str = re.sub(r'\](\s*)\[', r'],\1[', json_str)

        # Fix unescaped quotes in string values (basic heuristic)
        # This is tricky - only fix obvious cases like: "description": "It's a test"
        # Convert to: "description": "It\'s a test"
        # But skip already escaped quotes
        def fix_unescaped_quotes(match):
            key = match.group(1)
            value = match.group(2)
            # Escape single quotes that aren't already escaped
            value = re.sub(r"(?<!\\)'", r"\'", value)
            return f'"{key}": "{value}"'

        # Match "key": "value" pairs and fix unescaped quotes in values
        # This pattern is conservative to avoid breaking valid JSON
        json_str = re.sub(r'"([^"]+)":\s*"([^"]*[^\\]"[^"]*)"', fix_unescaped_quotes, json_str)

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
        json_match = re.search(r'\[.*\]', response, re.DOTALL)

        if not json_match:
            print("Warning: No JSON array found in response")
            return []

        json_str = json_match.group(0)

        try:
            patterns_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print("Attempting to repair JSON...")

            # Try to repair the JSON
            repaired_json = self._repair_json(json_str)

            try:
                patterns_data = json.loads(repaired_json)
                print("✓ Successfully repaired JSON")
            except json.JSONDecodeError as e2:
                print(f"Failed to repair JSON: {e2}")
                # Try one more aggressive repair: escape all single backslashes
                try:
                    # Replace single backslash with double backslash in string values
                    aggressive_json = repaired_json
                    # This is a last resort - may break some patterns but better than nothing
                    aggressive_json = aggressive_json.replace('\\', '\\\\')
                    # But we may have over-escaped, so fix double-double backslashes
                    aggressive_json = aggressive_json.replace('\\\\\\\\', '\\\\')
                    patterns_data = json.loads(aggressive_json)
                    print("✓ Successfully repaired JSON with aggressive escaping")
                except json.JSONDecodeError as e3:
                    print(f"Final attempt failed: {e3}")
                    print(f"Response preview: {response[:500]}")
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

    def _validate_and_fix_patterns(
        self,
        patterns: List[MigrationPattern],
        language: str,
        source_framework: Optional[str] = None,
        target_framework: Optional[str] = None
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
                # Exclude common method names that look like props but aren't
                # These are method calls, not component props
                method_names = ["render", "mount", "unmount", "update", "setState", "useState", "useEffect"]
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
