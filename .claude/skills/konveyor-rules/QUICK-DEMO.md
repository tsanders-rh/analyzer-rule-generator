# Quick Demo - Konveyor Rules Skill (2 Minutes)

Perfect for live presentations or quick demos.

## Setup (Before Demo)

```bash
# Ensure you're in the project
cd analyzer-rule-generator

# Set API key
export ANTHROPIC_API_KEY="your-key"

# Start Claude Code
# (Skill loads automatically)
```

---

## Demo Flow

### 1. Invoke the Skill (10 seconds)

**Type:**
```
konveyor-rules
```

**Say:**
> "Instead of remembering complex command-line arguments, I can just have a conversation with Claude."

---

### 2. Provide Information (20 seconds)

**Claude asks for:**
- Migration guide source
- Source framework
- Target framework
- Output directory (optional)
- LLM provider (optional)

**You provide:**
```
Guide: https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide
Source: spring-boot-3
Target: spring-boot-4
Output: [press enter for default]
Provider: anthropic
```

**Say:**
> "Claude guides me through the required information and uses smart defaults for optional parameters."

---

### 3. Watch Generation (60 seconds)

**Claude will:**
1. Validate the URL
2. Run the rule generator
3. Show progress updates
4. Extract migration patterns
5. Generate YAML rules

**Say:**
> "The AI analyzes the migration guide, identifies patterns, and generates Konveyor analyzer rules automatically."

**Point out:**
- Pattern extraction messages
- Number of rules being generated
- File locations being created

---

### 4. Review Results (20 seconds)

**Claude shows:**
- Number of patterns extracted
- Number of rules generated
- Output file locations
- Summary of rule types

**Say:**
> "We now have production-ready Konveyor rules that can detect Spring Boot 3 code that needs updating for version 4."

**Navigate to output:**
```bash
ls examples/output/spring-boot-4.0/
cat examples/output/spring-boot-4.0/001-[first-rule].yaml
```

---

### 5. Explain Next Steps (10 seconds)

**Claude suggests:**
- Testing rules with Kantra
- Customizing patterns
- Submitting to konveyor/rulesets

**Say:**
> "Claude also guides me through testing and submitting these rules to the Konveyor community."

---

## Alternative: One-Line Demo (30 seconds)

**Instead of invoking the skill explicitly, use natural language:**

**Type:**
```
Generate Konveyor rules for Spring Boot 3 to 4 migration from
https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide
```

**Say:**
> "Claude understands natural language requests and automatically activates the right skill."

**Claude will:**
- Recognize this is a rule generation request
- Extract the parameters
- Run the generator
- Show results

---

## Key Talking Points

### Before (Command-Line)
```bash
python scripts/generate_rules.py \
  --guide https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide \
  --source spring-boot-3 \
  --target spring-boot-4 \
  --provider anthropic \
  --output examples/output/spring-boot-4.0/migration-rules.yaml
```
**Problems:**
- Hard to remember flags
- Easy to make typos
- No guidance on what to do next

### After (Claude Skill)
```
Generate Spring Boot 4 migration rules from the official guide
```
**Benefits:**
- Natural conversation
- Interactive guidance
- Validation before running
- Explains results and next steps

---

## What to Show in the Output

Open one of the generated rule files:

```yaml
- ruleID: spring-boot-3-to-spring-boot-4-00001
  description: Update deprecated Spring Boot 3 configuration
  effort: 5
  category: mandatory
  labels:
    - konveyor.io/source=spring-boot-3
    - konveyor.io/target=spring-boot-4
  when:
    java.referenced:
      pattern: org.springframework.boot.autoconfigure.*
      location: IMPORT
  message: "Review Spring Boot 4.0 migration requirements..."
  links:
    - url: "https://github.com/spring-projects/spring-boot/wiki/..."
      title: "Spring Boot 4.0 Migration Guide"
```

**Say:**
> "Each rule identifies a specific migration pattern, estimates the effort to fix it, and provides helpful guidance to developers."

---

## Audience Questions to Anticipate

**Q: Can it handle local files too?**
```
Yes! Just provide the local file path instead of a URL.
```

**Q: What migration types are supported?**
```
Any framework: Java, React, Go, Python, Django, PatternFly, etc.
The AI adapts to the language and generates appropriate rules.
```

**Q: How accurate are the generated rules?**
```
They're a great starting point. You should always review and test them.
The skill also guides you through the testing process.
```

**Q: Can I customize the rules afterward?**
```
Absolutely. The generated YAML files are human-readable and editable.
Claude can help you customize them too.
```

**Q: Does it work with private documentation?**
```
Yes! As long as you have access to the guide (local file or accessible URL),
the skill can process it.
```

---

## Backup Demo (If Primary Fails)

If you encounter issues during the demo:

1. **Show the documentation instead:**
   ```
   cat .claude/skills/konveyor-rules/README.md
   ```

2. **Show pre-generated output:**
   ```
   ls examples/output/
   cat examples/output/[existing-rule-file].yaml
   ```

3. **Explain the concept:**
   - "The skill would normally walk me through this interactively"
   - "It validates inputs, runs the generator, and explains results"
   - "Think of it as an AI pair programmer for migration rules"

---

## Post-Demo Resources

**Share with audience:**
- Project URL: https://github.com/[your-org]/analyzer-rule-generator
- Skill documentation: `.claude/skills/konveyor-rules/README.md`
- Full demo script: `.claude/skills/konveyor-rules/DEMO.md`
- Claude Code: https://claude.com/claude-code

---

## Practice Script

**Run through this before presenting:**

1. Open terminal in project directory
2. Type: `konveyor-rules`
3. Provide Spring Boot guide and versions
4. Watch generation (familiarize with output)
5. Review generated files
6. Close and practice natural language version
7. Prepare answers to common questions

**Timing:**
- Setup: 10s
- Invocation: 10s
- Input: 20s
- Generation: 60s
- Review: 20s
- **Total: ~2 minutes**

---

## Success Metrics

Demo is successful if audience understands:

1. ✅ **It's conversational** - Not command-line flag memorization
2. ✅ **It's guided** - Interactive prompts prevent errors
3. ✅ **It's intelligent** - Validates inputs, explains outputs
4. ✅ **It's integrated** - Part of broader Konveyor workflow
5. ✅ **It's accessible** - Lowers barrier to rule creation

---

## Elevator Pitch (30 seconds)

> "The Konveyor Rule Generator now has a Claude Code skill that turns rule generation into a natural conversation. Instead of memorizing command-line flags, you just describe what you need: 'Generate Spring Boot 4 migration rules from the official guide.' Claude validates your inputs, runs the generator, explains the results, and guides you through testing. It's like having an AI migration expert sitting next to you."
