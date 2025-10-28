# OpenRewrite Integration Demos

Demo recordings showing the new OpenRewrite → Konveyor integration.

## Prerequisites

Install [VHS](https://github.com/charmbracelet/vhs) (terminal recorder):

```bash
brew install vhs
```

## Available Demos

### 1. Complete Workflow Demo (`openrewrite-demo.tape`)

**Duration:** ~60 seconds
**Shows:**
- Generating Konveyor rules from OpenRewrite Java 11→17 recipe
- Multiple rule categories (security, reflection, threading, etc.)
- Auto-generating test data with violations
- Complete end-to-end workflow

**Run:**
```bash
vhs media/openrewrite-demo.tape
```

**Output:** `media/openrewrite-demo.mp4`

---

### 2. Spring Boot Migration Demo (`openrewrite-spring-boot-demo.tape`)

**Duration:** ~50 seconds
**Shows:**
- Spring Boot 2.7 → 3.0 migration rules
- Code transformations (JPA, Security, Testing)
- Properties file migrations
- Real-world enterprise use case

**Run:**
```bash
vhs media/openrewrite-spring-boot-demo.tape
```

**Output:** `media/openrewrite-spring-boot-demo.mp4`

---

## What This Enables

### Before (Manual Rule Writing)
1. Read OpenRewrite recipe YAML
2. Understand transformation logic
3. Manually write detection patterns
4. Create test applications by hand
5. Hours of work per migration

### After (Automated with LLM)
1. Point to OpenRewrite recipe URL
2. Generate Konveyor rules automatically
3. Generate test data automatically
4. Minutes of work per migration

## OpenRewrite Recipe Coverage

The integration works with **500+ OpenRewrite recipes**, including:

**Java Ecosystem:**
- Java 8 → 11 → 17 → 21 → 25
- Spring Boot (all versions from 2.0 → 4.0)
- Jakarta EE / JavaEE migrations
- JUnit 4 → 5, Mockito, TestNG
- Guava, Lombok, Apache Commons

**Key Benefits:**
- ✅ Leverage OpenRewrite's battle-tested migration knowledge
- ✅ Expand Konveyor's coverage rapidly
- ✅ Both code AND configuration file patterns
- ✅ Auto-organized by migration concern
- ✅ Test data generation included

## Example Commands

### Java Version Migration
```bash
python scripts/generate_rules.py \
  --from-openrewrite https://raw.githubusercontent.com/openrewrite/rewrite-migrate-java/main/src/main/resources/META-INF/rewrite/java-version-17.yml \
  --source java11 \
  --target java17
```

### Spring Boot Upgrade
```bash
python scripts/generate_rules.py \
  --from-openrewrite https://raw.githubusercontent.com/openrewrite/rewrite-spring/main/src/main/resources/META-INF/rewrite/spring-boot-30.yml \
  --source spring-boot-2 \
  --target spring-boot-3
```

### Local Recipe File
```bash
python scripts/generate_rules.py \
  --from-openrewrite ./my-custom-recipe.yml \
  --source framework-v1 \
  --target framework-v2
```

## Sharing with Team

After generating the demo videos:

1. **Share the video:**
   ```bash
   # Videos are in media/
   open media/openrewrite-demo.mp4
   ```

2. **Upload to GitHub/Slack/Teams:**
   - Drag and drop the .mp4 file
   - Or convert to GIF: `vhs media/openrewrite-demo.tape --output demo.gif`

3. **Include in presentations:**
   - Embed in slides
   - Share URL if uploaded to cloud storage

## Customizing Demos

Edit the `.tape` files to:
- Change timing: Adjust `Sleep` durations
- Use different recipes: Modify URLs
- Change theme: Update `Set Theme` (see [VHS docs](https://github.com/charmbracelet/vhs))
- Adjust size: Modify `Width` and `Height`

## Tips for Recording

**Before running:**
1. Clean up old output directories:
   ```bash
   rm -rf examples/output/openrewrite-demo
   ```

2. Set API key:
   ```bash
   export ANTHROPIC_API_KEY="your-key"
   ```

3. Activate venv (if needed):
   ```bash
   source venv/bin/activate
   ```

**VHS will handle the rest automatically!**

## Related Documentation

- [OpenRewrite Recipes](https://docs.openrewrite.org/recipes)
- [Main README](../README.md)
- [Rule Viewer](https://tsanders-rh.github.io/analyzer-rule-generator/rule-viewer.html)
