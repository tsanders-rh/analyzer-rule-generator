# AI-Generated vs Manual Rule Generation Comparison

Comparing two approaches for generating Konveyor rules for JDK 21 Applet API removal (JEP 504).

## Approach 1: Manual (JavaRemovalRuleGenerator)

**Command:**
```bash
python scripts/generate_jdk21_applet_rules.py
```

**Results:**
- **Rules generated:** 6
- **Categories:** All mandatory
- **Effort range:** 5-7
- **Detection patterns:** Multiple locations per API (IMPORT, TYPE, INHERITANCE, CONSTRUCTOR_CALL)

**Pros:**
- ✅ More comprehensive detection (multiple location types)
- ✅ Precise, deterministic rules
- ✅ Better categorization (all mandatory since APIs are removed)
- ✅ No LLM cost
- ✅ Faster generation

**Cons:**
- ❌ Requires manual specification of each API
- ❌ Requires understanding of Konveyor rule structure
- ❌ Less flexible for ad-hoc migrations

## Approach 2: AI-Powered (LLM Extraction)

**Command:**
```bash
python scripts/generate_rules.py \
  --guide https://openjdk.org/jeps/504 \
  --source openjdk17 \
  --target openjdk21 \
  --output examples/output/jdk21/applet-removal-ai.yaml \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219
```

**Results:**
- **Rules generated:** 9
- **Categories:** 8 potential, 1 mandatory
- **Effort range:** 1-5
- **Detection patterns:** Single location per rule (mostly TYPE)

**Pros:**
- ✅ Discovered additional patterns (URL.getContent() casts)
- ✅ Zero code required - just point at guide
- ✅ Can extract from any migration documentation
- ✅ Caught package-level import pattern

**Cons:**
- ❌ Less comprehensive per-rule detection (single location)
- ❌ Overly conservative categorization (most as "potential")
- ❌ LLM cost and latency
- ❌ Non-deterministic results
- ❌ May miss edge cases

## Detailed Comparison

### Coverage

| API | Manual | AI | Winner |
|-----|--------|----|----|
| `java.applet.Applet` | ✅ (4 locations) | ✅ (TYPE only) | Manual |
| `java.applet.AppletContext` | ✅ (3 locations) | ✅ (TYPE only) | Manual |
| `java.applet.AppletStub` | ✅ (3 locations) | ✅ (TYPE only) | Manual |
| `java.applet.AudioClip` | ✅ (3 locations) | ✅ (TYPE only) | Manual |
| `javax.swing.JApplet` | ✅ (4 locations) | ✅ (TYPE only) | Manual |
| `java.beans.AppletInitializer` | ✅ (3 locations) | ✅ (TYPE only) | Manual |
| Package import `java.applet` | ❌ | ✅ | AI |
| `URL.getContent()` AudioClip cast | ❌ | ✅ | AI |
| `URLConnection.getContent()` cast | ❌ | ✅ | AI |

### Rule Quality

**Manual:**
- Specific, actionable messages with alternatives
- Example: "For Swing applications, migrate to JFrame or JPanel. Example: Before: public class MyApplet extends JApplet, After: public class MyApp extends JFrame"

**AI:**
- Generic guidance
- Example: "The Applet API is being removed as it's obsolete. Web browsers no longer support applets. Replace java.applet.Applet with Use AWT components instead."

## Recommendations

### Use Manual Generation When:
- You know the exact APIs being removed/changed
- You need comprehensive detection patterns
- You want deterministic, high-quality rules
- Migration is well-defined (e.g., JDK upgrades)

### Use AI Generation When:
- Exploring a new migration guide
- Don't know all the affected APIs upfront
- Need to quickly assess migration scope
- Documentation is narrative/unstructured

### Hybrid Approach (Best):
1. **Start with AI** to discover patterns from documentation
2. **Review and refine** the extracted patterns
3. **Use manual generator** for production rules with comprehensive detection
4. **Add AI-discovered edge cases** (like URL.getContent() casts) to manual spec

## Example Hybrid Workflow

```bash
# 1. AI discovery
python scripts/generate_rules.py \
  --guide https://openjdk.org/jeps/504 \
  --source openjdk17 --target openjdk21 \
  --output examples/output/jdk21/discovered.yaml

# 2. Review AI output, identify APIs
# 3. Create manual spec with discovered APIs
# 4. Generate production rules
python scripts/generate_jdk21_applet_rules.py

# 5. Manually add any unique AI patterns (e.g., URL casts)
```

## Conclusion

Both approaches have value:
- **Manual generator** produces higher-quality, more comprehensive rules
- **AI generator** discovers patterns you might miss

The **hybrid approach** leverages the strengths of both: AI for discovery, manual generation for production quality.
