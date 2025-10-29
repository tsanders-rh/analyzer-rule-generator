# VHS tape file for OpenRewrite Spring Boot integration demo
# Install: brew install vhs
# Run: vhs media/openrewrite-spring-boot-demo.tape
# Output: media/openrewrite-spring-boot-demo.mp4

Output media/openrewrite-spring-boot-demo.mp4

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
Type "# Generate Konveyor rules from OpenRewrite Spring Boot recipes 🍃"
Enter
Sleep 1s
Enter

Type "# Spring Boot 2.7 → 3.0 migration"
Enter
Sleep 1s

# Show the command
Type "python scripts/generate_rules.py \"
Sleep 300ms
Enter

Type "  --from-openrewrite https://raw.githubusercontent.com/openrewrite/rewrite-spring/main/src/main/resources/META-INF/rewrite/spring-boot-27.yml \"
Sleep 400ms
Enter

Type "  --source spring-boot-2.7 \"
Sleep 300ms
Enter

Type "  --target spring-boot-3.0 \"
Sleep 300ms
Enter

Type "  --provider anthropic"
Sleep 500ms
Enter

# Wait for generation to complete
Sleep 25s

# Add spacing
Enter
Sleep 1s

# Show generated files organized by concern
Type "# Generated rules organized by migration concern:"
Enter
Sleep 500ms

Type "ls -1 examples/output/spring-boot/*.yaml"
Enter
Sleep 4s

# Show a persistence rule
Enter
Type "# Example: JPA/Hibernate naming strategy migration"
Enter
Sleep 500ms

Type "head -30 examples/output/spring-boot/spring-boot-2.7-to-spring-boot-3.0-persistence.yaml"
Enter
Sleep 5s

# Show a properties migration
Enter
Type "# Also includes properties file migrations:"
Enter
Sleep 500ms

Type "python scripts/generate_rules.py --from-openrewrite https://raw.githubusercontent.com/openrewrite/rewrite-spring/main/src/main/resources/META-INF/rewrite/spring-boot-27-properties.yml --source spring-boot-2.7 --target spring-boot-3.0"
Enter
Sleep 20s

Enter
Type "# Properties migrations generated!"
Enter
Sleep 1s

Enter
Type "head -20 examples/output/spring-boot/spring-boot-2.7-to-spring-boot-3.0-properties.yaml"
Enter
Sleep 4s

# Summary
Enter
Enter
Type "# ✅ OpenRewrite has 100+ recipes for:"
Enter
Sleep 500ms
Type "#   • Java 8/11/17/21 migrations"
Enter
Sleep 500ms
Type "#   • Spring Boot (every version!)"
Enter
Sleep 500ms
Type "#   • JUnit, Mockito, Jakarta EE"
Enter
Sleep 500ms
Type "#   • Now available in Konveyor!"
Enter
Sleep 3s

# Final pause
Sleep 2s
