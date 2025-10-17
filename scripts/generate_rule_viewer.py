#!/usr/bin/env python3
"""
Generate an interactive HTML viewer for Konveyor analyzer rules.

Creates a standalone HTML file with search, filtering, and expandable rule details.

NOTE: This generates a standalone HTML file with rules baked in. For a web-based
viewer that can load any ruleset dynamically, see docs/rule-viewer.html which can
be hosted on GitHub Pages and load rules from URLs or local files.

Use this script when you want:
- Offline viewing (self-contained HTML)
- Shareable single-file viewers
- Archived snapshots of specific rulesets

Use docs/rule-viewer.html when you want:
- Dynamic loading from URLs/files
- GitHub Pages hosting
- One viewer for all rulesets
"""
import argparse
import sys
from pathlib import Path
import yaml
import json
from datetime import datetime


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rule Viewer: {title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background: linear-gradient(135deg, #0066cc 0%, #004494 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        header h1 {{
            font-size: 28px;
            margin-bottom: 8px;
        }}

        header .subtitle {{
            opacity: 0.9;
            font-size: 14px;
        }}

        .controls {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .controls-row {{
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }}

        .control-group {{
            flex: 1;
            min-width: 200px;
        }}

        .control-group label {{
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: #666;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        input[type="text"], select {{
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.2s;
        }}

        input[type="text"]:focus, select:focus {{
            outline: none;
            border-color: #0066cc;
        }}

        .stats {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}

        .stat-card {{
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #0066cc;
        }}

        .stat-label {{
            font-size: 12px;
            color: #666;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            color: #333;
            margin-top: 5px;
        }}

        .rules-container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .rule {{
            border-bottom: 1px solid #e0e0e0;
            transition: background-color 0.2s;
        }}

        .rule:last-child {{
            border-bottom: none;
        }}

        .rule:hover {{
            background: #f8f9fa;
        }}

        .rule-header {{
            padding: 20px;
            cursor: pointer;
            user-select: none;
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .rule-header:hover {{
            background: #f0f0f0;
        }}

        .expand-icon {{
            font-size: 14px;
            color: #999;
            transition: transform 0.2s;
            flex-shrink: 0;
        }}

        .rule.expanded .expand-icon {{
            transform: rotate(90deg);
        }}

        .rule-title {{
            flex: 1;
        }}

        .rule-id {{
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 13px;
            color: #0066cc;
            font-weight: 600;
        }}

        .rule-description {{
            font-size: 15px;
            color: #333;
            margin-top: 5px;
        }}

        .rule-meta {{
            display: flex;
            gap: 10px;
            align-items: center;
            flex-shrink: 0;
        }}

        .badge {{
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .badge-mandatory {{
            background: #fee;
            color: #c00;
        }}

        .badge-potential {{
            background: #fef3cd;
            color: #856404;
        }}

        .badge-optional {{
            background: #d1ecf1;
            color: #0c5460;
        }}

        .effort-badge {{
            background: #e0e0e0;
            color: #666;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }}

        .rule-details {{
            display: none;
            padding: 0 20px 20px 60px;
            background: #fafafa;
        }}

        .rule.expanded .rule-details {{
            display: block;
        }}

        .detail-section {{
            margin-bottom: 20px;
        }}

        .detail-label {{
            font-size: 12px;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .detail-content {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
        }}

        .code-block {{
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 13px;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            line-height: 1.5;
        }}

        .yaml-key {{
            color: #9cdcfe;
        }}

        .yaml-value {{
            color: #ce9178;
        }}

        .links-list {{
            list-style: none;
        }}

        .links-list li {{
            margin-bottom: 8px;
        }}

        .links-list a {{
            color: #0066cc;
            text-decoration: none;
            font-size: 14px;
        }}

        .links-list a:hover {{
            text-decoration: underline;
        }}

        .labels-list {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .label-tag {{
            background: #e0e0e0;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
        }}

        .no-results {{
            padding: 60px 20px;
            text-align: center;
            color: #999;
        }}

        .no-results-icon {{
            font-size: 48px;
            margin-bottom: 15px;
        }}

        footer {{
            text-align: center;
            padding: 30px;
            color: #999;
            font-size: 13px;
        }}

        @media (max-width: 768px) {{
            .controls-row {{
                flex-direction: column;
            }}

            .rule-header {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .rule-meta {{
                margin-top: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="subtitle">
                Generated from {source_file} • {timestamp}
            </div>
        </header>

        <div class="controls">
            <div class="controls-row">
                <div class="control-group">
                    <label for="search">Search</label>
                    <input type="text" id="search" placeholder="Search rules by ID, description, or pattern...">
                </div>
                <div class="control-group">
                    <label for="category-filter">Category</label>
                    <select id="category-filter">
                        <option value="">All Categories</option>
                        <option value="mandatory">Mandatory</option>
                        <option value="potential">Potential</option>
                        <option value="optional">Optional</option>
                    </select>
                </div>
                <div class="control-group">
                    <label for="effort-filter">Effort</label>
                    <select id="effort-filter">
                        <option value="">All Effort Levels</option>
                        <option value="1">1 (Trivial)</option>
                        <option value="3">3 (Low)</option>
                        <option value="5">5 (Medium)</option>
                        <option value="7">7 (High)</option>
                        <option value="10">10 (Expert)</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="stats">
            <div class="stats-grid" id="stats">
                <!-- Stats populated by JavaScript -->
            </div>
        </div>

        <div class="rules-container" id="rules-container">
            <!-- Rules populated by JavaScript -->
        </div>

        <footer>
            <a href="https://konveyor.io" target="_blank" style="color: #0066cc;">Konveyor</a> •
            <a href="https://github.com/konveyor/analyzer-lsp" target="_blank" style="color: #0066cc;">Analyzer LSP</a> •
            Open Source Application Modernization
        </footer>
    </div>

    <script>
        const rulesData = {rules_json};

        // Calculate statistics
        function calculateStats(rules) {{
            const stats = {{
                total: rules.length,
                mandatory: rules.filter(r => r.category === 'mandatory').length,
                potential: rules.filter(r => r.category === 'potential').length,
                optional: rules.filter(r => r.category === 'optional').length,
                effortCounts: {{}}
            }};

            rules.forEach(rule => {{
                const effort = rule.effort;
                stats.effortCounts[effort] = (stats.effortCounts[effort] || 0) + 1;
            }});

            return stats;
        }}

        // Render statistics
        function renderStats(stats) {{
            const statsContainer = document.getElementById('stats');
            statsContainer.innerHTML = `
                <div class="stat-card">
                    <div class="stat-label">Total Rules</div>
                    <div class="stat-value">${{stats.total}}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Mandatory</div>
                    <div class="stat-value">${{stats.mandatory}}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Potential</div>
                    <div class="stat-value">${{stats.potential}}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Optional</div>
                    <div class="stat-value">${{stats.optional}}</div>
                </div>
            `;
        }}

        // Render a single rule
        function renderRule(rule) {{
            const whenYaml = formatWhen(rule.when);
            const links = rule.links || [];
            const labels = rule.labels || [];

            return `
                <div class="rule" data-rule-id="${{rule.ruleID}}" data-category="${{rule.category}}" data-effort="${{rule.effort}}">
                    <div class="rule-header" onclick="toggleRule(this)">
                        <span class="expand-icon">▶</span>
                        <div class="rule-title">
                            <div class="rule-id">${{rule.ruleID}}</div>
                            <div class="rule-description">${{escapeHtml(rule.description)}}</div>
                        </div>
                        <div class="rule-meta">
                            <span class="badge badge-${{rule.category}}">${{rule.category}}</span>
                            <span class="effort-badge">Effort: ${{rule.effort}}</span>
                        </div>
                    </div>
                    <div class="rule-details">
                        <div class="detail-section">
                            <div class="detail-label">Message</div>
                            <div class="detail-content">${{formatMessage(rule.message)}}</div>
                        </div>

                        <div class="detail-section">
                            <div class="detail-label">When Condition</div>
                            <div class="code-block">${{whenYaml}}</div>
                        </div>

                        ${{labels.length > 0 ? `
                        <div class="detail-section">
                            <div class="detail-label">Labels</div>
                            <div class="labels-list">
                                ${{labels.map(l => `<span class="label-tag">${{l}}</span>`).join('')}}
                            </div>
                        </div>
                        ` : ''}}

                        ${{links.length > 0 ? `
                        <div class="detail-section">
                            <div class="detail-label">Documentation Links</div>
                            <ul class="links-list">
                                ${{links.map(l => `<li><a href="${{l.url}}" target="_blank">📄 ${{l.title}}</a></li>`).join('')}}
                            </ul>
                        </div>
                        ` : ''}}
                    </div>
                </div>
            `;
        }}

        // Format when condition as YAML
        function formatWhen(when) {{
            return escapeHtml(JSON.stringify(when, null, 2))
                .replace(/"([^"]+)":/g, '<span class="yaml-key">"$1"</span>:')
                .replace(/: "([^"]+)"/g, ': <span class="yaml-value">"$1"</span>');
        }}

        // Format message with code blocks
        function formatMessage(message) {{
            message = escapeHtml(message);
            // Convert code blocks (between ```)
            message = message.replace(/```([\\s\\S]*?)```/g, '<pre class="code-block">$1</pre>');
            // Convert inline code (between `)
            message = message.replace(/`([^`]+)`/g, '<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 13px;">$1</code>');
            // Convert newlines to <br>
            message = message.replace(/\\n/g, '<br>');
            return message;
        }}

        // Escape HTML
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        // Toggle rule expansion
        function toggleRule(header) {{
            const rule = header.parentElement;
            rule.classList.toggle('expanded');
        }}

        // Filter rules
        function filterRules() {{
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const categoryFilter = document.getElementById('category-filter').value;
            const effortFilter = document.getElementById('effort-filter').value;

            const rules = document.querySelectorAll('.rule');
            let visibleCount = 0;

            rules.forEach(rule => {{
                const ruleText = rule.textContent.toLowerCase();
                const category = rule.dataset.category;
                const effort = rule.dataset.effort;

                const matchesSearch = !searchTerm || ruleText.includes(searchTerm);
                const matchesCategory = !categoryFilter || category === categoryFilter;
                const matchesEffort = !effortFilter || effort === effortFilter;

                if (matchesSearch && matchesCategory && matchesEffort) {{
                    rule.style.display = '';
                    visibleCount++;
                }} else {{
                    rule.style.display = 'none';
                }}
            }});

            // Show/hide no results message
            const container = document.getElementById('rules-container');
            const existing = container.querySelector('.no-results');
            if (existing) existing.remove();

            if (visibleCount === 0) {{
                container.innerHTML += `
                    <div class="no-results">
                        <div class="no-results-icon">🔍</div>
                        <div>No rules match your filters</div>
                    </div>
                `;
            }}
        }}

        // Initialize
        function init() {{
            const stats = calculateStats(rulesData);
            renderStats(stats);

            const container = document.getElementById('rules-container');
            container.innerHTML = rulesData.map(renderRule).join('');

            // Add event listeners
            document.getElementById('search').addEventListener('input', filterRules);
            document.getElementById('category-filter').addEventListener('change', filterRules);
            document.getElementById('effort-filter').addEventListener('change', filterRules);
        }}

        init();
    </script>
</body>
</html>
"""


def load_rules(rule_file: Path) -> list:
    """Load rules from YAML file."""
    with open(rule_file, 'r') as f:
        content = yaml.safe_load(f)
        if isinstance(content, list):
            return content
        else:
            return [content]


def generate_html(rules: list, title: str, source_file: str) -> str:
    """Generate HTML from rules."""
    rules_json = json.dumps(rules)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = HTML_TEMPLATE.format(
        title=title,
        source_file=source_file,
        timestamp=timestamp,
        rules_json=rules_json
    )

    return html


def main():
    parser = argparse.ArgumentParser(
        description='Generate interactive HTML viewer for Konveyor analyzer rules',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate viewer for Spring Boot 4.0 rules
  python scripts/generate_rule_viewer.py \\
    --rules examples/output/spring-boot-4.0/migration-rules.yaml \\
    --output examples/output/spring-boot-4.0/viewer.html \\
    --title "Spring Boot 3.5 → 4.0 Migration Rules"

  # Open in browser automatically
  python scripts/generate_rule_viewer.py \\
    --rules examples/output/jdk21/applet-removal.yaml \\
    --output viewer.html \\
    --open
        """
    )

    parser.add_argument(
        '--rules',
        required=True,
        help='Path to rule YAML file'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output HTML file path'
    )
    parser.add_argument(
        '--title',
        help='Title for the viewer (auto-generated if not provided)'
    )
    parser.add_argument(
        '--open',
        action='store_true',
        help='Open the generated HTML in browser'
    )

    args = parser.parse_args()

    # Validate input
    rule_file = Path(args.rules)
    if not rule_file.exists():
        print(f"Error: Rule file not found: {rule_file}", file=sys.stderr)
        return 1

    # Load rules
    print(f"Loading rules from {rule_file}...")
    rules = load_rules(rule_file)
    print(f"  ✓ Loaded {len(rules)} rules")

    # Generate title
    if args.title:
        title = args.title
    else:
        # Extract from filename
        title = rule_file.stem.replace('-', ' ').replace('_', ' ').title()

    # Generate HTML
    print(f"Generating HTML viewer...")
    html = generate_html(rules, title, rule_file.name)

    # Write output
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  ✓ Generated {output_file}")
    print(f"\n✓ Rule viewer created successfully!")
    print(f"\nTo view:")
    print(f"  open {output_file}")

    # Open in browser if requested
    if args.open:
        import webbrowser
        webbrowser.open(f"file://{output_file.absolute()}")
        print(f"\n✓ Opened in browser")

    return 0


if __name__ == '__main__':
    sys.exit(main())
