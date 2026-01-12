# VHS tape - Claude Code Skill Interaction Demo
# Shows the user experience of using the konveyor-rules skill
# Run: vhs claude-skill-interaction-demo.tape

# Output configuration
Output claude-skill-interaction.gif
Output claude-skill-interaction.mp4
Output claude-skill-interaction.webm

# Terminal settings
Set FontSize 16
Set Width 1400
Set Height 1000
Set Theme "TokyoNight"
Set TypingSpeed 50ms
Set PlaybackSpeed 1.0
Set Padding 20

# Scene 1: Show we're in Claude Code
Type "# Claude Code Session - Konveyor Rule Generator"
Enter
Sleep 1s
Type "# Workspace: analyzer-rule-generator"
Enter
Enter
Sleep 1s

# Scene 2: User invokes the skill
Type "❯ "
Sleep 500ms
Type "konveyor-rules"
Enter
Sleep 2s

# Scene 3: Claude responds with skill activation
Type@300ms ""
Enter
Type@300ms "I'll help you generate Konveyor migration rules. Let me gather some information:"
Enter
Type@300ms ""
Enter
Type@300ms "- What is the migration guide source (URL or file path)?"
Enter
Type@300ms "- What is the source framework?"
Enter
Type@300ms "- What is the target framework?"
Enter
Type@300ms ""
Sleep 2s

# Scene 4: User provides information
Type "❯ "
Sleep 500ms
Type "Generate rules from examples/demo-guide-react18.md for react-17 to react-18"
Enter
Sleep 2s

# Scene 5: Claude confirms and starts
Type@300ms ""
Enter
Type@300ms "I'll generate Konveyor analyzer rules from the React 18 migration guide."
Enter
Type@300ms ""
Enter
Type@300ms "Running rule generator:"
Enter
Type@300ms "  • Guide: examples/demo-guide-react18.md"
Enter
Type@300ms "  • Source: react-17"
Enter
Type@300ms "  • Target: react-18"
Enter
Type@300ms "  • Output: demo-output/react-18/"
Enter
Type@300ms ""
Sleep 2s

# Scene 6: Show generation progress
Type@400ms "[1/3] Ingesting guide..."
Enter
Sleep 1s
Type@400ms "  ✓ Ingested 8,234 characters"
Enter
Sleep 1s

Type@400ms "[2/3] Extracting patterns with LLM..."
Enter
Sleep 500ms
Type@400ms "  → Processing content (8,234 chars)"
Enter
Sleep 1.5s
Type@300ms "  → Decision: Adding import verification for generic component (component=Suspense)"
Enter
Sleep 1s
Type@300ms "  → Decision: Auto-converting to combo rule (pattern=ReactDOM.render removal)"
Enter
Sleep 1s
Type@400ms "  ✓ Extracted 18 patterns"
Enter
Sleep 1s

Type@400ms "[3/3] Generating analyzer rules..."
Enter
Sleep 1.5s
Type@400ms "  ✓ Generated 18 rules across 8 concern(s)"
Enter
Sleep 1s

# Scene 7: Show results
Enter
Type@300ms "✓ Successfully generated 18 rules in 8 file(s)"
Enter
Enter
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

# Scene 8: Claude provides context
Type@300ms "I've generated migration rules for React 17→18. Key highlights:"
Enter
Type@300ms ""
Enter
Type@300ms "• Automatic quality improvements applied:"
Enter
Type@300ms "  - Added import verification for generic components"
Enter
Type@300ms "  - Converted patterns to combo rules for accuracy"
Enter
Type@300ms ""
Enter
Type@300ms "• Rule files created in demo-output/react-18/:"
Enter
Type@300ms "  - react-17-to-react-18-root-api.yaml"
Enter
Type@300ms "  - react-17-to-react-18-suspense.yaml"
Enter
Type@300ms "  - react-17-to-react-18-concurrent-features.yaml"
Enter
Type@300ms "  - and 5 more..."
Enter
Type@300ms ""
Sleep 3s

# Scene 9: User asks a follow-up
Type "❯ "
Sleep 500ms
Type "Show me one of the generated rules"
Enter
Sleep 1.5s

# Scene 10: Claude shows a rule
Type@300ms ""
Enter
Type@300ms "Here's the ReactDOM.render migration rule:"
Enter
Type@300ms ""
Sleep 500ms

Type@200ms "```yaml"
Enter
Type@200ms "- ruleID: react-17-to-react-18-00010"
Enter
Type@200ms "  description: ReactDOM.render should be replaced with createRoot"
Enter
Type@200ms "  effort: 5"
Enter
Type@200ms "  category: mandatory"
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
Type@200ms "        pattern: ReactDOM.render("
Enter
Type@200ms "  message: |"
Enter
Type@200ms "    In React 18, ReactDOM.render has been replaced"
Enter
Type@200ms "    with the createRoot API."
Enter
Type@200ms "```"
Enter
Sleep 3s

# Scene 11: Final message
Enter
Type@300ms "This rule uses a combo pattern to:"
Enter
Type@300ms "  1. Check for ReactDOM.render references (nodejs.referenced)"
Enter
Type@300ms "  2. Verify actual usage in code (builtin.filecontent)"
Enter
Type@300ms ""
Enter
Type@300ms "All 18 rules are ready to use with Konveyor analyzer-lsp!"
Enter
Sleep 3s

Enter
Type "# ✨ Zero configuration, production-ready migration rules"
Enter
Sleep 2s
