# Blog Post Demo Script

## Preparation (Before Demo/Screenshots)

```bash
# Ensure you're in the repo
cd /Users/tsanders/Workspace/analyzer-rule-generator

# Make sure dependencies are installed
source venv/bin/activate

# Set API key (use your preferred provider)
export ANTHROPIC_API_KEY="your-key"
# or
export OPENAI_API_KEY="your-key"
```

## Demo: Generate Spring Boot 4.0 Rules

### Command to Run

```bash
python scripts/generate_rules.py \
  --guide "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide" \
  --source spring-boot-3 \
  --target spring-boot-4 \
  --output blog-demo-spring-boot-4.yaml \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219
```

### Screenshot 1: Terminal Output During Generation

**When to capture:** During rule generation (shows AI working)

**What to show:**
- Terminal window with the command running
- LLM processing output showing:
  - "Fetching migration guide..."
  - "Analyzing content..."
  - "Detected X migration patterns"
  - "Generating rules..."
- Progress indicators

**Timing:** Capture after first few rules are displayed

**File name:** `screenshot-1-generating-rules.png`

---

### Screenshot 2: Generated Rules in Rule Viewer

**Steps:**
1. Open https://tsanders-rh.github.io/analyzer-rule-generator/rule-viewer.html
2. Click "Load from File"
3. Select `blog-demo-spring-boot-4.yaml`
4. Rules will display in the viewer

**What to capture:**
- Browser window showing the rule viewer
- Left sidebar: List of generated rules with IDs
- Main panel: One rule expanded showing:
  - Description
  - Effort score
  - When condition (showing the pattern)
  - Message
  - Links to documentation

**Good rule to highlight:** MongoDB property migration rule (clear, simple pattern)

**File name:** `screenshot-2-rule-viewer.png`

---

### Screenshot 3: Generated Test Data (Optional but Powerful)

**Command to run:**
```bash
python scripts/generate_test_data.py \
  --rules blog-demo-spring-boot-4.yaml \
  --output blog-demo-test-data \
  --source spring-boot-3 \
  --target spring-boot-4 \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219
```

**After generation, open in VS Code:**
```bash
code blog-demo-test-data
```

**What to capture:**
- VS Code window with two panes:
  - Left: `pom.xml` showing Spring Boot 3.x parent
  - Right: Java file showing deprecated code with comments
    - Example: `@Value("${spring.data.mongodb.host}")`
    - Comment above: `// Rule: spring-boot-3-to-spring-boot-4-00010`

**File name:** `screenshot-3-test-data.png`

---

## Alternative Screenshot Ideas

### Option A: Before/After Comparison

Create a side-by-side showing:
- **Left:** Spring Boot migration guide excerpt (browser)
- **Right:** Generated Konveyor rule (in viewer)

Shows the direct transformation from docs → rules.

### Option B: Terminal Output Highlight

Capture the summary at the end of generation:
```
✓ Generated 17 rules
✓ Effort scores: 1-5
✓ Rule IDs: spring-boot-3-to-spring-boot-4-00010 through 00170
✓ Output: blog-demo-spring-boot-4.yaml

Summary:
  Mandatory rules: 15
  Potential rules: 2
  Total patterns: 17
```

### Option C: Complete Workflow Diagram

Use the Mermaid diagram from the blog post but render it as an image:
- Open https://mermaid.live/
- Paste the diagram code
- Export as PNG
- Shows the complete flow visually

---

## Quick Reference: All Commands

```bash
# 1. Generate rules
python scripts/generate_rules.py \
  --guide "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide" \
  --source spring-boot-3 \
  --target spring-boot-4 \
  --output blog-demo-spring-boot-4.yaml \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219

# 2. View rules
# Open: https://tsanders-rh.github.io/analyzer-rule-generator/rule-viewer.html
# Load: blog-demo-spring-boot-4.yaml

# 3. Generate test data (optional)
python scripts/generate_test_data.py \
  --rules blog-demo-spring-boot-4.yaml \
  --output blog-demo-test-data \
  --source spring-boot-3 \
  --target spring-boot-4 \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219

# 4. View test data
code blog-demo-test-data
```

---

## Screenshot Specifications

**Recommended settings:**
- Resolution: 1920x1080 or higher
- Format: PNG
- Terminal: Use a clean theme (e.g., iTerm with Solarized)
- Browser: Chrome/Firefox, hide bookmarks bar for clean look
- Font size: Increase for readability (Terminal: 14pt, Code: 13pt)

**Cropping:**
- Leave some whitespace around edges
- Focus on the relevant content
- Don't need full desktop—just the relevant window

**Annotations (optional):**
- Add arrows or highlights to key elements
- Use subtle colors (yellow highlight, red arrow)
- Tools: macOS Preview, Skitch, or Snagit

---

## Timing Estimate

- Rule generation: ~2-3 minutes (depending on LLM)
- Screenshots: ~5 minutes total
- Test data generation: ~3-4 minutes (if included)

**Total demo time:** ~7-10 minutes for all three screenshots
**Quick demo:** ~3-5 minutes for just screenshots 1 & 2

---

## After Demo: Cleanup

```bash
# Optional: Remove demo files
rm blog-demo-spring-boot-4.yaml
rm -rf blog-demo-test-data
```

Or keep them in an `examples/blog-demo/` directory for reference.

---

## Tips for Best Screenshots

1. **Terminal (Screenshot 1):**
   - Clear scrollback before starting
   - Run command, let it complete
   - Scroll to show the most interesting output
   - Capture showing both command and results

2. **Rule Viewer (Screenshot 2):**
   - Zoom to 100% or 110% for readability
   - Expand a rule that's easy to understand
   - Make sure the link to docs is visible
   - Show the rule ID clearly

3. **Test Data (Screenshot 3):**
   - Split editor view to show both pom.xml and Java
   - Pick a Java file with clear violations and comments
   - Format code nicely
   - Ensure syntax highlighting is visible

---

## Blog Post Images Summary

**Minimum required (2 images):**
1. Screenshot 1: Terminal showing rule generation
2. Screenshot 2: Rule viewer with expanded rule

**Recommended (3 images):**
1. Screenshot 1: Terminal showing rule generation
2. Screenshot 2: Rule viewer with expanded rule
3. Screenshot 3: Generated test data in VS Code

**Optional extras:**
- Workflow diagram (rendered Mermaid)
- Before/after comparison (guide → rule)
- GitHub repo screenshot

Choose based on blog platform and available space!
