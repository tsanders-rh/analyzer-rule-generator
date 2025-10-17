# Testing the Analyzer Rule Generator

## Prerequisites

1. **Install dependencies**:
   ```bash
   cd /Users/tsanders/Workspace/analyzer-rule-generator
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set up API key**:
   ```bash
   # Copy example env file
   cp .env.example .env

   # Edit .env and add your API key
   # Choose one provider: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY
   ```

3. **Load environment**:
   ```bash
   source .env
   # or
   export OPENAI_API_KEY="sk-your-key-here"
   ```

## Run the Tool

### Example 1: Java Migration (Spring Boot 3 to 4)

```bash
python scripts/generate_rules.py \
  --guide https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide \
  --source spring-boot-3 \
  --target spring-boot-4 \
  --output examples/output/spring-boot-4.0/migration-rules.yaml
```

### Example 2: TypeScript/React Migration (PatternFly)

```bash
python scripts/generate_rules.py \
  --guide https://www.patternfly.org/get-started/upgrade/ \
  --source patternfly-v5 \
  --target patternfly-v6 \
  --output examples/output/patternfly-v6/migration-rules.yaml
```

### With Specific Provider

```bash
# Using OpenAI GPT-4
python scripts/generate_rules.py \
  --guide https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide \
  --source spring-boot-3 \
  --target spring-boot-4 \
  --provider openai \
  --model gpt-4-turbo \
  --output examples/output/spring-boot-4.0/migration-rules.yaml

# Using Anthropic Claude (Recommended)
python scripts/generate_rules.py \
  --guide https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide \
  --source spring-boot-3 \
  --target spring-boot-4 \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219 \
  --output examples/output/spring-boot-4.0/migration-rules.yaml

# Using Google Gemini
python scripts/generate_rules.py \
  --guide https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide \
  --source spring-boot-3 \
  --target spring-boot-4 \
  --provider google \
  --model gemini-1.5-pro \
  --output examples/output/spring-boot-4.0/migration-rules.yaml
```

## Expected Output

The tool should:
1. Fetch the migration guide from URL
2. Extract migration patterns using LLM
3. Generate analyzer rules based on detected language
4. Write YAML file to specified output path

### Expected Rule Structure (Java)

```yaml
- ruleID: spring-boot-3-to-spring-boot-4-00001
  description: "Update deprecated Spring Boot 3 API"
  effort: 3
  category: mandatory
  labels:
    - konveyor.io/source=spring-boot-3
    - konveyor.io/target=spring-boot-4
  when:
    java.referenced:
      pattern: org.springframework.boot.SomeDeprecatedClass
      location: IMPORT
  message: "Spring Boot 4.0 requires migration from deprecated API..."
  links:
    - url: "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide"
      title: "Spring Boot 4.0 Migration Guide"
```

### Expected Rule Structure (TypeScript/React)

```yaml
- ruleID: patternfly-v5-to-patternfly-v6-00001
  description: "isDisabled prop renamed to isAriaDisabled"
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
  links:
    - url: "https://www.patternfly.org/get-started/upgrade/"
      title: "PatternFly Upgrade Guide"
```

## Verification

Check that generated rules have:
- ✓ Valid `ruleID` format (`source-to-target-NNNNN`)
- ✓ `when` conditions appropriate to detected language:
  - **Java**: `java.referenced` with FQN and location type
  - **TypeScript/React/Go/Python**: `builtin.filecontent` with regex and file pattern
- ✓ Appropriate `effort` scores (1-10)
- ✓ Correct `category` (mandatory/potential/optional)
- ✓ Proper labels with source/target frameworks
- ✓ Helpful `message` with migration guidance
- ✓ Links to relevant documentation

## Viewing Generated Rules

Generate an interactive HTML viewer:

```bash
python scripts/generate_rule_viewer.py \
  --rules examples/output/spring-boot-4.0/migration-rules.yaml \
  --output viewer.html \
  --open
```

Or use the web-based viewer at: https://tsanders-rh.github.io/analyzer-rule-generator/rule-viewer.html

## Status

**Dependencies**: ✅ Installed
**Test run**: ⏸️  Requires API key (user must provide)

To complete testing, set an API key and run the commands above.
