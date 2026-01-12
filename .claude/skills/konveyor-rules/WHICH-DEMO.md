# Which Demo Should I Use?

Three demo tape files are available, each for different purposes.

## Quick Comparison

| Demo File | Shows | Duration | Requires API | Best For |
|-----------|-------|----------|--------------|----------|
| **claude-skill-interaction-demo.tape** | Claude Code conversation | ~60s | ❌ No | Skill demos, presentations |
| **claude-skill-demo.tape** | Python script execution | ~60s | ❌ No | Technical docs, quick demos |
| **claude-skill-demo-real.tape** | Real execution | ~120s | ✅ Yes | Proof of concept, authenticity |

## Detailed Breakdown

### 🎯 claude-skill-interaction-demo.tape (RECOMMENDED FOR SKILL DEMOS)

**What it shows**: The Claude Code skill user experience

```
❯ konveyor-rules

I'll help you generate Konveyor migration rules...

❯ Generate rules from examples/demo-guide-react18.md for react-17 to react-18

Running rule generator:
  • Guide: examples/demo-guide-react18.md
  ...
```

**Perfect for**:
- Demonstrating the Claude Code skill to users
- Presentations about the skill
- README/documentation showing user experience
- Social media posts showcasing the skill

**Pros**:
- Shows actual skill interaction
- Fast (60 seconds)
- No API key needed
- Consistent output every time

**Cons**:
- Simulated (not real execution)

**Run**:
```bash
vhs media/claude-skill-interaction-demo.tape
# Creates: claude-skill-interaction.{gif,mp4,webm}
```

---

### 🔧 claude-skill-demo.tape (GOOD FOR TECHNICAL DOCS)

**What it shows**: Direct Python script usage

```bash
python scripts/generate_rules.py \
  --guide examples/demo-guide-react18.md \
  --source react-17 \
  --target react-18

[1/3] Ingesting guide...
  ✓ Ingested 8,234 characters
...
```

**Perfect for**:
- Technical documentation
- Showing how the tool works under the hood
- Quick demos of the core functionality
- CI/CD documentation

**Pros**:
- Shows implementation details
- Fast (60 seconds)
- No API key needed
- Consistent output

**Cons**:
- Doesn't show Claude skill interface
- Simulated output

**Run**:
```bash
vhs media/claude-skill-demo.tape
# Creates: claude-skill-demo.{gif,mp4,webm}
```

---

### ✨ claude-skill-demo-real.tape (AUTHENTIC BUT SLOW)

**What it shows**: Real script execution with live API calls

```bash
python scripts/generate_rules.py \
  --guide examples/demo-guide-react18.md \
  --source react-17 \
  --target react-18

[Actually calls Anthropic API and generates real rules]
```

**Perfect for**:
- Proof of concept demos
- When authenticity is critical
- Technical deep-dives
- Showing real API integration

**Pros**:
- 100% authentic
- Shows real Decision: lines from LLM
- Real output files created

**Cons**:
- Slower (~120 seconds)
- Requires ANTHROPIC_API_KEY
- Uses API credits (~$0.10)
- Output may vary slightly

**Prerequisites**:
```bash
export ANTHROPIC_API_KEY="your-key-here"
source venv/bin/activate
rm -rf demo-output/react-18/
```

**Run**:
```bash
vhs media/claude-skill-demo-real.tape
# Creates: claude-skill-demo-real.{gif,mp4,webm}
```

---

## Recommendations by Use Case

### "I'm presenting the Claude skill to users"
→ Use **claude-skill-interaction-demo.tape**
- Shows the user experience
- Highlights the conversational interface
- Fast and reliable

### "I'm documenting the Python tool"
→ Use **claude-skill-demo.tape**
- Shows command-line usage
- Good for README technical section
- Fast and reliable

### "I need to prove it really works"
→ Use **claude-skill-demo-real.tape**
- Shows authentic execution
- Real API calls and output
- Best for skeptical audiences

### "I want to share on Twitter/LinkedIn"
→ Use **claude-skill-interaction-demo.tape**
- Most engaging for general audience
- Shows cool AI interaction
- Short and punchy

### "I'm writing a blog post tutorial"
→ Use **claude-skill-demo.tape** or **claude-skill-demo-real.tape**
- Shows actual tool usage
- Readers can follow along
- Real version builds trust

---

## Quick Test

Try the recommended one first:

```bash
# Navigate to project
cd ~/Workspace/analyzer-rule-generator

# Run the skill interaction demo (recommended)
vhs media/claude-skill-interaction-demo.tape

# View the result
open claude-skill-interaction.gif
```

**Output time**: ~60 seconds to generate
**File size**: ~2-5 MB (GIF), ~1-2 MB (MP4)

---

## Customization

All three can be customized by editing the `.tape` files:

**Change theme**:
```tape
Set Theme "Dracula"      # Instead of "Tokyo Night"
```

**Change timing**:
```tape
Sleep 2s                 # Make it 3s for slower pace
Sleep 500ms              # Make it 300ms for faster
```

**Change output**:
```tape
Output my-custom-name.gif
```

See `VHS-DEMO-README.md` for full customization guide.

---

## All Three Together

If you want all three versions:

```bash
cd ~/Workspace/analyzer-rule-generator

# Generate all three (skill interaction is fastest)
vhs media/claude-skill-interaction-demo.tape &
vhs media/claude-skill-demo.tape &

# Wait for those to finish, then run real version
wait
vhs media/claude-skill-demo-real.tape

# Now you have all three
ls -lh *.gif *.mp4 *.webm
```

Then use whichever fits your needs!
