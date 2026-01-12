# Claude Skill Demo Recording Script

This script is designed for a 2-3 minute screen recording demonstrating the konveyor-rules Claude Code skill.

## Pre-Recording Setup

1. **Clean terminal**: Clear your terminal history (`clear`)
2. **Start in project root**: `cd /path/to/analyzer-rule-generator`
3. **Verify Claude Code is running**: Ensure Claude Code session is active
4. **Prepare example**: We'll use a small React migration guide for quick demonstration

## Recording Script

### Scene 1: Introduction (15 seconds)

**[Screen: Terminal with Claude Code prompt]**

**Narration**: "Let me show you how to generate Konveyor migration rules using the Claude Code skill."

**Action**: Type in chat:
```
konveyor-rules
```

---

### Scene 2: Skill Activation (10 seconds)

**[Screen: Claude responds with skill activation]**

**Expected Output**:
```
I'll help you generate Konveyor migration rules. Let me gather some information:
- What is the migration guide source (URL or file path)?
- What is the source framework?
- What is the target framework?
```

**Narration**: "The skill activates and asks for the required information."

---

### Scene 3: Provide Information (20 seconds)

**Action**: Type in chat:
```
Generate rules from https://react.dev/blog/2022/03/08/react-18-upgrade-guide
Source: react-17
Target: react-18
Output: demo-output/react-18-rules/
```

**Narration**: "I provide the migration guide URL, source and target frameworks, and output directory."

---

### Scene 4: Generation Process (60 seconds)

**[Screen: Shows the three-stage process]**

**Expected Output** (summarized for demo):
```
[1/3] Ingesting guide...
  → Following related links (max depth: 1)
  ✓ Ingested 15,234 characters

[2/3] Extracting patterns with LLM...
  → Processing content (15,234 chars)
  → Decision: Adding import verification for generic component (component=Suspense)
  → Decision: Rejecting overly broad pattern (pattern=lazy)
  → Decision: Auto-converting to combo rule (pattern=ReactDOM.render removal)
  ✓ Extracted 18 patterns

[3/3] Generating analyzer rules...
  ✓ Generated 18 rules across 8 concern(s)
```

**Narration**: "Watch as it automatically:
- Fetches and ingests the migration guide
- Extracts patterns with built-in quality improvements
- Generates Konveyor analyzer rules"

**[Highlight the "Decision:" lines]**

**Narration**: "Notice the automatic quality improvements - adding import verification, rejecting overly broad patterns, and converting to combo rules."

---

### Scene 5: Results Summary (30 seconds)

**[Screen: Shows generation summary]**

**Expected Output**:
```
✓ Successfully generated 18 rules in 8 file(s)

Rule Summary:
  Total rules: 18
  Files generated: 8
  mandatory: 5
  potential: 13

Effort Distribution:
  1: ▓▓▓
  3: ▓▓▓▓▓▓▓▓▓▓▓▓▓▓
  5: ▓

Files Created:
  demo-output/react-18-rules/react-17-to-react-18-render-api.yaml
  demo-output/react-18-rules/react-17-to-react-18-suspense-updates.yaml
  demo-output/react-18-rules/react-17-to-react-18-automatic-batching.yaml
  ...
```

**Narration**: "In just a few minutes, we generated 18 migration rules organized by concern."

---

### Scene 6: View Generated Rules (25 seconds)

**Action**: Type in chat:
```
Can you show me one of the generated rules?
```

**Expected**: Claude reads and displays a rule file

**Action**: Or run in terminal:
```bash
cat demo-output/react-18-rules/react-17-to-react-18-render-api.yaml
```

**[Screen: Shows a well-formatted YAML rule]**

**Example Output**:
```yaml
- ruleID: react-17-to-react-18-00010
  description: ReactDOM.render should be replaced with ReactDOM.createRoot
  effort: 5
  category: mandatory
  when:
    and:
    - nodejs.referenced:
        pattern: ReactDOM.render
    - builtin.filecontent:
        pattern: ReactDOM\.render\(
        filePattern: \.(j|t)sx?$
  message: |-
    In React 18, ReactDOM.render has been replaced with createRoot API.

    Before:
    ```
    ReactDOM.render(<App />, document.getElementById('root'));
    ```

    After:
    ```
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
    ```
```

**Narration**: "Each rule includes detection patterns, effort estimates, and helpful migration guidance."

---

### Scene 7: Next Steps (10 seconds)

**Action**: Type in chat:
```
How do I use these rules with Konveyor?
```

**Expected**: Claude provides usage instructions

**Narration**: "Claude can guide you through using the rules with Konveyor analyzer."

---

## Recording Tips

### Camera/Screen Setup
- **Resolution**: 1920x1080 minimum
- **Font Size**: Increase terminal font to 14-16pt for visibility
- **Theme**: Use high-contrast theme (dark background, bright text)
- **Window Size**: Full screen or large enough to read comfortably

### Terminal Configuration
- Enable command history scrollback
- Set terminal to auto-scroll
- Consider using `asciinema` for perfect terminal recording

### Pacing
- Speak clearly and not too fast
- Pause 2-3 seconds after each command execution
- Let key output sections display fully before scrolling

### Highlighting Key Moments
- When "Decision:" lines appear, pause and highlight
- Zoom in on the final rule YAML to show quality
- Show the file count at the end

## Alternative: Quick Version (60 seconds)

If you need a shorter demo:

1. **Start** (5s): "Generate Konveyor migration rules with Claude Code"
2. **Invoke** (5s): Type `konveyor-rules`
3. **Input** (10s): Paste all info at once
4. **Process** (30s): Show extraction with Decision: lines highlighted
5. **Result** (10s): Show rule count and one sample rule

## Post-Recording

### Editing Suggestions
- Add title slide: "Konveyor Rule Generator - Claude Code Skill"
- Add text overlay for "Decision:" explanations
- Speed up long API calls (1.5x-2x speed)
- Add background music (subtle, low volume)
- End with call-to-action: "Try it: github.com/konveyor/analyzer-rule-generator"

### Export Settings
- Format: MP4 (H.264)
- Resolution: 1920x1080
- Frame rate: 30fps
- Audio: AAC, 128kbps (if narration)

## Troubleshooting During Recording

**If generation takes too long**:
- Use a smaller migration guide (5-10k chars ideal)
- Pre-generate once to cache, then re-record with cached results
- Or use "Quick Version" script above

**If API errors occur**:
- Have backup recording ready
- Or edit out the error and splice in retry

**If output is too verbose**:
- Edit config.py to reduce logging temporarily
- Or edit video to show summary only

## Example Migration Guides for Quick Demos

Fast generators (< 2 minutes):
- React 17→18 upgrade guide (15k chars, ~18 rules)
- Django 3→4 migration guide (8k chars, ~12 rules)
- Spring Boot 2→3 guide (20k chars, ~25 rules)

Impressive but longer (3-5 minutes):
- PatternFly v5→v6 (97k chars, ~139 rules) - shows adaptive chunking

## Demo Variants

### Variant A: "Speed Run" (Live coding style)
- Real-time typing
- Show thought process
- Interactive feel

### Variant B: "Polished Tutorial" (Edited)
- Pre-recorded commands (paste quickly)
- Voice-over narration added in post
- Clean cuts between stages
- Professional feel

### Variant C: "Side-by-side" (Comparison)
- Left: Manual rule writing (slow, tedious)
- Right: Claude skill (fast, automated)
- Synchronized playback showing time savings

Choose the variant that best fits your presentation context.
