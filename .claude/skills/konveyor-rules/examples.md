# Example Conversations

Real-world examples of using the Konveyor Rule Generator skill.

---

## Example 1: Spring Boot Migration

### Conversation

**User:**
```
konveyor-rules
```

**Claude:**
```
I'll help you generate Konveyor migration rules. Let me gather some information:

1. What is the migration guide source (URL or file path)?
2. What is the source framework?
3. What is the target framework?
4. Where should I save the output? (optional, defaults to examples/output/)
5. Which LLM provider would you like to use? (optional: openai, anthropic, google)
```

**User:**
```
1. https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide
2. spring-boot-3
3. spring-boot-4
4. examples/output/spring-boot-4.0/
5. anthropic
```

**Claude:**
```
Great! I'll generate Konveyor migration rules for Spring Boot 3 to 4.

Let me run the rule generator...

[Running command: python scripts/generate_rules.py --guide https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide --source spring-boot-3 --target spring-boot-4 --provider anthropic --output examples/output/spring-boot-4.0/]

Fetching guide content...
Extracting migration patterns...
Found 15 migration patterns
Generating rules...
Created 15 rule files

✓ Rules generated successfully!

Output location: examples/output/spring-boot-4.0/

Summary:
- 15 migration patterns identified
- 15 Konveyor analyzer rules generated
- Provider: Java (detected from patterns)
- Effort levels: 3 mandatory, 8 potential, 4 optional

Next steps:
1. Review the generated YAML files in examples/output/spring-boot-4.0/
2. Test the rules using Kantra: kantra analyze --input <test-app> --rules examples/output/spring-boot-4.0/
3. Customize rules as needed
4. Submit to konveyor/rulesets repository

Would you like help with any of these next steps?
```

**User:**
```
Can you show me what one of the rules looks like?
```

**Claude:**
```
Sure! Here's an example of a generated rule:

[Shows content of one rule file with explanation of each field]

This rule:
- Detects usage of deprecated Spring Boot 3 annotations
- Marks it as "mandatory" (must be fixed)
- Estimates 3 story points of effort
- Provides a helpful message with migration guidance
- Links to the official migration guide

The rule uses the "java.referenced" condition to find Java code that
references specific Spring Boot classes or annotations.
```

---

## Example 2: React Migration (Natural Language)

### Conversation

**User:**
```
I need to create migration rules for React 17 to React 18. Can you generate them
from the official React 18 upgrade guide?
```

**Claude:**
```
I'll help you generate Konveyor migration rules for React 17 to React 18.

Let me fetch the React 18 upgrade guide and generate the rules...

[Automatically determines the guide URL: https://react.dev/blog/2022/03/08/react-18-upgrade-guide]

Running the rule generator with:
- Guide: https://react.dev/blog/2022/03/08/react-18-upgrade-guide
- Source: react-17
- Target: react-18
- Output: examples/output/react-18/

Fetching guide...
Analyzing migration patterns...
Found 12 migration patterns
Generating rules...
Created 12 rule files

✓ Rules generated successfully!

Output location: examples/output/react-18/

Summary:
- 12 migration patterns identified
- Provider: Builtin (TypeScript/React detected)
- Pattern types: JSX changes, API updates, hook behaviors
- Effort levels: 2 mandatory, 7 potential, 3 optional

Key patterns found:
1. ReactDOM.render replacement (mandatory, 5 points)
2. New createRoot API (mandatory, 3 points)
3. Automatic batching changes (potential, 2 points)
4. Suspense behavior updates (potential, 3 points)
... and 8 more

The rules are ready for testing. Would you like help testing them or customizing any patterns?
```

---

## Example 3: Local File Migration

### Conversation

**User:**
```
konveyor-rules
```

**Claude:**
```
I'll help you generate Konveyor migration rules. Let me gather some information:

1. What is the migration guide source (URL or file path)?
2. What is the source framework?
3. What is the target framework?
```

**User:**
```
1. docs/internal/django-4-migration.md
2. django-3.2
3. django-4.0
```

**Claude:**
```
Let me check if the file exists...

✓ Found docs/internal/django-4-migration.md

Generating rules for Django 3.2 to 4.0 migration...

[Running: python scripts/generate_rules.py --guide docs/internal/django-4-migration.md --source django-3.2 --target django-4.0]

Processing local file...
Extracting migration patterns...
Found 18 migration patterns
Generating rules...
Created 18 rule files

✓ Rules generated successfully!

Output location: examples/output/django-4.0/

Summary:
- 18 migration patterns identified
- Provider: Builtin (Python detected)
- File patterns: *.py, settings.py, urls.py
- Effort levels: 5 mandatory, 10 potential, 3 optional

Notable patterns:
1. django.conf.urls.url() deprecation (mandatory)
2. USE_L10N setting removal (mandatory)
3. DEFAULT_AUTO_FIELD configuration (potential)
4. Model field type changes (potential)
... and 14 more

The rules are ready. Since this is an internal guide, you might want to
review the rules to ensure they capture all your organization-specific
migration requirements.
```

---

## Example 4: Error Handling - Missing API Key

### Conversation

**User:**
```
Generate rules for PatternFly v5 to v6 from https://www.patternfly.org/get-started/upgrade/
```

**Claude:**
```
I'll generate Konveyor migration rules for PatternFly v5 to v6.

Running the rule generator...

[Error output showing missing API key]

It looks like the API key is not set. To use the rule generator, you need to
set an API key for your chosen LLM provider.

For Anthropic Claude:
export ANTHROPIC_API_KEY="your-key-here"

For OpenAI:
export OPENAI_API_KEY="your-key-here"

For Google Gemini:
export GOOGLE_API_KEY="your-key-here"

Would you like to try again after setting the API key? Or would you like to
use a different provider?
```

**User:**
```
I set the ANTHROPIC_API_KEY. Can you try again?
```

**Claude:**
```
Great! Let me retry the generation...

[Running: python scripts/generate_rules.py --guide https://www.patternfly.org/get-started/upgrade/ --source patternfly-v5 --target patternfly-v6 --provider anthropic]

✓ API key detected
Fetching PatternFly upgrade guide...
Analyzing UI component changes...
Found 25 migration patterns
Generating rules...
Created 25 rule files

✓ Rules generated successfully!
[... continues with normal output]
```

---

## Example 5: Custom Model Selection

### Conversation

**User:**
```
I want to generate migration rules but use the Claude Opus model for better accuracy.
The migration is from Angular 15 to Angular 16.
```

**Claude:**
```
I'll generate rules for Angular 15 to 16 using Claude Opus.

What's the URL or file path for the Angular 16 migration guide?
```

**User:**
```
https://angular.io/guide/update-to-latest-version
```

**Claude:**
```
Perfect! Generating rules with Claude Opus for maximum accuracy...

[Running: python scripts/generate_rules.py --guide https://angular.io/guide/update-to-latest-version --source angular-15 --target angular-16 --provider anthropic --model claude-opus-4-20250514]

Using Claude Opus model...
Fetching Angular migration guide...
Performing detailed pattern analysis...
Found 22 migration patterns
Generating comprehensive rules...
Created 22 rule files

✓ Rules generated successfully!

Output location: examples/output/angular-16/

Summary:
- 22 migration patterns identified with detailed analysis
- Provider: Builtin (TypeScript detected)
- File patterns: *.ts, *.component.ts, *.module.ts, *.html
- Effort levels: 4 mandatory, 13 potential, 5 optional

The Opus model provided more detailed pattern analysis and comprehensive
descriptions for each rule. The rules include:
1. Standalone components migration (mandatory, 8 points)
2. Dependency injection changes (mandatory, 5 points)
3. Router updates (potential, 3 points)
... and 19 more

Would you like me to explain any specific patterns or help with testing?
```

---

## Example 6: Batch Processing

### Conversation

**User:**
```
I need to generate rules for multiple Spring migrations:
1. Spring Boot 3 to 4
2. Spring Framework 5 to 6

Can you help with both?
```

**Claude:**
```
I'll help you generate rules for both migrations. Let me process them one at a time.

First, let's handle Spring Boot 3 to 4. What's the migration guide URL?
```

**User:**
```
Spring Boot: https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide
Spring Framework: https://github.com/spring-projects/spring-framework/wiki/Upgrading-to-Spring-Framework-6.x
```

**Claude:**
```
Great! I'll process both migrations and organize them in separate directories.

=== Migration 1: Spring Boot 3 to 4 ===

[Running: python scripts/generate_rules.py --guide https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide --source spring-boot-3 --target spring-boot-4 --output examples/output/spring-boot-4.0/]

✓ Generated 15 rules in examples/output/spring-boot-4.0/

=== Migration 2: Spring Framework 5 to 6 ===

[Running: python scripts/generate_rules.py --guide https://github.com/spring-projects/spring-framework/wiki/Upgrading-to-Spring-Framework-6.x --source spring-framework-5 --target spring-framework-6 --output examples/output/spring-framework-6.0/]

✓ Generated 28 rules in examples/output/spring-framework-6.0/

=== Summary ===

Successfully generated rules for both migrations:

Spring Boot 3 → 4:
- 15 rules
- Location: examples/output/spring-boot-4.0/
- Focus: Boot-specific configuration, auto-configuration changes

Spring Framework 5 → 6:
- 28 rules
- Location: examples/output/spring-framework-6.0/
- Focus: Core framework changes, Jakarta EE namespace updates

Total: 43 migration rules generated

Both rule sets are ready for testing. Note that some applications may need
both rule sets if they're migrating from Spring Boot 3 (which uses Spring
Framework 5) to Spring Boot 4 (which uses Spring Framework 6).

Would you like help testing these rules or understanding the differences
between the two migrations?
```

---

## Example 7: Asking for Workflow Guidance

### Conversation

**User:**
```
I'm new to Konveyor. Can you walk me through the complete process of generating
and using migration rules?
```

**Claude:**
```
I'll guide you through the complete workflow for generating and using Konveyor
migration rules. Let's break it down into steps:

=== Step 1: Generate Rules ===

First, let's generate some rules. I'll use the konveyor-rules skill to help.

What migration are you working on? (e.g., "Spring Boot 3 to 4" or "React 17 to 18")
```

**User:**
```
Spring Boot 3 to 4
```

**Claude:**
```
Perfect! Let's generate Spring Boot 4 migration rules.

[Runs through the rule generation process as in Example 1]

✓ Generated 15 rules in examples/output/spring-boot-4.0/

=== Step 2: Review the Rules ===

Let me show you what a rule looks like:

[Shows example rule with detailed explanation]

Each rule has:
- ruleID: Unique identifier
- description: What it detects
- effort: Estimated story points to fix
- category: mandatory/potential/optional
- when: The pattern to match
- message: Guidance for developers
- links: Reference documentation

=== Step 3: Create or Use Test Application ===

To test the rules, you need a Spring Boot 3 application. You can either:

Option A: Use an existing Spring Boot 3 app
Option B: Create a simple test app with known migration issues

Which would you prefer?
```

**User:**
```
I have an existing app at ~/projects/my-spring-app
```

**Claude:**
```
Great! Let's test the rules on your application.

=== Step 4: Test with Kantra ===

Kantra is the Konveyor analyzer CLI tool. To analyze your app:

kantra analyze \
  --input ~/projects/my-spring-app \
  --output analysis-output \
  --rules examples/output/spring-boot-4.0/ \
  --target spring-boot-4

This will:
1. Scan your Spring Boot 3 code
2. Apply the generated rules
3. Identify migration issues
4. Generate a report

=== Step 5: Review Analysis Results ===

After analysis completes, check:
- analysis-output/output.yaml - Detailed violations
- analysis-output/static-report/ - HTML report (open in browser)

The report will show:
- Which files have issues
- What needs to change
- Effort estimates
- Links to migration guides

=== Step 6: Refine Rules (if needed) ===

If rules miss issues or have false positives:
1. Edit the YAML files in examples/output/spring-boot-4.0/
2. Adjust patterns, effort levels, or messages
3. Re-run analysis to verify improvements

=== Step 7: Submit to Konveyor (optional) ===

If your rules would benefit others:
1. Fork github.com/konveyor/rulesets
2. Add rules to default/generated/
3. Create PR with:
   - Rule files
   - Test evidence (analysis results)
   - Documentation

Would you like me to help you with any of these steps in detail?
```

---

## Example 8: Understanding Output

### Conversation

**User:**
```
I generated rules but I'm not sure I understand the output. Can you explain?
```

**Claude:**
```
I'd be happy to explain! What migration did you generate rules for?
```

**User:**
```
React 17 to 18
```

**Claude:**
```
Let me look at the React 17 to 18 rules you generated...

[Checks examples/output/react-18/ directory]

I can see you have several rule files. Let me explain the structure:

=== Rule File Organization ===

Each file represents one migration concern:
- 001-reactdom-render-replacement.yaml
- 002-createroot-api.yaml
- 003-automatic-batching.yaml
... etc.

Each concern gets its own file for easier management and testing.

=== Inside Each Rule File ===

Let's look at 001-reactdom-render-replacement.yaml:

```yaml
- ruleID: react-17-to-react-18-00001
  description: Replace ReactDOM.render with createRoot
  effort: 5
  category: mandatory
  when:
    builtin.filecontent:
      pattern: ReactDOM\.render\(
      filePattern: '*.{tsx,jsx,ts,js}'
  message: |
    ReactDOM.render is deprecated in React 18.
    Replace with createRoot API...
```

Breaking this down:

**ruleID**: Unique identifier
- Format: source-to-target-00001
- Sequential numbering

**effort**: Story points (1-13)
- 5 = moderate effort
- Usually 1-4 hours to fix

**category**:
- mandatory = must fix
- potential = likely needs attention
- optional = nice to have

**when.builtin.filecontent**:
- pattern: Regex to find the issue
- filePattern: Which files to check
- This finds "ReactDOM.render(" in JS/TS/JSX/TSX files

**message**: Developer guidance
- What's wrong
- How to fix it
- Why it matters

=== Ruleset Metadata ===

The ruleset.yaml file contains:
- name: Human-readable ruleset name
- description: What this ruleset does
- labels: Source and target tags

=== Generation Summary ===

The summary you saw means:
- 12 patterns found = 12 distinct migration issues
- 12 rules generated = one rule per pattern
- Builtin provider = uses regex (not Java analysis)
- Effort distribution = 2 must-fix, 7 likely, 3 optional

Does this help? Would you like me to explain any specific rule in more detail?
```

---

## Tips for Writing Your Own Queries

### Effective Queries

✅ **Good:**
```
Generate rules for Django 3 to 4 from docs/migration.md
```

✅ **Good:**
```
konveyor-rules
[Then provide details when prompted]
```

✅ **Good:**
```
I need Spring Boot 4 migration rules. Can you help?
```

❌ **Less Effective:**
```
rules
```
(Too vague - what kind of rules?)

❌ **Less Effective:**
```
Run the script
```
(Which script? What parameters?)

### Getting Help

```
How do I test the generated rules?
What migration types are supported?
Can you explain this rule file?
How do I customize the effort levels?
```

The skill is designed to be conversational, so ask questions naturally!
