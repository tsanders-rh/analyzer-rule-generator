#!/bin/bash
# Fix Go modules by running go mod tidy on all test data directories

cd /Users/tsanders/Workspace/analyzer-rule-generator/demo-output/go-1.17-to-go-1.18/tests/data

for dir in */; do
  if [ -f "${dir}go.mod" ]; then
    echo "=== Processing $dir ==="
    (cd "$dir" && GOWORK=off go mod tidy 2>&1)
    if [ $? -eq 0 ]; then
      echo "✓ $dir - go.sum created"
    else
      echo "✗ $dir - failed"
    fi
  fi
done
