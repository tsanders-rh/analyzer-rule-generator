# Demo Recording Cheat Sheet

Quick reference for live demo recording.

## Setup Checklist

- [ ] Clear terminal (`clear`)
- [ ] cd to project root
- [ ] Increase font size (14-16pt)
- [ ] Start Claude Code session
- [ ] Have this cheatsheet open on second monitor

## Demo Commands (Copy-Paste Ready)

### Option 1: Local Demo Guide (Fast - Recommended)
```
konveyor-rules
```

Then paste:
```
Guide: examples/demo-guide-react18.md
Source: react-17
Target: react-18
Output: demo-output/react-18/
Provider: anthropic
```

**Expected time**: ~90 seconds
**Expected rules**: ~15-20 rules

---

### Option 2: Real React Guide (Impressive)
```
konveyor-rules
```

Then paste:
```
Generate rules from https://react.dev/blog/2022/03/08/react-18-upgrade-guide for react-17 to react-18 migration, save to demo-output/react-18/
```

**Expected time**: ~2-3 minutes
**Expected rules**: ~18-25 rules

---

### Option 3: PatternFly (Show Chunking)
```
konveyor-rules
```

Then paste:
```
Guide: https://www.patternfly.org/get-started/upgrade
Source: patternfly-v5
Target: patternfly-v6
Output: demo-output/patternfly/
Provider: anthropic
```

**Expected time**: ~22 minutes (DON'T use for short demo!)
**Expected rules**: ~139 rules

---

## Key Talking Points

### When extraction starts:
"Notice the three-stage process: ingestion, extraction, and rule generation"

### When "Decision:" lines appear:
"These are automatic quality improvements happening in real-time"

### When chunking happens:
"The system automatically splits large guides into manageable chunks"

### When rules are generated:
"Each rule includes detection patterns, effort estimates, and migration guidance"

## What to Highlight

1. ✅ **Zero configuration** - Just provide URL and framework names
2. ✅ **Automatic quality** - Shows Decision: lines
3. ✅ **Professional output** - Well-formatted YAML rules
4. ✅ **Production ready** - Rules work with Konveyor analyzer immediately

## Commands to Show Results

### View rule count:
```bash
find demo-output/react-18 -name "*.yaml" | wc -l
```

### View a sample rule:
```bash
cat demo-output/react-18/react-17-to-react-18-root-api.yaml | head -30
```

### View all rule files:
```bash
ls -lh demo-output/react-18/
```

### Quick stats:
```bash
grep -r "ruleID:" demo-output/react-18/ | wc -l
```

## If Something Goes Wrong

### Generation takes too long:
- Ctrl+C and restart with Option 1 (local guide)
- Or pause recording and edit out the wait

### API error:
- Check API key: `echo $ANTHROPIC_API_KEY`
- Restart Claude Code session
- Re-record this section

### Skill not found:
- Restart Claude Code in project directory
- Check `.claude/skills/konveyor-rules/SKILL.md` exists

## Post-Demo Commands

### Clean up demo output:
```bash
rm -rf demo-output/
```

### View logs:
```bash
tail -100 /tmp/patternfly_generation.log
```

## Time Markers (for editing)

- 0:00 - Introduction
- 0:15 - Skill invocation
- 0:25 - Provide parameters
- 0:35 - Ingestion phase
- 0:45 - Extraction phase (highlight Decision: lines)
- 2:00 - Generation complete
- 2:10 - Show sample rule
- 2:30 - Wrap up

## Backup Plan

If live demo fails, have pre-recorded terminal session with:
```bash
asciinema rec demo.cast
# Run demo
# Ctrl+D to stop
asciinema play demo.cast
```
