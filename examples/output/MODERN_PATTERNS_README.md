# Angular Modern Patterns - Usage Guide

## Overview

The `angular-modern-patterns` ruleset detects **legacy patterns** in Angular 17+ codebases that should be modernized. These rules apply to **any Angular 17+ application**, regardless of which version you migrated from.

## When to Use These Rules

✅ **DO USE if:**
- Your app is on Angular 17 or later
- You want to identify opportunities to modernize your codebase
- You want to adopt signals, new control flow, or standalone components
- You're doing code quality improvements

❌ **DON'T USE if:**
- Your app is on Angular 16 or earlier (these features aren't available)
- You just want migration-blocking issues (use version-specific rulesets instead)

## Current Labels (Confusing)

```yaml
konveyor.io/source=angular-16
konveyor.io/target=angular-17
```

**Note:** These labels suggest a v16→v17 migration, but the rules actually apply to ANY Angular 17+ codebase. We labeled them this way because:
- Angular 17 introduced these modern patterns
- If you're on v16, upgrading to v17 makes these patterns available

## Better Way to Think About It

Think of this ruleset as **"Angular 17+ Modernization Detector"** rather than a migration ruleset.

## Rules Breakdown by Angular Version

### Angular 17.0+ (Control Flow & Components)

**Control Flow Syntax:**
- `*ngIf` → `@if` 
- `*ngFor` → `@for`
- `*ngSwitch` → `@switch`

**Component Directives:**
- `[ngClass]` → `[class.x]` bindings
- `[ngStyle]` → `[style.x]` bindings

**Standalone Components:**
- Detect non-standalone components

### Angular 17.1+ (Signals)

**Signal-based APIs:**
- `@Input()` → `input()` signal inputs
- `@Output()` → `output()` signal outputs  
- `@ViewChild()` → `viewChild()` signal queries
- `@ContentChild()` → `contentChild()` signal queries

## Usage Examples

### Example 1: Quality Audit of Angular 18 App

```bash
# You're on Angular 18, want to see what can be modernized
kantra analyze \
  --input /path/to/angular-18-app \
  --target angular-17 \
  --rules examples/output/angular-modern-patterns/migration-rules.yaml \
  --output modernization-report
```

**Result:** Shows all legacy patterns that could use modern Angular features.

### Example 2: Post-Migration Cleanup

```bash
# You just migrated from v14 to v19, now want to modernize
kantra analyze \
  --input /path/to/newly-upgraded-app \
  --target angular-17 \
  --rules examples/output/angular-modern-patterns/migration-rules.yaml \
  --output cleanup-report
```

**Result:** Identifies code still using old patterns (decorators, *ngIf, etc.)

### Example 3: Combined with Migration Rules

```bash
# If migrating v16 → v21, run both migration AND modernization
kantra analyze \
  --input /path/to/angular-app \
  --target angular-21 \
  --rules examples/output/angular-v16-to-v21/migration-rules.yaml \
  --rules examples/output/angular-modern-patterns/migration-rules.yaml \
  --output complete-analysis
```

## Priority Recommendations

After running these rules, prioritize modernization:

### High Priority (Do First)
1. **Control flow syntax** (`*ngIf` → `@if`)
   - Easier to read and type-safe
   - Can be automated with Angular schematic
   - Low risk, high benefit

2. **Standalone components**
   - Simplifies dependency management
   - Smaller bundles with better tree-shaking
   - Required for future Angular

### Medium Priority (Do Next)
3. **Class/style bindings** (`[ngClass]` → `[class.x]`)
   - Better performance
   - More explicit
   - Easy to refactor

### Low Priority (Optional/Gradual)
4. **Signal inputs/outputs**
   - Breaking change for component APIs
   - Do incrementally, starting with leaf components
   - Great for new components, risky for existing ones

5. **Signal queries**
   - Less urgent than inputs/outputs
   - Do when touching the code anyway

## Pattern Applicability Matrix

| Pattern | Works in v14 | Works in v15 | Works in v16 | Works in v17 | Works in v18+ |
|---------|--------------|--------------|--------------|--------------|---------------|
| Standalone components | ⚠️ Beta | ✅ Stable | ✅ | ✅ | ✅ |
| `[class.x]` bindings | ✅ | ✅ | ✅ | ✅ | ✅ |
| `[style.x]` bindings | ✅ | ✅ | ✅ | ✅ | ✅ |
| `@if`/`@for` control flow | ❌ | ❌ | ❌ | ✅ | ✅ |
| `input()` signals | ❌ | ❌ | ❌ | ✅ v17.1+ | ✅ |
| `output()` signals | ❌ | ❌ | ❌ | ✅ v17.1+ | ✅ |
| `viewChild()` queries | ❌ | ❌ | ❌ | ✅ v17.1+ | ✅ |

## Automated Migrations

Angular provides schematics for some of these:

```bash
# Control flow migration (v17+)
ng generate @angular/core:control-flow

# Standalone migration (v15+)  
ng generate @angular/core:standalone

# Signal input migration (v17.1+)
ng generate @angular/core:signal-input-migration
```

## Summary

**TL;DR:**
- These rules work on **any Angular 17+ codebase**
- They detect **legacy patterns**, not migration blockers
- Use them for **code quality improvement**, not just migration
- The `angular-16 → angular-17` labels are misleading
- Think of this as **"Modernization Detector"** not migration rules
