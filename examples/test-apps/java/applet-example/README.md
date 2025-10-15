# JDK 21 Applet API Test Example

This test application contains code using deprecated Applet APIs that were removed in JDK 21 (JEP 504).

## Purpose

This code is used to validate the generated Konveyor analyzer rules for detecting Applet API usage.

## Test Files

### SimpleApplet.java
- Extends `java.applet.Applet` (triggers rule 00001)
- Uses `AudioClip` interface (triggers rule 00004)

### SwingApplet.java
- Extends `javax.swing.JApplet` (triggers rule 00005)

### AppletContextExample.java
- Uses `AppletContext` interface (triggers rule 00002)
- Extends `Applet` (triggers rule 00001)

### AppletInitializerExample.java
- Implements `AppletInitializer` interface (triggers rule 00006)
- References `Applet` class (triggers rule 00001)

## Expected Rule Violations

When analyzed with the generated rules (`examples/output/jdk21/applet-removal.yaml`), this application should detect:

1. **jdk-21-applet-api-removal-00001**: `java.applet.Applet` usage
2. **jdk-21-applet-api-removal-00002**: `java.applet.AppletContext` usage
3. **jdk-21-applet-api-removal-00004**: `java.applet.AudioClip` usage
4. **jdk-21-applet-api-removal-00005**: `javax.swing.JApplet` usage
5. **jdk-21-applet-api-removal-00006**: `java.beans.AppletInitializer` usage

## Running Analysis

```bash
# Using Konveyor analyzer-lsp
kantra analyze \
  --input examples/test-apps/java/applet-example \
  --rules examples/output/jdk21/applet-removal.yaml \
  --output analysis-output
```

## Note

This code will NOT compile with JDK 21+ because the Applet APIs have been removed. Use JDK 17 or earlier for source compilation, or analyze source files directly without compilation.
