# Pre-Recording Checklist

Run through this checklist before starting your demo recording.

## ✅ Environment Setup

### 1. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 2. Verify Setup
```bash
bash /tmp/test-demo.sh
```

You should see:
- ✅ Claude skill found
- ✅ Demo guide found
- ✅ ANTHROPIC_API_KEY set
- ✅ Virtual environment activated
- ✅ Python dependencies installed

### 3. Clean Previous Demo Outputs
```bash
rm -rf demo-output/
```

## 🎥 Recording Setup

### Terminal Configuration
- [ ] Increase font size: 14-16pt
- [ ] Set theme: High contrast (dark background recommended)
- [ ] Clear terminal: `clear`
- [ ] Resize window: Full screen or 1920x1080
- [ ] Set working directory: `cd ~/Workspace/analyzer-rule-generator`

### Monitor Setup
- [ ] Primary monitor: Terminal + Claude Code
- [ ] Secondary monitor: DEMO-CHEATSHEET.md open for reference

### Claude Code
- [ ] Start Claude Code session in project directory
- [ ] Test skill is available: Type `/konveyor-rules` (should auto-complete)

## 📋 What to Have Ready

1. **Script**: `.claude/skills/konveyor-rules/RECORDING-DEMO.md`
2. **Cheatsheet**: `.claude/skills/konveyor-rules/DEMO-CHEATSHEET.md`
3. **This checklist**: Keep it open for final verification

## 🎬 Recording Options

### Option A: Quick Demo (90 seconds - RECOMMENDED for first recording)
Uses local demo guide for fast, predictable results.

**Commands to paste:**
```
konveyor-rules
```

Then:
```
Guide: examples/demo-guide-react18.md
Source: react-17
Target: react-18
Output: demo-output/react-18/
```

### Option B: Live Web Demo (2-3 minutes)
Fetches real React 18 upgrade guide.

**Commands to paste:**
```
konveyor-rules
```

Then:
```
Generate rules from https://react.dev/blog/2022/03/08/react-18-upgrade-guide for react-17 to react-18, save to demo-output/react-18/
```

### Option C: Impressive Long Demo (20+ minutes - NOT for quick demos)
Shows chunking on large guide.

**Only use if you want to show:**
- Adaptive chunking in action
- Large-scale rule generation (139 rules)
- Real-world production scenario

```
konveyor-rules
```

Then:
```
Guide: https://www.patternfly.org/get-started/upgrade
Source: patternfly-v5
Target: patternfly-v6
Output: demo-output/patternfly/
```

## 🎤 Narration Tips

### Key Messages to Convey

1. **"Zero configuration needed"**
   - Just URL and framework names
   - No manual rule writing

2. **"Automatic quality improvements"**
   - Point out "Decision:" lines
   - Explain they're happening in real-time

3. **"Production-ready output"**
   - Show well-formatted YAML
   - Mention rules work with Konveyor immediately

### Pacing

- Speak clearly, not too fast
- Pause 2-3 seconds after each command
- Let important output fully display before moving on

## 🔧 Troubleshooting

### If generation seems stuck
- Wait at least 30 seconds before worrying
- LLM API calls can take 20-30 seconds each
- You'll see progress indicators

### If you get an error
- Don't panic - pause recording
- Check error message
- Restart if needed and edit videos together

### If skill doesn't activate
- Verify you're in the project directory
- Restart Claude Code
- Check `.claude/skills/konveyor-rules/SKILL.md` exists

## 📊 Post-Recording Verification

After recording, verify the output:

```bash
# Count rules generated
find demo-output/react-18 -name "*.yaml" ! -name "ruleset.yaml" | wc -l

# View a sample rule
ls demo-output/react-18/*.yaml | head -1 | xargs cat

# Check for quality indicators in log
grep "Decision:" /tmp/patternfly_generation.log | tail -10
```

Expected for React 18 demo:
- **15-20 rule files** generated
- **Clean YAML format** with proper indentation
- **2-4 Decision: lines** showing automatic improvements

## ✨ Final Checks

Before hitting record:

- [ ] Terminal is clear and at project root
- [ ] Font is large enough to read
- [ ] Claude Code is responsive
- [ ] Cheatsheet is visible on second monitor
- [ ] You know which demo option you're doing (A, B, or C)
- [ ] You've practiced the narration once
- [ ] Recording software is ready

## 🎥 Recommended Recording Tools

### macOS
- **QuickTime**: Built-in, simple
- **ScreenFlow**: Professional editing
- **OBS Studio**: Free, powerful

### Linux
- **SimpleScreenRecorder**: Easy to use
- **OBS Studio**: Free, powerful
- **Kazam**: Lightweight

### Windows
- **OBS Studio**: Free, powerful
- **Camtasia**: Professional
- **Xbox Game Bar**: Built-in

## 📝 After Recording

1. **Review the recording**
   - Check audio levels
   - Verify all text is readable
   - Note any sections to re-record

2. **Edit if needed**
   - Cut long pauses
   - Speed up API calls (1.5x)
   - Add title cards
   - Add music (optional, keep subtle)

3. **Export settings**
   - Format: MP4 (H.264)
   - Resolution: 1920x1080
   - Frame rate: 30fps
   - Audio: AAC 128kbps

4. **Clean up**
   ```bash
   rm -rf demo-output/
   deactivate  # Exit venv
   ```

---

## Quick Reference: Full Demo Flow

1. `clear` - Clean terminal
2. Start Claude Code
3. Type: `konveyor-rules`
4. Paste parameters from cheatsheet
5. Watch extraction (highlight Decision: lines)
6. Show generated rules
7. Explain how to use with Konveyor

**Total time: 2-3 minutes**

Good luck with your recording! 🎬
