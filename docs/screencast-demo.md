# Screencast Demo Script

## Setup Before Recording

1. **Clean terminal** - Clear screen and set a good size
   ```bash
   clear
   cd /Users/tsanders/Workspace/analyzer-rule-generator
   ```

2. **Remove old output** (for fresh demo)
   ```bash
   rm -f examples/output/jdk21/applet-removal.yaml
   ```

3. **Verify environment**
   ```bash
   source venv/bin/activate
   ```

4. **Terminal settings** (optional but recommended)
   - Font size: 16-18pt for readability
   - Theme: Light theme for better visibility
   - Window size: ~120 chars wide, 30 lines tall

## Recording Steps

### Scene 1: Introduction (5 seconds)
```bash
# Show the README
cat README.md | head -20
```

**Narration:**
"Let's generate Konveyor analyzer rules from a JDK migration guide using AI."

### Scene 2: Show the Command (5 seconds)
```bash
# Display the command (don't run yet)
cat << 'EOF'
python scripts/generate_rules.py \
  --guide https://openjdk.org/jeps/504 \
  --source openjdk17 \
  --target openjdk21 \
  --output examples/output/jdk21/applet-removal.yaml \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219
EOF
```

**Narration:**
"We'll point it at JEP 504, the Applet API removal guide, and let the AI extract migration patterns."

### Scene 3: Run the Generator (15-20 seconds)
```bash
python scripts/generate_rules.py \
  --guide https://openjdk.org/jeps/504 \
  --source openjdk17 \
  --target openjdk21 \
  --output examples/output/jdk21/applet-removal.yaml \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219
```

**Narration:**
"The tool fetches the guide, uses Claude to extract patterns, and generates Konveyor rules."

**Expected output:**
```
Generating analyzer rules: openjdk17 → openjdk21
Guide: https://openjdk.org/jeps/504
LLM: anthropic claude-3-7-sonnet-20250219

[1/3] Ingesting guide...
  ✓ Ingested 7949 characters
[2/3] Extracting patterns with LLM...
  ✓ Extracted 9 patterns
[3/3] Generating analyzer rules...
  ✓ Generated 9 rules

Writing rules to examples/output/jdk21/applet-removal.yaml...
✓ Successfully generated 9 rules

Output: examples/output/jdk21/applet-removal.yaml

Rule Summary:
  Total rules: 9
  mandatory: 7
  potential: 2

Effort Distribution:
  5: ▓▓▓
  7: ▓▓▓▓▓▓▓
```

### Scene 4: Show Generated Rules (10 seconds)
```bash
# Show first rule
head -35 examples/output/jdk21/applet-removal.yaml
```

**Narration:**
"Here's a generated rule detecting Applet usage with proper categorization and effort scoring."

**Expected output:**
```yaml
- ruleID: openjdk17-to-openjdk21-00001
  description: java.applet.Applet should be replaced with...
  effort: 7
  category: mandatory
  labels:
    - konveyor.io/source=openjdk17
    - konveyor.io/target=openjdk21+
  when:
    java.referenced:
      pattern: java.applet.Applet
      location: TYPE
  message: 'The Applet API has been removed...'
  links:
    - url: https://openjdk.org/jeps/504
      title: JDK 21 Applet API Removal
```

### Scene 5: Show Summary (5 seconds)
```bash
# Count rules by category
echo "Generated rules:"
grep "^- ruleID:" examples/output/jdk21/applet-removal.yaml | wc -l
echo ""
echo "Categories:"
grep "category:" examples/output/jdk21/applet-removal.yaml | sort | uniq -c
```

**Narration:**
"Nine rules generated automatically, with seven marked as mandatory for API removals."

## Total Time: ~40-50 seconds

## Recording Tools

### macOS
```bash
# Use built-in screenshot tool
# Cmd + Shift + 5 → Screen Recording

# Or use QuickTime Player:
# File → New Screen Recording
```

### Alternative: asciinema (terminal recording)
```bash
brew install asciinema

# Record
asciinema rec demo.cast

# Play back
asciinema play demo.cast

# Upload to share
asciinema upload demo.cast
```

### Alternative: vhs (automated terminal recording)
```bash
brew install vhs

# Create a vhs script (see below)
vhs screencast.tape
```

## Automated Recording with VHS

Create `screencast.tape`:
```vhs
# VHS documentation: https://github.com/charmbracelet/vhs

Output examples/output/demo.gif

Set FontSize 18
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"

Type "cd /Users/tsanders/Workspace/analyzer-rule-generator"
Enter
Sleep 500ms

Type "source venv/bin/activate"
Enter
Sleep 500ms

Type "# Generate Konveyor rules from JEP 504 using AI"
Enter
Sleep 1s

Type "python scripts/generate_rules.py \"
Enter
Type "  --guide https://openjdk.org/jeps/504 \"
Enter
Type "  --source openjdk17 \"
Enter
Type "  --target openjdk21 \"
Enter
Type "  --output examples/output/jdk21/applet-removal.yaml \"
Enter
Type "  --provider anthropic \"
Enter
Type "  --model claude-3-7-sonnet-20250219"
Enter

Sleep 15s

Type "# Show generated rule"
Enter
Sleep 500ms

Type "head -35 examples/output/jdk21/applet-removal.yaml"
Enter
Sleep 5s
```

Then run:
```bash
vhs screencast.tape
```

## Tips for Best Results

1. **Slow down** - Type slowly or use `Sleep` commands
2. **Clear screen** between sections with `clear` or Ctrl+L
3. **Highlight key output** by pausing after important sections
4. **Keep it short** - Under 60 seconds is ideal
5. **Test run first** - Do a practice recording to catch issues
6. **Use comments** - Add `# comments` to explain what's happening
7. **Good lighting** - If showing your face/hands
8. **Minimal distractions** - Close notifications, hide desktop icons

## Post-Processing

If you need to edit:
- **iMovie** (macOS, free)
- **QuickTime Player** (basic trimming)
- **FFmpeg** (command-line)
  ```bash
  # Trim video
  ffmpeg -i input.mov -ss 00:00:05 -t 00:00:45 -c copy output.mov

  # Convert to GIF
  ffmpeg -i input.mov -vf "fps=10,scale=800:-1" output.gif
  ```

## Sharing

- **YouTube** - Best for longer demos
- **Twitter/X** - Max 2:20, use GIF for <15s
- **README.md** - Embed GIF directly
- **asciinema.org** - For terminal-only recordings

Good luck with your screencast! 🎥
