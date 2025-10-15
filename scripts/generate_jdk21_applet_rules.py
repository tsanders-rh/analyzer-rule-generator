#!/usr/bin/env python3
"""
Generate Konveyor rules for JDK 21 Applet API removal (JEP 504).

This script generates rules to detect usage of removed Applet APIs:
- java.applet.* package
- javax.swing.JApplet
- java.beans.AppletInitializer
"""
import sys
from pathlib import Path
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_generator.java_removal import JavaRemovalRuleGenerator, RemovedJavaAPI
from rule_generator.schema import Category


def main():
    """Generate JDK 21 Applet removal rules."""

    # Initialize generator
    generator = JavaRemovalRuleGenerator(
        migration_name="JDK 21 Applet API Removal",
        source_version="openjdk17",
        target_version="openjdk21",
        guide_url="https://openjdk.org/jeps/504"
    )

    # Define removed APIs from JEP 504
    removals = [
        # java.applet package classes
        RemovedJavaAPI(
            fqn="java.applet.Applet",
            api_type="class",
            category=Category.MANDATORY,
            effort=7,
            message=(
                "The Applet API has been removed in JDK 21 (JEP 504). "
                "Applets are no longer supported by modern browsers. "
                "Consider migrating to:\n"
                "- Java Web Start (if still supported in your environment)\n"
                "- Modern web technologies (HTML5, JavaScript)\n"
                "- Desktop applications using JavaFX or Swing"
            )
        ),
        RemovedJavaAPI(
            fqn="java.applet.AppletContext",
            api_type="interface",
            category=Category.MANDATORY,
            effort=7,
            message=(
                "The AppletContext interface has been removed in JDK 21 (JEP 504). "
                "This interface was part of the deprecated Applet API. "
                "Migrate to modern deployment technologies."
            )
        ),
        RemovedJavaAPI(
            fqn="java.applet.AppletStub",
            api_type="interface",
            category=Category.MANDATORY,
            effort=7,
            message=(
                "The AppletStub interface has been removed in JDK 21 (JEP 504). "
                "This interface was part of the deprecated Applet API. "
                "Migrate to modern deployment technologies."
            )
        ),
        RemovedJavaAPI(
            fqn="java.applet.AudioClip",
            api_type="interface",
            category=Category.MANDATORY,
            effort=5,
            message=(
                "The AudioClip interface has been removed in JDK 21 (JEP 504). "
                "For audio playback, use javax.sound.sampled.Clip instead."
            )
        ),

        # javax.swing
        RemovedJavaAPI(
            fqn="javax.swing.JApplet",
            api_type="class",
            category=Category.MANDATORY,
            effort=5,
            message=(
                "JApplet has been removed in JDK 21 (JEP 504). "
                "For Swing applications, migrate to JFrame or JPanel. "
                "Example:\n"
                "  Before: public class MyApplet extends JApplet\n"
                "  After:  public class MyApp extends JFrame"
            )
        ),

        # java.beans
        RemovedJavaAPI(
            fqn="java.beans.AppletInitializer",
            api_type="interface",
            category=Category.MANDATORY,
            effort=7,
            message=(
                "The AppletInitializer interface has been removed in JDK 21 (JEP 504). "
                "This interface was part of the deprecated Applet API. "
                "Migrate to modern deployment technologies."
            )
        ),
    ]

    # Generate rules
    rules = generator.generate_rules(removals)

    # Convert to YAML format (list of rules)
    rules_data = []
    for rule in rules:
        rule_dict = rule.model_dump(exclude_none=True, mode='json')
        # Convert category enum to string
        if 'category' in rule_dict:
            rule_dict['category'] = rule_dict['category']
        rules_data.append(rule_dict)

    # Output directory
    output_dir = Path(__file__).parent.parent / "examples" / "output" / "jdk21"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write to file
    output_file = output_dir / "applet-removal.yaml"
    with open(output_file, 'w') as f:
        yaml.dump(rules_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"✓ Generated {len(rules)} rules")
    print(f"✓ Output: {output_file}")

    # Print summary
    print("\nGenerated rules for:")
    for removal in removals:
        print(f"  - {removal.fqn} ({removal.api_type})")


if __name__ == "__main__":
    main()
