# Rule Viewers

This project provides two ways to view Konveyor analyzer rules with an interactive interface.

## 🌐 Web-Based Viewer (Recommended for most users)

**Location:** `docs/rule-viewer.html`

A single-page web application that can load any ruleset dynamically from URLs or local files.

### Features

- ✅ Load rules from GitHub URLs (auto-converts blob URLs to raw URLs)
- ✅ Upload local YAML files (drag & drop supported)
- ✅ Share links with pre-loaded rulesets via `?url=...` parameter
- ✅ Switch between different rulesets without regenerating
- ✅ Search, filter by category/effort
- ✅ Expandable rule details
- ✅ Works entirely client-side (no backend needed)

### Usage

#### Option 1: GitHub Pages (Best for sharing)

Host on GitHub Pages for easy access:

```bash
# The viewer is in docs/rule-viewer.html
# Access via: https://yourusername.github.io/repo-name/rule-viewer.html
```

Share with pre-loaded rules:
```
https://yourusername.github.io/repo-name/rule-viewer.html?url=https://raw.githubusercontent.com/konveyor/rulesets/main/default/generated/00-discovery.windup.yaml
```

#### Option 2: Local File

```bash
# Open locally
open docs/rule-viewer.html

# Then choose:
# - Load from URL: Paste GitHub raw URL or any CORS-enabled URL
# - Load from File: Upload or drag-drop your YAML file
```

### When to Use

- ✅ Exploring multiple rulesets
- ✅ Sharing rules with team members via links
- ✅ Viewing upstream Konveyor rules from GitHub
- ✅ Quick rule browsing without generating files
- ✅ GitHub Pages hosting

## 📄 Standalone HTML Generator

**Location:** `scripts/generate_rule_viewer.py`

Generates self-contained HTML files with rules baked in.

### Features

- ✅ Single HTML file contains all rules (works offline)
- ✅ No internet required after generation
- ✅ Easy to share via email/file transfer
- ✅ Archived snapshots of rulesets

### Usage

```bash
# Basic usage
python scripts/generate_rule_viewer.py \
  --rules examples/output/patternfly-v6/migration-rules.yaml \
  --output viewer.html

# With custom title and auto-open
python scripts/generate_rule_viewer.py \
  --rules examples/output/patternfly-v6/migration-rules.yaml \
  --output patternfly-v6-viewer.html \
  --title "PatternFly v5 → v6 Migration Rules" \
  --open
```

### When to Use

- ✅ Offline viewing (no internet needed)
- ✅ Sharing single-file viewers via email/Slack
- ✅ Creating archived snapshots of specific rulesets
- ✅ Embedding in documentation packages
- ✅ Distributing rules to users without GitHub access

## Comparison

| Feature | Web Viewer | Standalone Generator |
|---------|-----------|---------------------|
| **File Size** | ~60KB | ~60KB + rules size |
| **Internet Required** | Yes (to load rules) | No |
| **Switch Rulesets** | ✅ Click button | ❌ Regenerate file |
| **Share Method** | URL with `?url=` | Send HTML file |
| **GitHub Pages** | ✅ Perfect fit | ⚠️ One file per ruleset |
| **Offline Use** | ❌ Needs internet | ✅ Fully offline |
| **Update Rules** | Reload from URL | ❌ Regenerate |

## Examples

### Web Viewer Examples

```bash
# View PatternFly rules from GitHub
https://yourusername.github.io/analyzer-rule-generator/rule-viewer.html?url=https://raw.githubusercontent.com/konveyor/rulesets/main/default/generated/camel3/30-component-changes.groovy.windup.yaml

# View local rules
open docs/rule-viewer.html
# Then click "Load from File" and select your YAML
```

### Standalone Generator Examples

```bash
# Generate for JDK migration
python scripts/generate_rule_viewer.py \
  --rules examples/output/jdk21/migration-rules.yaml \
  --output jdk21-rules.html \
  --open

# Generate for Spring Boot migration
python scripts/generate_rule_viewer.py \
  --rules examples/output/spring-boot-4.0/migration-rules.yaml \
  --output spring-boot-4.0-rules.html \
  --title "Spring Boot 3.5 → 4.0 Rules"
```

## Recommendation

**For most use cases:** Use the **web-based viewer** (`docs/rule-viewer.html`)
- Host on GitHub Pages once
- Load any ruleset dynamically
- Easy sharing with URL parameters

**For specific cases:** Use the **standalone generator** (`generate_rule_viewer.py`)
- Need offline viewing
- Distributing to users without GitHub access
- Creating permanent snapshots for archival
