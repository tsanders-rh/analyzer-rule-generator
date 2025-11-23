#!/usr/bin/env python3
"""Compare two ruleset directories to identify unique and common rules."""

import yaml
from pathlib import Path
from collections import defaultdict

def extract_rules_from_dir(directory):
    """Extract all rules from YAML files in a directory."""
    rules = []
    dir_path = Path(directory)

    for yaml_file in dir_path.glob("*.yaml"):
        if yaml_file.name == "ruleset.yaml":
            continue

        with open(yaml_file, 'r') as f:
            try:
                data = yaml.safe_load(f)
                if data:
                    for rule in data:
                        rules.append({
                            'file': yaml_file.name,
                            'description': rule.get('description', ''),
                            'pattern': rule.get('when', {}),
                            'category': rule.get('category', ''),
                            'effort': rule.get('effort', 0)
                        })
            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")

    return rules

def get_pattern_key(rule):
    """Generate a key for pattern matching."""
    when = rule.get('pattern', {})

    # Extract the actual pattern based on provider type
    if 'nodejs.referenced' in when:
        pattern = when['nodejs.referenced'].get('pattern', '')
    elif 'builtin.filecontent' in when:
        pattern = when['builtin.filecontent'].get('pattern', '')
    else:
        pattern = str(when)

    return (pattern, rule.get('description', '').lower()[:50])

def compare_rulesets(dir1, dir2, name1="Directory 1", name2="Directory 2"):
    """Compare two ruleset directories."""
    print(f"Comparing {name1} vs {name2}\n")

    rules1 = extract_rules_from_dir(dir1)
    rules2 = extract_rules_from_dir(dir2)

    print(f"{name1}: {len(rules1)} rules")
    print(f"{name2}: {len(rules2)} rules")
    print(f"Difference: {len(rules1) - len(rules2)} rules\n")

    # Group by pattern key
    patterns1 = {get_pattern_key(r): r for r in rules1}
    patterns2 = {get_pattern_key(r): r for r in rules2}

    # Find unique patterns
    only_in_1 = set(patterns1.keys()) - set(patterns2.keys())
    only_in_2 = set(patterns2.keys()) - set(patterns1.keys())
    common = set(patterns1.keys()) & set(patterns2.keys())

    print(f"Common patterns: {len(common)}")
    print(f"Only in {name1}: {len(only_in_1)}")
    print(f"Only in {name2}: {len(only_in_2)}\n")

    # Show category distribution
    print(f"\n=== Category Distribution ===")
    print(f"\n{name1}:")
    cat1 = defaultdict(int)
    for r in rules1:
        cat1[r['category']] += 1
    for cat, count in sorted(cat1.items()):
        print(f"  {cat}: {count}")

    print(f"\n{name2}:")
    cat2 = defaultdict(int)
    for r in rules2:
        cat2[r['category']] += 1
    for cat, count in sorted(cat2.items()):
        print(f"  {cat}: {count}")

    # Show effort distribution
    print(f"\n=== Effort Distribution ===")
    print(f"\n{name1}:")
    eff1 = defaultdict(int)
    for r in rules1:
        eff1[r['effort']] += 1
    for eff, count in sorted(eff1.items()):
        print(f"  {eff}: {count}")

    print(f"\n{name2}:")
    eff2 = defaultdict(int)
    for r in rules2:
        eff2[r['effort']] += 1
    for eff, count in sorted(eff2.items()):
        print(f"  {eff}: {count}")

    # Show sample unique rules
    print(f"\n=== Sample Rules Only in {name1} (first 10) ===")
    for i, key in enumerate(sorted(only_in_1)[:10]):
        rule = patterns1[key]
        print(f"{i+1}. [{rule['file']}] {rule['description'][:80]}")

    print(f"\n=== Sample Rules Only in {name2} (first 10) ===")
    for i, key in enumerate(sorted(only_in_2)[:10]):
        rule = patterns2[key]
        print(f"{i+1}. [{rule['file']}] {rule['description'][:80]}")

if __name__ == "__main__":
    compare_rulesets(
        "examples/output/patternfly-v6/new/",
        "/tmp/patternfly-cleaned/",
        "New Output",
        "Cleaned Output"
    )
