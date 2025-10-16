#!/usr/bin/env python3
"""
Generate test data (Java code with violations) for Konveyor analyzer rules.

This script uses an LLM to generate a minimal Java test application that
contains code violations matching the generated rules.
"""
import argparse
import sys
from pathlib import Path
import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rule_generator.llm import get_llm_provider


def build_test_generation_prompt(rules: list, source: str, target: str, guide_url: str) -> str:
    """
    Build prompt for LLM to generate test application code.

    Args:
        rules: List of rule dictionaries
        source: Source framework/version
        target: Target framework/version
        guide_url: URL to migration guide

    Returns:
        Prompt string
    """
    # Extract patterns that need to be tested
    patterns_to_test = []
    for rule in rules:
        pattern_info = {
            'ruleID': rule.get('ruleID'),
            'description': rule.get('description'),
            'pattern': None,
            'location': None
        }

        # Extract pattern from when condition
        when = rule.get('when', {})
        if 'java.referenced' in when:
            java_ref = when['java.referenced']
            pattern_info['pattern'] = java_ref.get('pattern')
            pattern_info['location'] = java_ref.get('location')
        elif 'or' in when:
            # Take first condition from OR
            first_cond = when['or'][0]
            if 'java.referenced' in first_cond:
                java_ref = first_cond['java.referenced']
                pattern_info['pattern'] = java_ref.get('pattern')
                pattern_info['location'] = java_ref.get('location')

        if pattern_info['pattern']:
            patterns_to_test.append(pattern_info)

    # Build patterns summary
    patterns_summary = "\n".join([
        f"- Rule {p['ruleID']}: {p['description']}\n  Pattern: {p['pattern']} (location: {p['location']})"
        for p in patterns_to_test
    ])

    prompt = f"""Generate a minimal Java test application for Konveyor analyzer rule testing.

Migration: {source} → {target}
Guide: {guide_url}

You need to create Java code that will trigger these analyzer rules:

{patterns_summary}

Requirements:
1. Create a complete, compilable Java project structure
2. Include code that uses EACH deprecated pattern exactly once
3. Keep the code minimal - just enough to trigger the rules
4. Use realistic class/variable names based on the patterns
5. Add comments indicating which rule each code segment tests
6. For PACKAGE location patterns, use actual property references with @Value or @ConfigurationProperties
7. For TYPE location patterns, use the class/interface in field declarations or method signatures
8. For ANNOTATION location patterns, use the annotation on classes/methods
9. Ensure each pattern appears in a way that static analysis can detect

Output two files:

1. **pom.xml** - Maven project file with:
   - Parent: Spring Boot or appropriate framework at SOURCE version
   - Minimal dependencies needed for the patterns
   - Java version (11 or 17)

2. **Application.java** - Main application with:
   - Package: com.example
   - Code using each deprecated pattern
   - Comments: // Rule {source}-to-{target}-00001

Format your response as:

```xml
<!-- pom.xml -->
<project>
...
</project>
```

```java
// Application.java
package com.example;

...
```

Generate ONLY the file contents. Do not include explanations before or after the code blocks.
"""

    return prompt


def extract_code_blocks(response: str) -> dict:
    """
    Extract pom.xml and Application.java from LLM response.

    Args:
        response: LLM response text

    Returns:
        Dict with 'pom' and 'java' keys
    """
    import re

    result = {'pom': None, 'java': None}

    # Extract XML (pom.xml)
    xml_pattern = r'```xml\s*(.*?)\s*```'
    xml_match = re.search(xml_pattern, response, re.DOTALL | re.IGNORECASE)
    if xml_match:
        result['pom'] = xml_match.group(1).strip()

    # Extract Java
    java_pattern = r'```java\s*(.*?)\s*```'
    java_match = re.search(java_pattern, response, re.DOTALL | re.IGNORECASE)
    if java_match:
        result['java'] = java_match.group(1).strip()

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Generate test data for Konveyor analyzer rules using AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate test data for Spring Boot 4.0 rules
  python scripts/generate_test_data.py \\
    --rules examples/output/spring-boot-4.0/migration-rules.yaml \\
    --output examples/konveyor-submission/spring-boot-4.0/tests/data/mongodb \\
    --source spring-boot-3.5 \\
    --target spring-boot-4.0 \\
    --guide-url "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide" \\
    --provider anthropic \\
    --model claude-3-7-sonnet-20250219
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

    # Initialize LLM
    print(f"\nInitializing {args.provider} LLM...")
    llm = get_llm_provider(args.provider, args.model, args.api_key)
    print(f"  ✓ Using model: {llm.model if hasattr(llm, 'model') else llm.model_name}")

    # Build prompt
    print(f"\nGenerating test data with AI...")
    prompt = build_test_generation_prompt(rules, args.source, args.target, args.guide_url)

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
    code = extract_code_blocks(response)

    if not code['pom']:
        print("Error: Could not extract pom.xml from response", file=sys.stderr)
        print(f"\nResponse preview:\n{response[:500]}", file=sys.stderr)
        return 1

    if not code['java']:
        print("Error: Could not extract Java code from response", file=sys.stderr)
        print(f"\nResponse preview:\n{response[:500]}", file=sys.stderr)
        return 1

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create source directory
    src_dir = output_dir / 'src' / 'main' / 'java' / 'com' / 'example'
    src_dir.mkdir(parents=True, exist_ok=True)

    # Write pom.xml
    pom_path = output_dir / 'pom.xml'
    with open(pom_path, 'w') as f:
        f.write(code['pom'])
    print(f"  ✓ {pom_path}")

    # Write Application.java
    java_path = src_dir / 'Application.java'
    with open(java_path, 'w') as f:
        f.write(code['java'])
    print(f"  ✓ {java_path}")

    print(f"\n✓ Test data generated successfully!")
    print(f"\nNext steps:")
    print(f"  1. Review generated files in: {output_dir}")
    print(f"  2. Verify code compiles: mvn -f {pom_path} compile")
    print(f"  3. Run analyzer tests: kantra test <test-file>.test.yaml")

    return 0


if __name__ == '__main__':
    sys.exit(main())
