# VHS tape file for OpenRewrite integration demo
# Install: brew install vhs
# Run: vhs media/openrewrite-demo.tape
# Output: media/openrewrite-demo.mp4

Output media/openrewrite-demo.mp4

Set FontSize 16
Set Width 1400
Set Height 900
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms
Set Padding 20

# Start in project directory
Hide
Type "cd /Users/tsanders/Workspace/analyzer-rule-generator && source venv/bin/activate && clear"
Enter
Show

Sleep 500ms

# Intro
Type "# NEW: Generate Konveyor rules from OpenRewrite recipes! 🚀"
Enter
Sleep 1s
Enter

Type "# Example: Java 11 → 17 migration from OpenRewrite"
Enter
Sleep 1s

# Show the command
Type "python scripts/generate_rules.py \"
Sleep 300ms
Enter

Type "  --from-openrewrite https://raw.githubusercontent.com/openrewrite/rewrite-migrate-java/main/src/main/resources/META-INF/rewrite/java-version-17.yml \"
Sleep 400ms
Enter

Type "  --source java11 \"
Sleep 300ms
Enter

Type "  --target java17 \"
Sleep 300ms
Enter

Type "  --output examples/output/openrewrite-demo/java17 \"
Sleep 300ms
Enter

Type "  --provider anthropic"
Sleep 500ms
Enter

# Wait for generation to complete (AI processing takes time)
Sleep 25s

# Add spacing
Enter
Sleep 1s

# Show generated files
Type "# What did we get?"
Enter
Sleep 500ms

Type "ls -l examples/output/openrewrite-demo/java17/"
Enter
Sleep 3s

# Show a sample rule
Enter
Type "# Sample rule - Security migration:"
Enter
Sleep 500ms

Type "head -25 examples/output/openrewrite-demo/java17/java11-to-java17-security.yaml"
Enter
Sleep 5s

# Show stats
Enter
Type "# Quick stats:"
Enter
Sleep 500ms

Type "echo 'Total rules:' && find examples/output/openrewrite-demo/java17 -name '*.yaml' ! -name 'ruleset.yaml' -exec grep -h '^- ruleID:' {} \\; | wc -l"
Enter
Sleep 2s

Enter
Type "echo 'Categories covered:' && ls examples/output/openrewrite-demo/java17/*.yaml | grep -v ruleset | wc -l"
Enter
Sleep 2s

# Now show test data generation
Enter
Sleep 500ms
Type "# Now generate test data with violations:"
Enter
Sleep 1s

Type "python scripts/generate_test_data.py \"
Sleep 300ms
Enter

Type "  --rules examples/output/openrewrite-demo/java17/java11-to-java17-security.yaml \"
Sleep 400ms
Enter

Type "  --output examples/output/openrewrite-demo/test-app \"
Sleep 300ms
Enter

Type "  --source java11 \"
Sleep 300ms
Enter

Type "  --target java17 \"
Sleep 300ms
Enter

Type "  --guide-url 'https://docs.oracle.com/en/java/javase/17/migrate' \"
Sleep 300ms
Enter

Type "  --provider anthropic"
Sleep 500ms
Enter

# Wait for test data generation
Sleep 15s

# Show generated test code
Enter
Sleep 1s
Type "# Generated test application:"
Enter
Sleep 500ms

Type "ls -la examples/output/openrewrite-demo/test-app/"
Enter
Sleep 2s

Enter
Type "# Test code with violations:"
Enter
Sleep 500ms

Type "head -15 examples/output/openrewrite-demo/test-app/src/main/java/com/example/Application.java"
Enter
Sleep 4s

# Summary
Enter
Enter
Type "# ✨ Complete workflow:"
Enter
Sleep 500ms
Type "# 1. OpenRewrite recipe → Konveyor rules"
Enter
Sleep 500ms
Type "# 2. Auto-generate test data"
Enter
Sleep 500ms
Type "# 3. Ready for analyzer testing!"
Enter
Sleep 2s

# Final pause
Sleep 3s
