# VHS tape file for Konveyor Rule Generator Claude Skill demo
# Install VHS: https://github.com/charmbracelet/vhs
# Run: vhs claude-skill-demo.tape

# Output configuration
Output claude-skill-demo.gif
Output claude-skill-demo.mp4
Output claude-skill-demo.webm

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

# Start in project directory
Type "cd ~/Workspace/analyzer-rule-generator"
Enter
Sleep 500ms

Type "source venv/bin/activate"
Enter
Sleep 500ms

Type "clear"
Enter
Sleep 500ms

Show

# Scene 1: Introduction
Type "# Konveyor Rule Generator - Claude Code Skill Demo"
Sleep 1s
Enter
Enter
Sleep 500ms

Type "# Let's generate migration rules from a React 18 upgrade guide"
Sleep 1s
Enter
Sleep 1s

# Scene 2: Run the generation script directly (simulating Claude skill)
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
Enter
Sleep 2s

# Scene 3: Show the generation process (simulated output)
Type@500ms "Generating analyzer rules: react-17 → react-18"
Enter
Type@500ms "Guide: examples/demo-guide-react18.md"
Enter
Type@500ms "Output: demo-output/react-18/"
Enter
Type@500ms "LLM: anthropic"
Enter
Enter
Sleep 1s

Type@500ms "[1/3] Ingesting guide..."
Enter
Sleep 1s
Type@500ms "  ✓ Ingested 8,234 characters"
Enter
Sleep 1s

Type@500ms "[2/3] Extracting patterns with LLM..."
Enter
Sleep 500ms
Type@500ms "  → Processing content (8,234 chars)"
Enter
Sleep 2s
Type@300ms "  → Decision: Adding import verification for generic component (component=Suspense)"
Enter
Sleep 1s
Type@300ms "  → Decision: Auto-converting to combo rule (pattern=ReactDOM.render removal)"
Enter
Sleep 1s
Type@500ms "  ✓ Extracted 18 patterns"
Enter
Sleep 1s

Type@500ms "[3/3] Generating analyzer rules..."
Enter
Sleep 2s
Type@500ms "  ✓ Generated 18 rules across 8 concern(s)"
Enter
Sleep 1s

# Scene 4: Show summary
Enter
Type@300ms "✓ Successfully generated 18 rules in 8 file(s)"
Enter
Enter
Sleep 1s

Type@300ms "Rule Summary:"
Enter
Type@300ms "  Total rules: 18"
Enter
Type@300ms "  Files generated: 8"
Enter
Type@300ms "  mandatory: 5"
Enter
Type@300ms "  potential: 13"
Enter
Enter
Sleep 2s

# Scene 5: Show generated files
Type "ls -1 demo-output/react-18/"
Enter
Sleep 1s

Type@300ms "react-17-to-react-18-automatic-batching.yaml"
Enter
Type@300ms "react-17-to-react-18-concurrent-features.yaml"
Enter
Type@300ms "react-17-to-react-18-new-hooks.yaml"
Enter
Type@300ms "react-17-to-react-18-root-api.yaml"
Enter
Type@300ms "react-17-to-react-18-strict-mode.yaml"
Enter
Type@300ms "react-17-to-react-18-suspense.yaml"
Enter
Type@300ms "react-17-to-react-18-typescript.yaml"
Enter
Type@300ms "ruleset.yaml"
Enter
Sleep 2s

# Scene 6: Show a sample rule
Enter
Type "# Let's look at one of the generated rules"
Enter
Sleep 1s

Type "cat demo-output/react-18/react-17-to-react-18-root-api.yaml | head -30"
Enter
Sleep 1s

Type@200ms "- ruleID: react-17-to-react-18-00010"
Enter
Type@200ms "  description: ReactDOM.render should be replaced with ReactDOM.createRoot"
Enter
Type@200ms "  effort: 5"
Enter
Type@200ms "  category: mandatory"
Enter
Type@200ms "  labels:"
Enter
Type@200ms "  - konveyor.io/source=react-17"
Enter
Type@200ms "  - konveyor.io/target=react-18"
Enter
Type@200ms "  when:"
Enter
Type@200ms "    and:"
Enter
Type@200ms "    - nodejs.referenced:"
Enter
Type@200ms "        pattern: ReactDOM.render"
Enter
Type@200ms "    - builtin.filecontent:"
Enter
Type@200ms "        pattern: ReactDOM\\.render\\("
Enter
Type@200ms "        filePattern: \\.(j|t)sx?$"
Enter
Type@200ms "  message: |-"
Enter
Type@200ms "    In React 18, ReactDOM.render has been replaced with createRoot API."
Enter
Sleep 3s

# Scene 7: Closing
Enter
Enter
Type "# ✨ Migration rules generated in seconds!"
Enter
Sleep 1s
Type "# Ready to use with Konveyor analyzer-lsp"
Enter
Sleep 3s
