#!/usr/bin/env python3
"""
Analyze kantra output to summarize violations by rule.
"""

import sys
import re
from collections import defaultdict

def analyze_kantra_output(filepath):
    """Parse kantra output and count violations by rule."""
    rule_counts = defaultdict(int)
    current_rule = None

    with open(filepath, 'r') as f:
        for line in f:
            # Match rule IDs (they appear indented under violations)
            rule_match = re.match(r'^\s{2,4}(patternfly-5-to-patternfly-6-[^:]+):', line)
            if rule_match:
                current_rule = rule_match.group(1)

            # Count incidents (uri lines appear under each rule)
            if '- uri: file://' in line and current_rule:
                rule_counts[current_rule] += 1

    return rule_counts

if __name__ == '__main__':
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'examples/output/patternfly-improved-detection-analysis/output.yaml'

    rule_counts = analyze_kantra_output(filepath)

    # Sort by count descending
    sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)

    total_rules = len(rule_counts)
    total_incidents = sum(rule_counts.values())

    print(f"Analysis Results")
    print(f"=" * 80)
    print(f"Total Rules Fired: {total_rules}")
    print(f"Total Incidents: {total_incidents}")
    print(f"\nViolations by Rule:")
    print(f"-" * 80)

    for rule_id, count in sorted_rules:
        print(f"{count:5d}  {rule_id}")

    print(f"\nTop 10 Rules:")
    print(f"-" * 80)
    for rule_id, count in sorted_rules[:10]:
        print(f"{count:5d}  {rule_id}")
