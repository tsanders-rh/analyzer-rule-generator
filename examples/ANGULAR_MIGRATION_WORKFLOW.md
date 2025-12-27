# Angular v2 → v21 Migration Workflow

Complete step-by-step guide for migrating an Angular application from v2 to v21 using Konveyor analyzer rules.

## Overview

Angular requires **incremental upgrades** - you cannot jump directly from v2 to v21. This workflow guides you through each version range with automated rule detection.

---

## Prerequisites

- [ ] Install [Konveyor Kantra](https://github.com/konveyor/kantra)
- [ ] Have Angular v2 application source code
- [ ] Backup your codebase
- [ ] Create a migration branch: `git checkout -b upgrade-to-angular-21`

---

## Phase 1: Angular v2 → v8 (Early Angular)

### 1.1 Run Static Analysis

```bash
kantra analyze \
  --input /path/to/your/angular-app \
  --target angular-8 \
  --rules examples/output/angular-v2-to-v8/migration-rules.yaml \
  --output analysis-v8
```

### 1.2 Review Results

```bash
# View HTML report
open analysis-v8/static-report/index.html

# Or view YAML output
cat analysis-v8/output.yaml
```

**Expected Findings:** 7 rules covering:
- OpaqueToken → InjectionToken
- Renderer → Renderer2
- Router parameter changes
- Template syntax updates
- Directive updates

### 1.3 Fix Issues

Address all issues found by the analyzer before proceeding.

### 1.4 Update Angular

```bash
# Update to Angular 8
ng update @angular/core@8 @angular/cli@8
```

### 1.5 Test

```bash
npm test
ng build --configuration production
# Manual testing of critical paths
```

### 1.6 Commit

```bash
git add .
git commit -m "Upgrade to Angular 8"
```

---

## Phase 2: Angular v9 → v10 (Ivy Introduction)

### 2.1 Run Static Analysis

```bash
kantra analyze \
  --input /path/to/your/angular-app \
  --target angular-10 \
  --rules examples/output/angular-v9-to-v10/migration-rules.yaml \
  --output analysis-v10
```

**Expected Findings:** 5 rules covering:
- Build optimization
- Forms API changes
- Ivy compatibility
- Testing API updates
- Type safety improvements

### 2.2 Update Angular 9

```bash
ng update @angular/core@9 @angular/cli@9
```

**Manual Steps:**
- Remove `enableIvy` from `tsconfig.json` (now default)
- Remove `entryComponents` from NgModules
- Update `ModuleWithProviders` to specify generic type

### 2.3 Test & Commit

```bash
npm test
ng build --configuration production
git commit -am "Upgrade to Angular 9"
```

### 2.4 Update to Angular 10

```bash
kantra analyze \
  --input /path/to/your/angular-app \
  --target angular-10 \
  --rules examples/output/angular-v9-to-v10/migration-rules.yaml \
  --output analysis-v10

# Fix any remaining issues
ng update @angular/core@10 @angular/cli@10
npm test
git commit -am "Upgrade to Angular 10"
```

---

## Phase 3: Angular v11-v13 (Configuration Changes)

⚠️ **No automated rules available** - these versions are primarily configuration changes.

### 3.1 Angular 11

```bash
ng update @angular/core@11 @angular/cli@11
```

**Manual Changes:**
- Update `relativeLinkResolution` in router config
- Replace `ViewEncapsulation.Native` with `ViewEncapsulation.ShadowDom`
- Update `initialNavigation` router options

### 3.2 Angular 12

```bash
ng update @angular/core@12 @angular/cli@12
```

**Manual Changes:**
- Update `XhrFactory` imports (`@angular/common/http` → `@angular/common`)
- Review forms with `min`/`max` validation

### 3.3 Angular 13

```bash
ng update @angular/core@13 @angular/cli@13
```

**Manual Changes:**
- Convert string-based `loadChildren` to dynamic imports
- Update service worker usage (if applicable)

**Test & Commit after each version:**
```bash
npm test
ng build --configuration production
git commit -am "Upgrade to Angular 13"
```

---

## Phase 4: Angular v14 → v15 (Typed Forms)

### 4.1 Run Static Analysis

```bash
kantra analyze \
  --input /path/to/your/angular-app \
  --target angular-15 \
  --rules examples/output/angular-v14/migration-rules.yaml \
  --output analysis-v15
```

**Expected Findings:** 6 rules covering:
- Component usage patterns
- Router type changes
- Testing API updates
- Angular CDK/Material updates

### 4.2 Update Angular 14

```bash
ng update @angular/core@14 @angular/cli@14
```

**Manual Steps:**
- Consider migrating to typed forms
- Or use `UntypedFormControl`, `UntypedFormGroup`, `UntypedFormArray`

### 4.3 Update to Angular 15

```bash
# Fix issues from analysis
ng update @angular/core@15 @angular/cli@15
```

**Manual Steps:**
- Remove `enableIvy` from `tsconfig.json`
- Update decorator usage for base classes
- Review `@keyframes` scoping (if using animations in TypeScript)

### 4.4 Test & Commit

```bash
npm test
ng build --configuration production
git commit -am "Upgrade to Angular 15"
```

---

## Phase 5: Angular v16 → v21 (Modern Angular)

### 5.1 Run Static Analysis

```bash
kantra analyze \
  --input /path/to/your/angular-app \
  --target angular-21 \
  --rules examples/output/angular-v16-to-v21/migration-rules.yaml \
  --output analysis-v21
```

**Expected Findings:** 7 rules covering:
- Import path changes
- API removals
- Router event types
- Renderer style changes

### 5.2 Update Through Versions

```bash
# v16
ng update @angular/core@16 @angular/cli@16
npm test && git commit -am "Upgrade to Angular 16"

# v17
ng update @angular/core@17 @angular/cli@17
npm test && git commit -am "Upgrade to Angular 17"

# v18
ng update @angular/core@18 @angular/cli@18
npm test && git commit -am "Upgrade to Angular 18"

# v19
ng update @angular/core@19 @angular/cli@19
npm test && git commit -am "Upgrade to Angular 19"

# v20
ng update @angular/core@20 @angular/cli@20
npm test && git commit -am "Upgrade to Angular 20"

# v21
ng update @angular/core@21 @angular/cli@21
npm test && git commit -am "Upgrade to Angular 21"
```

---

## Phase 6: Modernization (Optional but Recommended)

### 6.1 Run Modern Pattern Detection

```bash
kantra analyze \
  --input /path/to/your/angular-app \
  --target angular-17 \
  --rules examples/output/angular-modern-patterns/migration-rules.yaml \
  --output analysis-modern
```

**Expected Findings:** 7 rules for modern patterns:
- `@Input()` → `input()` signals
- `@Output()` → `output()` function
- `@ViewChild()` → `viewChild()` queries
- `*ngIf` → `@if` control flow
- `[ngClass]` → class bindings
- `[ngStyle]` → style bindings
- Standalone components

### 6.2 Prioritize Modernization

Review findings and prioritize based on:
1. **High impact, low effort:** `*ngIf`/`*ngFor` → `@if`/`@for`
2. **Medium effort:** Standalone components
3. **Low priority:** Signal inputs/outputs (can do incrementally)

### 6.3 Apply Angular Schematics

```bash
# Convert to standalone components
ng generate @angular/core:standalone

# Convert to new control flow
ng generate @angular/core:control-flow

# Convert to signal inputs (Angular 17.1+)
ng generate @angular/core:signal-input-migration
```

---

## Validation Checklist

After completing migration:

### Functional Testing
- [ ] All unit tests pass
- [ ] All e2e tests pass
- [ ] Production build succeeds
- [ ] Manual testing of critical user flows
- [ ] No console errors in development
- [ ] No console errors in production build

### Performance Testing
- [ ] Compare bundle sizes (should be smaller with v21)
- [ ] Run Lighthouse audits
- [ ] Check initial load time
- [ ] Verify lazy loading still works

### Code Quality
- [ ] Run linter: `ng lint`
- [ ] Check for any `@ts-ignore` or `any` types added during migration
- [ ] Review deprecated API warnings

---

## Troubleshooting

### Common Issues

**"Cannot find module '@angular/...'"**
```bash
rm -rf node_modules package-lock.json
npm install
```

**TypeScript compilation errors**
- Check TypeScript version compatibility
- Review `tsconfig.json` strict mode settings
- Update `@types/*` packages

**Runtime errors after upgrade**
- Check browser console for errors
- Verify all lazy-loaded modules load
- Test on multiple browsers

**Build performance degraded**
- Clear Angular cache: `ng cache clean`
- Review build optimization settings in `angular.json`

---

## Timeline Estimate

Typical migration timeline for a medium-sized application:

| Phase | Duration | Effort |
|-------|----------|--------|
| Phase 1 (v2→v8) | 2-3 weeks | High - major changes |
| Phase 2 (v9→v10) | 1 week | Medium - Ivy transition |
| Phase 3 (v11→v13) | 1 week | Low - mostly config |
| Phase 4 (v14→v15) | 1-2 weeks | Medium - typed forms |
| Phase 5 (v16→v21) | 2-3 weeks | Medium - incremental |
| Phase 6 (Modernization) | 2-4 weeks | Variable - optional |
| **Total** | **9-16 weeks** | |

*Note: Timeline varies significantly based on application size, test coverage, and team size.*

---

## Resources

- [Angular Update Guide](https://angular.dev/update-guide)
- [Angular Migrations Reference](https://angular.dev/reference/migrations)
- [Konveyor Documentation](https://konveyor.io/docs)
- [Angular Blog](https://blog.angular.dev/)

---

## Success Criteria

✅ Application runs on Angular 21  
✅ All tests pass  
✅ No deprecated API warnings  
✅ Production build successful  
✅ Bundle size maintained or reduced  
✅ Core functionality verified  
✅ Modern patterns applied (optional)

**Your application is now on the latest Angular with automated migration assistance from Konveyor!**
