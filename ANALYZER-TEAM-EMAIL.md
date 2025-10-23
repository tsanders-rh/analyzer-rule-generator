# Email to Konveyor Analyzer Team

## Subject
TypeScript/React Analysis Support - Two Critical Fixes

---

## Email Body

Hi Konveyor Analyzer Team,

I've been working on generating migration rules for TypeScript/React projects using the analyzer-lsp, and I've discovered two critical issues that prevent the generic provider from analyzing TypeScript/React codebases. I have fixes for both issues that I'd like to contribute.

### Issue 1: TypeScript Provider Cannot Analyze React Projects

**Problem:**

The nodejs service client in the generic-external-provider only scans `.ts` and `.js` files, completely missing React components in `.tsx` and `.jsx` files. Additionally, the code to skip the `node_modules` directory is commented out.

**Impact:**

1. **Missing files:** TypeScript React projects return 0 files - the provider doesn't see any `.tsx` files
2. **Extreme slowness:** Without skipping `node_modules`, the provider attempts to scan all dependency files (often 500+) with a 2-second sleep delay per file (line 208), resulting in 15-20 minute hangs on simple projects

**Test Results:**

- **Before fix:** Analysis timeout after 5+ minutes, 0 `.tsx` files found
- **After fix:** Analysis completes in 5-7 seconds, correctly finds and analyzes `.tsx` files

### Issue 2: No Brace Expansion Support in File Patterns

**Problem:**

The builtin provider uses Go's `filepath.Match()` for pattern matching, which doesn't support brace expansion syntax like `*.{ts,tsx}` or `*.{css,scss}`. This forces users to write separate rules for each file extension.

**Impact:**

- Migration rules must use single extensions: `*.tsx` instead of the more convenient `*.{ts,tsx}`
- Users need to create duplicate rules for different file types
- Generated rules are more verbose and harder to maintain

**Solution:**

Integrate the `github.com/gobwas/glob` library which supports brace expansion and maintains backward compatibility with existing patterns.

**Test Results:**

- Pattern `*.{tsx,jsx}` successfully matches `.tsx` files ✅
- Pattern `*.{ts,tsx,js,jsx}` matches all TypeScript/JavaScript files ✅
- Pattern `*.{css,scss,js,jsx,ts,tsx}` matches CSS and TS/JS files ✅
- Backward compatible - existing single-extension patterns still work ✅

### Proposed Contribution

I plan to submit a PR (or two separate PRs if you prefer) with:

1. **TypeScript Provider Fixes**
   - Add `.tsx` and `.jsx` file extension support
   - Uncomment the `node_modules` skip logic
   - File: `external-providers/generic-external-provider/pkg/server_configurations/nodejs/service_client.go`

2. **Brace Expansion Support**
   - Integrate `github.com/gobwas/glob` library
   - Update pattern matching in `provider/lib.go`
   - Add dependency to `go.mod`

Both fixes have been tested locally and work correctly. I can submit them as:
- **Option A:** Single combined PR (recommended - they work together for TypeScript/React support)
- **Option B:** Two separate PRs (easier to review individually)

Let me know which approach you'd prefer!

### Use Case / Context

I'm working on a PatternFly v5 to v6 migration for our TypeScript/React codebase and wanted to trial using Konveyor with AI assistance to help automate the migration process.

To support this, I've built an analyzer-rule-generator that uses LLMs to automatically generate Konveyor migration rules from official framework documentation (PatternFly upgrade guide, React docs, etc.). The goal is to:

1. Generate migration rules automatically from PatternFly v6 upgrade documentation
2. Use the TypeScript provider to perform semantic analysis of our React components
3. Identify all instances that need migration (component renames, prop changes, deprecated patterns, etc.)
4. Use Konveyor AI to suggest fixes based on the generated rules

However, without these fixes, the TypeScript provider is essentially unusable for React projects:
- It doesn't see any `.tsx` files (our entire codebase is TypeScript React)
- It times out trying to scan `node_modules`
- We can't use convenient file patterns like `*.{ts,tsx}` in our rules

These fixes enable us to trial Konveyor AI for our real-world PatternFly migration, which could become a valuable use case / case study for the Konveyor project.

### Questions

1. Would you prefer a single combined PR or two separate PRs?
2. Are there any specific testing requirements or CI checks I should be aware of?
3. Should I add any additional documentation as part of these PRs?

I have all the code ready and tested locally. I can create the PR(s) as soon as I hear back on your preferred approach.

Thanks for your work on analyzer-lsp!

Best regards,
[Your Name]

---

## Attachments (Optional)

You could also attach:
1. Test output showing before/after performance
2. Screenshot of successful rule analysis
3. Link to the analyzer-rule-generator project (if public)

---

## Alternative: Shorter Version

If you prefer a more concise email:

---

Hi Konveyor Analyzer Team,

I'm working on a PatternFly v5 → v6 migration for our TypeScript/React codebase and wanted to trial using Konveyor AI to assist with the migration. While testing analyzer-lsp, I found two critical issues preventing TypeScript/React analysis:

**Issue 1: TypeScript Provider - Missing .tsx/.jsx Support**
- The nodejs client only scans `.ts`/`.js` files, missing React `.tsx`/`.jsx` files
- The `node_modules` skip is commented out, causing 15+ minute hangs on typical projects
- Fix: Add .tsx/.jsx support and uncomment node_modules skip
- Result: Analysis time drops from timeout to 5-7 seconds

**Issue 2: No Brace Expansion in File Patterns**
- `filepath.Match()` doesn't support `*.{ts,tsx}` syntax
- Forces duplicate rules for each file extension
- Fix: Use `github.com/gobwas/glob` library (backward compatible)
- Result: Patterns like `*.{ts,tsx,js,jsx}` now work

I have both fixes tested and ready to contribute. These fixes would enable us to trial Konveyor AI for our PatternFly migration, which could be a good use case / case study for the project.

Would you prefer:
- A) Single combined PR (they work together for TypeScript/React support)
- B) Two separate PRs (easier to review individually)

Let me know and I'll submit the PR(s)!

Thanks,
[Your Name]
