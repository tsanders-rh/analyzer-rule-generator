# Plan: Build Analyzer Rule Generator for JDK 21 Applet API Removal

## Objective
Extend the analyzer-rule-generator to create Konveyor rules for detecting deprecated Applet APIs in Java code, using JEP 504 as the test case.

## Migration Guide
**JEP 504: Remove the Applet API**
https://openjdk.org/jeps/504

## Steps

1. **Review JEP 504 migration guide**
   - Study the affected APIs and removal rationale
   - Document all classes/methods being removed

2. **Identify all Applet API classes and methods to detect**
   - `java.applet.*` (Applet, AppletContext, AppletStub, AudioClip)
   - `javax.swing.JApplet`
   - `java.beans.AppletInitializer`
   - Related methods in `java.beans.Beans` and `javax.swing.RepaintManager`

3. **Design rule schema for Java provider detection patterns**
   - Define input format for specifying Java API removals
   - Map to Konveyor rule conditions (type references, method calls)

4. **Implement generator logic for Java provider rules**
   - Add Java provider support to the generator
   - Create templates for type/method detection patterns

5. **Generate Konveyor rules for Applet API removal**
   - Run generator against Applet API specification
   - Produce valid YAML ruleset

6. **Create test Java code using deprecated Applet APIs**
   - Write sample code that imports/extends Applet classes
   - Include various usage patterns

7. **Validate generated rules against test code using analyzer**
   - Run Konveyor analyzer with generated rules
   - Verify incidents are detected correctly

8. **Refine generator based on validation results**
   - Fix any issues found during validation
   - Improve rule quality and messages

## Success Criteria
- Generator produces valid Konveyor YAML rules for Java provider
- Rules correctly detect all Applet API usage patterns
- Analyzer successfully identifies violations in test code
- Tool remains generic and reusable for other Java migrations
