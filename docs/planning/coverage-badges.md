# Adding Code Coverage Badges to GitHub

This guide shows you how to add code coverage badges to your repository's README.

## Option 1: Codecov (Recommended)

Codecov is free for public repositories and provides the best integration with GitHub.

### Setup Steps

**1. Sign up for Codecov**
   - Go to https://codecov.io
   - Click "Sign up with GitHub"
   - Authorize Codecov to access your repositories
   - Select your repository: `analyzer-rule-generator`

**2. Get your Codecov token**
   - In Codecov dashboard, go to your repository settings
   - Copy the "Repository Upload Token"

**3. Add token to GitHub Secrets**
   - Go to your GitHub repo: Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `CODECOV_TOKEN`
   - Value: Paste your Codecov token
   - Click "Add secret"

**4. Add badge to README**

Add this to the top of your `README.md`:

```markdown
[![codecov](https://codecov.io/gh/tsanders-rh/analyzer-rule-generator/branch/main/graph/badge.svg)](https://codecov.io/gh/tsanders-rh/analyzer-rule-generator)
```

**5. Push and verify**

```bash
git add .github/workflows/tests.yml
git commit -m "Add code coverage workflow with Codecov"
git push
```

After the workflow runs, your badge will show the current coverage percentage!

### Codecov Badge Customization

You can customize the badge style:

```markdown
<!-- Flat style (default) -->
[![codecov](https://codecov.io/gh/USER/REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/USER/REPO)

<!-- Flat-square style -->
[![codecov](https://codecov.io/gh/USER/REPO/branch/main/graph/badge.svg?style=flat-square)](https://codecov.io/gh/USER/REPO)

<!-- For-the-badge style -->
[![codecov](https://codecov.io/gh/USER/REPO/branch/main/graph/badge.svg?style=for-the-badge)](https://codecov.io/gh/USER/REPO)
```

---

## Option 2: Coveralls

Coveralls is another popular option, also free for public repos.

### Setup Steps

**1. Sign up for Coveralls**
   - Go to https://coveralls.io
   - Sign in with GitHub
   - Add your repository

**2. Update GitHub Actions workflow**

```yaml
- name: Upload coverage to Coveralls
  uses: coverallsapp/github-action@v2
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

**3. Add badge to README**

```markdown
[![Coverage Status](https://coveralls.io/repos/github/tsanders-rh/analyzer-rule-generator/badge.svg?branch=main)](https://coveralls.io/github/tsanders-rh/analyzer-rule-generator?branch=main)
```

---

## Option 3: GitHub Actions + Shields.io (No external service)

If you prefer not to use external services, you can generate a badge directly.

### Setup Steps

**1. Update workflow to generate coverage badge**

Add this to your `.github/workflows/tests.yml`:

```yaml
- name: Generate coverage badge
  run: |
    pip install coverage-badge
    coverage-badge -o coverage.svg -f

- name: Commit coverage badge
  if: github.ref == 'refs/heads/main'
  run: |
    git config --local user.email "github-actions[bot]@users.noreply.github.com"
    git config --local user.name "github-actions[bot]"
    git add coverage.svg
    git diff --cached --quiet || git commit -m "Update coverage badge"
    git push
```

**2. Add badge to README**

```markdown
![Coverage](./coverage.svg)
```

---

## Option 4: Manual Badge with Shields.io

Create a custom badge using your latest coverage percentage:

```markdown
![Coverage](https://img.shields.io/badge/coverage-42%25-yellow)
```

Update the percentage manually or with a script after each test run.

---

## Recommended Badge Collection

Here's a nice collection of badges to add to your README:

```markdown
# Analyzer Rule Generator

![Tests](https://github.com/tsanders-rh/analyzer-rule-generator/workflows/Tests/badge.svg)
[![codecov](https://codecov.io/gh/tsanders-rh/analyzer-rule-generator/branch/main/graph/badge.svg)](https://codecov.io/gh/tsanders-rh/analyzer-rule-generator)
![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)
[![License](https://img.shields.io/github/license/tsanders-rh/analyzer-rule-generator)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
```

---

## Troubleshooting

### Badge not updating

**Problem:** Badge shows old coverage percentage

**Solutions:**
1. Wait a few minutes - badges are cached
2. Force refresh: Add `?` to the badge URL (e.g., `badge.svg?`)
3. Check that your workflow is running successfully
4. Verify coverage report is being uploaded

### "Coverage not found" error

**Problem:** Codecov/Coveralls can't find coverage report

**Solutions:**
1. Ensure `coverage.xml` is being generated:
   ```bash
   pytest --cov=src/rule_generator --cov-report=xml
   ```
2. Check file path in upload action
3. Verify coverage report exists in workflow logs

### Badge shows "unknown"

**Problem:** No coverage data uploaded yet

**Solutions:**
1. Push a commit to trigger the workflow
2. Wait for workflow to complete successfully
3. Check workflow logs for upload errors

---

## Coverage Goals

Set coverage thresholds in `pytest.ini`:

```ini
[coverage:report]
fail_under = 80
show_missing = True
```

This will fail tests if coverage drops below 80%.

---

## Best Practices

1. **Place badges at the top of README** for visibility
2. **Link badges to reports** so viewers can see details
3. **Set coverage goals** and enforce them in CI
4. **Update regularly** - run tests on every push
5. **Monitor trends** using Codecov's graphs and reports

---

## Example README Header

```markdown
# Konveyor Analyzer Rule Generator

[![Tests](https://github.com/tsanders-rh/analyzer-rule-generator/workflows/Tests/badge.svg)](https://github.com/tsanders-rh/analyzer-rule-generator/actions)
[![codecov](https://codecov.io/gh/tsanders-rh/analyzer-rule-generator/branch/main/graph/badge.svg)](https://codecov.io/gh/tsanders-rh/analyzer-rule-generator)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/tsanders-rh/analyzer-rule-generator)](LICENSE)

Automatically generate Konveyor analyzer rules from migration guides and OpenRewrite recipes using LLMs.

## Quick Start

\`\`\`bash
python scripts/generate_rules.py --guide <url> --source v1 --target v2
\`\`\`
```

---

## Next Steps

After setting up badges:

1. **Monitor coverage trends** in Codecov dashboard
2. **Set up branch protection** to require passing tests
3. **Add coverage comments** to PRs (Codecov does this automatically)
4. **Improve coverage** targeting uncovered code

## Resources

- [Codecov Documentation](https://docs.codecov.com/)
- [Coveralls Documentation](https://docs.coveralls.io/)
- [Shields.io Badge Generator](https://shields.io/)
- [GitHub Actions Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
