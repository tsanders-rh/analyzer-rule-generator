# VHS tape file for blog post demo
# Install: brew install vhs
# Run: vhs media/blog-demo.tape
# Output: media/blog-demo.mp4

Output media/blog-demo.mp4

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
Type "# Generate Konveyor analyzer rules from Spring Boot 4.0 migration guide"
Enter
Sleep 1s

# Show the command
Type "python scripts/generate_rules.py \"
Sleep 300ms
Enter

Type "  --guide 'https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide' \"
Sleep 300ms
Enter

Type "  --source spring-boot-3 \"
Sleep 300ms
Enter

Type "  --target spring-boot-4 \"
Sleep 300ms
Enter

Type "  --output spring-boot \"
Sleep 300ms
Enter

Type "  --provider anthropic \"
Sleep 300ms
Enter

Type "  --model claude-3-7-sonnet-latest"
Sleep 500ms
Enter

# Wait for generation to complete (AI processing takes time)
Sleep 50s

# Add spacing
Enter
Sleep 1s

# Final message
Enter
Sleep 500ms
Type "# Rules ready! View in browser: https://tsanders-rh.github.io/analyzer-rule-generator/rule-viewer.html"
Enter
Enter
Enter
Enter
Sleep 5s
