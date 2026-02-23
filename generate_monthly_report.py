#!/usr/bin/env python3
"""
Generate monthly work log by combining:
1. Weekly GitHub contribution reports
2. Obsidian completed tasks
3. Auto-categorization by product area
4. Duplicate detection
5. Time allocation percentage calculation
"""

import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import argparse

# Paths
REPO_ROOT = Path(__file__).parent
OBSIDIAN_VAULT = Path.home() / "Documents" / "Obsidian Vault"
OBSIDIAN_COMPLETED = OBSIDIAN_VAULT / "Things-to-do" / "Things-I-did" / "2026"
DESKTOP_FINANCE = Path.home() / "Desktop" / "finance_percentages"
WEEKLY_REPORTS = REPO_ROOT / "reports"


def load_categories():
    """Load repository categories from YAML config."""
    with open(REPO_ROOT / "repo-categories.yaml") as f:
        config = yaml.safe_load(f)

    # Build reverse mapping: repo -> category
    repo_to_category = {}
    category_names = {}
    for cat_key, cat_data in config["categories"].items():
        category_names[cat_key] = cat_data["name"]
        for repo in cat_data["repos"]:
            repo_to_category[repo] = cat_key

    return repo_to_category, category_names, config.get("default_category", "other")


def extract_pr_numbers(text):
    """Extract PR/issue numbers from text (e.g., #12345, PR #123)."""
    return set(re.findall(r'#(\d+)', text))


def parse_weekly_reports(month, year):
    """Parse all weekly GitHub reports for a given month."""
    items_by_category = defaultdict(list)
    all_pr_numbers = set()

    # Get all reports for the month
    month_num = datetime.strptime(month, "%B").month
    month_str = f"{year}-{month_num:02d}"

    report_files = sorted(WEEKLY_REPORTS.glob(f"report-{month_str}-*.md"))

    for report_file in report_files:
        with open(report_file) as f:
            content = f.read()

        # Extract date from filename
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', report_file.name)
        if not date_match:
            continue
        report_date = date_match.group(1)

        # Parse each section by product
        sections = re.split(r'^## 📘 (.+)$', content, flags=re.MULTILINE)

        for i in range(1, len(sections), 2):
            product_name = sections[i].strip()
            section_content = sections[i + 1] if i + 1 < len(sections) else ""

            # Extract PRs, issues, reviews
            pr_matches = re.findall(r'- \[#(\d+)\] (.+)', section_content)

            for pr_num, pr_title in pr_matches:
                all_pr_numbers.add(pr_num)
                items_by_category[product_name].append({
                    'type': 'github',
                    'text': f"[#{pr_num}] {pr_title}",
                    'pr_numbers': {pr_num},
                    'date': report_date
                })

    return items_by_category, all_pr_numbers


def parse_obsidian_tasks(month, year):
    """Parse Obsidian completed tasks for a given month."""
    items_by_date = defaultdict(list)

    month_file = OBSIDIAN_COMPLETED / f"{month}.md"
    if not month_file.exists():
        print(f"⚠️  Warning: Obsidian file not found: {month_file}")
        return items_by_date

    with open(month_file) as f:
        content = f.read()

    # Split by date headers (e.g., "Feb. 23")
    date_sections = re.split(r'^([A-Za-z]+\.\s+\d+)$', content, flags=re.MULTILINE)

    for i in range(1, len(date_sections), 2):
        date_str = date_sections[i].strip()
        tasks = date_sections[i + 1] if i + 1 < len(date_sections) else ""

        # Parse individual task lines
        task_lines = [line.strip() for line in tasks.split('\n') if line.strip() and not line.strip().startswith('#')]

        for task in task_lines:
            if task:
                items_by_date[date_str].append({
                    'type': 'obsidian',
                    'text': task,
                    'pr_numbers': extract_pr_numbers(task)
                })

    return items_by_date


def categorize_obsidian_task(task_text, repo_to_category):
    """Attempt to categorize an Obsidian task based on keywords and repo mentions."""
    text_lower = task_text.lower()

    # Check for repo names in task
    for repo, category in repo_to_category.items():
        repo_name = repo.split('/')[-1].lower()
        if repo_name in text_lower or repo.lower() in text_lower:
            return category

    # Keyword-based categorization
    if any(kw in text_lower for kw in ['workbench', 'rstudio-pro', 'ide', 'positron']):
        return 'wb-ide'
    elif any(kw in text_lower for kw in ['connect', 'rsconnect']):
        return 'connect'
    elif any(kw in text_lower for kw in ['package manager', 'ppm']):
        return 'ppm'
    elif any(kw in text_lower for kw in ['chronicle']):
        return 'chronicle'
    elif any(kw in text_lower for kw in ['snowflake', 'partnership', 'data-sources', 'data sources', 'pro drivers']):
        return 'platform'
    elif any(kw in text_lower for kw in ['docs.rstudio.com', 'troubleshooting', 'doc-reviewer', 'style guide', 'meeting', 'training', 'okr']):
        return 'other'

    # Default
    return 'other'


def deduplicate_items(github_items, obsidian_items_by_date, repo_to_category):
    """Combine GitHub and Obsidian items, removing duplicates."""
    # Build a set of all GitHub PR numbers
    github_pr_numbers = set()
    for items in github_items.values():
        for item in items:
            github_pr_numbers.update(item['pr_numbers'])

    # Categorize Obsidian tasks and filter out duplicates
    categorized_obsidian = defaultdict(list)

    for date_str, tasks in obsidian_items_by_date.items():
        for task in tasks:
            # Skip if this task mentions a PR already in GitHub data
            if task['pr_numbers'] and task['pr_numbers'].intersection(github_pr_numbers):
                continue  # Duplicate

            # Categorize the task
            category = categorize_obsidian_task(task['text'], repo_to_category)
            categorized_obsidian[category].append({
                **task,
                'date': date_str
            })

    return categorized_obsidian


def calculate_percentages(all_items, category_names):
    """Calculate time allocation percentages by category."""
    # Simple counting approach: count number of items per category
    category_counts = defaultdict(int)

    for category, items in all_items.items():
        category_counts[category] = len(items)

    total = sum(category_counts.values())
    if total == 0:
        return {cat: 0 for cat in category_names.keys()}

    percentages = {}
    for cat_key in category_names.keys():
        count = category_counts.get(cat_key, 0)
        percentages[cat_key] = round((count / total) * 100)

    # Adjust to ensure sum is 100%
    current_sum = sum(percentages.values())
    if current_sum != 100 and percentages:
        # Add difference to largest category
        max_cat = max(percentages, key=percentages.get)
        percentages[max_cat] += (100 - current_sum)

    return percentages


def generate_monthly_report(month, year):
    """Generate the complete monthly work log."""
    print(f"🔍 Generating report for {month} {year}...")

    # Load configuration
    repo_to_category, category_names, default_category = load_categories()

    # Parse data sources
    print("📊 Parsing weekly GitHub reports...")
    github_items, github_pr_numbers = parse_weekly_reports(month, year)

    print("📝 Parsing Obsidian completed tasks...")
    obsidian_items_by_date = parse_obsidian_tasks(month, year)

    print("🔄 Deduplicating and categorizing...")
    obsidian_categorized = deduplicate_items(github_items, obsidian_items_by_date, repo_to_category)

    # Combine GitHub and Obsidian items by category
    all_items = defaultdict(list)

    # Add GitHub items (already categorized by product name)
    for product_name, items in github_items.items():
        # Map product name back to category key
        category = None
        for cat_key, cat_name in category_names.items():
            if cat_name == product_name:
                category = cat_key
                break
        if category:
            all_items[category].extend(items)

    # Add Obsidian items
    for category, items in obsidian_categorized.items():
        all_items[category].extend(items)

    # Calculate percentages
    percentages = calculate_percentages(all_items, category_names)

    # Generate markdown report
    month_num = datetime.strptime(month, "%B").month
    report_lines = [
        f"# {month} {year} Work Log",
        "",
        "## Time Allocation by Product/Area",
        "",
        "| Month   | WB/IDE | Connect | PPM | Chronicle | Platform | Other |",
        "|---------|--------|---------|-----|-----------|----------|-------|",
        f"| {month} | {percentages.get('wb-ide', 0)}%     | {percentages.get('connect', 0)}%      | {percentages.get('ppm', 0)}%  | {percentages.get('chronicle', 0)}%        | {percentages.get('platform', 0)}%       | {percentages.get('other', 0)}%    |",
        "",
        '**Note:** "Platform" includes Snowflake/Partnerships work and Data sources. "Other" includes Style Guide, Troubleshooting, docs.posit.co, meetings, training, and administrative tasks.',
        "",
        "---",
        ""
    ]

    # Group all items by date for chronological display
    items_by_date = defaultdict(lambda: defaultdict(list))

    for category, items in all_items.items():
        cat_name = category_names.get(category, category)
        for item in items:
            date_key = item['date']
            items_by_date[date_key][cat_name].append(item['text'])

    # Sort dates in reverse chronological order
    for date_str in sorted(items_by_date.keys(), reverse=True):
        report_lines.append(f"## {date_str}")
        report_lines.append("")

        categories = items_by_date[date_str]
        for cat_name in sorted(categories.keys()):
            tasks = categories[cat_name]
            report_lines.append(f"**{cat_name}**")
            for task in tasks:
                report_lines.append(f"- {task}")
            report_lines.append("")

        report_lines.append("")

    # Write report
    output_dir = DESKTOP_FINANCE / month
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{month.lower()}-work-log.md"

    with open(output_file, 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"✅ Report generated: {output_file}")
    print(f"\n📈 Time Allocation Summary:")
    for cat_key, cat_name in category_names.items():
        print(f"   {cat_name}: {percentages.get(cat_key, 0)}%")


def main():
    parser = argparse.ArgumentParser(description='Generate monthly work log')
    parser.add_argument('month', help='Month name (e.g., February)')
    parser.add_argument('year', type=int, help='Year (e.g., 2026)')

    args = parser.parse_args()
    generate_monthly_report(args.month, args.year)


if __name__ == '__main__':
    main()
