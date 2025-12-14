#!/bin/bash
# Batch classify all rulesets in a directory

set -e

RULESET_DIR="${1:-examples/output}"
DRY_RUN="${2:-false}"

if [ "$DRY_RUN" = "true" ]; then
  DRY_RUN_FLAG="--dry-run"
else
  DRY_RUN_FLAG=""
fi

echo "Classifying rulesets in: $RULESET_DIR"
echo "Dry run: $DRY_RUN"
echo ""

# Find all YAML files
find "$RULESET_DIR" -name "*.yaml" -o -name "*.yml" | while read -r ruleset; do
  echo "Processing: $ruleset"
  python scripts/classify_existing_rules.py \
    --ruleset "$ruleset" \
    $DRY_RUN_FLAG
  echo ""
done

echo "✓ Batch classification complete"
