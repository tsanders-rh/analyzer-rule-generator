# Quick Start Guide

Generate Konveyor analyzer rules from migration guides in 3 easy steps.

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

## Example 2: Generate from Local File

```bash
python scripts/generate_rules.py \
  --guide examples/guides/spring-boot-to-quarkus.md \
  --source spring-boot \
  --target quarkus \
  --output examples/output/spring-boot-to-quarkus.yaml \
  --provider openai
```

## Example 3: Use Different LLM Providers

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

## Output

The tool generates a YAML file with Konveyor analyzer rules:

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

### 1. Choose Good Migration Guides
✅ **Good:**
- Official upgrade guides with code examples
- Technical documentation with API changes
- JEPs, RFCs, or specification documents

❌ **Bad:**
- Marketing content or blog posts
- Guides without specific API details
- Purely conceptual documentation

### 2. Use Descriptive Framework Names
```bash
# Good
--source openjdk17 --target openjdk21
--source spring-boot-2 --target spring-boot-3

# Less helpful
--source old --target new
```

### 3. Review and Refine
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
- For critical migrations, use the hybrid approach (see [AI vs Manual Comparison](ai-vs-manual-comparison.md))

## Submitting Rules to Konveyor

After generating rules, you can prepare them for submission to the official Konveyor rulesets repository:

```bash
# Prepare submission package with tests
python scripts/prepare_submission.py \
  --rules examples/output/spring-boot-4.0/migration-rules.yaml \
  --source spring-boot-3.5 \
  --target spring-boot-4.0 \
  --guide-url "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide" \
  --output submission/spring-boot-4.0 \
  --data-dir-name mongodb
```

This creates a complete submission package with:
- Rule YAML file
- Test template with test cases for each rule
- Test data directory structure
- README with submission instructions

See [Konveyor Submission Guide](konveyor-submission-guide.md) for complete details on:
- Creating test applications
- Running tests with Kantra
- Submitting pull requests
- CI/CD requirements

## Next Steps

- **Submit to Konveyor**: See [Konveyor Submission Guide](konveyor-submission-guide.md)
- **Test your rules**: Use the generated rules with [Konveyor analyzer](https://github.com/konveyor/analyzer-lsp)
- **Learn the hybrid approach**: See [AI vs Manual Comparison](ai-vs-manual-comparison.md)
- **Advanced usage**: Check [Architecture Overview](ARCHITECTURE.md)

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
