# Quick Start Guide

Generate Konveyor analyzer rules from migration guides in 3 easy steps.

https://raw.githubusercontent.com/konveyor/rulesets/main/default/generated/quarkus/218-jms-to-reactive-quarkus.windup.yaml

## Prerequisites

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your API key (choose one)
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
export GOOGLE_API_KEY="your-key-here"
```

## Basic Usage

Point the tool at any migration guide and generate rules:

```bash
python scripts/generate_rules.py \
  --guide <url-or-file> \
  --source <source-framework> \
  --target <target-framework> \
  --output <output.yaml>
```

## Example 1: Generate from URL

```bash
python scripts/generate_rules.py \
  --guide https://openjdk.org/jeps/504 \
  --source openjdk17 \
  --target openjdk21 \
  --output examples/output/jdk21/applet-removal.yaml \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219
```

**What this does:**
1. Fetches JEP 504 (Applet API Removal) from the web
2. Uses Claude to extract migration patterns
3. Generates Konveyor rules automatically

## Example 2: TypeScript/React Migration (PatternFly)

The tool automatically detects non-Java migrations and uses the builtin provider:

```bash
python scripts/generate_rules.py \
  --guide examples/guides/patternfly-v5-to-v6.md \
  --source patternfly-v5 \
  --target patternfly-v6 \
  --output examples/output/patternfly-v6/migration-rules.yaml \
  --provider anthropic
```

**What this generates:**
- Builtin provider rules with regex patterns
- File patterns for TypeScript/React files (`*.{tsx,jsx}`)
- Detection of prop changes, import updates, CSS variable renames
- Works for TypeScript, JavaScript, Go, Python, and more

## Example 3: Generate from Local File

```bash
python scripts/generate_rules.py \
  --guide examples/guides/spring-boot-to-quarkus.md \
  --source spring-boot \
  --target quarkus \
  --output examples/output/spring-boot-to-quarkus.yaml \
  --provider openai
```

## Example 4: Use Different LLM Providers

**Anthropic Claude (recommended):**
```bash
python scripts/generate_rules.py \
  --guide migration-guide.md \
  --source java-ee \
  --target jakarta-ee \
  --output rules.yaml \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219
```

**OpenAI:**
```bash
python scripts/generate_rules.py \
  --guide migration-guide.md \
  --source java-ee \
  --target jakarta-ee \
  --output rules.yaml \
  --provider openai \
  --model gpt-4-turbo
```

**Google Gemini:**
```bash
python scripts/generate_rules.py \
  --guide migration-guide.md \
  --source java-ee \
  --target jakarta-ee \
  --output rules.yaml \
  --provider google
```

## Viewing Generated Rules

Generate an interactive HTML viewer to browse your rules:

```bash
python scripts/generate_rule_viewer.py \
  --rules examples/output/spring-boot-4.0/migration-rules.yaml \
  --output viewer.html \
  --open
```

This creates a searchable, filterable web interface with:
- ✅ Expand/collapse rule details
- ✅ Search by ID, description, or pattern
- ✅ Filter by category and effort level
- ✅ Statistics and summaries
- ✅ Syntax highlighting for code

## Output

The tool generates a YAML file with Konveyor analyzer rules. The format depends on the detected language:

### Java Provider Rules

For Java migrations, rules use the `java.referenced` provider:

```yaml
- ruleID: spring-boot-to-quarkus-00001
  description: Replace Spring @RestController with JAX-RS @Path
  effort: 3
  category: mandatory
  labels:
    - konveyor.io/source=spring-boot
    - konveyor.io/target=quarkus
  when:
    java.referenced:
      pattern: org.springframework.web.bind.annotation.RestController
      location: ANNOTATION
  message: "Spring @RestController must be replaced with JAX-RS @Path..."
  links:
    - url: "https://quarkus.io/guides/rest-json"
      title: "Quarkus REST Guide"
```

### Builtin Provider Rules

For TypeScript, JavaScript, Go, Python, and other languages, rules use the `builtin.filecontent` provider:

```yaml
- ruleID: patternfly-v5-to-patternfly-v6-00001
  description: isDisabled should be replaced with isAriaDisabled
  effort: 3
  category: potential
  labels:
    - konveyor.io/source=patternfly-v5
    - konveyor.io/target=patternfly-v6
  when:
    builtin.filecontent:
      pattern: isDisabled\s*[=:]
      filePattern: '*.{tsx,jsx,ts,js}'
  message: "The isDisabled prop has been renamed to isAriaDisabled..."
```

## Command Line Options

| Option | Required | Description | Example |
|--------|----------|-------------|---------|
| `--guide` | Yes | Path or URL to migration guide | `https://example.com/guide.html` |
| `--source` | Yes | Source framework/version | `spring-boot`, `openjdk17` |
| `--target` | Yes | Target framework/version | `quarkus`, `openjdk21` |
| `--output` | Yes | Output YAML file path | `rules.yaml` |
| `--provider` | No | LLM provider (default: openai) | `anthropic`, `openai`, `google` |
| `--model` | No | Specific model name | `claude-3-7-sonnet-20250219` |
| `--api-key` | No | API key (uses env var if not set) | `sk-...` |

## Tips for Best Results

### 1. Supports Multiple Languages
The tool automatically detects the language and generates appropriate rules:

- ✅ **Java**: Uses `java.referenced` provider with FQNs and location types
- ✅ **TypeScript/React**: Uses `builtin.filecontent` with regex patterns for `.tsx/.jsx` files
- ✅ **Go**: Detects imports and syntax, generates builtin rules for `.go` files
- ✅ **Python**: Detects module imports, generates builtin rules for `.py` files
- ✅ **CSS/SCSS**: Detects CSS custom properties and selectors

### 2. Choose Good Migration Guides
✅ **Good:**
- Official upgrade guides with code examples (Spring Boot, React, PatternFly)
- Technical documentation with API changes
- JEPs, RFCs, or specification documents
- Component library migration guides (PatternFly v5→v6, Material-UI, etc.)

❌ **Bad:**
- Marketing content or blog posts
- Guides without specific API details
- Purely conceptual documentation

### 3. Use Descriptive Framework Names
```bash
# Good
--source openjdk17 --target openjdk21
--source spring-boot-2 --target spring-boot-3
--source patternfly-v5 --target patternfly-v6
--source react-16 --target react-18

# Less helpful
--source old --target new
```

### 4. Review and Refine
The AI-generated rules are a starting point. Always:
1. Review the generated rules
2. Test against real code
3. Refine patterns and messages
4. Add missing edge cases

## Troubleshooting

**Error: "No patterns extracted"**
- Guide may not contain enough technical detail
- Try a different/more detailed guide
- Check that API key is set correctly

**Error: "API key not found"**
```bash
# Set the appropriate environment variable
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
```

**Rules seem incomplete:**
- LLM extraction is best-effort
- Review and refine generated rules against real code for completeness

## Submitting Rules to Konveyor

After generating rules, you can prepare them for submission to the official Konveyor rulesets repository using our automated workflow:

### Step 1: Prepare Submission Package
```bash
python scripts/prepare_submission.py \
  --rules examples/output/spring-boot-4.0/migration-rules.yaml \
  --source spring-boot-3.5 \
  --target spring-boot-4.0 \
  --guide-url "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide" \
  --output submission/spring-boot-4.0 \
  --data-dir-name mongodb
```

This creates:
- Rule YAML file
- Test template with test cases for each rule
- Test data directory structure
- README with submission instructions

### Step 2: Generate Test Data with AI
```bash
python scripts/generate_test_data.py \
  --rules examples/output/spring-boot-4.0/migration-rules.yaml \
  --output submission/spring-boot-4.0/tests/data/mongodb \
  --source spring-boot-3.5 \
  --target spring-boot-4.0 \
  --guide-url "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide" \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219
```

This generates:
- Complete `pom.xml` with correct dependencies
- Java application code with violations for each rule
- Comments mapping code to rule IDs

### Step 3: Test and Submit
```bash
# Test locally with Kantra
kantra test submission/spring-boot-4.0/tests/*.test.yaml

# Copy to Konveyor rulesets fork and submit PR
# See detailed guide for complete instructions
```

See [Konveyor Submission Guide](konveyor-submission-guide.md) for complete details on:
- Creating test applications
- Running tests with Kantra
- Submitting pull requests
- CI/CD requirements

## Next Steps

- **Submit to Konveyor**: See [Konveyor Submission Guide](konveyor-submission-guide.md)
- **Test your rules**: Use the generated rules with [Konveyor analyzer](https://github.com/konveyor/analyzer-lsp)
- **View your rules**: See [Rule Viewers Guide](RULE_VIEWERS.md)

## Real-World Example

Complete workflow for JDK 21 migration:

```bash
# 1. Generate rules from JEP 504
python scripts/generate_rules.py \
  --guide https://openjdk.org/jeps/504 \
  --source openjdk17 \
  --target openjdk21 \
  --output jdk21-applet-removal.yaml \
  --provider anthropic

# 2. Review output
cat jdk21-applet-removal.yaml

# 3. Use with Konveyor analyzer
kantra analyze \
  --input /path/to/your/java/app \
  --rules jdk21-applet-removal.yaml \
  --output analysis-results
```

That's it! You're now generating migration rules with AI. 🎉
