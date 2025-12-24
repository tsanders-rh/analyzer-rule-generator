#!/usr/bin/env python3
"""
Generate test data (code with violations) for Konveyor analyzer rules.

This script uses an LLM to generate a minimal test application that
contains code violations matching the generated rules.

Supports multiple languages: Java, TypeScript, Go, Python, etc.
"""
import argparse
import sys
from pathlib import Path
import yaml
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rule_generator.llm import get_llm_provider


def detect_language(rules: list) -> str:
    """
    Detect the programming language from rule conditions.

    Args:
        rules: List of rule dictionaries

    Returns:
        Language name (java, typescript, go, python, etc.)
    """
    # First, check labels for language hints (e.g., konveyor.io/source=go-1.17)
    for rule in rules:
        labels = rule.get('labels', [])
        for label in labels:
            if isinstance(label, str):
                label_lower = label.lower()
                # Check source/target labels for language hints
                if 'go-' in label_lower or '=go' in label_lower or label_lower.startswith('go'):
                    return 'go'
                elif 'java-' in label_lower or '=java' in label_lower or 'spring' in label_lower:
                    return 'java'
                elif 'node' in label_lower or 'react' in label_lower or 'angular' in label_lower or 'typescript' in label_lower:
                    return 'typescript'
                elif 'python' in label_lower or 'django' in label_lower:
                    return 'python'

    def check_condition(cond):
        """Helper to check a single condition."""
        if 'nodejs.referenced' in cond or 'nodejs.dependency' in cond:
            return 'typescript'
        elif 'java.referenced' in cond or 'java.dependency' in cond:
            return 'java'
        elif 'builtin.filecontent' in cond or 'builtin.file' in cond:
            # Check filePattern for language hints
            builtin_cond = cond.get('builtin.filecontent') or cond.get('builtin.file', {})
            file_pattern = builtin_cond.get('filePattern', '')

            # Check for JS/TS patterns: .js, .jsx, .ts, .tsx
            # Common patterns: \.(j|t)sx?$, \.tsx?$, \.jsx?$, etc.
            if any(pattern in file_pattern for pattern in ['.ts', '.tsx', '.js', '.jsx', '(j|t)s', 'jsx?', 'tsx?']):
                return 'typescript'
            elif '.go' in file_pattern:
                return 'go'
            elif '.py' in file_pattern:
                return 'python'
            elif '.java' in file_pattern:
                return 'java'
        return None

    for rule in rules:
        when = rule.get('when', {})

        # Check for 'and' conditions
        if 'and' in when:
            and_conditions = when['and'] if isinstance(when['and'], list) else [when['and']]
            for cond in and_conditions:
                lang = check_condition(cond)
                if lang:
                    return lang
        # Check for 'or' conditions
        elif 'or' in when:
            or_conditions = when['or'] if isinstance(when['or'], list) else [when['or']]
            for cond in or_conditions:
                lang = check_condition(cond)
                if lang:
                    return lang
        # Check direct conditions
        else:
            lang = check_condition(when)
            if lang:
                return lang

    # Default to java if can't determine
    return 'java'


def get_language_config(language: str) -> dict:
    """
    Get language-specific configuration for test generation.

    Args:
        language: Programming language name

    Returns:
        Dict with language configuration
    """
    configs = {
        'java': {
            'build_file': 'pom.xml',
            'build_file_type': 'xml',
            'source_dir': 'src/main/java/com/example',
            'main_file': 'Application.java',
            'main_file_type': 'java',
            'package_manager': 'Maven',
            'test_instructions': 'Maven project with dependencies'
        },
        'typescript': {
            'build_file': 'package.json',
            'build_file_type': 'json',
            'source_dir': 'src',
            'main_file': 'App.tsx',
            'main_file_type': 'tsx',
            'package_manager': 'npm',
            'test_instructions': 'npm project with dependencies'
        },
        'go': {
            'build_file': 'go.mod',
            'build_file_type': 'go',
            'source_dir': '.',
            'main_file': 'main.go',
            'main_file_type': 'go',
            'package_manager': 'Go modules',
            'test_instructions': 'Go module with dependencies'
        },
        'python': {
            'build_file': 'requirements.txt',
            'build_file_type': 'text',
            'source_dir': 'src',
            'main_file': 'main.py',
            'main_file_type': 'python',
            'package_manager': 'pip',
            'test_instructions': 'Python project with requirements.txt'
        }
    }

    return configs.get(language, configs['java'])


def extract_patterns_from_rules(rules: list, language: str) -> list:
    """
    Extract patterns that need to be tested from rules.

    Args:
        rules: List of rule dictionaries
        language: Programming language

    Returns:
        List of pattern dictionaries with code hints
    """
    patterns_to_test = []

    def process_condition(cond, rule_id, description, message=''):
        """Process a single condition and extract pattern info."""
        pattern_info = {
            'ruleID': rule_id,
            'description': description,
            'message': message,
            'pattern': None,
            'location': None,
            'provider': None,
            'component': None,
            'code_hint': None
        }

        # Check for nodejs.referenced
        if 'nodejs.referenced' in cond:
            nodejs_ref = cond['nodejs.referenced']
            pattern_info['pattern'] = nodejs_ref.get('pattern')
            pattern_info['component'] = nodejs_ref.get('pattern')
            pattern_info['location'] = nodejs_ref.get('location', 'IMPORT')
            pattern_info['provider'] = 'nodejs'

        # Check for java provider
        elif 'java.referenced' in cond:
            java_ref = cond['java.referenced']
            pattern_info['pattern'] = java_ref.get('pattern')
            pattern_info['location'] = java_ref.get('location')
            pattern_info['provider'] = 'java'

            # Extract import statements if location is IMPORT
            if java_ref.get('location') == 'IMPORT' and message:
                imports = extract_java_imports_from_message(message)
                if imports:
                    pattern_info['code_hint'] = '\n'.join(imports)

        elif 'java.dependency' in cond:
            java_dep = cond['java.dependency']
            pattern_info['pattern'] = java_dep.get('name')
            pattern_info['location'] = 'DEPENDENCY'
            pattern_info['provider'] = 'java'

        # Check for builtin.filecontent (this contains the actual code pattern!)
        elif 'builtin.filecontent' in cond:
            builtin = cond['builtin.filecontent']
            pattern_info['pattern'] = builtin.get('pattern')
            pattern_info['location'] = 'FILE_CONTENT'
            pattern_info['provider'] = 'builtin'
            pattern_info['filePattern'] = builtin.get('filePattern', '')

            # Check if this is a configuration file pattern
            file_pattern = builtin.get('filePattern', '')
            if any(ext in file_pattern for ext in ['.properties', '.yaml', '.yml', '.factories', '.xml']):
                pattern_info['is_config_file'] = True
                # Determine config file type and name
                if '.properties' in file_pattern and 'spring.factories' not in file_pattern:
                    pattern_info['config_type'] = 'properties'
                    pattern_info['config_file_name'] = 'application.properties'
                elif 'spring.factories' in file_pattern or '.factories' in file_pattern:
                    pattern_info['config_type'] = 'properties'  # spring.factories uses properties format
                    pattern_info['config_file_name'] = 'spring.factories'
                    pattern_info['config_file_path'] = 'META-INF/spring.factories'  # Standard location
                elif '.yaml' in file_pattern or '.yml' in file_pattern:
                    pattern_info['config_type'] = 'yaml'
                    pattern_info['config_file_name'] = 'application.yaml'
                elif '.xml' in file_pattern:
                    pattern_info['config_type'] = 'xml'
                    pattern_info['config_file_name'] = 'application.xml'
                else:
                    pattern_info['config_type'] = 'properties'  # default
                    pattern_info['config_file_name'] = 'application.properties'
            else:
                pattern_info['is_config_file'] = False

            # Parse JSX/TSX patterns to generate code hints
            jsx_pattern = builtin.get('pattern', '')
            pattern_info['code_hint'] = generate_code_hint_from_pattern(jsx_pattern, language, description, message)

        elif 'builtin.file' in cond:
            builtin = cond['builtin.file']
            pattern_info['pattern'] = builtin.get('pattern')
            pattern_info['location'] = 'FILE_PATTERN'
            pattern_info['provider'] = 'builtin'
            pattern_info['filePattern'] = builtin.get('filePattern', '')

        return pattern_info if pattern_info['pattern'] else None

    for rule in rules:
        rule_id = rule.get('ruleID')
        description = rule.get('description', '')
        message = rule.get('message', '')
        when = rule.get('when', {})

        patterns = []

        # Handle 'and' conditions
        if 'and' in when:
            and_conditions = when['and'] if isinstance(when['and'], list) else [when['and']]
            for cond in and_conditions:
                info = process_condition(cond, rule_id, description, message)
                if info:
                    patterns.append(info)

        # Handle 'or' conditions
        elif 'or' in when:
            or_conditions = when['or'] if isinstance(when['or'], list) else [when['or']]
            for cond in or_conditions:
                info = process_condition(cond, rule_id, description, message)
                if info:
                    patterns.append(info)

        # Handle direct condition
        else:
            info = process_condition(when, rule_id, description, message)
            if info:
                patterns.append(info)

        # Merge patterns for the same rule
        if patterns:
            merged = {
                'ruleID': rule_id,
                'description': description,
                'patterns': patterns,
                'component': None,
                'code_hint': None
            }

            # Extract component name and code hint
            for p in patterns:
                if p.get('component'):
                    merged['component'] = p['component']
                if p.get('code_hint'):
                    merged['code_hint'] = p['code_hint']

            patterns_to_test.append(merged)

    return patterns_to_test


def extract_java_imports_from_message(message: str) -> list:
    """
    Extract Java import statements from a rule message's "Before:" section.

    Args:
        message: Rule message (may contain Before/After code examples)

    Returns:
        List of import statement strings
    """
    if not message:
        return []

    import re

    imports = []

    # Look for code blocks after "Before:"
    # Handle both actual newlines and literal \n (backslash-n) in the message
    before_match = re.search(r'Before:(?:\\n|\n)```(?:java)?(?:\\n|\n)(.*?)(?:\\n|\n)```', message, re.DOTALL)
    if before_match:
        code = before_match.group(1).strip()
        # Replace literal \n with actual newlines if present
        if '\\n' in code:
            code = code.replace('\\n', '\n')

        # Extract import statements from the code
        # Pattern: import package.name.ClassName;
        import_pattern = r'import\s+[\w.]+\s*;'
        found_imports = re.findall(import_pattern, code)
        imports.extend(found_imports)

    return imports


def generate_code_hint_from_pattern(pattern: str, language: str, description: str = '', message: str = '') -> str:
    """
    Generate a code example hint from a regex pattern or rule message.

    Args:
        pattern: Regex pattern from builtin.filecontent
        language: Programming language
        description: Rule description
        message: Rule message (may contain Before/After code examples)

    Returns:
        Code example string
    """
    if language != 'typescript':
        return None

    import re

    # FIRST: Try to extract code from the message's "Before:" section
    # This is the most reliable source of correct JSX
    if message:
        # Look for code blocks after "Before:"
        # Handle both actual newlines and literal \n (backslash-n) in the message
        # Some YAML files have literal \n sequences instead of actual newlines
        before_match = re.search(r'Before:(?:\\n|\n)```(?:\\n|\n)(.*?)(?:\\n|\n)```', message, re.DOTALL)
        if before_match:
            code = before_match.group(1).strip()
            # Replace literal \n with actual newlines if present
            if '\\n' in code:
                code = code.replace('\\n', '\n')
            # Skip if contains template variables ({{ }})
            if '{{' not in code and '}}' not in code:
                # Return the code if it looks like JSX (contains < and >)
                if '<' in code and '>' in code:
                    return code

    # Fallback: Try to extract JSX tag patterns from the regex

    # Pattern: <ComponentName[^>]*\battribute=['"]value['"][^>]*>
    jsx_match = re.search(r'<(\w+)([^>]*?)>', pattern)
    if jsx_match:
        component = jsx_match.group(1)
        attributes_pattern = jsx_match.group(2)

        # Extract specific attributes
        attrs = []

        # Look for variant="value"
        variant_match = re.search(r'\\bvariant=.*?[\'"](\w+)[\'"]', attributes_pattern)
        if variant_match:
            attrs.append(f'variant="{variant_match.group(1)}"')

        # Look for isFlat, isCompact, etc (boolean props)
        bool_props = re.findall(r'\\b(is[A-Z]\w+)', attributes_pattern)
        for prop in bool_props:
            attrs.append(prop)

        # Build example
        attr_str = ' ' + ' '.join(attrs) if attrs else ''

        # Check if it's a self-closing or has children
        if 'icon' in pattern.lower() or 'children' in pattern.lower():
            return f'<{component}{attr_str}>\n  <SomeIcon />\n</{component}>'
        else:
            return f'<{component}{attr_str}>Content</{component}>'

    # Look for import patterns
    import_match = re.search(r'import.*?from.*?[\'"](@[\w/-]+)[\'"]', pattern)
    if import_match:
        package = import_match.group(1)
        return f'import {{ Component }} from "{package}";'

    return None


def build_test_generation_prompt(rules: list, source: str, target: str, guide_url: str, language: str) -> str:
    """
    Build prompt for LLM to generate test application code.

    Args:
        rules: List of rule dictionaries
        source: Source framework/version
        target: Target framework/version
        guide_url: URL to migration guide
        language: Programming language

    Returns:
        Prompt string
    """
    config = get_language_config(language)
    patterns = extract_patterns_from_rules(rules, language)

    # Build patterns summary with specific code examples
    patterns_list = []
    has_config_files = False
    config_file_type = 'properties'  # default

    for p in patterns:
        pattern_text = f"- Rule {p['ruleID']}: {p['description']}"

        # Check if any pattern needs config files or has Java imports
        has_java_imports = False
        config_file_name = None
        config_file_path = None
        for pattern in p.get('patterns', []):
            if pattern.get('is_config_file'):
                has_config_files = True
                config_file_type = pattern.get('config_type', 'properties')
                config_file_name = pattern.get('config_file_name', f'application.{config_file_type}')
                config_file_path = pattern.get('config_file_path', '')
                # Add config file specific instruction
                pattern_obj = pattern.get('pattern', '')
                if config_file_path:
                    pattern_text += f"\n  **MUST BE IN CONFIG FILE ({config_file_type}) at {config_file_path}:** {pattern_obj}"
                else:
                    pattern_text += f"\n  **MUST BE IN CONFIG FILE ({config_file_type}) named {config_file_name}:** {pattern_obj}"

            # Check for Java imports
            if pattern.get('provider') == 'java' and pattern.get('location') == 'IMPORT' and pattern.get('code_hint'):
                has_java_imports = True
                pattern_text += f"\n\n  **YOU MUST INCLUDE THESE EXACT IMPORT STATEMENTS:**\n  ```java\n  // {p['ruleID']}\n  {pattern['code_hint']}\n  ```"

        # Add code hint if available (for code-based rules)
        if p.get('code_hint') and not has_java_imports:
            if language == 'typescript':
                pattern_text += f"\n\n  **YOU MUST GENERATE THIS EXACT JSX CODE:**\n  ```tsx\n  // {p['ruleID']}\n  {p['code_hint']}\n  ```"
        elif p.get('component'):
            pattern_text += f"\n  Component: {p['component']} (MUST be used in JSX, not just imported)"

        patterns_list.append(pattern_text)

    patterns_summary = "\n\n".join(patterns_list)

    # Language-specific instructions
    config_file_instructions = ""
    final_config_file_name = config_file_name if config_file_name else f'application.{config_file_type}'
    final_config_file_path = config_file_path if config_file_path else f'src/main/resources/{final_config_file_name}'
    if has_config_files and language == 'java':
        config_file_instructions = f"""
3. **{final_config_file_name}** - Configuration file with deprecated properties:
   - Location: {final_config_file_path}
   - CRITICAL: The deprecated property patterns marked as "MUST BE IN CONFIG FILE" below MUST appear in this file
   - Do NOT use @Value annotations in Java code for these patterns
   - Include the EXACT deprecated property names from the "Before:" examples in the rule messages
   - Format the properties correctly for {config_file_type} format
   - Include actual values for each deprecated property
   - Example: If pattern is spring\\.data\\.cassandra\\., include properties like:
     spring.data.cassandra.contact-points=localhost
     spring.data.cassandra.port=9042
"""

    lang_instructions = {
        'java': """
1. **{build_file}** - Maven project file with:
   - Parent: Spring Boot or appropriate framework at SOURCE version
   - Minimal dependencies needed for the patterns
   - Java version (11 or 17)

2. **{main_file}** - Main application with:
   - Package: com.example
   - Code using each deprecated pattern
   - Comments: // Rule {source}-to-{target}-00001

{config_file_instructions}

For Java patterns:
- IMPORT location: Add actual import statements at the top of the file (e.g., import org.example.ClassName;)
- PACKAGE location: Use @Value("${{property}}") or @ConfigurationProperties
- TYPE location: Use class/interface in field declarations or method signatures
- ANNOTATION location: Use @Annotation on classes/methods
- DEPENDENCY location: Include in pom.xml dependencies
- CONFIG FILE patterns: Add actual property in application.properties or application.yaml

CRITICAL: When import statements are shown above with "YOU MUST INCLUDE THESE EXACT IMPORT STATEMENTS",
add them EXACTLY as shown at the top of your Java file, after the package declaration.
""",
        'typescript': """
1. **{build_file}** - package.json with:
   - Dependencies at SOURCE version (e.g., "@patternfly/react-core": "^5.0.0")
   - React and TypeScript dependencies
   - Minimal required packages

2. **{main_file}** - React/TypeScript component (.tsx file) with:
   - Import statements for EACH component specified in the rules
   - ACTUAL JSX CODE using each component with the exact deprecated patterns
   - Comments before each pattern: // Rule {source}-to-{target}-XXXXX
   - Export a React component

CRITICAL REQUIREMENTS FOR REACT/JSX:
- File MUST be valid TSX (TypeScript + JSX)
- Components MUST be used in JSX, not just imported
- JSX code MUST match the exact patterns shown above (attributes, props, children)
- Each deprecated pattern MUST appear at least once in the JSX
- Do NOT generate generic examples - use the EXACT code patterns specified above
""",
        'go': """
1. **{build_file}** - Go module file with:
   - Module name
   - Go version at SOURCE
   - Required dependencies

2. **{main_file}** - Main application with:
   - Package main
   - Imports using each deprecated pattern
   - Comments: // Rule {source}-to-{target}-00001

For Go patterns:
- Import deprecated packages
- Use deprecated functions/types
- Reference deprecated APIs
""",
        'python': """
1. **{build_file}** - requirements.txt with:
   - Dependencies at SOURCE version
   - Minimal required packages

2. **{main_file}** - Main application with:
   - Imports using each deprecated pattern
   - Comments: # Rule {source}-to-{target}-00001

For Python patterns:
- Import statements for deprecated modules
- Usage of deprecated functions/classes
- References to deprecated APIs
"""
    }

    specific_instructions = lang_instructions.get(language, lang_instructions['java']).format(
        build_file=config['build_file'],
        main_file=config['main_file'],
        source=source,
        target=target,
        config_file_instructions=config_file_instructions
    )

    prompt = f"""Generate a minimal {language.upper()} test application for Konveyor analyzer rule testing.

Migration: {source} → {target}
Guide: {guide_url}
Language: {language}

CRITICAL: You MUST create code that triggers these SPECIFIC analyzer rules.
Each rule looks for EXACT patterns in the code. You MUST include the EXACT code shown below.

{patterns_summary}

REQUIREMENTS:
1. Create a complete, compilable {language} project structure
2. For EACH rule above, include the EXACT code/configuration pattern specified
3. If a code example is shown with "YOU MUST GENERATE THIS EXACT JSX CODE", copy it EXACTLY
4. Add comment before each pattern: // Rule ID (or # Rule ID for properties/yaml files)
5. Keep the code minimal - one example per rule
6. Ensure static analysis can detect each pattern

CRITICAL FOR CONFIGURATION FILES:
- If a rule says "MUST BE IN CONFIG FILE", create the configuration file (application.properties or application.yaml)
- Extract the EXACT deprecated property names from the rule's "Before:" code example
- Include those deprecated properties with realistic values in your configuration file
- Do NOT use @Value annotations in Java code for config file patterns - put them in the actual config file

CRITICAL FOR TSX/JSX FILES:
- Components must be USED in JSX, not just imported
- Match the EXACT JSX syntax: attributes, props, children
- Do not improvise - use the patterns shown above

Output files:

{specific_instructions}

Format your response with clear code blocks:

```{config['build_file_type']}
{config['build_file']}
```

```{config['main_file_type']}
{config['main_file']}
```
{"" if not has_config_files else f'''
```{config_file_type}
{final_config_file_name}
```
'''}
Generate ONLY the file contents. Do not include explanations before or after the code blocks.

IMPORTANT: If generating a config file other than application.properties/yaml, include the FULL filename in the code block header.
For example: ```properties spring.factories``` or ```yaml application-dev.yaml```
"""

    return prompt


def extract_code_blocks(response: str, language: str) -> dict:
    """
    Extract build file, source file, and config file from LLM response.

    Args:
        response: LLM response text
        language: Programming language

    Returns:
        Dict with build_file, source_file, and config_file keys
    """
    import re

    config = get_language_config(language)
    result = {'build_file': None, 'source_file': None, 'config_file': None}

    # Try to extract code blocks
    # Pattern: ```type\n content \n```
    code_blocks = re.findall(r'```(\w+)\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)

    for block_type, content in code_blocks:
        content = content.strip()

        # Match build file types
        if block_type.lower() in ['xml', 'json', 'go', 'text', 'txt', 'toml']:
            if not result['build_file']:
                result['build_file'] = content
        # Match config file types
        elif block_type.lower() in ['properties', 'yaml', 'yml']:
            if not result['config_file']:
                # Try to extract filename from content (first line might have filename as comment)
                # or infer from block type
                filename = None
                first_line = content.split('\n')[0].strip() if content else ''
                # Check if first line looks like a filename comment or path
                if first_line.startswith('#') or first_line.startswith('//'):
                    potential_name = first_line.lstrip('#/ ').strip()
                    if '.' in potential_name and not potential_name.startswith('Rule'):
                        filename = potential_name.split('/')[-1]  # Extract just filename from path

                if not filename:
                    filename = f'application.{block_type.lower()}'

                result['config_file'] = {
                    'type': block_type.lower(),
                    'content': content,
                    'filename': filename
                }
        # Match source file types
        elif block_type.lower() in ['java', 'typescript', 'tsx', 'ts', 'python', 'py', 'go', 'javascript', 'jsx', 'js']:
            if not result['source_file']:
                result['source_file'] = content

    # Fallback: try to find files by name/comment
    if not result['build_file']:
        build_pattern = rf'```\w*\s*(?:<!--\s*)?{re.escape(config["build_file"])}.*?```'
        build_match = re.search(build_pattern, response, re.DOTALL | re.IGNORECASE)
        if build_match:
            # Extract content between ```
            content_match = re.search(r'```\w*\s*(.*?)\s*```', build_match.group(0), re.DOTALL)
            if content_match:
                result['build_file'] = content_match.group(1).strip()

    if not result['source_file']:
        source_pattern = rf'```\w*\s*(?://|#)?\s*{re.escape(config["main_file"])}.*?```'
        source_match = re.search(source_pattern, response, re.DOTALL | re.IGNORECASE)
        if source_match:
            content_match = re.search(r'```\w*\s*(.*?)\s*```', source_match.group(0), re.DOTALL)
            if content_match:
                result['source_file'] = content_match.group(1).strip()

    return result


def create_directory_structure(output_dir: Path, language: str):
    """
    Create language-specific directory structure.

    Args:
        output_dir: Base output directory
        language: Programming language
    """
    config = get_language_config(language)

    # Create source directory
    src_dir = output_dir / config['source_dir']
    src_dir.mkdir(parents=True, exist_ok=True)

    return src_dir


def generate_test_yaml(rule_file_path: Path, data_dir_name: str, rules: list, output_dir: Path) -> Path:
    """
    Generate a Konveyor test YAML file.

    Args:
        rule_file_path: Path to the rule YAML file
        data_dir_name: Name of the data directory (e.g., "button")
        rules: List of rule dictionaries
        output_dir: Output directory for tests

    Returns:
        Path to created test YAML file
    """
    # Extract rule IDs
    rule_ids = [rule.get('ruleID') for rule in rules if rule.get('ruleID')]

    # Determine providers from rules
    def extract_providers(cond):
        """Helper to extract providers from a condition."""
        found = set()
        if 'java.referenced' in cond or 'java.dependency' in cond:
            found.add('java')
        if 'nodejs.referenced' in cond or 'nodejs.dependency' in cond:
            found.add('nodejs')
        if 'builtin.file' in cond or 'builtin.filecontent' in cond:
            found.add('builtin')
        if 'go.referenced' in cond or 'go.dependency' in cond:
            found.add('go')
        if 'python.referenced' in cond or 'python.dependency' in cond:
            found.add('python')

        # If only builtin provider, try to infer language-specific provider from filePattern
        if found == {'builtin'}:
            builtin_cond = cond.get('builtin.filecontent') or cond.get('builtin.file', {})
            file_pattern = builtin_cond.get('filePattern', '')

            # Add language-specific provider based on filePattern
            if any(pattern in file_pattern for pattern in ['.ts', '.tsx', '.js', '.jsx', '(j|t)s', 'jsx?', 'tsx?']):
                found.add('nodejs')
            elif '.java' in file_pattern:
                found.add('java')
            elif '.go' in file_pattern:
                found.add('go')
            elif '.py' in file_pattern:
                found.add('python')

        return found

    providers = set()
    for rule in rules:
        when = rule.get('when', {})

        # Check for 'and' conditions
        if 'and' in when:
            and_conditions = when['and'] if isinstance(when['and'], list) else [when['and']]
            for cond in and_conditions:
                providers.update(extract_providers(cond))
        # Check for 'or' conditions
        elif 'or' in when:
            or_conditions = when['or'] if isinstance(when['or'], list) else [when['or']]
            for cond in or_conditions:
                providers.update(extract_providers(cond))
        # Check direct conditions
        else:
            providers.update(extract_providers(when))

    # Default to java and builtin if we can't determine
    if not providers:
        providers = {'java', 'builtin'}

    # Build test structure
    test_data = {
        'rulesPath': f'../rules/{rule_file_path.name}',
        'providers': [
            {'name': provider, 'dataPath': f'./data/{data_dir_name}'}
            for provider in sorted(providers)
        ],
        'tests': [
            {
                'ruleID': rule_id,
                'testCases': [
                    {
                        'name': 'tc-1',
                        'hasIncidents': {'atLeast': 1}
                    }
                ]
            }
            for rule_id in rule_ids
        ]
    }

    # Write test YAML file
    test_file_name = rule_file_path.stem + '.test.yaml'
    test_file_path = output_dir / test_file_name

    with open(test_file_path, 'w') as f:
        yaml.dump(test_data, f, default_flow_style=False, sort_keys=False)

    return test_file_path


def main():
    parser = argparse.ArgumentParser(
        description='Generate test data for Konveyor analyzer rules using AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate Java test data for Spring Boot 4.0 rules
  python scripts/generate_test_data.py \\
    --rules examples/output/spring-boot-4.0/migration-rules.yaml \\
    --output submission/tests/data/mongodb \\
    --source spring-boot-3.5 \\
    --target spring-boot-4.0 \\
    --guide-url "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide"

  # Generate TypeScript test data for a directory of rules
  python scripts/generate_test_data.py \\
    --rules /path/to/rulesets/patternfly \\
    --output /path/to/rulesets/patternfly/tests \\
    --source patternfly-v5 \\
    --target patternfly-v6 \\
    --language typescript \\
    --guide-url "https://www.patternfly.org/get-started/upgrade/"
        """
    )

    parser.add_argument(
        '--rules',
        required=True,
        help='Path to rule YAML file or directory containing rule files'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output directory for test data'
    )
    parser.add_argument(
        '--source',
        required=True,
        help='Source framework/version'
    )
    parser.add_argument(
        '--target',
        required=True,
        help='Target framework/version'
    )
    parser.add_argument(
        '--guide-url',
        required=True,
        help='URL to migration guide'
    )
    parser.add_argument(
        '--language',
        choices=['java', 'typescript', 'go', 'python'],
        help='Programming language (auto-detected if not specified)'
    )
    parser.add_argument(
        '--provider',
        default='anthropic',
        choices=['openai', 'anthropic', 'google'],
        help='LLM provider (default: anthropic)'
    )
    parser.add_argument(
        '--model',
        help='Model name (uses provider default if not specified)'
    )
    parser.add_argument(
        '--api-key',
        help='API key (uses environment variable if not specified)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=8.0,
        help='Delay in seconds between API calls to avoid rate limits (default: 8.0)'
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum number of retries for rate limit errors (default: 3)'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip rule files that already have generated test data'
    )

    args = parser.parse_args()

    # Validate inputs
    rules_path = Path(args.rules)
    if not rules_path.exists():
        print(f"Error: Path not found: {rules_path}", file=sys.stderr)
        return 1

    # Determine if input is a file or directory
    if rules_path.is_file():
        # Single file mode
        rule_files = [rules_path]
    elif rules_path.is_dir():
        # Directory mode - find all YAML files except ruleset.yaml
        rule_files = sorted([
            f for f in rules_path.glob('*.yaml')
            if f.name != 'ruleset.yaml' and not f.name.endswith('.test.yaml')
        ])
        if not rule_files:
            print(f"Error: No rule YAML files found in {rules_path}", file=sys.stderr)
            return 1
    else:
        print(f"Error: {rules_path} is neither a file nor directory", file=sys.stderr)
        return 1

    print(f"Found {len(rule_files)} rule file(s) to process")

    # Initialize LLM once
    print(f"\nInitializing {args.provider} LLM...")
    llm = get_llm_provider(args.provider, args.model, args.api_key)
    print(f"  ✓ Using model: {llm.model if hasattr(llm, 'model') else llm.model_name}")

    # Setup output directory structure
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir = output_dir / 'data'
    data_dir.mkdir(exist_ok=True)

    # Process each rule file
    total_files = len(rule_files)
    skipped_count = 0
    for idx, rule_file in enumerate(rule_files, 1):
        print(f"\n{'='*70}")
        print(f"Processing {idx}/{total_files}: {rule_file.name}")
        print(f"{'='*70}")

        # Check if test already exists
        test_file_name = rule_file.stem + '.test.yaml'
        test_file_path = output_dir / test_file_name
        if args.skip_existing and test_file_path.exists():
            print(f"  ⊘ Skipping (test already exists)")
            skipped_count += 1
            continue

        # Load rules from file
        with open(rule_file, 'r') as f:
            content = yaml.safe_load(f)
            if isinstance(content, list):
                rules = content
            else:
                rules = [content]

        print(f"  ✓ Loaded {len(rules)} rule(s)")

        # Detect or use specified language
        language = args.language or detect_language(rules)
        print(f"  ✓ Language: {language}")

        config = get_language_config(language)

        # Generate data directory name from rule file
        # e.g., "patternfly-v5-to-patternfly-v6-button.yaml" -> "button"
        data_dir_name = rule_file.stem.replace(f'{args.source}-to-{args.target}-', '')

        # Build prompt
        print(f"  Generating test data with AI...")
        prompt = build_test_generation_prompt(rules, args.source, args.target, args.guide_url, language)

        # Generate with LLM (with retry logic for rate limits)
        response = None
        for retry in range(args.max_retries):
            try:
                result = llm.generate(prompt)
                response = result.get('response', '')

                # Show token usage if available
                if 'usage' in result:
                    usage = result['usage']
                    if 'input_tokens' in usage:
                        print(f"    Input tokens: {usage['input_tokens']}, Output tokens: {usage['output_tokens']}")
                    elif 'prompt_tokens' in usage:
                        print(f"    Prompt tokens: {usage['prompt_tokens']}, Completion tokens: {usage['completion_tokens']}")
                break  # Success, exit retry loop

            except Exception as e:
                error_str = str(e)
                if 'rate_limit' in error_str.lower() or '429' in error_str:
                    if retry < args.max_retries - 1:
                        wait_time = 60 * (retry + 1)  # Exponential backoff: 60s, 120s, 180s
                        print(f"  ⚠ Rate limit hit, waiting {wait_time}s before retry {retry + 2}/{args.max_retries}...")
                        time.sleep(wait_time)
                    else:
                        print(f"  ✗ Rate limit exceeded after {args.max_retries} retries", file=sys.stderr)
                        response = None
                        break
                else:
                    print(f"  ✗ Error generating test data: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc()
                    response = None
                    break

        if not response:
            continue  # Skip to next file

        # Extract code blocks
        code = extract_code_blocks(response, language)

        if not code['build_file'] or not code['source_file']:
            print(f"  ✗ Could not extract required files from response", file=sys.stderr)
            continue  # Skip to next file

        # Create test data directory
        test_data_dir = data_dir / data_dir_name
        src_dir = create_directory_structure(test_data_dir, language)

        # Write build file
        build_file_path = test_data_dir / config['build_file']
        with open(build_file_path, 'w') as f:
            f.write(code['build_file'])
        print(f"  ✓ {build_file_path.relative_to(output_dir)}")

        # Write source file
        source_file_path = src_dir / config['main_file']
        with open(source_file_path, 'w') as f:
            f.write(code['source_file'])
        print(f"  ✓ {source_file_path.relative_to(output_dir)}")

        # Write config file if present (for Java/Spring Boot projects)
        if code['config_file'] and language == 'java':
            config_filename = code['config_file'].get('filename', f"application.{code['config_file']['type']}")

            # Determine the correct directory based on the filename
            if 'spring.factories' in config_filename:
                # spring.factories goes in META-INF/
                config_dir = test_data_dir / 'src' / 'main' / 'resources' / 'META-INF'
            else:
                # Other config files go in resources/
                config_dir = test_data_dir / 'src' / 'main' / 'resources'

            config_dir.mkdir(parents=True, exist_ok=True)
            config_file_path = config_dir / config_filename

            with open(config_file_path, 'w') as f:
                f.write(code['config_file']['content'])
            print(f"  ✓ {config_file_path.relative_to(output_dir)}")

        # Generate test YAML file
        test_yaml_path = generate_test_yaml(rule_file, data_dir_name, rules, output_dir)
        print(f"  ✓ {test_yaml_path.relative_to(output_dir)}")

        # Add delay between API calls (except for the last file)
        if idx < total_files and args.delay > 0:
            print(f"  Waiting {args.delay}s before next file...")
            time.sleep(args.delay)

    print(f"\n{'='*70}")
    generated_count = total_files - skipped_count
    print(f"✓ Processed {total_files} rule file(s)")
    if skipped_count > 0:
        print(f"  - Generated: {generated_count}")
        print(f"  - Skipped: {skipped_count}")
    print(f"\nOutput directory: {output_dir}")
    print(f"  - Test YAML files: {len(list(output_dir.glob('*.test.yaml')))} files")
    if data_dir.exists():
        print(f"  - Test data directories: {len(list(data_dir.iterdir()))} directories")
    print(f"\nNext steps:")
    print(f"  1. Review generated files in: {output_dir}")
    print(f"  2. Run tests: kantra test {output_dir}/*.test.yaml")

    return 0


if __name__ == '__main__':
    sys.exit(main())
