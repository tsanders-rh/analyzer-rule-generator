# PatternFly Rules Conversion Summary

## Directories

### Original Rules (preserved)
```
/Users/tsanders/Workspace/analyzer-rule-generator/examples/output/patternfly-improved-detection/
```

### New Combo Rules
```
/Users/tsanders/Workspace/analyzer-rule-generator/examples/output/patternfly-improved-detection-combo/
```

## Changes Summary

### Before (Original)
- **Total rules:** 56
- **builtin.filecontent only:** 36 rules
- **nodejs.referenced only:** 8 rules
- **nodejs + builtin combo:** 12 rules

### After (Combo)
- **Total rules:** 56
- **builtin.filecontent only:** 36 rules
- **nodejs.referenced only:** 0 rules ✅
- **nodejs + builtin combo:** 20 rules ✅

**Result:** All 8 nodejs-only rules have been successfully converted to combo rules!

## Rules Converted

### File: patternfly-5-to-patternfly-6-component-props.yaml (7 rules)

| Rule ID | Component | What It Detects | New Pattern |
|---------|-----------|----------------|-------------|
| 00000 | AccordionContent | `isHidden` prop | `<AccordionContent[^>]*\bisHidden\b` |
| 00010 | AccordionToggle | `isExpanded` prop | `<AccordionToggle[^>]*\bisExpanded\b` |
| 00020 | Avatar | `border=` prop | `<Avatar[^>]*\bborder\s*=` |
| 00030 | Banner | `variant=` prop | `<Banner[^>]*\bvariant\s*=` |
| 00040 | Button | `isActive` prop | `<Button[^>]*\bisActive\b` |
| 00050 | Card | Deprecated props | `<Card[^>]*\b(isSelectableRaised\|isDisabledRaised\|hasSelectableInput\|selectableInputAriaLabel)\b` |
| 00060 | Checkbox | `isLabelBeforeButton` prop | `<Checkbox[^>]*\bisLabelBeforeButton\b` |

### File: patternfly-5-to-patternfly-6-components.yaml (1 rule)

| Rule ID | Component | What It Detects | New Pattern |
|---------|-----------|----------------|-------------|
| 00040 | EmptyState | Component usage | `<EmptyState` |

## Why This Matters

The `nodejs.referenced` provider alone only finds symbols in `node_modules` - it does NOT find actual usage in your code.

### Example: Card Component

**Code in target-card.tsx:121**
```tsx
<Card
  key={`target-card-${target.id}`}
  className="target-card"
  id={idCard}
  data-target-name={target.name}
  data-target-id={target.id}
  isSelectable={readOnly}
  isSelected={cardSelected}
  isFullHeight
  isCompact
  isFlat
>
```

❌ **Original rule (nodejs-only)** - Would NOT detect this
```yaml
when:
  nodejs.referenced:
    pattern: Card
```

✅ **New combo rule** - WILL detect this
```yaml
when:
  and:
  - nodejs.referenced:
      pattern: Card
  - builtin.filecontent:
      pattern: <Card[^>]*\b(isSelectableRaised|isDisabledRaised|hasSelectableInput|selectableInputAriaLabel)\b
      filePattern: \.(j|t)sx?$
```

## Testing

Test the new combo rules:

```bash
kantra analyze \
  --input /path/to/tackle2-ui \
  --output /path/to/output \
  --rules /Users/tsanders/Workspace/analyzer-rule-generator/examples/output/patternfly-improved-detection-combo \
  --target patternfly-6
```

Compare against original:

```bash
kantra analyze \
  --input /path/to/tackle2-ui \
  --output /path/to/output-original \
  --rules /Users/tsanders/Workspace/analyzer-rule-generator/examples/output/patternfly-improved-detection \
  --target patternfly-6
```

## Expected Improvements

The combo rules should detect **more actual usage** in the codebase because they look for:
1. The component is imported from PatternFly (`nodejs.referenced`)
2. The component is actually used in JSX with specific props (`builtin.filecontent`)

This addresses the question: "they only add the ability to get symbols from node_modules" - now they find actual usage too!
