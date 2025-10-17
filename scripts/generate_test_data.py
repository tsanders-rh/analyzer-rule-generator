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
    for rule in rules:
        when = rule.get('when', {})

        # Check for language-specific providers
        if 'java.referenced' in when or 'java.dependency' in when:
            return 'java'
        elif 'or' in when:
            # Check first condition in OR
            first_cond = when['or'][0] if isinstance(when['or'], list) else when['or']
            if 'java.referenced' in first_cond or 'java.dependency' in first_cond:
                return 'java'

        # Check for builtin provider patterns that might indicate language
        if 'builtin.file' in when or 'builtin.filecontent' in when:
            # Try to infer from file patterns
            if 'builtin.filecontent' in when:
                file_pattern = when['builtin.filecontent'].get('filePattern', '')
                if '.ts' in file_pattern or '.tsx' in file_pattern:
                    return 'typescript'
                elif '.go' in file_pattern:
                    return 'go'
                elif '.py' in file_pattern:
                    return 'python'

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
            'main_file': 'index.ts',
            'main_file_type': 'typescript',
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
        List of pattern dictionaries
    """
    patterns_to_test = []

    for rule in rules:
        pattern_info = {
            'ruleID': rule.get('ruleID'),
            'description': rule.get('description'),
            'pattern': None,
            'location': None,
            'provider': None
        }

        # Extract pattern from when condition
        when = rule.get('when', {})

        # Check for java provider
        if 'java.referenced' in when:
            java_ref = when['java.referenced']
            pattern_info['pattern'] = java_ref.get('pattern')
            pattern_info['location'] = java_ref.get('location')
            pattern_info['provider'] = 'java'
        elif 'java.dependency' in when:
            java_dep = when['java.dependency']
            pattern_info['pattern'] = java_dep.get('name')
            pattern_info['location'] = 'DEPENDENCY'
            pattern_info['provider'] = 'java'
        # Check for builtin provider
        elif 'builtin.filecontent' in when:
            builtin = when['builtin.filecontent']
            pattern_info['pattern'] = builtin.get('pattern')
            pattern_info['location'] = 'FILE_CONTENT'
            pattern_info['provider'] = 'builtin'
        elif 'builtin.file' in when:
            builtin = when['builtin.file']
            pattern_info['pattern'] = builtin.get('pattern')
            pattern_info['location'] = 'FILE_PATTERN'
            pattern_info['provider'] = 'builtin'
        # Check for OR conditions
        elif 'or' in when:
            # Take first condition from OR
            first_cond = when['or'][0] if isinstance(when['or'], list) else when['or']
            if 'java.referenced' in first_cond:
                java_ref = first_cond['java.referenced']
                pattern_info['pattern'] = java_ref.get('pattern')
                pattern_info['location'] = java_ref.get('location')
                pattern_info['provider'] = 'java'

        if pattern_info['pattern']:
            patterns_to_test.append(pattern_info)

    return patterns_to_test


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

    # Build patterns summary
    patterns_summary = "\n".join([
        f"- Rule {p['ruleID']}: {p['description']}\n  Pattern: {p['pattern']} (location: {p['location']})"
        for p in patterns
    ])

    # Language-specific instructions
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

For Java patterns:
- PACKAGE location: Use @Value("${{property}}") or @ConfigurationProperties
- TYPE location: Use class/interface in field declarations or method signatures
- ANNOTATION location: Use @Annotation on classes/methods
- DEPENDENCY location: Include in pom.xml dependencies
""",
        'typescript': """
1. **{build_file}** - package.json with:
   - Dependencies at SOURCE version
   - TypeScript configuration
   - Minimal required packages

2. **{main_file}** - Main application with:
   - Imports using each deprecated pattern
   - Comments: // Rule {source}-to-{target}-00001

For TypeScript patterns:
- Import statements for deprecated modules
- Usage of deprecated APIs, classes, functions
- Type annotations with deprecated types
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
        target=target
    )

    prompt = f"""Generate a minimal {language.upper()} test application for Konveyor analyzer rule testing.

Migration: {source} → {target}
Guide: {guide_url}
Language: {language}

You need to create {language} code that will trigger these analyzer rules:

{patterns_summary}

Requirements:
1. Create a complete, compilable {language} project structure
2. Include code that uses EACH deprecated pattern exactly once
3. Keep the code minimal - just enough to trigger the rules
4. Use realistic naming based on the patterns
5. Add comments indicating which rule each code segment tests
6. Ensure each pattern appears in a way that static analysis can detect

Output files:

{specific_instructions}

Format your response with clear code blocks:

```{config['build_file_type']}
{config['build_file']}
```

```{config['main_file_type']}
{config['main_file']}
```

Generate ONLY the file contents. Do not include explanations before or after the code blocks.
"""

    return prompt


def extract_code_blocks(response: str, language: str) -> dict:
    """
    Extract build file and source file from LLM response.

    Args:
        response: LLM response text
        language: Programming language

    Returns:
        Dict with build_file and source_file keys
    """
    import re

    config = get_language_config(language)
    result = {'build_file': None, 'source_file': None}

    # Try to extract code blocks
    # Pattern: ```type\n content \n```
    code_blocks = re.findall(r'```(\w+)\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)

    for block_type, content in code_blocks:
        content = content.strip()

        # Match build file types
        if block_type.lower() in ['xml', 'json', 'go', 'text', 'txt', 'toml']:
            if not result['build_file']:
                result['build_file'] = content
        # Match source file types
        elif block_type.lower() in ['java', 'typescript', 'ts', 'python', 'py', 'go', 'javascript', 'js']:
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

  # Generate TypeScript test data
  python scripts/generate_test_data.py \\
    --rules examples/output/react-18/migration-rules.yaml \\
    --output submission/tests/data/react \\
    --source react-17 \\
    --target react-18 \\
    --language typescript \\
    --guide-url "https://react.dev/blog/2022/03/29/react-v18"
        """
    )

    parser.add_argument(
        '--rules',
        required=True,
        help='Path to rule YAML file'
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

    args = parser.parse_args()

    # Validate inputs
    rule_file = Path(args.rules)
    if not rule_file.exists():
        print(f"Error: Rule file not found: {rule_file}", file=sys.stderr)
        return 1

    # Load rules
    print(f"Loading rules from {rule_file}...")
    with open(rule_file, 'r') as f:
        content = yaml.safe_load(f)
        if isinstance(content, list):
            rules = content
        else:
            rules = [content]

    print(f"  ✓ Loaded {len(rules)} rules")

    # Detect or use specified language
    language = args.language or detect_language(rules)
    print(f"  ✓ Detected language: {language}")

    config = get_language_config(language)

    # Initialize LLM
    print(f"\nInitializing {args.provider} LLM...")
    llm = get_llm_provider(args.provider, args.model, args.api_key)
    print(f"  ✓ Using model: {llm.model if hasattr(llm, 'model') else llm.model_name}")

    # Build prompt
    print(f"\nGenerating {language} test data with AI...")
    prompt = build_test_generation_prompt(rules, args.source, args.target, args.guide_url, language)

    # Generate with LLM
    try:
        result = llm.generate(prompt)
        response = result.get('response', '')

        # Show token usage if available
        if 'usage' in result:
            usage = result['usage']
            if 'input_tokens' in usage:
                print(f"  Input tokens: {usage['input_tokens']}")
                print(f"  Output tokens: {usage['output_tokens']}")
            elif 'prompt_tokens' in usage:
                print(f"  Prompt tokens: {usage['prompt_tokens']}")
                print(f"  Completion tokens: {usage['completion_tokens']}")

    except Exception as e:
        print(f"Error generating test data: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    # Extract code blocks
    print(f"\nExtracting generated code...")
    code = extract_code_blocks(response, language)

    if not code['build_file']:
        print(f"Error: Could not extract {config['build_file']} from response", file=sys.stderr)
        print(f"\nResponse preview:\n{response[:500]}", file=sys.stderr)
        return 1

    if not code['source_file']:
        print(f"Error: Could not extract {config['main_file']} from response", file=sys.stderr)
        print(f"\nResponse preview:\n{response[:500]}", file=sys.stderr)
        return 1

    # Create output directory structure
    output_dir = Path(args.output)
    src_dir = create_directory_structure(output_dir, language)

    # Write build file
    build_file_path = output_dir / config['build_file']
    with open(build_file_path, 'w') as f:
        f.write(code['build_file'])
    print(f"  ✓ {build_file_path}")

    # Write source file
    source_file_path = src_dir / config['main_file']
    with open(source_file_path, 'w') as f:
        f.write(code['source_file'])
    print(f"  ✓ {source_file_path}")

    print(f"\n✓ Test data generated successfully!")
    print(f"\nNext steps:")
    print(f"  1. Review generated files in: {output_dir}")

    # Language-specific verification commands
    verify_commands = {
        'java': f"mvn -f {build_file_path} compile",
        'typescript': f"cd {output_dir} && npm install && npm run build",
        'go': f"cd {output_dir} && go build",
        'python': f"cd {output_dir} && pip install -r requirements.txt"
    }

    if language in verify_commands:
        print(f"  2. Verify code compiles: {verify_commands[language]}")
    print(f"  3. Run analyzer tests: kantra test <test-file>.test.yaml")

    return 0


if __name__ == '__main__':
    sys.exit(main())
