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

### Basic Usage

```bash
python scripts/generate_rules.py \
  --guide examples/guides/spring-boot-to-quarkus.md \
  --source spring-boot \
  --target quarkus \
  --output examples/output/spring-boot-to-quarkus.yaml
```

### With Specific Provider

```bash
# Using OpenAI GPT-4
python scripts/generate_rules.py \
  --guide examples/guides/spring-boot-to-quarkus.md \
  --source spring-boot \
  --target quarkus \
  --provider openai \
  --model gpt-4-turbo \
  --output examples/output/spring-boot-to-quarkus.yaml

# Using Anthropic Claude
python scripts/generate_rules.py \
  --guide examples/guides/spring-boot-to-quarkus.md \
  --source spring-boot \
  --target quarkus \
  --provider anthropic \
  --model claude-3-5-sonnet-20241022 \
  --output examples/output/spring-boot-to-quarkus.yaml

# Using Google Gemini
python scripts/generate_rules.py \
  --guide examples/guides/spring-boot-to-quarkus.md \
  --source spring-boot \
  --target quarkus \
  --provider google \
  --model gemini-1.5-pro \
  --output examples/output/spring-boot-to-quarkus.yaml
```

## Expected Output

The tool should:
1. Ingest the guide (~800 characters)
2. Extract 3 patterns using LLM
3. Generate 3 analyzer rules
4. Write YAML file to `examples/output/spring-boot-to-quarkus.yaml`

### Expected Rule Structure

```yaml
- ruleID: spring-boot-to-quarkus-00001
  description: "@RestController should be replaced with @Path"
  effort: 3
  category: mandatory
  labels:
    - konveyor.io/source=spring-boot
    - konveyor.io/target=quarkus
  when:
    or:
      - java.referenced:
          pattern: org.springframework.web.bind.annotation.RestController
          location: ANNOTATION
  message: "Spring @RestController must be replaced with JAX-RS @Path..."
  links:
    - url: "https://quarkus.io/guides/..."
      title: "quarkus Documentation"
  customVariables: []
```

## Verification

Check that generated rules have:
- ✓ Valid `ruleID` format
- ✓ `when` conditions with fully qualified names
- ✓ Appropriate `effort` scores (1-10)
- ✓ Correct `category` (mandatory/potential/optional)
- ✓ Proper labels with source/target frameworks
- ✓ Helpful `message` with migration guidance

## Status

**Dependencies**: ✅ Installed
**Test run**: ⏸️  Requires API key (user must provide)

To complete testing, set an API key and run the command above.
