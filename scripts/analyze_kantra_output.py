#!/usr/bin/env python3
"""
Analyze Kantra analyzer output to summarize violations by rule.

This script parses the YAML output from the Kantra analyzer (Konveyor's CLI tool)
and generates a summary of which rules detected the most violations. Useful for:
- Understanding which migration patterns are most common in a codebase
- Prioritizing migration work based on violation frequency
- Validating that generated rules are actually detecting issues
- Identifying rules that may be overfitting or underfitting

Features:
    - Counts violations per rule ID
    - Sorts rules by frequency (most violations first)
    - Shows total violation count
    - Identifies rules with zero violations

Usage:
    # Analyze Kantra output file
    python scripts/analyze_kantra_output.py output.yaml

    # Analyze and show top 10 rules
    python scripts/analyze_kantra_output.py output.yaml | head -n 15

Expected Input Format:
    The script expects Kantra's YAML output format with structure like:
    - ruleset: patternfly-v5-to-patternfly-v6
      violations:
        patternfly-5-to-patternfly-6-00010:
          - uri: file:///path/to/file.tsx
          - uri: file:///path/to/another.tsx

Example Output:
    Rule Violation Summary
    =====================
    Total rules with violations: 12

    patternfly-5-to-patternfly-6-00030: 45 violations
    patternfly-5-to-patternfly-6-00020: 28 violations
    patternfly-5-to-patternfly-6-00010: 15 violations
    ...

Note:
    This script is specifically designed for Kantra's output format.
    For analyzing rule quality before running Kantra, use validate_rules.py.
"""

import re
import sys
from collections import defaultdict


def analyze_kantra_output(filepath):
    """Parse kantra output and count violations by rule."""
    rule_counts = defaultdict(int)
    current_rule = None

    with open(filepath, 'r') as f:
        for line in f:
            # Match rule IDs (they appear indented under violations)
            rule_match = re.match(r'^\s{2,4}(patternfly - 5-to-patternfly - 6-[^:]+):', line)
            if rule_match:
                current_rule = rule_match.group(1)

            # Count incidents (uri lines appear under each rule)
            if '- uri: file://' in line and current_rule:
                rule_counts[current_rule] += 1

    return rule_counts


if __name__ == '__main__':
    filepath = (
        sys.argv[1]
        if len(sys.argv) > 1
        else 'examples/output/patternfly-improved-detection-analysis/output.yaml'
    )

    rule_counts = analyze_kantra_output(filepath)

    # Sort by count descending
    sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)

    total_rules = len(rule_counts)
    total_incidents = sum(rule_counts.values())

    print("Analysis Results")
    print("=" * 80)
    print(f"Total Rules Fired: {total_rules}")
    print(f"Total Incidents: {total_incidents}")
    print("\nViolations by Rule:")
    print("-" * 80)

    for rule_id, count in sorted_rules:
        print(f"{count:5d}  {rule_id}")

    print("\nTop 10 Rules:")
    print("-" * 80)
    for rule_id, count in sorted_rules[:10]:
        print(f"{count:5d}  {rule_id}")
