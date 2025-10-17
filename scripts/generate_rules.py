#!/usr/bin/env python3
"""
Generate Konveyor analyzer rules from migration guides.

Usage:
    python scripts/generate_rules.py \\
        --guide <path_or_url> \\
        --source <framework> \\
        --target <framework> \\
        --output <output.yaml>
"""
import sys
import argparse
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_generator.ingestion import GuideIngester
from rule_generator.extraction import MigrationPatternExtractor
from rule_generator.generator import AnalyzerRuleGenerator
from rule_generator.llm import get_llm_provider
from rule_generator.schema import Category, LocationType


def enum_representer(dumper, data):
    """YAML representer for enums."""
    return dumper.represent_scalar('tag:yaml.org,2002:str', data.value)


# Register enum representers for clean YAML output
yaml.add_representer(Category, enum_representer)
yaml.add_representer(LocationType, enum_representer)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Konveyor analyzer rules from migration guides"
    )

    parser.add_argument(
        "--guide",
        required=True,
        help="Path to migration guide (file or URL)"
    )

    parser.add_argument(
        "--source",
        required=True,
        help="Source framework name (e.g., 'spring-boot')"
    )

    parser.add_argument(
        "--target",
        required=True,
        help="Target framework name (e.g., 'quarkus')"
    )

    parser.add_argument(
        "--output",
        help="Output YAML file path (auto-generated from source/target if not specified)"
    )

    parser.add_argument(
        "--provider",
        default="openai",
        choices=["openai", "anthropic", "google"],
        help="LLM provider to use (default: openai)"
    )

    parser.add_argument(
        "--model",
        help="Specific model name (uses provider default if not specified)"
    )

    parser.add_argument(
        "--api-key",
        help="API key (uses environment variable if not specified)"
    )

    args = parser.parse_args()

    # Auto-generate output filename if not specified
    if not args.output:
        # Extract technology name from source (remove version info)
        # e.g., "patternfly-v5" -> "patternfly", "spring-boot-3" -> "spring-boot"
        source_parts = args.source.split('-')
        target_parts = args.target.split('-')

        # Find where version info starts (v*, numeric suffix, etc.)
        def extract_base_name(parts):
            base = []
            for part in parts:
                # Stop at version indicators
                if part.startswith('v') or part.replace('.', '').isdigit():
                    break
                base.append(part)
            return '-'.join(base) if base else '-'.join(parts)

        source_base = extract_base_name(source_parts)

        # Generate filename: {source}-to-{target}.yaml
        output_filename = f"{args.source}-to-{args.target}.yaml"
        args.output = f"examples/output/{source_base}/{output_filename}"

    print(f"Generating analyzer rules: {args.source} → {args.target}")
    print(f"Guide: {args.guide}")
    print(f"Output: {args.output}")
    print(f"LLM: {args.provider} {args.model or '(default)'}")
    print()

    # Step 1: Ingest guide
    print("[1/3] Ingesting guide...")
    ingester = GuideIngester()
    guide_content = ingester.ingest(args.guide)

    if not guide_content:
        print("Error: Failed to ingest guide")
        sys.exit(1)

    print(f"  ✓ Ingested {len(guide_content)} characters")

    # Step 2: Extract patterns
    print("[2/3] Extracting patterns with LLM...")
    llm = get_llm_provider(
        provider=args.provider,
        model=args.model,
        api_key=args.api_key
    )

    extractor = MigrationPatternExtractor(llm)
    patterns = extractor.extract_patterns(
        guide_content,
        source_framework=args.source,
        target_framework=args.target
    )

    if not patterns:
        print("Error: No patterns extracted")
        sys.exit(1)

    print(f"  ✓ Extracted {len(patterns)} patterns")

    # Step 3: Generate rules (grouped by concern)
    print("[3/3] Generating analyzer rules...")

    generator = AnalyzerRuleGenerator(
        source_framework=args.source,
        target_framework=args.target,
        rule_file_name=None  # Will be set per-concern
    )

    rules_by_concern = generator.generate_rules_by_concern(patterns)

    if not rules_by_concern:
        print("Error: No rules generated")
        sys.exit(1)

    total_rules = sum(len(rules) for rules in rules_by_concern.values())
    print(f"  ✓ Generated {total_rules} rules across {len(rules_by_concern)} concern(s)")

    # Write output files (one per concern)
    output_path = Path(args.output)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract base name for generating filenames
    source_parts = args.source.split('-')
    target_parts = args.target.split('-')

    # Find where version info starts (v*, numeric suffix, etc.)
    def extract_base_name(parts):
        base = []
        for part in parts:
            # Stop at version indicators
            if part.startswith('v') or part.replace('.', '').isdigit():
                break
            base.append(part)
        return '-'.join(base) if base else '-'.join(parts)

    source_base = extract_base_name(source_parts)

    print(f"\nWriting rules to {output_dir}...")

    written_files = []
    all_rules = []

    for concern, rules in sorted(rules_by_concern.items()):
        # Generate filename: {source}-to-{target}-{concern}.yaml
        if len(rules_by_concern) == 1:
            # Single concern - use original filename
            concern_output = output_path
        else:
            # Multiple concerns - add concern suffix
            concern_output = output_dir / f"{args.source}-to-{args.target}-{concern}.yaml"

        # Update generator with correct rule file name for this concern
        generator.rule_file_name = concern_output.stem

        # Regenerate rules with correct IDs
        generator._rule_counter = 0
        concern_patterns = [p for p in patterns if (p.concern or "general") == concern]
        rules = []
        for pattern in concern_patterns:
            rule = generator._pattern_to_rule(pattern)
            if rule:
                rules.append(rule)

        # Convert rules to dicts for YAML serialization
        rules_data = [rule.model_dump(exclude_none=True) for rule in rules]

        with open(concern_output, 'w') as f:
            yaml.dump(rules_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        written_files.append(str(concern_output))
        all_rules.extend(rules)
        print(f"  ✓ {concern_output.name}: {len(rules)} rules")

    print(f"\n✓ Successfully generated {len(all_rules)} rules in {len(written_files)} file(s)")

    # Show summary
    print("\nRule Summary:")
    print(f"  Total rules: {len(all_rules)}")
    print(f"  Files generated: {len(written_files)}")

    # Group by category
    categories = {}
    for rule in all_rules:
        cat = rule.category.value
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    # Show effort distribution
    efforts = {}
    for rule in all_rules:
        eff = rule.effort
        efforts[eff] = efforts.get(eff, 0) + 1

    print(f"\nEffort Distribution:")
    for eff in sorted(efforts.keys()):
        print(f"  {eff}: {'▓' * efforts[eff]}")

    # Show files created
    print(f"\nFiles created:")
    for file in written_files:
        print(f"  {file}")


if __name__ == "__main__":
    main()
