#!/usr/bin/env python3
"""
Generate Konveyor analyzer rules from migration guides.

Usage:
    python scripts/generate_rules.py \\
        --guide <path_or_url> \\
        --source <framework> \\
        --target <framework> \\
        --output <output_directory>
"""
import sys
import argparse
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_generator.ingestion import GuideIngester
from rule_generator.extraction import MigrationPatternExtractor, detect_language_from_frameworks
from rule_generator.generator import AnalyzerRuleGenerator
from rule_generator.llm import get_llm_provider
from rule_generator.schema import Category, LocationType
from rule_generator.validate_rules import RuleValidator


def enum_representer(dumper, data):
    """YAML representer for enums."""
    return dumper.represent_scalar('tag:yaml.org,2002:str', data.value)


def str_representer(dumper, data):
    """
    YAML representer for strings that uses literal block scalar (|-) for multiline strings.
    This produces cleaner, more readable YAML output for rule messages.
    """
    if '\n' in data:
        # Use literal block scalar (|) for multiline strings
        # The | style preserves the literal formatting
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


def validate_rules(rules):
    """
    Validate generated rules and return warnings.

    Returns:
        Dictionary of issue_type -> list of warnings
    """
    from collections import defaultdict
    issues = defaultdict(list)

    for rule in rules:
        # Check for overly broad builtin patterns
        if 'builtin.filecontent' in str(rule.when):
            when_dict = rule.when
            if 'builtin.filecontent' in when_dict:
                pattern = when_dict['builtin.filecontent'].get('pattern', '')
                if len(pattern) < 5:
                    issues['overly_broad'].append(f"{rule.ruleID}: pattern too short '{pattern}'")

        # Check for missing file patterns on builtin rules
        if 'builtin.filecontent' in str(rule.when):
            when_dict = rule.when
            if 'builtin.filecontent' in when_dict:
                if not when_dict['builtin.filecontent'].get('filePattern'):
                    issues['missing_file_pattern'].append(f"{rule.ruleID}: builtin without filePattern")

        # Check for identical before/after in description
        if ' should be replaced with ' in rule.description:
            parts = rule.description.split(' should be replaced with ')
            if len(parts) == 2 and parts[0].strip() == parts[1].strip():
                issues['identical_source_target'].append(f"{rule.ruleID}: {parts[0]}")

    return dict(issues)


# Create custom dumper with our representers
class CustomDumper(yaml.Dumper):
    pass

# Register representers on custom dumper
CustomDumper.add_representer(Category, enum_representer)
CustomDumper.add_representer(LocationType, enum_representer)
CustomDumper.add_representer(str, str_representer)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Konveyor analyzer rules from migration guides or OpenRewrite recipes"
    )

    # Create mutually exclusive group for input source
    input_group = parser.add_mutually_exclusive_group(required=True)

    input_group.add_argument(
        "--guide",
        help="Path to migration guide (file or URL)"
    )

    input_group.add_argument(
        "--from-openrewrite",
        help="Path or URL to OpenRewrite recipe YAML file"
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
        help="Output directory for generated YAML files (auto-generated from source/target if not specified)"
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

    parser.add_argument(
        "--follow-links",
        action="store_true",
        default=False,
        help="Follow related links from migration guides (release notes, breaking changes, etc.)"
    )

    parser.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="Maximum depth for recursive link following (default: 2)"
    )

    args = parser.parse_args()

    # Auto-generate output directory if not specified
    if not args.output:
        # Extract technology name from source (remove version info)
        # e.g., "patternfly-v5" -> "patternfly", "spring-boot-3" -> "spring-boot"
        source_parts = args.source.split('-')

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

        # Generate directory: examples/output/{source_base}
        args.output = f"examples/output/{source_base}"

    # Determine input source
    input_source = args.guide or args.from_openrewrite
    from_openrewrite = args.from_openrewrite is not None

    print(f"Generating analyzer rules: {args.source} → {args.target}")
    print(f"{'OpenRewrite Recipe' if from_openrewrite else 'Guide'}: {input_source}")
    print(f"Output: {args.output}")
    print(f"LLM: {args.provider} {args.model or '(default)'}")
    print()

    # Step 1: Ingest content
    if from_openrewrite:
        print("[1/3] Ingesting OpenRewrite recipe...")
        from rule_generator.openrewrite import OpenRewriteRecipeIngester
        ingester = OpenRewriteRecipeIngester()
        guide_content = ingester.ingest(args.from_openrewrite)
    else:
        print("[1/3] Ingesting guide...")
        if args.follow_links:
            print(f"  → Following related links (max depth: {args.max_depth})")
        ingester = GuideIngester(
            follow_links=args.follow_links,
            max_depth=args.max_depth
        )
        guide_content = ingester.ingest(args.guide)

    if not guide_content:
        print(f"Error: Failed to ingest {'recipe' if from_openrewrite else 'guide'}")
        sys.exit(1)

    print(f"  ✓ Ingested {len(guide_content)} characters")

    # Step 2: Extract patterns
    print("[2/3] Extracting patterns with LLM...")
    llm = get_llm_provider(
        provider=args.provider,
        model=args.model,
        api_key=args.api_key
    )

    extractor = MigrationPatternExtractor(llm, from_openrewrite=from_openrewrite)
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

    # DEDUPLICATE across concerns
    print("  → Deduplicating rules across concerns...")
    from collections import defaultdict

    # Track unique patterns by (when condition hash, description)
    seen_patterns = {}
    deduplicated_by_concern = defaultdict(list)
    duplicate_count = 0

    for concern, rules in rules_by_concern.items():
        for rule in rules:
            # Create unique key from when condition and description
            # Convert when to string for hashing
            when_str = str(rule.when)
            key = (when_str, rule.description)

            if key not in seen_patterns:
                seen_patterns[key] = concern
                deduplicated_by_concern[concern].append(rule)
            else:
                duplicate_count += 1
                print(f"    ! Skipping duplicate: {rule.description[:60]}... (already in {seen_patterns[key]})")

    rules_by_concern = dict(deduplicated_by_concern)
    print(f"  ✓ Removed {duplicate_count} duplicate rules")

    total_rules = sum(len(rules) for rules in rules_by_concern.values())
    print(f"  ✓ Generated {total_rules} rules across {len(rules_by_concern)} concern(s)")

    # POST-GENERATION LLM VALIDATION (optional, only if enabled)
    # Collect all rules for validation
    all_generated_rules = []
    for rules in rules_by_concern.values():
        all_generated_rules.extend(rules)

    # Detect language for validation
    language = detect_language_from_frameworks(args.source, args.target)

    # Run LLM validation if language is JS/TS and we have rules to validate
    if language in ["javascript", "typescript"] and all_generated_rules:
        print("\n" + "=" * 80)
        print("LLM-BASED VALIDATION (EXPERIMENTAL)")
        print("=" * 80)
        print("This step uses LLM to detect and fix common rule quality issues.")
        print("Note: This is an experimental feature and may use additional API credits.")

        # Initialize validator with same LLM as extraction
        validator = RuleValidator(llm, language)

        # Run validation
        validation_report = validator.validate_rules(all_generated_rules)

        # Show validation summary
        print(f"\n{validation_report.generate_report()}")

        # Auto-apply import verification improvements
        if validation_report.improvements:
            print(f"\n{'='*80}")
            print(f"APPLYING IMPROVEMENTS")
            print(f"{'='*80}")
            print(f"Auto-applying {len(validation_report.improvements)} import verification improvements...")

            # Apply improvements to all rules
            all_generated_rules = validator.apply_improvements(all_generated_rules, validation_report)

            # Update rules in rules_by_concern dictionary
            # Create a mapping of rule IDs to improved rules
            improved_rules_by_id = {rule.ruleID: rule for rule in all_generated_rules}

            # Replace rules in concern groups with improved versions
            for concern in rules_by_concern:
                updated_rules = []
                for rule in rules_by_concern[concern]:
                    if rule.ruleID in improved_rules_by_id:
                        improved_rule = improved_rules_by_id[rule.ruleID]
                        updated_rules.append(improved_rule)
                    else:
                        updated_rules.append(rule)
                rules_by_concern[concern] = updated_rules

            print(f"✓ Applied improvements to {len(validation_report.improvements)} rules")

    # Write output files (one per concern)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nWriting rules to {output_dir}...")

    written_files = []
    all_rules = []

    for concern, rules in sorted(rules_by_concern.items()):
        # Generate filename: {source}-to-{target}-{concern}.yaml
        if len(rules_by_concern) == 1:
            # Single concern - use simple filename
            concern_output = output_dir / f"{args.source}-to-{args.target}.yaml"
        else:
            # Multiple concerns - add concern suffix
            concern_output = output_dir / f"{args.source}-to-{args.target}-{concern}.yaml"

        # Use the rules from rules_by_concern (which includes any validation improvements)
        # instead of regenerating from patterns (which would lose improvements)

        # Convert rules to dicts for YAML serialization
        rules_data = [rule.model_dump(exclude_none=True) for rule in rules]

        with open(concern_output, 'w') as f:
            yaml.dump(rules_data, f, Dumper=CustomDumper, default_flow_style=False, sort_keys=False, allow_unicode=True)

        written_files.append(str(concern_output))
        all_rules.extend(rules)
        print(f"  ✓ {concern_output.name}: {len(rules)} rules")

    # Create ruleset.yaml metadata file (required by Konveyor analyzer)
    ruleset_file = output_dir / "ruleset.yaml"
    ruleset_data = {
        "name": f"{args.source}/{args.target}",
        "description": f"This ruleset provides guidance for migrating from {args.source} to {args.target}"
    }
    with open(ruleset_file, 'w') as f:
        yaml.dump(ruleset_data, f, Dumper=CustomDumper, default_flow_style=False, sort_keys=False, allow_unicode=True)

    written_files.append(str(ruleset_file))
    print(f"  ✓ {ruleset_file.name}: ruleset metadata")

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

    # Validation Report
    print("\n" + "="*60)
    print("Validation Report")
    print("="*60)
    validation_issues = validate_rules(all_rules)
    if validation_issues:
        for issue_type, warnings in validation_issues.items():
            print(f"\n  ⚠ {issue_type} ({len(warnings)} issues):")
            for warning in warnings[:5]:  # Show first 5
                print(f"    - {warning}")
            if len(warnings) > 5:
                print(f"    ... and {len(warnings) - 5} more")
    else:
        print("  ✓ No validation issues found")

    # Show files created
    print(f"\n" + "="*60)
    print(f"Files Created")
    print("="*60)
    for file in written_files:
        print(f"  {file}")


if __name__ == "__main__":
    main()
