# Konveyor Rule Generator Skill

A Claude Code skill that helps you generate Konveyor analyzer migration rules from migration guides using AI.

## What is this skill?

This skill turns the analyzer-rule-generator into an interactive AI assistant within Claude Code. Instead of manually running command-line scripts, you can have a natural conversation with Claude to generate migration rules.

## Prerequisites

Before using this skill, ensure you have:

1. **Python 3.9+** installed
2. **Dependencies installed**: Run `pip install -r requirements.txt` in the project root
3. **API Key configured** for your preferred LLM provider:
   - `OPENAI_API_KEY` for OpenAI (default)
   - `ANTHROPIC_API_KEY` for Anthropic Claude
   - `GOOGLE_API_KEY` for Google Gemini

## Installation

The skill is already set up as a **project-level skill** in `.claude/skills/konveyor-rules/`. When you start Claude Code in this project directory, the skill will be automatically available.

To verify the skill is loaded, you can check the available skills in your Claude Code session.

## How to Use the Skill

### Starting the Skill

In your Claude Code session, invoke the skill using:

```
konveyor-rules
```

Or use the slash command:

```
/konveyor-rules
```

### Interactive Workflow

Once the skill is activated, Claude will guide you through the process:

1. **Provide the migration guide source**
   - Can be a URL (e.g., GitHub wiki)
   - Can be a local file path
   - Supported formats: Markdown, HTML, plain text

2. **Specify the source framework** (e.g., "spring-boot-3", "react-17")

3. **Specify the target framework** (e.g., "spring-boot-4", "react-18")

4. **Choose output directory** (optional, defaults to `examples/output/`)

5. **Select LLM provider** (optional, defaults to OpenAI)
   - `openai` - OpenAI GPT models
   - `anthropic` - Anthropic Claude models
   - `google` - Google Gemini models

### Example Conversations

#### Example 1: Simple Rule Generation

```
You: konveyor-rules

Claude: I'll help you generate Konveyor migration rules. Let me gather some information:
- What is the migration guide source (URL or file path)?
- What is the source framework?
- What is the target framework?

You: The guide is at https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide
Source is spring-boot-3, target is spring-boot-4

Claude: [Runs the rule generator and provides output analysis]
```

#### Example 2: With Custom Options

```
You: konveyor-rules

Claude: [Asks for information]

You: Guide: docs/django-migration.md
Source: django-3
Target: django-4
Provider: anthropic
Output: output/django-rules/

Claude: [Generates rules using Anthropic Claude and saves to specified directory]
```

#### Example 3: Quick Generation

You can also provide all information upfront:

```
You: Generate Konveyor rules from the React 18 migration guide at
https://react.dev/blog/2022/03/08/react-18-upgrade-guide
for react-17 to react-18 migration

Claude: [Activates skill automatically and processes your request]
```

## What the Skill Does

The skill will:

1. **Validate inputs** - Check that guide source exists and parameters are correct
2. **Run the generator** - Execute `scripts/generate_rules.py` with appropriate parameters
3. **Monitor progress** - Show you the extraction and generation process with automatic quality improvements
4. **Analyze output** - Review the generated YAML rule files
5. **Provide guidance** - Explain the results and suggest next steps

### Automatic Quality Improvements

The generator includes built-in quality improvements that run automatically during extraction:

- **Prevents false positives** - Detects and rejects overly broad patterns (6 patterns rejected in typical runs)
- **Adds import verification** - Common component names like "Text", "Button", "Modal" get automatic import checks to avoid conflicts with other libraries
- **Smart pattern enhancement** - Auto-converts simple patterns to combo rules with proper verification when needed
- **Reliable processing** - Adaptive chunking ensures large guides (90k+ chars) process smoothly without timeouts

You'll see these improvements in the logs as "Decision:" messages showing what was automatically fixed or enhanced.

## Output

The skill generates:

- **Individual rule files** - One YAML file per migration concern
- **Ruleset metadata** - A ruleset file with metadata
- **Generation summary** - Statistics about patterns found and rules created
- **Usage instructions** - How to use the rules with Konveyor analyzer-lsp

## Supported Languages

The generator supports migration rules for:

- Java
- TypeScript/JavaScript/React
- Go
- Python
- CSS

## Troubleshooting

### Skill not found

If you see "Unknown skill: konveyor-rules":
- Ensure you're in the project directory
- Restart your Claude Code session
- Verify `.claude/skills/konveyor-rules/SKILL.md` exists

### API Key errors

If you get API key errors:
- Check that your environment variable is set: `echo $OPENAI_API_KEY`
- Try exporting the key: `export OPENAI_API_KEY=your-key-here`
- Or specify it in `.env` file in the project root

### Python errors

If you get Python import errors:
- Ensure dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.9+)
- Try using a virtual environment

## Advanced Usage

### Using Different Models

You can specify a particular model:

```
You: Use the Claude Opus model for this generation
```

Claude will add the `--model` parameter with the appropriate model name.

### Custom Output Locations

You can organize outputs by migration type:

```
You: Save the Spring Boot 4 rules to examples/output/spring-boot-4.0/
```

### Batch Processing

You can ask to generate rules for multiple guides:

```
You: Generate rules for both the Spring Boot 4 migration guide and the
Spring Framework 6 migration guide
```

The skill will process them sequentially and organize the outputs.

## Best Practices

1. **Clear guide sources** - Ensure migration guides are comprehensive and well-structured
2. **Meaningful framework names** - Use clear, version-specific names (e.g., "spring-boot-3.2" vs "spring-boot-3")
3. **Review generated rules** - Always review and test rules before using in production
4. **Iterative refinement** - If rules aren't accurate, provide feedback to regenerate
5. **Save outputs** - Keep generated rules in version control for team use

## Next Steps After Generation

Once rules are generated, the skill will guide you on:

1. **Testing rules** - How to test with sample codebases
2. **Integration** - Adding rules to Konveyor analyzer-lsp
3. **Customization** - Adjusting patterns, effort levels, or messages
4. **Validation** - Ensuring rules catch real migration issues

## Demo and Examples

Want to see the skill in action or learn from examples?

- **[Quick Demo (2 min)](QUICK-DEMO.md)** - Fast demo script perfect for presentations
- **[Full Demo Script](DEMO.md)** - Comprehensive demo scenarios with 7 different use cases
- **[Example Conversations](examples.md)** - Real-world conversation examples showing different usage patterns

These resources are great for:
- Learning how to use the skill effectively
- Preparing presentations or demos
- Understanding best practices
- Troubleshooting common scenarios

## Contributing

To improve this skill:

1. Edit `.claude/skills/konveyor-rules/SKILL.md`
2. Test changes in a new Claude Code session
3. Submit improvements via pull request

## Support

For issues with:
- **The skill itself** - Open an issue in this repository
- **Claude Code** - Visit [Claude Code documentation](https://code.claude.com/docs)
- **Konveyor analyzer** - Visit [Konveyor documentation](https://konveyor.io)
