# Analyzer Rule Generator Presentation Outline

## Slide 1: Title
**Analyzer Rule Generator**
*AI-Powered Migration Rule Generation for Konveyor*

[Your name/team]
[Date]

---

## Slide 2: The Problem
**Manual Rule Authoring is Slow and Error-Prone**

- Migration guides have hundreds of patterns to identify
- Writing Konveyor rules manually requires:
  - Deep understanding of analyzer-lsp rule schema
  - Knowledge of Java/TypeScript/Go language providers
  - Extracting patterns from verbose documentation
  - Creating test applications for validation
- **Time investment**: Days to weeks per migration guide
- **Barrier to contribution**: High technical knowledge required

---

## Slide 3: The Solution
**Automate Rule Generation with AI**

Turn migration guides into Konveyor rules automatically:
- **Input**: Migration guide URL or document
- **Output**: Production-ready analyzer rules + test applications
- **Time**: Minutes instead of days

*"From documentation to deployable rules in under 10 minutes"*

---

## Slide 4: How It Works
**Three-Stage AI Pipeline**

```
📄 Migration Guide → 🤖 LLM Extraction → 📋 Konveyor Rules
                   ↓
              🧪 Test Generation → 🎯 Validation
```

1. **Guide Ingestion**: Fetch and process documentation (supports URLs, Markdown, multi-page)
2. **Pattern Extraction**: LLM identifies migration patterns, FQNs, complexity
3. **Rule Generation**: Converts to Konveyor analyzer-lsp format
4. **Test Generation**: AI creates test applications with violations

---

## Slide 5: Key Features

**Multi-Language Support**
- Java (java.referenced provider)
- TypeScript/React/JavaScript (nodejs.referenced + builtin.filecontent)
- Go, Python, CSS (builtin providers)

**Intelligent Pattern Detection**
- Auto-detects language from guide content
- Extracts fully qualified names (Java)
- Generates regex patterns (TypeScript/React)
- Hybrid detection (combo rules) for TypeScript

**Migration Complexity Classification**
- Automatic complexity scoring (trivial → expert)
- Predicts AI automation success rates
- Helps prioritize migration work

---

## Slide 6: Real Results

**PatternFly v5 → v6 Migration**
- **Input**: PatternFly upgrade documentation
- **Output**: 41 comprehensive rules
- **Quality**: Hybrid detection (nodejs + builtin) eliminates false positives
- **Time saved**: ~2 weeks of manual authoring → 15 minutes

**Spring Boot 3 → 4 Migration**
- **Input**: GitHub wiki migration guide
- **Output**: Complete ruleset with effort scoring
- **Accuracy**: Correctly identifies deprecated APIs, annotation changes

---

## Slide 7: Developer Experience

**Two Ways to Use**

**1. Command Line**
```bash
python scripts/generate_rules.py \
  --guide https://spring.io/migration-guide \
  --source spring-boot-3 \
  --target spring-boot-4
```

**2. Claude Code Skill (Interactive)**
```
You: "Generate Konveyor rules from the React 18 migration guide"
Claude: [Guides you through the process conversationally]
```

---

## Slide 8: Integration with Konveyor Ecosystem

**Seamless Workflow**

1. **Generate Rules** → analyzer-rule-generator
2. **Submit Rules** → konveyor/rulesets (PR)
3. **Test Rules** → kantra local validation
4. **CI Integration** → go-konveyor-tests (automated test expectations)

**Included Tools**:
- Test data generator (AI-powered)
- CI test updater (automated expectations)
- Rule viewer (web-based exploration)
- Batch classification for existing rulesets

---

## Slide 9: Quality & Testing

**Built-in Validation**

- **Test Generation**: AI creates realistic code with violations
- **Local Testing**: Validate with kantra before submission
- **CI Integration**: Automated test expectations for go-konveyor-tests
- **Complexity Classification**: Predict automation success rates

**Example Test Output**:
```yaml
rulesPath: ../migration-rules.yaml
providers:
  - name: java
    dataPath: ./data/spring-boot
tests:
  - ruleID: spring-boot-3-to-4-00000
    testCases:
      - name: tc-1
        hasIncidents: {atLeast: 1}
```

---

## Slide 10: Flexibility

**Supports Multiple LLM Providers**
- OpenAI (GPT-4, GPT-4 Turbo)
- Anthropic (Claude 3.5 Sonnet, Opus)
- Google (Gemini)

**Customizable Output**
- Single-file or multi-file rulesets (grouped by concern)
- Configurable effort scoring
- Custom labels and metadata
- Batch processing for multiple guides

**Advanced Features**
- Follow links to sub-pages
- Configurable crawl depth
- Rate limiting for large guides
- Directory processing for multiple rulesets

---

## Slide 11: Migration Complexity Classification

**Automatic Complexity Scoring**

Classifies rules into 5 levels based on AI automation potential:

| Level | AI Success Rate | Example |
|-------|----------------|---------|
| Trivial | 95%+ | javax → jakarta namespace changes |
| Low | 80%+ | @Stateless → @ApplicationScoped |
| Medium | 60%+ | JMS → Reactive Messaging |
| High | 30-50% | Spring Security configuration |
| Expert | <30% | Custom security realm implementations |

**Benefits**:
- Resource allocation (junior vs senior devs)
- AI-assisted migration routing
- Realistic effort estimation

---

## Slide 12: Live Demo

**Let's Generate Some Rules**

[Demo using either CLI or Claude Code skill]

Example: Generate rules from a real migration guide
- Show input (URL/doc)
- Run generator
- Review output (rules YAML)
- Show generated test application
- Quick validation with kantra

---

## Slide 13: Success Metrics

**What Teams Are Saying**

- **Time Savings**: 90%+ reduction in rule authoring time
- **Accessibility**: Non-experts can contribute rules
- **Quality**: Comprehensive coverage of migration patterns
- **Validation**: Built-in test generation ensures accuracy

**Community Impact**:
- Faster response to new framework versions
- Lower barrier to Konveyor ruleset contributions
- Consistent rule quality across projects

---

## Slide 14: Roadmap

**Current Capabilities** ✅
- Java, TypeScript/React, Go, Python, CSS
- Multi-provider LLM support
- Test data generation
- Complexity classification

**Coming Soon** 🚀
- Additional language providers (C#, Ruby, PHP)
- Enhanced test generation (edge cases, negative tests)
- Rule refinement loop (iterative improvement)
- Integration with konveyor-iq evaluation framework

---

## Slide 15: Getting Started

**Try It Today**

**Prerequisites**:
- Python 3.9+
- LLM API key (OpenAI, Anthropic, or Google)

**Quick Start**:
```bash
git clone https://github.com/tsanders-rh/analyzer-rule-generator
cd analyzer-rule-generator
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"

python scripts/generate_rules.py \
  --guide https://your-migration-guide-url \
  --source framework-v1 \
  --target framework-v2
```

**Documentation**: [GitHub README](https://github.com/tsanders-rh/analyzer-rule-generator)

---

## Slide 16: Call to Action

**Join Us in Accelerating Migration**

**For Rule Authors**:
- Turn your migration guides into Konveyor rules
- Contribute to konveyor/rulesets
- Share feedback on generated rule quality

**For Framework Maintainers**:
- Auto-generate rules for your migration guides
- Provide users with automated migration detection
- Reduce migration friction

**For Contributors**:
- Extend language support
- Improve extraction algorithms
- Add new features

**Questions? Let's chat!**

---

## Optional Appendix Slides

### A1: Example Rule Output
```yaml
- ruleID: patternfly-v5-to-v6-00010
  description: isDisabled should be replaced with isAriaDisabled
  effort: 3
  category: potential
  labels:
    - konveyor.io/source=patternfly-v5
    - konveyor.io/target=patternfly-v6
  when:
    and:
      - builtin.filecontent:
          pattern: "import.*from ['\"@patternfly/react-core.*['\"]"
          filePattern: '\.(tsx|jsx|ts|js)$'
      - builtin.filecontent:
          pattern: 'isDisabled\s*[=:]'
          filePattern: '\.(tsx|jsx|ts|js)$'
  message: |
    The isDisabled prop has been renamed to isAriaDisabled for better accessibility.
    Replace `isDisabled` with `isAriaDisabled`.
  links:
    - url: "https://www.patternfly.org/get-started/upgrade/"
      title: "PatternFly v6 Upgrade Guide"
  migration_complexity: low
```

### A2: Architecture Diagram
[Visual showing the three stages: Ingestion → Extraction → Generation]

### A3: Comparison Table
| Approach | Time Required | Expertise Needed | Test Coverage |
|----------|--------------|------------------|---------------|
| Manual | Days-Weeks | High | Manual |
| analyzer-rule-generator | Minutes | Low | Automated |

### A4: FAQ
**Q: Does it work with private/internal migration guides?**
A: Yes, supports local files and URLs.

**Q: Can I customize the generated rules?**
A: Yes, edit the YAML output as needed.

**Q: What if the LLM makes mistakes?**
A: Review and refine. Test generation helps catch issues early.

**Q: Cost of LLM API calls?**
A: Typically $0.10-$2.00 per migration guide depending on size and provider.

---

## Presentation Tips

**For a 15-minute presentation**: Slides 1-9, 12 (demo), 15-16
**For a 30-minute presentation**: Include slides 10-11, 13-14
**For a technical deep-dive**: Add appendix slides, show more code examples

**Key Messages to Emphasize**:
1. **Time savings**: 90%+ reduction in authoring time
2. **Accessibility**: Non-experts can contribute
3. **Integration**: Works seamlessly with Konveyor ecosystem
4. **Quality**: AI-generated + automated testing = reliable rules
