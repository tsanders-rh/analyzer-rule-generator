#!/usr/bin/env python3
"""
Update go-konveyor-tests dependency expectations from analyzer output.

This script:
1. Reads analyzer output (YAML/JSON) containing discovered dependencies
2. Generates Go code for the Dependencies section
3. Can update existing test case files or generate new ones

Usage:
    python scripts/update_test_dependencies.py \
        --analyzer-output /path/to/output/output.yaml \
        --test-case tc_myapp_deps.go

Kantra Output Location:
    After running: kantra analyze --input myapp --output analysis_output

    The dependencies are typically in one of these files:
    - analysis_output/output.yaml (main analysis results)
    - analysis_output/dependencies.yaml (if separate)

    Look for YAML with structure like:
      dependencies:
        - name: "org.springframework.boot:spring-boot-starter-web"
          version: "2.7.0"
          labels:
            - "konveyor.io/dep-source=java"

Example analyzer output formats supported:

    Format 1 (Konveyor standard):
      dependencies:
        - name: "org.springframework.boot:spring-boot-starter-web"
          version: "2.7.0"
          labels:
            - "konveyor.io/dep-source=java"

    Format 2 (Simple):
      dependencies:
        - name: "org.springframework.boot"
          version: "2.5.0"
          provider: "java"
"""
import argparse
import sys
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any
import re


class Dependency:
    """Represents a technology dependency."""

    def __init__(self, name: str, version: str, provider: str):
        self.name = name
        self.version = version
        self.provider = provider

    def to_go_struct(self) -> str:
        """Convert to Go api.TechDependency struct."""
        return f'''{{
\t\t\tName:     "{self.name}",
\t\t\tVersion:  "{self.version}",
\t\t\tProvider: "{self.provider}",
\t\t}}'''


def parse_analyzer_output(file_path: Path) -> List[Dependency]:
    """
    Parse analyzer output file and extract dependencies.

    Supports both YAML and JSON formats.

    Args:
        file_path: Path to analyzer output file

    Returns:
        List of Dependency objects
    """
    with open(file_path, 'r') as f:
        content = f.read()

    # Try YAML first, then JSON
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            print(f"Error: Could not parse {file_path} as YAML or JSON", file=sys.stderr)
            sys.exit(1)

    dependencies = []

    # Handle different output formats
    if isinstance(data, dict):
        # Format 1: {dependencies: [...]}
        if 'dependencies' in data:
            deps_data = data['dependencies']
        # Format 2: {techDependencies: [...]}
        elif 'techDependencies' in data:
            deps_data = data['techDependencies']
        # Format 3: Top-level keys are dependency names
        else:
            print(f"Warning: Unrecognized format, attempting to extract dependencies", file=sys.stderr)
            deps_data = []
    elif isinstance(data, list):
        # Format 4: Kantra dependencies.yaml format - list of file objects
        # Each object has: {fileURI: ..., provider: ..., dependencies: [...]}
        # We need to extract all dependencies from all files
        deps_data = []
        for file_obj in data:
            if isinstance(file_obj, dict) and 'dependencies' in file_obj:
                file_provider = file_obj.get('provider', 'java')
                for dep in file_obj['dependencies']:
                    # Add file-level provider if not set on dependency
                    if isinstance(dep, dict) and 'provider' not in dep:
                        dep['provider'] = file_provider
                    deps_data.append(dep)

        # If we didn't find any nested dependencies, treat as direct list
        if not deps_data:
            deps_data = data
    else:
        print(f"Error: Unexpected data format", file=sys.stderr)
        sys.exit(1)

    # Parse dependency objects
    for dep in deps_data:
        if isinstance(dep, dict):
            name = dep.get('name') or dep.get('Name', '')
            version = dep.get('version') or dep.get('Version', '')
            provider = dep.get('provider') or dep.get('Provider')

            # If provider not explicitly set, try to extract from labels
            if not provider:
                labels = dep.get('labels', [])
                for label in labels:
                    if 'dep-source=' in label:
                        provider = label.split('dep-source=')[1]
                        break

            # Default to java if still not found
            if not provider:
                provider = 'java'

            if name:  # Only add if we have a name
                dependencies.append(Dependency(name, version, provider))

    return dependencies


def generate_go_dependencies(dependencies: List[Dependency]) -> str:
    """
    Generate Go code for Dependencies field.

    Args:
        dependencies: List of Dependency objects

    Returns:
        Go code string
    """
    if not dependencies:
        return "\t\tDependencies: []api.TechDependency{},\n"

    deps_code = "\t\tDependencies: []api.TechDependency{\n"

    for dep in sorted(dependencies, key=lambda d: d.name):
        deps_code += "\t\t" + dep.to_go_struct() + ",\n"

    deps_code += "\t\t},\n"

    return deps_code


def update_test_case_file(file_path: Path, dependencies_code: str) -> None:
    """
    Update existing test case file with new dependencies.

    Args:
        file_path: Path to test case .go file
        dependencies_code: Generated Go dependencies code
    """
    if not file_path.exists():
        print(f"Error: Test case file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    with open(file_path, 'r') as f:
        content = f.read()

    # Pattern to match the Dependencies field
    # This matches from "Dependencies:" to the closing "},"
    pattern = r'(\s+Dependencies:\s+\[]api\.TechDependency\s*\{)[^}]*(\},)'

    # Replace the dependencies section
    updated_content = re.sub(
        pattern,
        r'\n' + dependencies_code.rstrip() + r'\n\t',
        content,
        flags=re.DOTALL
    )

    if updated_content == content:
        print(f"Warning: Could not find Dependencies section to update in {file_path}", file=sys.stderr)
        print("The file may need to be updated manually.", file=sys.stderr)
        return

    # Write back
    with open(file_path, 'w') as f:
        f.write(updated_content)

    print(f"✓ Updated {file_path}")


def generate_test_case_template(
    test_name: str,
    app_name: str,
    dependencies: List[Dependency]
) -> str:
    """
    Generate a complete test case file template.

    Args:
        test_name: Name of the test case
        app_name: Application name
        dependencies: List of dependencies

    Returns:
        Complete Go file content
    """
    deps_code = generate_go_dependencies(dependencies).strip()

    # Sanitize names for Go variable naming
    var_name = re.sub(r'[^a-zA-Z0-9]', '', test_name.title())

    template = f'''package analysis

import (
\t"github.com/konveyor-ecosystem/go-konveyor-tests/data"
\t"github.com/konveyor-ecosystem/go-konveyor-tests/hack/addon"
\tapi "github.com/konveyor/tackle2-hub/api"
)

var {var_name} = TC{{
\tName: "{test_name}",
\tApplication: data.{app_name},
\tTask: Task,
\tAnalysis: api.Analysis{{
{deps_code}
\t}},
}}
'''

    return template


def main():
    parser = argparse.ArgumentParser(
        description="Update go-konveyor-tests dependencies from analyzer output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update existing test case file:
  python scripts/update_test_dependencies.py \\
      --analyzer-output analysis.yaml \\
      --test-case tc_myapp_deps.go

  # Generate new test case file:
  python scripts/update_test_dependencies.py \\
      --analyzer-output analysis.yaml \\
      --output tc_newapp_deps.go \\
      --test-name "NewApp Dependencies" \\
      --app-name "NewApp"
        """
    )

    parser.add_argument(
        '--analyzer-output',
        required=True,
        help='Path to analyzer output file (YAML or JSON)'
    )

    parser.add_argument(
        '--test-case',
        help='Path to existing test case file to update'
    )

    parser.add_argument(
        '--output',
        help='Path for new test case file (if creating new)'
    )

    parser.add_argument(
        '--test-name',
        help='Test case name (required for new files)'
    )

    parser.add_argument(
        '--app-name',
        help='Application name (required for new files)'
    )

    parser.add_argument(
        '--print-only',
        action='store_true',
        help='Print generated code without writing files'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.test_case and not args.output:
        print("Error: Either --test-case or --output must be specified", file=sys.stderr)
        sys.exit(1)

    if args.output and (not args.test_name or not args.app_name):
        print("Error: --test-name and --app-name are required when creating new file", file=sys.stderr)
        sys.exit(1)

    # Parse analyzer output
    print(f"Parsing analyzer output: {args.analyzer_output}")
    dependencies = parse_analyzer_output(Path(args.analyzer_output))
    print(f"  ✓ Found {len(dependencies)} dependencies")

    # Generate code
    if args.test_case:
        # Update existing file
        deps_code = generate_go_dependencies(dependencies)

        if args.print_only:
            print("\nGenerated dependencies code:")
            print(deps_code)
        else:
            update_test_case_file(Path(args.test_case), deps_code)

    else:
        # Generate new file
        content = generate_test_case_template(
            args.test_name,
            args.app_name,
            dependencies
        )

        if args.print_only:
            print("\nGenerated test case file:")
            print(content)
        else:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(content)
            print(f"✓ Generated {output_path}")


if __name__ == '__main__':
    main()
