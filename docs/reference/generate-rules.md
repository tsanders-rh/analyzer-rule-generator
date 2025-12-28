# Generate Rules Script Reference

Complete reference documentation for the `generate_rules.py` script.

## Table of Contents

- [Overview](#overview)
- [Installation & Setup](#installation--setup)
- [Basic Usage](#basic-usage)
- [Command-Line Arguments](#command-line-arguments)
- [Input Sources](#input-sources)
- [LLM Providers](#llm-providers)
- [Output Structure](#output-structure)
- [How It Works](#how-it-works)
- [Advanced Usage](#advanced-usage)
- [Examples by Framework](#examples-by-framework)
- [Troubleshooting](#troubleshooting)

## Overview

The `generate_rules.py` script automatically generates Konveyor analyzer rules from migration guides or OpenRewrite recipes using Large Language Models (LLMs). It extracts migration patterns from documentation and converts them into structured YAML rules that can be used by the Konveyor analyzer for static code analysis.

**Key Features:**
- Supports multiple input formats (URLs, local files, OpenRewrite recipes)
- Automatic language detection (Java, TypeScript, React, Go, Python, etc.)
- Smart provider selection (Java provider for Java, Builtin provider for others)
- Multiple LLM providers (OpenAI, Anthropic, Google)
- Organized output with concerns-based file grouping
- Automatic ruleset metadata generation

## Installation & Setup

### Prerequisites

- Python 3.9 or higher
- API key for at least one LLM provider (OpenAI, Anthropic, or Google)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure API Keys

Set your LLM provider API key as an environment variable:

```bash
# OpenAI
export OPENAI_API_KEY="your-key-here"

# Anthropic
export ANTHROPIC_API_KEY="your-key-here"

# Google
export GOOGLE_API_KEY="your-key-here"
```

Alternatively, you can pass the API key directly using the `--api-key` argument.

## Basic Usage

### From Migration Guide

```bash
python scripts/generate_rules.py \
  --guide <path_or_url> \
  --source <source-framework> \
  --target <target-framework>
```

### From OpenRewrite Recipe

```bash
python scripts/generate_rules.py \
  --from-openrewrite <path_or_url> \
  --source <source-framework> \
  --target <target-framework>
```

### Minimal Example

```bash
python scripts/generate_rules.py \
  --guide https://example.com/migration-guide \
  --source spring-boot-3 \
  --target spring-boot-4
```

## Command-Line Arguments

### Required Arguments

#### Input Source (Mutually Exclusive)

**`--guide <path_or_url>`**
- Path or URL to a migration guide
- Supports: URLs, local files (markdown, text)
- Example: `--guide https://github.com/org/repo/wiki/Migration-Guide`
- Example: `--guide ./migration-guide.md`

**`--from-openrewrite <path_or_url>`**
- Path or URL to OpenRewrite recipe YAML file
- Optimized prompts for OpenRewrite recipe format
- Example: `--from-openrewrite https://example.com/recipe.yml`

**Note:** You must specify either `--guide` or `--from-openrewrite`, but not both.

#### Framework Identification

**`--source <framework>`**
- Name of the source framework/version
- Used for labeling and pattern detection
- Example: `--source spring-boot-3`
- Example: `--source patternfly-v5`

**`--target <framework>`**
- Name of the target framework/version
- Used for labeling and output file naming
- Example: `--target spring-boot-4`
- Example: `--target patternfly-v6`

### Optional Arguments

**`--output <directory>`**
- Output directory for generated YAML files
- Auto-generated if not specified: `examples/output/{base-name}/`
- Auto-generation removes version suffixes (e.g., `patternfly-v5` → `patternfly`)
- Example: `--output ./my-rules`

**`--provider <provider>`**
- LLM provider to use
- Choices: `openai`, `anthropic`, `google`
- Default: `openai`
- Example: `--provider anthropic`

**`--model <model-name>`**
- Specific model to use with the provider
- Uses provider default if not specified
- OpenAI default: `gpt-4o`
- Anthropic default: `claude-3-5-sonnet-20241022`
- Google default: `gemini-2.0-flash-exp`
- Example: `--model gpt-4o-mini`

**`--api-key <key>`**
- API key for the LLM provider
- Uses environment variable if not specified
- Environment variables: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`
- Example: `--api-key sk-...`

**`--follow-links`**
- Follow related links from migration guides (optional)
- Automatically discovers and processes linked content (release notes, breaking changes, etc.)
- Useful for comprehensive migration guides with multiple pages
- Example: `--follow-links`

**`--max-depth <number>`**
- Maximum depth for recursive link following (optional)
- Only used when `--follow-links` is enabled
- Default: 2
- Example: `--max-depth 1` (follow only direct links, not nested)

## Input Sources

### Migration Guides

Migration guides are documentation that describes how to migrate from one version/framework to another. The script can process:

**Supported Formats:**
- Web pages (HTML converted to markdown)
- Markdown files (`.md`)
- Plain text files (`.txt`)
- GitHub wiki pages
- Documentation sites

**Best Practices:**
- Use comprehensive guides with specific migration patterns
- Guides should include code examples and explanations
- Links to official documentation work best

**Example Sources:**
- Spring Boot migration guides
- PatternFly upgrade documentation
- Framework-specific migration docs

### OpenRewrite Recipes

OpenRewrite recipes are YAML files that describe automated code transformations. The script uses specialized prompts to extract patterns from recipe definitions.

**Recipe Structure:**
- YAML format with transformation rules
- Includes search patterns and replacements
- Metadata about the transformation

**Example:**
```bash
python scripts/generate_rules.py \
  --from-openrewrite https://github.com/openrewrite/rewrite-spring/blob/main/recipes/spring-boot-3.yml \
  --source spring-boot-2 \
  --target spring-boot-3
```

## LLM Providers

### OpenAI

**Setup:**
```bash
export OPENAI_API_KEY="sk-..."
```

**Usage:**
```bash
python scripts/generate_rules.py \
  --provider openai \
  --model gpt-4o \
  ...
```

**Available Models:**
- `gpt-4o` (default, recommended)
- `gpt-4o-mini` (faster, lower cost)
- `gpt-4-turbo`

### Anthropic Claude

**Setup:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Usage:**
```bash
python scripts/generate_rules.py \
  --provider anthropic \
  --model claude-3-5-sonnet-20241022 \
  ...
```

**Available Models:**
- `claude-3-5-sonnet-20241022` (default, recommended)
- `claude-3-5-haiku-20241022` (faster, lower cost)
- `claude-3-opus-20240229`

### Google Gemini

**Setup:**
```bash
export GOOGLE_API_KEY="..."
```

**Usage:**
```bash
python scripts/generate_rules.py \
  --provider google \
  --model gemini-2.0-flash-exp \
  ...
```

**Available Models:**
- `gemini-2.0-flash-exp` (default, recommended)
- `gemini-1.5-pro`

## Output Structure

### Directory Layout

When you run the script with auto-generated output (no `--output` specified):

```
examples/output/{technology}/
├── ruleset.yaml                          # Ruleset metadata
└── {source}-to-{target}.yaml             # Rules (single concern)
```

Or with multiple concerns:

```
examples/output/{technology}/
├── ruleset.yaml                          # Ruleset metadata
├── {source}-to-{target}-general.yaml     # General rules
├── {source}-to-{target}-security.yaml    # Security rules
└── {source}-to-{target}-performance.yaml # Performance rules
```

### File Naming

**Ruleset Metadata:** `ruleset.yaml`
- Required by Konveyor analyzer
- Contains ruleset name and description

**Rule Files:**
- Single concern: `{source}-to-{target}.yaml`
- Multiple concerns: `{source}-to-{target}-{concern}.yaml`
- Concern examples: `general`, `security`, `performance`, `api-changes`

### Generated Files

**`ruleset.yaml` Example:**
```yaml
name: spring-boot-3/spring-boot-4
description: This ruleset provides guidance for migrating from spring-boot-3 to spring-boot-4
```

**Rule File Example:**
```yaml
- ruleID: spring-boot-3-to-spring-boot-4-00001
  description: Replace deprecated Spring Boot 3 annotations
  effort: 3
  category: mandatory
  labels:
    - konveyor.io/source=spring-boot-3
    - konveyor.io/target=spring-boot-4
  when:
    java.referenced:
      pattern: org.springframework.web.bind.annotation.RestController
      location: ANNOTATION
  message: "Review Spring Boot 4.0 migration requirements for REST controllers"
  links:
    - url: "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide"
      title: "Spring Boot 4.0 Migration Guide"
  migration_complexity: low
```

## How It Works

### Processing Pipeline

The script follows a three-step process:

**Step 1: Ingestion**
- Downloads or reads the input source
- Converts HTML to markdown (for web pages)
- Prepares content for LLM processing

**Step 2: Pattern Extraction**
- Sends content to LLM with specialized prompts
- LLM identifies migration patterns
- Extracts:
  - Description and message
  - Complexity/effort level (1-10)
  - Migration complexity (trivial, low, medium, high, expert)
  - Category (mandatory, potential, optional)
  - Concern (security, performance, etc.)
  - Language-specific patterns

**Step 3: Rule Generation**
- Converts patterns to Konveyor rule format
- Groups rules by concern
- Generates unique rule IDs
- Writes YAML files
- Creates ruleset metadata

### Provider Selection Logic

The script automatically selects the appropriate Konveyor provider based on detected language:

**Java Provider:**
- Used for: Java code
- Pattern format: Fully qualified class names
- Locations: ANNOTATION, METHOD_CALL, CONSTRUCTOR_CALL, etc.
- Example: `org.springframework.web.bind.annotation.RestController`

**Builtin Provider:**
- Used for: TypeScript, JavaScript, React, Go, Python, CSS, etc.
- Pattern format: Regular expressions
- File patterns: Glob patterns (e.g., `*.{tsx,jsx}`)
- Example: `isDisabled\s*[=:]`

### Rule ID Format

Rules are assigned sequential IDs:
```
{source}-to-{target}-{number}
```

Example: `spring-boot-3-to-spring-boot-4-00001`

The number is zero-padded to 5 digits and increments globally across all concerns (rule IDs are globally unique, not per-concern).

### Post-Generation Validation (Experimental)

After rules are generated, the script automatically runs LLM-based quality validation to detect and fix common issues. This is an experimental feature that may use additional API credits.

**What Gets Validated:**

1. **Import Verification (JavaScript/TypeScript + PatternFly only)**
   - Adds import verification to rules that reference PatternFly components
   - Prevents false positives from matching component names in comments or non-PatternFly code
   - Only runs when both conditions are met:
     - Language is JavaScript or TypeScript
     - Source/target frameworks contain "patternfly"

2. **Overly Broad Patterns**
   - Detects patterns that are too short or generic
   - Warns about patterns that may match unintended code
   - Example: Pattern `ab` would match `about`, `table`, `abs()`, etc.

3. **Pattern Quality Review**
   - Checks if patterns accurately detect what the description claims
   - Suggests improvements for better specificity

4. **Duplicate Detection**
   - Identifies rules with identical or very similar patterns
   - Helps avoid redundant rules in the ruleset

**Example Output:**

```
================================================================================
POST-GENERATION VALIDATION
================================================================================

→ Checking for missing import verification...
  ! Rule patternfly-v5-to-v6-00010 needs import verification
  ✓ Applied import verification to patternfly-v5-to-v6-00010

→ Checking for overly broad patterns...
  ! Rule test-00020 has overly broad pattern

→ Reviewing pattern quality...

→ Checking for duplicates...

✓ Validation complete
  - 1 rules improved
  - 1 issues detected
```

**Import Verification Example:**

Before validation:
```yaml
when:
  nodejs.referenced:
    pattern: Alert
```

After validation (import verification added):
```yaml
when:
  and:
    - builtin.filecontent:
        pattern: import.*\{[^}]*\bAlert\b[^}]*\}.*from ['"]@patternfly/react-
        filePattern: \.(j|t)sx?$
    - builtin.filecontent:
        pattern: <Alert[^/>]*(?:/>|>)
        filePattern: \.(j|t)sx?$
```

**Automatic Improvements:**

The validator can automatically apply certain improvements:
- **Import verification**: Automatically added to eligible rules
- **Pattern refinements**: Applied if validation confidence is high
- **Other issues**: Reported but require manual review

**Cost Considerations:**

This validation step uses the same LLM provider as rule generation. For a typical ruleset:
- 50 rules: ~$0.10-0.25 in additional API costs
- 200 rules: ~$0.50-1.00 in additional API costs

The validation is fast (runs in parallel with rule writing) and typically adds less than 10 seconds to total generation time.

**Disabling Validation:**

Currently, post-generation validation always runs during rule generation. To skip it, you would need to modify the `generate_rules.py` script. A future enhancement may add a `--skip-validation` flag.

## Advanced Usage

### Using Specific Models

Use a different model for cost optimization:

```bash
# OpenAI with cheaper model
python scripts/generate_rules.py \
  --provider openai \
  --model gpt-4o-mini \
  --guide https://example.com/guide \
  --source old-version \
  --target new-version
```

### Custom Output Directory

Organize rules in a custom location:

```bash
python scripts/generate_rules.py \
  --guide ./migration-guide.md \
  --source v1 \
  --target v2 \
  --output ./custom/output/path
```

### Using Local Files

Process local documentation:

```bash
python scripts/generate_rules.py \
  --guide ./docs/migration.md \
  --source framework-1.0 \
  --target framework-2.0
```

### Inline API Key

Provide API key directly (useful for CI/CD):

```bash
python scripts/generate_rules.py \
  --guide https://example.com/guide \
  --source v1 \
  --target v2 \
  --provider anthropic \
  --api-key $SECRET_API_KEY
```

## Examples by Framework

### Java (Spring Boot)

```bash
python scripts/generate_rules.py \
  --guide https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide \
  --source spring-boot-3 \
  --target spring-boot-4 \
  --provider openai
```

**Output:** Java provider rules with fully qualified class names

### TypeScript/React (PatternFly)

```bash
python scripts/generate_rules.py \
  --guide https://www.patternfly.org/get-started/upgrade/ \
  --source patternfly-v5 \
  --target patternfly-v6 \
  --follow-links \
  --max-depth 1 \
  --provider anthropic
```

**Output:** Builtin provider rules with regex patterns and file globs
**Note:** Using `--follow-links` extracts patterns from multiple related pages (41 rules vs 10 rules without)

### Go

```bash
python scripts/generate_rules.py \
  --guide https://example.com/go-framework-migration \
  --source go-framework-v1 \
  --target go-framework-v2 \
  --provider google
```

**Output:** Builtin provider rules for `.go` files

### From OpenRewrite Recipe

```bash
python scripts/generate_rules.py \
  --from-openrewrite https://github.com/openrewrite/rewrite-spring/blob/main/recipes/spring-boot-3.yml \
  --source spring-boot-2 \
  --target spring-boot-3 \
  --provider openai
```

**Output:** Rules extracted from OpenRewrite transformations

## Troubleshooting

### Common Issues

#### No Patterns Extracted

**Symptoms:**
```
Error: No patterns extracted
```

**Causes:**
- Migration guide has insufficient detail
- Content is not accessible (404, auth required)
- LLM API issues

**Solutions:**
- Verify the guide URL is accessible
- Check that the guide contains specific migration patterns
- Try a different LLM provider or model
- Check API key is valid

#### LLM API Errors

**Symptoms:**
```
Error: Failed to extract patterns
API Error: ...
```

**Causes:**
- Invalid or expired API key
- Rate limiting
- Network issues
- Insufficient credits

**Solutions:**
- Verify API key: `echo $OPENAI_API_KEY`
- Check API provider status
- Wait and retry (for rate limits)
- Use `--api-key` to provide key directly

#### Empty Output Files

**Symptoms:**
- Files created but contain no rules
- Only `ruleset.yaml` is generated

**Causes:**
- Patterns extracted but conversion failed
- Language detection issues

**Solutions:**
- Check the generation log for errors
- Verify source/target names are descriptive
- Try with a more detailed migration guide

#### File Permission Errors

**Symptoms:**
```
Error: Permission denied writing to ...
```

**Solutions:**
- Ensure you have write permissions to output directory
- Use a different output path with `--output`
- Check disk space

### Debugging Tips

**1. Check API Key**
```bash
# Verify environment variable is set
echo $OPENAI_API_KEY
```

**2. Test with Simple Guide**
```bash
# Use a known working guide to verify setup
python scripts/generate_rules.py \
  --guide https://www.patternfly.org/get-started/upgrade/ \
  --source test-v1 \
  --target test-v2
```

**3. Try Different Provider**
```bash
# If one provider fails, try another
python scripts/generate_rules.py \
  --guide ./guide.md \
  --source v1 \
  --target v2 \
  --provider anthropic  # or google
```

**4. Verify Input Content**
```bash
# For local files, check content is readable
cat ./migration-guide.md

# For URLs, check accessibility
curl -I https://example.com/guide
```

**5. Check Output Directory**
```bash
# Ensure directory is writable
ls -la examples/output/
```

### Getting Help

If you encounter issues not covered here:

1. Check the [main README](../README.md) for general guidance
2. Review the [Konveyor documentation](https://github.com/konveyor/analyzer-lsp)
3. Open an issue with:
   - Command used
   - Error message
   - LLM provider and model
   - Input source (if shareable)

## Related Documentation

- [Konveyor Submission Guide](../guides/konveyor-submission-guide.md) - End-to-end workflow
- [Updating CI Tests](../guides/updating-ci-tests.md) - Step-by-step guide for go-konveyor-tests
- [Java Rule Schema](java-rule-schema.md) - Rule structure reference
- [Rule Viewers Guide](rule-viewers.md) - Viewing generated rules
- [CI Test Updater Reference](ci-test-updater.md) - Script documentation
