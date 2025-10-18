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

Type "  --output blog-demo-spring-boot-4.yaml \"
Sleep 300ms
Enter

Type "  --provider anthropic \"
Sleep 300ms
Enter

Type "  --model claude-3-7-sonnet-latest"
Sleep 500ms
Enter

# Wait for generation to complete (AI processing takes time)
Sleep 25s

# Add spacing
Enter
Sleep 1s

# Show generated rules structure
Type "# View generated rules:"
Enter
Sleep 500ms

Type "head -40 blog-demo-spring-boot-4.yaml"
Enter
Sleep 6s

# Show rule statistics
Enter
Type "# Rule statistics:"
Enter
Sleep 500ms

Type "echo 'Total rules generated:' && grep '^- ruleID:' blog-demo-spring-boot-4.yaml | wc -l"
Enter
Sleep 2s

Enter
Type "echo 'Effort distribution:' && grep 'effort:' blog-demo-spring-boot-4.yaml | sort | uniq -c"
Enter
Sleep 3s

Enter
Type "echo 'Categories:' && grep 'category:' blog-demo-spring-boot-4.yaml | sort | uniq -c"
Enter
Sleep 3s

# Show one complete rule example
Enter
Type "# Example rule (MongoDB property migration):"
Enter
Sleep 500ms

Type "grep -A 15 'spring.data.mongodb' blog-demo-spring-boot-4.yaml | head -20"
Enter
Sleep 5s

# Final message
Enter
Sleep 500ms
Type "# Rules ready! View in browser: https://tsanders-rh.github.io/analyzer-rule-generator/rule-viewer.html"
Enter
Sleep 3s
