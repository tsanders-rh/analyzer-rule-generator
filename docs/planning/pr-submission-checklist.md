# PR Submission Checklist

## Overview

You're submitting a single combined PR for TypeScript/React support to konveyor/analyzer-lsp.

## What You're Including

### 1. Code Changes
- ✅ Fix 1: Add .tsx/.jsx support + skip node_modules (branch: `fix/nodejs-tsx-support`)
- ✅ Fix 2: Add brace expansion support (branch: `fix/brace-expansion-support`)

### 2. Test Files (NEW - Recommended)
Located in `/Users/tsanders/Workspace/analyzer-rule-generator/pr-test-files/`:
- `test-tsx-support.yaml` - Tests .tsx file detection
- `test-brace-expansion.yaml` - Tests brace expansion patterns
- `README.md` - Test instructions for reviewers

### 3. Documentation
- Detailed PR description (included in PR creation command)
- Test evidence and before/after results
- Use case explanation (PatternFly v5→v6 migration)

## Files to Reference

### Setup Guide
📄 **COMBINED-PR-STEPS.md** - Step-by-step instructions to create the PR

### Testing Guide
📄 **PR-TESTING-PACKAGE.md** - Comprehensive testing instructions for reviewers

### Email (Already Sent)
📧 **ANALYZER-TEAM-EMAIL.md** - Email explaining the issues

### Original Plans
📄 **ANALYZER-LSP-PR-PLAN.md** - Original detailed plan for both fixes
📄 **TYPESCRIPT-PROVIDER-PR-PLAN.md** - Original TypeScript provider fix plan only

## Pre-Submission Checklist

Before running the PR creation steps:

- [ ] Both fix branches committed and pushed to fork
  - [ ] `fix/nodejs-tsx-support` pushed
  - [ ] `fix/brace-expansion-support` pushed
- [ ] Email sent to analyzer team (received confirmation for single PR)
- [ ] Test files prepared in `pr-test-files/` directory
- [ ] Reviewed COMBINED-PR-STEPS.md
- [ ] Have ~30 minutes to complete the process

## During Submission

Follow **COMBINED-PR-STEPS.md** exactly:

1. ✅ Update main branch
2. ✅ Create combined branch: `fix/typescript-react-support`
3. ✅ Merge both fix branches
4. ✅ Verify changes
5. ✅ Rebuild and test
6. ✅ **Add test files** (Step 6 - RECOMMENDED)
7. ✅ Run quick test (Step 7)
8. ✅ Create combined commit (Step 8 - optional squash)
9. ✅ Push to fork
10. ✅ Create PR with full description

## Post-Submission Checklist

After PR is created:

- [ ] Verify PR shows up on GitHub
- [ ] Check that CI/CD passes (if applicable)
- [ ] Monitor for review comments
- [ ] Be ready to respond within 24-48 hours
- [ ] Update PR if requested

## Quick Reference Commands

### Check PR Status
```bash
gh pr list --repo konveyor/analyzer-lsp --author tsanders-rh
gh pr view --repo konveyor/analyzer-lsp --web
gh pr checks --repo konveyor/analyzer-lsp
```

### Make Updates to PR
```bash
cd ~/Workspace/analyzer-lsp
git checkout fix/typescript-react-support

# Make changes
git add <files>
git commit -s -m "Address review feedback: <description>"
git push fork fix/typescript-react-support
```

## Success Indicators

✅ PR created successfully
✅ All commits signed with DCO (`-s` flag)
✅ Test files included in PR
✅ CI/CD checks pass (green checkmarks)
✅ No merge conflicts
✅ Clear description with test evidence
✅ Maintainers acknowledge receipt

## What Reviewers Will See

### PR Title
**Enable TypeScript/React analysis support**

### PR Files Changed
1. `external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go`
2. `provider/lib.go`
3. `go.mod`
4. `test/test-tsx-support.yaml` (NEW)
5. `test/test-brace-expansion.yaml` (NEW)
6. `test/README.md` (NEW)

### Key Selling Points
- ✅ Fixes critical blockers for TypeScript/React analysis
- ✅ Enables PatternFly migration use case
- ✅ Trials Konveyor AI for real-world migration
- ✅ Includes comprehensive test files
- ✅ Backward compatible
- ✅ Performance improvement: 15+ minutes → 5-7 seconds

## Timeline Expectations

- **Day 0:** Submit PR ⏳
- **Day 1-2:** Initial review and CI/CD checks
- **Day 3-7:** Address feedback if needed
- **Week 2+:** Potential merge

## Contingency Plans

### If Reviewers Ask to Split the PR

Response:
> "Happy to split if preferred! The fixes work well together for TypeScript/React support, but I can submit as:
> - PR 1: TypeScript provider fixes (.tsx support + skip node_modules)
> - PR 2: Brace expansion support
>
> Let me know which you prefer."

### If CI/CD Fails

1. Check failure logs: `gh pr checks --repo konveyor/analyzer-lsp`
2. Fix locally and push update
3. Comment on PR explaining the fix

### If Merge Conflicts Arise

```bash
git checkout fix/typescript-react-support
git fetch origin
git rebase origin/main
# Fix conflicts
git push fork fix/typescript-react-support --force
```

## Resources

- **GitHub Repo:** https://github.com/konveyor/analyzer-lsp
- **Your Fork:** https://github.com/tsanders-rh/analyzer-lsp
- **PR Branch:** `fix/typescript-react-support`
- **Test Files:** `/Users/tsanders/Workspace/analyzer-rule-generator/pr-test-files/`

## Notes

- Be polite and professional in all interactions
- Thank reviewers for their time
- Be patient - open source reviews can take time
- Offer to help with testing or documentation
- Emphasize the PatternFly migration use case

## Ready?

When you're ready to submit:

1. Open **COMBINED-PR-STEPS.md**
2. Follow each step carefully
3. Don't skip the test files (Step 6)
4. Verify everything before pushing

Good luck! 🚀
