# Demo Cheatsheet - Quick Reference

Keep this open during your demo for quick command reference.

## Pre-Demo Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Test run (optional)
./scripts/demo.sh all

# Clean previous output
./scripts/demo.sh clean
```

## Demo Commands

### Full Automated Demo
```bash
./scripts/demo.sh all
```

### Step-by-Step (Recommended)
```bash
./scripts/demo.sh 1  # Generate rules (~5-8 min)
./scripts/demo.sh 2  # Generate tests (~5-8 min)
./scripts/demo.sh 3  # Validate with Kantra (~2-3 min)
./scripts/demo.sh 4  # Show next steps (~2 min)
```

### Skip Pauses (For Recording)
```bash
INTERACTIVE=no ./scripts/demo.sh all
```

## What to Say During Each Step

### Step 1: Generate Rules
- "Fetching real migration guide from PatternFly"
- "LLM extracts patterns automatically"
- "Generates Konveyor analyzer rules in seconds"
- **Point out**: Multiple rule files, complexity classification, sample rule

### Step 2: Generate Tests
- "AI creates test applications with violations"
- "No manual test code needed"
- "Ready for automated validation"
- **Point out**: Directory structure, package.json, .test.yaml config

### Step 3: Validate
- "Kantra proves our rules work"
- "Finds violations in generated test app"
- "Ready for production use"
- **Point out**: Violation count, analysis output

### Step 4: Submission
- "Complete workflow in ~15 minutes"
- "Everything ready for konveyor/rulesets PR"
- "Rules + tests + validation"

## Key Messages

1. **Time Savings**: "Days of manual work → 15 minutes"
2. **Accessibility**: "Anyone can contribute, no expert knowledge needed"
3. **Quality**: "AI-generated + automated testing = reliable"
4. **Integration**: "Works seamlessly with Konveyor ecosystem"

## Show These Files

```bash
# After step 1
cat demo-output/rules/accessibility.yaml | head -30

# After step 2
tree demo-output/tests
cat demo-output/tests/*.test.yaml

# After step 3
cat demo-output/analysis-output.yaml | head -40
```

## Backup Commands (If Demo Fails)

### Network Issues
```bash
# Use pre-generated example
cd examples/output/patternfly-v6
ls -la
cat accessibility.yaml
```

### API Rate Limits
"This is actually a good thing - means the tool is being used! In practice, we add delays between requests."

### Kantra Not Installed
"Step 3 is optional - you can also validate by manual review or in CI/CD"

## Time Management

**5-minute version**: Pre-generate, show results only
**15-minute version**: Steps 1, 2, 4 (skip Kantra)
**30-minute version**: All steps + detailed explanations

## Expected Questions

**Q: "How accurate is it?"**
A: "Very accurate. We validate with real tests, and recommend review before production."

**Q: "What does it cost?"**
A: "$0.10-$2 per guide. Far cheaper than developer time."

**Q: "Can I use my own guides?"**
A: "Yes! Local files or private URLs work."

**Q: "What languages?"**
A: "Java, TypeScript/React, Go, Python, CSS. More coming."

## Cleanup

```bash
# Remove demo files
./scripts/demo.sh clean
```

## Emergency Fallback

If everything fails, show the README and examples:

```bash
# Show pre-existing examples
cd examples/output
ls -la
cat patternfly-v6/*/accessibility.yaml
```

## Quick Guide Options

**3 pre-configured options in `scripts/demo.sh`:**

1. **React 17→18** (SMALL ~5 min) ⭐ Best for quick demos
2. **Spring Boot 2→3** (MEDIUM ~8-10 min)
3. **PatternFly v5→v6** (LARGE ~15-20 min) - Default

**To switch**: Edit `scripts/demo.sh` and uncomment your choice

---

**Remember**: Pause between steps, engage the audience, show enthusiasm!
