# Konveyor Rule Generator Skill - Demo Script

This demo script shows how to use the Konveyor Rule Generator Claude Code skill in various scenarios.

## Prerequisites

Before starting the demo, ensure:

1. You're in the analyzer-rule-generator project directory
2. Dependencies are installed: `pip install -r requirements.txt`
3. API key is set: `export ANTHROPIC_API_KEY="your-key"`
4. Claude Code session is started

## Demo 1: Simple Spring Boot Migration

**Scenario:** Generate rules for Spring Boot 3 to 4 migration using GitHub wiki

### User Input

```
konveyor-rules
```

### Expected Claude Response

```
I'll help you generate Konveyor migration rules. Let me gather some information:

1. What is the migration guide source (URL or file path)?
2. What is the source framework?
3. What is the target framework?
4. Where should I save the output? (optional, defaults to examples/output/)
5. Which LLM provider would you like to use? (optional: openai, anthropic, google)
```

### User Response

```
1. https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide
2. spring-boot-3
3. spring-boot-4
4. Just use the default
5. anthropic
```

### Expected Claude Actions

Claude will:
1. Validate the URL is accessible
2. Run: `python scripts/generate_rules.py --guide https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide --source spring-boot-3 --target spring-boot-4 --provider anthropic --output examples/output/spring-boot-4.0/`
3. Monitor the progress and show key outputs
4. Summarize the results

### Expected Output Summary

Claude will explain:
- Number of patterns extracted
- Number of rules generated
- Location of generated YAML files
- Next steps for testing the rules

---

## Demo 2: Quick Generation (All-in-One)

**Scenario:** Provide all information upfront for React 18 migration

### User Input

```
Generate Konveyor migration rules from https://react.dev/blog/2022/03/08/react-18-upgrade-guide
for migrating from react-17 to react-18. Save to output/react-18-rules/
```

### Expected Claude Response

Claude should:
1. Recognize this is a rule generation request
2. Automatically invoke the skill
3. Extract the parameters from the request:
   - Guide: https://react.dev/blog/2022/03/08/react-18-upgrade-guide
   - Source: react-17
   - Target: react-18
   - Output: output/react-18-rules/
4. Run the generator with these parameters
5. Show the progress and results

### Key Points to Highlight

- No need to explicitly type "konveyor-rules"
- Natural language understanding
- Automatic parameter extraction
- Context-aware defaults

---

## Demo 3: Local File with Custom Options

**Scenario:** Generate rules from a local migration guide with specific model

### User Input

```
konveyor-rules
```

### User Response to Prompts

```
Guide: docs/migration-guides/django-4-migration.md
Source: django-3
Target: django-4
Output: examples/output/django-4/
Provider: anthropic
Model: claude-opus-4-20250514
```

### Expected Claude Actions

1. Check if the local file exists
2. If not found, ask user to verify the path
3. If found, proceed with generation using the specified model
4. Show detailed progress since this is a custom configuration

### What to Demonstrate

- Local file support
- Custom model selection
- File validation before running
- Helpful error messages if file doesn't exist

---

## Demo 4: Batch Processing

**Scenario:** Generate rules for multiple migration guides

### User Input

```
I need to generate rules for both the Spring Boot 4.0 and Spring Framework 6 migration guides.
Save them in separate directories under examples/output/
```

### Expected Claude Response

Claude should:
1. Recognize this requires multiple runs
2. Ask for details about each guide:
   - Spring Boot guide URL and framework versions
   - Spring Framework guide URL and versions
3. Process them sequentially
4. Organize outputs in separate directories
5. Provide a summary of both generations

### User Provides

```
Spring Boot:
- Guide: https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide
- Source: spring-boot-3
- Target: spring-boot-4
- Output: examples/output/spring-boot-4.0/

Spring Framework:
- Guide: https://github.com/spring-projects/spring-framework/wiki/Upgrading-to-Spring-Framework-6.x
- Source: spring-framework-5
- Target: spring-framework-6
- Output: examples/output/spring-framework-6.0/
```

### What to Highlight

- Handling multiple migrations in one session
- Organized output structure
- Comprehensive summary at the end

---

## Demo 5: Troubleshooting Common Issues

**Scenario:** Handle common errors gracefully

### Demo 5a: Missing API Key

**Setup:** Unset the API key first
```bash
unset ANTHROPIC_API_KEY
```

**User Input:**
```
konveyor-rules
```

**User provides guide URL and frameworks**

**Expected Claude Behavior:**
- Run the script
- Detect API key error
- Explain the issue clearly
- Provide solution: `export ANTHROPIC_API_KEY="your-key"`
- Offer to retry after user sets the key

### Demo 5b: Invalid Guide URL

**User Input:**
```
Generate rules from https://example.com/nonexistent-guide
for spring-boot-3 to spring-boot-4
```

**Expected Claude Behavior:**
- Attempt to fetch the URL
- Detect 404 or connection error
- Explain the issue
- Ask user to verify the URL
- Suggest checking if URL is accessible

### Demo 5c: Python Import Error

**Setup:** (Temporarily rename a dependency)

**Expected Claude Behavior:**
- Run the script
- Detect import error
- Explain that dependencies may not be installed
- Suggest: `pip install -r requirements.txt`
- Offer to help debug if issue persists

---

## Demo 6: Advanced Features

**Scenario:** Using advanced options and understanding the output

### User Input

```
konveyor-rules
```

### User Requests

```
Generate rules for PatternFly v5 to v6 migration.
Guide: https://www.patternfly.org/get-started/upgrade/
Use Anthropic Claude Opus model.
I want detailed output so I can understand what patterns were found.
```

### Expected Claude Actions

1. Run with verbose/detailed mode if available
2. Show the extraction process:
   - Patterns being identified
   - Language detection (TypeScript/React)
   - Provider selection (Builtin)
3. Explain each generated rule file:
   - What pattern it covers
   - Why certain effort levels were assigned
   - File patterns used
4. Provide guidance on customizing the rules

### What to Demonstrate

- Detailed output interpretation
- Understanding the extraction process
- How to customize generated rules
- Best practices for rule refinement

---

## Demo 7: Integration Workflow

**Scenario:** Complete workflow from generation to testing

### User Input

```
I want to generate rules for a Spring Boot 3 to 4 migration and test them with Konveyor.
What's the complete workflow?
```

### Expected Claude Guidance

Claude should explain and guide through:

1. **Generate Rules** (using the skill)
   ```
   konveyor-rules
   ```

2. **Review Generated Rules**
   - Show where files are located
   - Explain the structure
   - Point out key sections (ruleID, patterns, messages)

3. **Create Test Application**
   - Suggest using the test data generator
   - Or creating a simple Spring Boot 3 app with known issues

4. **Test with Kantra**
   ```bash
   kantra analyze --input /path/to/test-app \
     --output /path/to/output \
     --rules /path/to/generated/rules \
     --target spring-boot-4
   ```

5. **Review Results**
   - Check the analysis output
   - Verify violations are detected
   - Refine rules if needed

6. **Submit to Konveyor**
   - Fork konveyor/rulesets
   - Add rules to appropriate directory
   - Create PR with testing evidence

### What to Highlight

- End-to-end workflow
- Integration with Konveyor ecosystem
- Testing before submission
- Best practices for rule validation

---

## Presentation Tips

When demoing the skill:

1. **Start Simple**
   - Begin with Demo 1 (basic Spring Boot example)
   - Show the interactive nature
   - Highlight the natural conversation flow

2. **Show Flexibility**
   - Demo 2 shows natural language input
   - Demo 3 shows customization options
   - Demonstrates the skill adapts to user preferences

3. **Handle Errors Gracefully**
   - Demo 5 shows error handling
   - Emphasizes helpful error messages
   - Shows the assistant guides through troubleshooting

4. **Advanced Usage**
   - Demo 6 for power users
   - Demo 7 for complete workflow
   - Shows integration with broader ecosystem

5. **Key Messages**
   - Natural language interface lowers barrier to entry
   - Interactive guidance prevents common mistakes
   - Context-aware suggestions improve results
   - Integrates seamlessly with existing tools

---

## Quick Demo Script (5 Minutes)

For a quick presentation:

```
# 1. Show the skill invocation (30 seconds)
User: "konveyor-rules"
Claude: [Shows prompts]

# 2. Provide example input (1 minute)
User: Provides Spring Boot migration guide URL and versions

# 3. Watch the generation (2 minutes)
Claude: Runs the script, shows progress

# 4. Review the output (1 minute)
Claude: Summarizes results, shows generated files

# 5. Next steps (30 seconds)
Claude: Explains how to test and use the rules
```

**Key Points to Make:**
- "Natural conversation instead of remembering command-line flags"
- "Interactive guidance prevents errors"
- "Automatic validation of inputs"
- "Context-aware suggestions"

---

## Talking Points

### Why use the skill vs command-line?

**Command-line approach:**
```bash
python scripts/generate_rules.py \
  --guide https://very-long-url... \
  --source spring-boot-3 \
  --target spring-boot-4 \
  --provider anthropic \
  --output examples/output/spring-boot-4.0/
```

**Skill approach:**
```
Generate Spring Boot 4 migration rules from the official guide
```

### Benefits Demonstrated

1. **Natural Language** - No memorizing flags or syntax
2. **Interactive** - Asks clarifying questions
3. **Validating** - Checks inputs before running
4. **Guiding** - Explains outputs and next steps
5. **Error-Friendly** - Helpful messages when things go wrong
6. **Context-Aware** - Understands project structure

### Common Questions

**Q: Does this replace the command-line tool?**
A: No, it complements it. The skill is great for interactive use, exploration, and learning. The CLI is perfect for automation and CI/CD.

**Q: Can I use this with my own migration guides?**
A: Yes! Local files, URLs, any format supported by the underlying tool.

**Q: What if I need to customize the generated rules?**
A: The skill will show you where the files are and how to edit them. You can also ask Claude for help customizing specific patterns.

**Q: Does it work with all LLM providers?**
A: Yes - OpenAI, Anthropic, and Google Gemini are all supported.
