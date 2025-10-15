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
        required=True,
        help="Output YAML file path"
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

    print(f"Generating analyzer rules: {args.source} → {args.target}")
    print(f"Guide: {args.guide}")
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

    # Step 3: Generate rules
    print("[3/3] Generating analyzer rules...")
    generator = AnalyzerRuleGenerator(
        source_framework=args.source,
        target_framework=args.target
    )

    rules = generator.generate_rules(patterns)

    if not rules:
        print("Error: No rules generated")
        sys.exit(1)

    print(f"  ✓ Generated {len(rules)} rules")

    # Write output
    print(f"\nWriting rules to {args.output}...")

    # Convert rules to dicts for YAML serialization
    rules_data = [rule.model_dump(exclude_none=True) for rule in rules]

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        yaml.dump(rules_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"✓ Successfully generated {len(rules)} rules")
    print(f"\nOutput: {args.output}")

    # Show summary
    print("\nRule Summary:")
    print(f"  Total rules: {len(rules)}")

    # Group by category
    categories = {}
    for rule in rules:
        cat = rule.category.value
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    # Show effort distribution
    efforts = {}
    for rule in rules:
        eff = rule.effort
        efforts[eff] = efforts.get(eff, 0) + 1

    print(f"\nEffort Distribution:")
    for eff in sorted(efforts.keys()):
        print(f"  {eff}: {'▓' * efforts[eff]}")


if __name__ == "__main__":
    main()
