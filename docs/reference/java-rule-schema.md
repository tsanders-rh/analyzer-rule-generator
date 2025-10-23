# Java Provider Rule Schema Design

## Konveyor Rule Structure

### Required Fields
- `ruleID`: Unique identifier (e.g., `applet-removal-00001`)
- `description`: Short summary of the issue
- `message`: Detailed explanation for developers
- `category`: Rule severity (`mandatory`, `optional`, `potential`)
- `effort`: Estimated remediation effort (1-13)
- `labels`: Array of tags (e.g., `["konveyor.io/target=openjdk21"]`)
- `when`: Condition block defining what to detect

### Condition Types for Java Provider

#### 1. Type Reference Detection
Detects usage of a specific class/interface:
```yaml
when:
  java.referenced:
    location: TYPE
    pattern: java.applet.Applet
```

#### 2. Import Detection
Detects imports of specific packages/classes:
```yaml
when:
  java.referenced:
    location: IMPORT
    pattern: java.applet.*
```

#### 3. Inheritance Detection
Detects classes extending/implementing:
```yaml
when:
  java.referenced:
    location: INHERITANCE
    pattern: javax.swing.JApplet
```

#### 4. Method Call Detection
Detects calls to specific methods:
```yaml
when:
  java.referenced:
    location: METHOD_CALL
    pattern: java.applet.Applet.init()
```

#### 5. Constructor Call Detection
Detects instantiation of classes:
```yaml
when:
  java.referenced:
    location: CONSTRUCTOR_CALL
    pattern: java.applet.Applet
```

## Input Schema for Generator

To generate rules for removed APIs, the generator should accept:

```json
{
  "migration": {
    "name": "JDK 21 Applet API Removal",
    "source": "openjdk17",
    "target": "openjdk21",
    "guide_url": "https://openjdk.org/jeps/504"
  },
  "removals": [
    {
      "type": "class",
      "fqn": "java.applet.Applet",
      "category": "mandatory",
      "effort": 5,
      "message": "The Applet API has been removed in JDK 21. Consider migrating to Java Web Start or browser-based alternatives."
    },
    {
      "type": "class",
      "fqn": "javax.swing.JApplet",
      "category": "mandatory",
      "effort": 5,
      "message": "JApplet has been removed in JDK 21. Consider migrating to JFrame or JPanel for Swing applications."
    }
  ]
}
```

## Rule Generation Strategy

For each removed class, generate multiple rules to catch different usage patterns:

1. **Import detection** - Catches `import java.applet.Applet;`
2. **Type reference** - Catches variable declarations, parameters, etc.
3. **Inheritance** - Catches `extends Applet` or `implements AppletContext`
4. **Constructor calls** - Catches `new Applet()`
5. **Method calls** - Catches calls to removed methods

## Example Generated Rule

```yaml
- ruleID: applet-removal-00001
  description: "java.applet.Applet usage detected"
  message: "The Applet API has been removed in JDK 21. Consider migrating to Java Web Start or browser-based alternatives."
  category: mandatory
  effort: 5
  labels:
    - konveyor.io/source=openjdk17
    - konveyor.io/target=openjdk21+
  links:
    - title: "JEP 504: Remove the Applet API"
      url: "https://openjdk.org/jeps/504"
  when:
    or:
      - java.referenced:
          location: IMPORT
          pattern: java.applet.Applet
      - java.referenced:
          location: INHERITANCE
          pattern: java.applet.Applet
      - java.referenced:
          location: TYPE
          pattern: java.applet.Applet
      - java.referenced:
          location: CONSTRUCTOR_CALL
          pattern: java.applet.Applet
```
