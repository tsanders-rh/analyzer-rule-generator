# Demo Guide for Analyzer Rule Generator

This guide helps you prepare and deliver effective demonstrations of the analyzer-rule-generator tool.

## Quick Start

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Run the complete demo
./scripts/demo.sh all
```

**Note**: The demo script automatically activates the virtual environment if found, but you can also activate it manually first.

## Demo Script Overview

The `scripts/demo.sh` script provides an interactive walkthrough of the complete rule generation workflow:

1. **Generate Rules** - Extract migration rules from a guide using AI
2. **Generate Tests** - Create test applications automatically
3. **Validate** - Run Kantra analysis (if installed)
4. **Show Next Steps** - Explain submission process

## Preparation Checklist

### Before Your Demo

- [ ] **Activate Virtual Environment**: `source venv/bin/activate`
- [ ] **Set API Key**: Export `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- [ ] **Test the Demo**: Run `./scripts/demo.sh all` once to verify it works
- [ ] **Clear Previous Output**: Run `./scripts/demo.sh clean` to start fresh
- [ ] **Install Kantra** (optional): For step 3 validation
- [ ] **Prepare Slides**: Use `docs/presentation-outline.md`
- [ ] **Check Internet**: Script fetches live migration guides

### Terminal Setup

For better visibility during live demos:

```bash
# Increase terminal font size
# MacOS: Cmd + (plus)
# Linux: Ctrl + Shift + (plus)

# Use a light theme for projectors
# Or ensure high contrast if using dark theme

# Enable color output
export TERM=xterm-256color
```

## Demo Modes

### Mode 1: Step-by-Step (Recommended for Live Demos)

Run each step individually with pauses for explanation:

```bash
# Step 1: Explain what we're doing, then run
./scripts/demo.sh 1

# While it runs, explain:
# - Fetching migration guide
# - LLM extracting patterns
# - Generating YAML rules

# Step 1b (OPTIONAL): Validate generated rules
./scripts/demo.sh 1b

# Explain rule validation:
# - Syntactic checks (fast, free)
# - Optional semantic validation (AI-powered)

# Step 2: Show generated rules, then run
./scripts/demo.sh 2

# Explain test generation while it runs

# Step 3: Validate (if kantra installed)
./scripts/demo.sh 3

# Step 4: Show submission process
./scripts/demo.sh 4
```

**Timing**: ~15-20 minutes total
- Step 1: 5-8 minutes
- Step 1b: 1-2 minutes (optional)
- Step 2: 5-8 minutes
- Step 3: 2-3 minutes (if kantra installed)
- Step 4: 2 minutes

### Mode 2: Automated Run (For Recorded Demos)

Run all steps without pauses:

```bash
INTERACTIVE=no ./scripts/demo.sh all
```

**Timing**: ~10-15 minutes (depending on API response times)

### Mode 3: Pre-Generated (For Quick Overviews)

Generate everything beforehand, then show results:

```bash
# Before the demo
INTERACTIVE=no ./scripts/demo.sh all

# During the demo
# Show files in demo-output/ directory
# Walk through the generated rules
# Explain the workflow
```

**Timing**: ~5 minutes

## What to Highlight

### Step 1: Rule Generation

**Key Points**:
- "We're using AI to read a real migration guide"
- "The LLM extracts patterns, FQNs, and complexity automatically"
- "Rules are generated in Konveyor analyzer-lsp format"

**Show**:
- The migration guide URL
- Sample generated rule (the script shows the first one)
- Migration complexity classification
- Multiple rule files (grouped by concern)

**Expected Output**:
```
✓ Rules generated successfully!
Generated files:
  - accessibility.yaml: 5 rules
  - components.yaml: 12 rules
  - props.yaml: 15 rules
```

### Step 1b: Rule Validation (Optional)

**Key Points**:
- "Quality checks ensure rules are well-formed"
- "Syntactic validation is instant and free"
- "Optional semantic validation uses AI to verify description/pattern alignment"

**Show**:
- Syntactic validation output (required fields, effort scores)
- Optional: Semantic validation checking for mismatches
- Green checkmarks for clean rules

**Expected Output**:
```
✓ Running syntactic validation (fast, free)...

Validation Summary:
  Issues:   0
  Warnings: 0

✅ All rules validated successfully!
```

**Why This Matters**:
- Catches common issues before submission
- Prevents description/pattern mismatches
- Ensures rules meet quality standards

### Step 2: Test Generation

**Key Points**:
- "AI generates realistic test applications"
- "Tests contain actual violations for each rule"
- "Ready for automated validation"

**Show**:
- Test directory structure
- Sample test configuration (.test.yaml)
- Generated source code with violations

**Expected Output**:
```
✓ Test data generated successfully!
Generated structure:
  tests/
    data/
      patternfly-v6/
        src/
          App.tsx
        package.json
```

### Step 3: Validation (Optional)

**Key Points**:
- "Kantra validates our rules work correctly"
- "Confirms violations are detected"
- "Ready for submission"

**Show**:
- Kantra command
- Analysis output
- Violation counts

**Expected Output**:
```
✓ Analysis completed!
Violations found: 15
```

### Step 4: Submission

**Key Points**:
- "Everything needed for a konveyor/rulesets PR"
- "Complete with rules, tests, and validation"
- "From guide to submission in ~15 minutes"

## Customizing the Demo

### Use a Different Migration Guide

The demo script includes 4 pre-configured options. Edit `scripts/demo.sh` and uncomment your choice:

**Option 1: React 17→18 (SMALL - ~5 min) ⭐ Recommended for quick demos**
```bash
GUIDE_URL="https://react.dev/blog/2022/03/08/react-18-upgrade-guide"
SOURCE="react-17"
TARGET="react-18"
FOLLOW_LINKS_FLAG=""  # Single page guide
```

**Option 2: Go 1.17→1.18 (SMALL - ~5-8 min) - Go generics migration**
```bash
GUIDE_URL="https://go.dev/blog/go1.18"
SOURCE="go-1.17"
TARGET="go-1.18"
FOLLOW_LINKS_FLAG=""  # Single page guide
```

**Option 3: Spring Boot 2→3 (MEDIUM - ~8-10 min)**
```bash
GUIDE_URL="https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide"
SOURCE="spring-boot-2"
TARGET="spring-boot-3"
FOLLOW_LINKS_FLAG=""  # Single page guide
```

**Option 4: PatternFly v5→v6 (LARGE - ~15-20 min, comprehensive) - Default**
```bash
GUIDE_URL="https://www.patternfly.org/get-started/upgrade/"
SOURCE="patternfly-v5"
TARGET="patternfly-v6"
FOLLOW_LINKS_FLAG="--follow-links --max-depth 1"
```

To switch, simply comment out the current option and uncomment your preferred one in `scripts/demo.sh`.

### Change LLM Provider

The script auto-detects based on your API key. To force a specific provider:

```bash
PROVIDER="openai" ./scripts/demo.sh all
```

### Skip Kantra Validation

If you don't have Kantra installed:

```bash
./scripts/demo.sh 1  # Generate rules
./scripts/demo.sh 2  # Generate tests
./scripts/demo.sh 4  # Show next steps (skips step 3)
```

## Troubleshooting

### "No API key found"

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key"

# Verify it's set
echo $ANTHROPIC_API_KEY
```

### "Rules generation taking too long"

- Normal for large guides (5-10 minutes)
- Consider using a smaller guide for demos
- Or pre-generate and show results

### "API temporarily unavailable" warning during generation

- This is normal - transient API errors happen occasionally
- The tool automatically skips the failed chunk and continues
- You'll still get rules from successful chunks
- **What to say**: "The tool handles API hiccups gracefully - it just skips that chunk and continues. This is exactly the kind of resilience you want in automation."
- Consider it a feature demonstration!

### "Test generation failed"

- Check API rate limits
- Increase delay: edit `--delay` in demo.sh
- Verify rule file format is correct

### "Kantra not found"

- Optional step - skip with steps 1, 2, 4
- Or install: https://github.com/konveyor/kantra

## Demo Script Variations

### Quick 5-Minute Demo

```bash
# Pre-generate everything
INTERACTIVE=no ./scripts/demo.sh all

# During demo
cd demo-output/rules
ls -la  # Show generated rules
cat accessibility.yaml | head -30  # Show sample rule
cd ../tests
tree  # Show test structure
```

### Deep Technical Demo (30 minutes)

```bash
# Run step by step with detailed explanations

./scripts/demo.sh 1
# - Explain LLM prompt engineering
# - Show rule schema details
# - Discuss provider selection (java vs nodejs vs builtin)

./scripts/demo.sh 2
# - Explain test generation approach
# - Show generated code in detail
# - Discuss validation strategy

./scripts/demo.sh 3
# - Walk through Kantra analysis
# - Show incident details
# - Explain how rules match code

./scripts/demo.sh 4
# - Detailed submission workflow
# - Integration with go-konveyor-tests
# - CI/CD implications
```

### Comparison Demo (Show Before/After)

```bash
# Before: Show manual rule authoring
# - Display analyzer-lsp docs
# - Show hand-written rule example
# - Explain complexity

# After: Run automated demo
./scripts/demo.sh all
# - Same result in minutes
# - Higher consistency
# - Includes tests
```

## FAQ During Demos

**Q: "How accurate are the generated rules?"**
A: Very accurate for well-documented migrations. The script shows validation with real test apps. Always review before production use.

**Q: "What if the LLM makes mistakes?"**
A: Rules are YAML - easy to edit. Test generation catches issues. We recommend reviewing all generated rules.

**Q: "How much does it cost?"**
A: Typically $0.10-$2.00 per migration guide depending on size and provider. Much cheaper than developer time.

**Q: "Can it handle private/internal guides?"**
A: Yes! Works with local files: `--guide /path/to/guide.md`

**Q: "What languages are supported?"**
A: Java, TypeScript/React, Go, Python, CSS. More coming.

**Q: "How long does it take?"**
A: 5-15 minutes for most migration guides. Large guides with many sub-pages may take longer.

## After the Demo

### Provide Resources

Share these with attendees:

- **Repository**: https://github.com/tsanders-rh/analyzer-rule-generator
- **Quick Start**: `QUICKSTART.md`
- **Documentation**: `docs/guides/konveyor-submission-guide.md`
- **Demo Output**: Share the `demo-output/` directory

### Cleanup

```bash
# Remove demo files
./scripts/demo.sh clean
```

### Follow Up

Encourage users to:
1. Try it with their own migration guides
2. Submit generated rules to konveyor/rulesets
3. Report issues or suggestions
4. Contribute improvements

## Tips for Success

1. **Practice First**: Run the demo 2-3 times before presenting
2. **Have Backup**: Pre-generate output in case of network issues
3. **Manage Time**: Know which steps to skip for time constraints
4. **Engage Audience**: Ask questions between steps
5. **Show Real Value**: Emphasize time savings and accessibility
6. **Be Honest**: Acknowledge that manual review is still recommended
7. **Invite Participation**: Let attendees suggest migration guides to try

## Example Narrative

Here's a sample script for narrating the demo:

### Introduction (1 min)
"Today I'm going to show you how we can go from a migration guide to production-ready Konveyor rules in under 15 minutes, using AI. Let me show you..."

### Step 1 (5-8 min)
"We start with any migration guide - I'm using PatternFly's v6 upgrade guide. Watch as the tool fetches the documentation, uses an LLM to extract migration patterns, and generates analyzer rules. [Run step 1]

"While this runs, the LLM is reading through the documentation, identifying patterns like deprecated props, renamed components, and API changes. It's also classifying complexity - is this a trivial find/replace or does it need expert review?

"And we're done! Look at this - we've generated multiple rule files, grouped by concern. Here's a sample rule... notice it has the pattern, the migration message, effort scoring, and even links back to the documentation. All generated automatically."

### Step 2 (5-8 min)
"Now the magic happens - we need to test these rules. Traditionally, you'd manually create test applications. Watch this... [Run step 2]

"The AI is now generating a complete TypeScript application that violates our rules. It's creating realistic code based on the migration patterns.

"Perfect! We now have a full test application with package.json, source files, everything. And it's configured to work with Kantra for validation."

### Step 3 (2-3 min)
"Let's prove the rules work. [Run step 3 if available]

"Kantra found violations! Our AI-generated rules successfully detected the migration issues in our AI-generated test application. This is ready for submission."

### Step 4 (2 min)
"So what do we have? In about 15 minutes, we went from a migration guide URL to a complete, tested ruleset ready for konveyor/rulesets. This is work that used to take days or weeks.

"Anyone can do this - you don't need to be a Konveyor expert. You just need a migration guide and an API key. Questions?"

---

Ready to demo! Start with: `./scripts/demo.sh all`
