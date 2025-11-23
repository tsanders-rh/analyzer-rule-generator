# PatternFly Improved Detection - Combo Rules

This directory contains an enhanced version of the PatternFly 5-to-6 migration rules with **improved detection accuracy**.

## What Changed?

All rules that previously used **only** `nodejs.referenced` provider have been converted to **combo rules** that use both:
- `nodejs.referenced` - Ensures the component is imported from `@patternfly/react-core`
- `builtin.filecontent` - Finds actual JSX usage with specific props/patterns in the code

## Why This Matters

The `nodejs.referenced` provider only detects symbols that exist in `node_modules` dependencies. It does NOT find actual usage in your code.

### Example Problem

**Original rule (nodejs-only):**
```yaml
when:
  nodejs.referenced:
    pattern: Card
```

This would find that `Card` exists in `@patternfly/react-core` but would NOT find this code:
```tsx
<Card isSelectableRaised isDisabledRaised />
```

**Fixed rule (combo):**
```yaml
when:
  and:
  - nodejs.referenced:
      pattern: Card
  - builtin.filecontent:
      pattern: <Card[^>]*\b(isSelectableRaised|isDisabledRaised)\b
      filePattern: \.(j|t)sx?$
```

This WILL find the actual usage in your TSX/JSX files.

## Files Modified

### patternfly-5-to-patternfly-6-component-props.yaml
All 7 rules converted to combo:

1. **AccordionContent** - Detects `isHidden` prop usage
2. **AccordionToggle** - Detects `isExpanded` prop usage
3. **Avatar** - Detects `border=` prop usage
4. **Banner** - Detects `variant=` prop usage
5. **Button** - Detects `isActive` prop usage
6. **Card** - Detects deprecated props: `isSelectableRaised`, `isDisabledRaised`, `hasSelectableInput`, `selectableInputAriaLabel`
7. **Checkbox** - Detects `isLabelBeforeButton` prop usage

### patternfly-5-to-patternfly-6-components.yaml
1 rule converted to combo:

1. **EmptyState** - Detects `<EmptyState` component usage

## Testing

To test these rules against the tackle2-ui codebase:

```bash
kantra analyze \
  --input /path/to/tackle2-ui \
  --output /path/to/output \
  --rules /path/to/patternfly-improved-detection-combo \
  --target patternfly-6
```

## Expected Results

The combo rules should now detect:
- **target-card.tsx:121** - Card component with deprecated props
- All other PatternFly component usages with deprecated props

## Original Rules Preserved

The original nodejs-only rules are preserved in:
```
/Users/tsanders/Workspace/analyzer-rule-generator/examples/output/patternfly-improved-detection/
```
