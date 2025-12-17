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
    def check_condition(cond):
        """Helper to check a single condition."""
        if 'nodejs.referenced' in cond or 'nodejs.dependency' in cond:
            return 'typescript'
        elif 'java.referenced' in cond or 'java.dependency' in cond:
            return 'java'
        elif 'builtin.filecontent' in cond:
            file_pattern = cond['builtin.filecontent'].get('filePattern', '')
            if '.ts' in file_pattern or '.tsx' in file_pattern or '.js' in file_pattern or '.jsx' in file_pattern:
                return 'typescript'
            elif '.go' in file_pattern:
                return 'go'
            elif '.py' in file_pattern:
                return 'python'
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
        'rulesPath': f'../{rule_file_path.name}',
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
