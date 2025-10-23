# Testing Package for TypeScript/React Support PR

## Overview

This document provides test rules, test applications, and instructions for reviewers to verify the PR fixes work correctly.

## Quick Test (5 minutes)

For reviewers who want to quickly verify the fixes:

### Prerequisites
```bash
# Build the analyzer with the PR changes
make build

# Install TypeScript language server (if not already installed)
npm install -g typescript-language-server typescript
```

### Test 1: Verify .tsx File Support (Fix 1a)

**Test Rule:** `test-tsx-support.yaml`
```yaml
- ruleID: test-tsx-support-00000
  description: Test that .tsx files are scanned
  when:
    builtin.filecontent:
      pattern: "import.*React"
      filePattern: "*.tsx"
  message: Found React import in .tsx file
  effort: 1
  category: potential
```

**Test Application:** Create a simple React component
```bash
mkdir -p /tmp/test-tsx-app/src
cat > /tmp/test-tsx-app/src/Component.tsx <<'EOF'
import React from 'react';

export const MyComponent: React.FC = () => {
  return <div>Hello World</div>;
};
EOF
```

**Provider Settings:** `/tmp/builtin-provider-settings.json`
```json
[
  {
    "name": "builtin",
    "binaryPath": "",
    "initConfig": [
      {
        "location": "/tmp/test-tsx-app",
        "analysisMode": "full"
      }
    ]
  }
]
```

**Run Test:**
```bash
./konveyor-analyzer \
  --provider-settings=/tmp/builtin-provider-settings.json \
  --rules=/tmp/test-tsx-support.yaml \
  --output-file=/tmp/test-output.yaml \
  --verbose=1

# Verify it found the .tsx file
grep -q "violations:" /tmp/test-output.yaml && echo "✅ PASS: .tsx files detected" || echo "❌ FAIL: .tsx files not detected"
```

**Expected:** Should find violations in `Component.tsx`

### Test 2: Verify node_modules is Skipped (Fix 1b)

**Setup:**
```bash
# Add a node_modules directory with many files
mkdir -p /tmp/test-tsx-app/node_modules/react
echo "export const React = {};" > /tmp/test-tsx-app/node_modules/react/index.js

# Create 100 dummy files to simulate a real node_modules
for i in {1..100}; do
  echo "export const lib$i = {};" > /tmp/test-tsx-app/node_modules/lib$i.js
done
```

**Run Test:**
```bash
# Time the analysis
time ./konveyor-analyzer \
  --provider-settings=/tmp/builtin-provider-settings.json \
  --rules=/tmp/test-tsx-support.yaml \
  --output-file=/tmp/test-output.yaml \
  --verbose=1
```

**Expected:**
- Should complete in < 10 seconds
- Should NOT scan node_modules files
- Output should only show violations in source files

### Test 3: Verify Brace Expansion Works (Fix 2)

**Test Rule:** `test-brace-expansion.yaml`
```yaml
- ruleID: test-brace-expansion-00000
  description: Test brace expansion with multiple extensions
  when:
    builtin.filecontent:
      pattern: "React"
      filePattern: "*.{ts,tsx,js,jsx}"
  message: Found React reference
  effort: 1
  category: potential
```

**Setup:**
```bash
# Create files with different extensions
echo "import React from 'react';" > /tmp/test-tsx-app/src/test.ts
echo "import React from 'react';" > /tmp/test-tsx-app/src/test.tsx
echo "import React from 'react';" > /tmp/test-tsx-app/src/test.js
echo "import React from 'react';" > /tmp/test-tsx-app/src/test.jsx
```

**Run Test:**
```bash
./konveyor-analyzer \
  --provider-settings=/tmp/builtin-provider-settings.json \
  --rules=/tmp/test-brace-expansion.yaml \
  --output-file=/tmp/test-output.yaml \
  --verbose=1

# Count violations (should find 5: Component.tsx + 4 test files)
grep -c "uri: file://" /tmp/test-output.yaml
```

**Expected:** Should find violations in ALL file types: `.ts`, `.tsx`, `.js`, `.jsx`

---

## Comprehensive Test (15 minutes)

For more thorough testing with real-world scenarios.

### Test Application: React TypeScript Project

**Location:** Can be provided as a GitHub repository or tarball

**Structure:**
```
test-react-app/
├── src/
│   ├── Component.tsx          # React component
│   ├── utils.ts              # TypeScript utility
│   ├── legacy.jsx            # Legacy JSX component
│   └── test.css              # CSS file
├── node_modules/             # Dependencies (should be skipped)
│   └── react/
├── package.json
└── tsconfig.json
```

**Download/Clone:**
```bash
# Option 1: Clone from repository (if you create one)
git clone https://github.com/tsanders-rh/analyzer-test-tsx-app.git /tmp/test-react-app

# Option 2: Use the example from analyzer-rule-generator
cp -r /Users/tsanders/Workspace/analyzer-rule-generator/examples/test-apps/typescript/test-react-app /tmp/test-react-app
```

### Test Rules: PatternFly Migration Scenarios

**File:** `patternfly-test-rules.yaml`

```yaml
# Test 1: TypeScript provider - Find component references
- ruleID: patternfly-test-00000
  description: Find Chip component usage (PatternFly v5 → v6)
  when:
    typescript.referenced:
      pattern: "Chip"
  message: Chip component renamed to Label in PatternFly v6
  effort: 5
  category: potential

# Test 2: Builtin provider with single extension
- ruleID: patternfly-test-00010
  description: Find deprecated lifecycle methods
  when:
    builtin.filecontent:
      pattern: "componentWillMount"
      filePattern: "*.tsx"
  message: componentWillMount is deprecated
  effort: 3
  category: mandatory

# Test 3: Builtin provider with brace expansion
- ruleID: patternfly-test-00020
  description: Find React.FC usage (all TS/JS files)
  when:
    builtin.filecontent:
      pattern: "React\\.FC"
      filePattern: "*.{ts,tsx,js,jsx}"
  message: React.FC is no longer recommended
  effort: 1
  category: potential

# Test 4: Brace expansion with CSS files
- ruleID: patternfly-test-00030
  description: Find old PatternFly CSS variables
  when:
    builtin.filecontent:
      pattern: "--pf-v5-global--.*"
      filePattern: "*.{css,scss,js,jsx,ts,tsx}"
  message: PatternFly v5 CSS variables need migration
  effort: 3
  category: potential
```

### Provider Settings for TypeScript Provider

**File:** `typescript-provider-settings.json`

```json
[
  {
    "name": "typescript",
    "binaryPath": "/usr/local/bin/generic-external-provider",
    "initConfig": [
      {
        "location": "/tmp/test-react-app",
        "analysisMode": "full",
        "providerSpecificConfig": {
          "lspServerName": "nodejs",
          "lspServerPath": "/opt/homebrew/bin/typescript-language-server",
          "lspServerArgs": ["--stdio"],
          "workspaceFolders": ["file:///tmp/test-react-app"],
          "dependencyFolders": []
        }
      }
    ]
  }
]
```

**Note:** Adjust paths based on your system:
- `lspServerPath`: Use `which typescript-language-server` to find the correct path
- On Linux: Usually `/usr/local/bin/typescript-language-server` or `/usr/bin/typescript-language-server`
- On macOS (Homebrew): Usually `/opt/homebrew/bin/typescript-language-server`

### Run Comprehensive Tests

```bash
# Test with builtin provider only (tests brace expansion + .tsx support)
./konveyor-analyzer \
  --provider-settings=/tmp/builtin-provider-settings.json \
  --rules=/tmp/patternfly-test-rules.yaml \
  --output-file=/tmp/builtin-output.yaml \
  --verbose=1

# Test with TypeScript provider (tests typescript.referenced + .tsx support)
./konveyor-analyzer \
  --provider-settings=/tmp/typescript-provider-settings.json \
  --rules=/tmp/patternfly-test-rules.yaml \
  --output-file=/tmp/typescript-output.yaml \
  --verbose=1
```

### Expected Results

**Builtin Provider Test:**
- ✅ Rule `patternfly-test-00010`: Should find violations in `.tsx` files
- ✅ Rule `patternfly-test-00020`: Should find violations in `.tsx`, `.ts`, `.jsx`, `.js` files
- ✅ Rule `patternfly-test-00030`: Should find violations in `.css` files
- ✅ Analysis completes in < 10 seconds
- ✅ Does NOT scan node_modules (check verbose output)

**TypeScript Provider Test:**
- ✅ Rule `patternfly-test-00000`: Should find component references in `.tsx` files
- ✅ Analysis completes in < 10 seconds
- ✅ Only scans source files (not node_modules)

---

## Performance Benchmark

### Before PR (Expected to Fail/Timeout)

```bash
# Checkout main branch
git checkout main
make build

# Run same test - should timeout or take 15+ minutes
time ./konveyor-analyzer \
  --provider-settings=/tmp/builtin-provider-settings.json \
  --rules=/tmp/test-tsx-support.yaml \
  --output-file=/tmp/before-output.yaml \
  --verbose=4 2>&1 | tee /tmp/before-test.log
```

**Expected Issues:**
- ❌ No `.tsx` files found (0 violations)
- ❌ Scans node_modules (see verbose logs)
- ❌ Takes 15+ minutes or times out

### After PR (Should Pass Quickly)

```bash
# Checkout PR branch
git checkout fix/typescript-react-support
make build

# Run same test - should complete quickly
time ./konveyor-analyzer \
  --provider-settings=/tmp/builtin-provider-settings.json \
  --rules=/tmp/test-tsx-support.yaml \
  --output-file=/tmp/after-output.yaml \
  --verbose=4 2>&1 | tee /tmp/after-test.log
```

**Expected Results:**
- ✅ Finds `.tsx` files (violations detected)
- ✅ Skips node_modules (check logs for "SkipDir")
- ✅ Completes in < 10 seconds

### Compare Results

```bash
echo "Before PR:"
wc -l /tmp/before-output.yaml
grep -c "violations:" /tmp/before-output.yaml || echo "0 violations"

echo "After PR:"
wc -l /tmp/after-output.yaml
grep -c "violations:" /tmp/after-output.yaml
```

---

## Test Files to Include in PR

You can create a `test/` directory in the PR with these files:

```
test/
├── README.md                           # This document
├── test-tsx-support.yaml              # Test .tsx file detection
├── test-brace-expansion.yaml          # Test brace expansion
├── patternfly-test-rules.yaml         # Real-world scenario
├── builtin-provider-settings.json     # Builtin provider config
├── typescript-provider-settings.json  # TypeScript provider config
└── test-app/                          # Minimal test application
    ├── src/
    │   ├── Component.tsx
    │   ├── test.ts
    │   ├── test.tsx
    │   ├── test.js
    │   ├── test.jsx
    │   └── test.css
    └── package.json
```

---

## CI/CD Integration

If the project has CI/CD, consider adding these as automated tests:

```yaml
# .github/workflows/typescript-provider-test.yml
name: TypeScript Provider Tests

on: [pull_request]

jobs:
  test-typescript-provider:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install TypeScript Language Server
        run: npm install -g typescript-language-server typescript

      - name: Build analyzer
        run: make build

      - name: Run .tsx support test
        run: |
          ./konveyor-analyzer \
            --provider-settings=test/builtin-provider-settings.json \
            --rules=test/test-tsx-support.yaml \
            --output-file=/tmp/output.yaml

          # Verify violations were found
          grep -q "violations:" /tmp/output.yaml

      - name: Run brace expansion test
        run: |
          ./konveyor-analyzer \
            --provider-settings=test/builtin-provider-settings.json \
            --rules=test/test-brace-expansion.yaml \
            --output-file=/tmp/output.yaml

          # Verify pattern matched multiple file types
          test $(grep -c "uri: file://" /tmp/output.yaml) -ge 4
```

---

## Summary Checklist for Reviewers

- [ ] Build succeeds with `make build`
- [ ] `.tsx` files are detected by the provider
- [ ] `.jsx` files are detected by the provider
- [ ] `node_modules` directory is skipped
- [ ] Analysis completes in < 10 seconds (vs 15+ minutes before)
- [ ] Brace expansion patterns work: `*.{ts,tsx}`
- [ ] Brace expansion patterns work: `*.{css,scss}`
- [ ] Backward compatible: existing `*.tsx` patterns still work
- [ ] TypeScript provider rules work with `.tsx` files
- [ ] No regressions in existing functionality

---

## Contact

If you have questions about testing, please comment on the PR or reach out to:
- GitHub: @tsanders-rh
- Email: [your email]
