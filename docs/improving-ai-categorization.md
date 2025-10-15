# Improving AI-Generated Rule Categorization

The AI-generated rules initially categorized most patterns as "potential" when they should have been "mandatory" for API removals. Here's how we improved this.

## The Problem

**Before improvements:**
```
Rule Summary:
  Total rules: 9
  mandatory: 1
  potential: 8
```

All the removed Applet APIs were marked as "potential" even though they're completely removed in JDK 21 (code won't compile).

## Root Cause

The categorization logic in `generator.py` only looked at **complexity**:
- TRIVIAL or HIGH/EXPERT → mandatory
- LOW/MEDIUM → potential

The AI was labeling API removals as "MEDIUM" complexity, so they became "potential".

## Solutions Implemented

### 1. Updated Complexity Definitions in Prompt

Modified `src/rule_generator/extraction.py` to give better guidance:

```python
7. **Complexity**: One of:
   - TRIVIAL: Mechanical find-replace (e.g., package rename, simple import changes)
   - LOW: Straightforward API equivalents with 1:1 replacement
   - MEDIUM: Requires understanding context or minor refactoring
   - HIGH: Removed/deprecated APIs requiring architectural changes  # ← Clarified
   - EXPERT: Complex architectural changes needing human review
```

### 2. Added Keyword Detection

Enhanced `_determine_category()` in `src/rule_generator/generator.py`:

```python
# API removals should be mandatory regardless of complexity
# Look for keywords in rationale that indicate removal/deprecation
rationale_lower = pattern.rationale.lower()
removal_keywords = ['removed', 'removal', 'deprecated for removal',
                    'no longer available', 'deleted']
if any(keyword in rationale_lower for keyword in removal_keywords):
    return Category.MANDATORY
```

## Results

**After improvements:**
```
Rule Summary:
  Total rules: 9
  mandatory: 7  ← Improved!
  potential: 2
```

The keyword detection successfully identified API removal patterns from the rationale text and marked them as mandatory.

## When to Use Each Approach

### Prompt Updates (Solution 1)
✅ Use when: You want the AI to make better initial decisions
✅ Pros: Teaches the AI, improves future extractions
❌ Cons: Non-deterministic, AI might still make mistakes

### Keyword Detection (Solution 2)
✅ Use when: You can identify patterns in the rationale text
✅ Pros: Reliable, deterministic post-processing
❌ Cons: Requires updating keywords for different scenarios

### Both Together (Recommended)
Use both for best results:
1. Prompt guides AI to better complexity assessment
2. Keyword detection catches any the AI misses

## Customization

You can add more keywords for your specific migration:

```python
removal_keywords = [
    'removed', 'removal', 'deprecated for removal',
    'no longer available', 'deleted',
    'obsolete', 'discontinued',  # Add your keywords
    'end of life', 'eol'
]
```

Or detect other patterns:

```python
# Mark security-related changes as mandatory
if any(word in rationale_lower for word in ['security', 'vulnerability', 'cve']):
    return Category.MANDATORY

# Mark breaking changes as mandatory
if 'breaking change' in rationale_lower:
    return Category.MANDATORY
```

## Testing Your Improvements

```bash
# Generate rules with improvements
python scripts/generate_rules.py \
  --guide https://openjdk.org/jeps/504 \
  --source openjdk17 \
  --target openjdk21 \
  --output test-output.yaml \
  --provider anthropic \
  --model claude-3-7-sonnet-20250219

# Check the summary
# Should see more "mandatory" rules
```

## Alternative: Manual Override

For critical migrations, you can also manually override the AI's categorization:

```python
# After generation, update specific rules
for rule in rules:
    if 'applet' in rule.description.lower():
        rule.category = Category.MANDATORY
```

This gives you full control while still benefiting from AI pattern discovery.
