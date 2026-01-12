# VHS tape file - REAL execution version
# This actually runs the rule generator (requires API key and takes ~90 seconds)
# Install VHS: https://github.com/charmbracelet/vhs
# Run: vhs claude-skill-demo-real.tape

# Output configuration
Output claude-skill-demo-real.gif
Output claude-skill-demo-real.mp4
Output claude-skill-demo-real.webm

# Terminal settings
Set FontSize 16
Set Width 1400
Set Height 900
Set Theme "Monokai"
Set TypingSpeed 50ms
Set PlaybackSpeed 1.0
Set Padding 20

# Hide initial setup
Hide
Type "cd ~/Workspace/analyzer-rule-generator"
Enter
Sleep 500ms
Type "source venv/bin/activate"
Enter
Sleep 500ms
Type "rm -rf demo-output/react-18/"
Enter
Sleep 500ms
Type "clear"
Enter
Show

# Scene 1: Introduction
Type "# Konveyor Rule Generator - Claude Code Skill Demo"
Sleep 1s
Enter
Enter
Type "# Generate migration rules from React 18 upgrade guide"
Sleep 1s
Enter
Enter
Sleep 1s

# Scene 2: Show the command
Type "python scripts/generate_rules.py \\"
Enter
Sleep 300ms
Type "  --guide examples/demo-guide-react18.md \\"
Enter
Sleep 300ms
Type "  --source react-17 \\"
Enter
Sleep 300ms
Type "  --target react-18 \\"
Enter
Sleep 300ms
Type "  --output demo-output/react-18/ \\"
Enter
Sleep 300ms
Type "  --provider anthropic"
Sleep 1s
Enter

# This will actually run and take ~90 seconds
# VHS will capture the real output including Decision: lines
Sleep 120s

# Scene 3: Show generated files
Enter
Type "# Rules generated! Let's see what we got"
Enter
Sleep 1s

Type "ls -1 demo-output/react-18/"
Enter
Sleep 2s

# Scene 4: Show a sample rule
Type "cat demo-output/react-18/react-17-to-react-18-root-api.yaml | head -30"
Enter
Sleep 5s

# Scene 5: Count rules
Enter
Type "# Count total rules generated"
Enter
Type "grep -c '^- ruleID:' demo-output/react-18/*.yaml | awk -F: '{sum+=$2} END {print \"Total rules: \" sum}'"
Enter
Sleep 2s

# Closing
Enter
Type "# ✨ Production-ready migration rules in under 2 minutes!"
Enter
Sleep 3s
