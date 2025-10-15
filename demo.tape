# VHS tape file for automated screencast recording
# Install: brew install vhs
# Run: vhs demo.tape
# Output: demo.gif

Output demo.mp4

Set FontSize 16
Set Width 1400
Set Height 800
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms
Set Padding 20

# Start in project directory
Hide
Type "cd /Users/tsanders/Workspace/analyzer-rule-generator && source venv/bin/activate && clear"
Enter
Show

Sleep 500ms

# Show intro comment
Type "# Generate Konveyor analyzer rules from JDK migration guide using AI"
Enter
Sleep 1s

# Show the command being built
Type "python scripts/generate_rules.py \"
Sleep 300ms
Enter

Type "  --guide https://openjdk.org/jeps/504 \"
Sleep 300ms
Enter

Type "  --source openjdk17 \"
Sleep 300ms
Enter

Type "  --target openjdk21 \"
Sleep 300ms
Enter

Type "  --output examples/output/jdk21/demo-output.yaml \"
Sleep 300ms
Enter

Type "  --provider anthropic \"
Sleep 300ms
Enter

Type "  --model claude-3-7-sonnet-20250219"
Sleep 500ms
Enter

# Wait for generation to complete (AI processing takes time)
Sleep 20s

# Add spacing
Enter
Sleep 500ms

# Show first rule
Type "# Generated rule example:"
Enter
Sleep 500ms

Type "head -35 examples/output/jdk21/demo-output.yaml"
Enter

# Show the output
Sleep 6s

# Clear and show summary
Enter
Type "# Rule summary:"
Enter
Sleep 500ms

Type "echo 'Total rules:' && grep '^- ruleID:' examples/output/jdk21/demo-output.yaml | wc -l"
Enter
Sleep 2s

Enter
Type "echo 'By category:' && grep 'category:' examples/output/jdk21/demo-output.yaml | sort | uniq -c"
Enter
Sleep 2s

Enter
Type "echo 'By effort:' && grep 'effort:' examples/output/jdk21/demo-output.yaml | sort | uniq -c"
Enter
Sleep 3s

# Final pause
Sleep 2s
