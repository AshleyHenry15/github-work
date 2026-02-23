# Setup Guide for GitHub Work Tracking

This repository automatically tracks your GitHub contributions and combines them with your Obsidian tasks to generate monthly work logs.

## Initial Setup

### 1. GitHub Token Configuration

Create a GitHub Personal Access Token with the following scopes:
- `repo` (full control of private repositories)
- `workflow` (update GitHub Action workflows)

**Steps:**
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with the scopes above
3. Copy the token
4. Go to your forked repository → Settings → Secrets and variables → Actions
5. Create a new repository secret named `WEEKLY_TOKEN` and paste your token
6. Configure SSO for all organizations you want to track (rstudio, posit-dev, etc.)

### 2. Test Your Token

To verify your token has the right permissions:

```bash
curl -s -H "Authorization: token YOUR_TOKEN_HERE" \
  https://api.github.com/orgs/rstudio/repos | jq '.[].full_name'
```

If this returns a list of repos, your token is working correctly.

### 3. Customize Repository Categories

Edit `repo-categories.yaml` to add or remove repositories you want to track. The file maps repos to product areas:

```yaml
categories:
  wb-ide:
    name: "WB/IDE"
    repos:
      - "rstudio/rstudio-pro"
      - "rstudio/rstudio"
```

### 4. Enable GitHub Pages (Optional)

If you want to publish your reports as a website:
1. Go to Settings → Pages
2. Select `main` branch as source
3. Click Save

## Usage

### Weekly Reports

Weekly reports are generated automatically every **Friday at 3pm EST** via GitHub Actions.

You can also trigger a manual run:
1. Go to Actions tab
2. Select "Generate GitHub Contribution Report"
3. Click "Run workflow"

Reports are saved to `reports/report-YYYY-MM-DD.md`

### Monthly Reports

At the end of each month, generate a comprehensive work log that combines GitHub activity with your Obsidian tasks:

```bash
cd /Users/sarahsdao/Documents/GitHub/Repositories/github-work
python3 generate_monthly_report.py February 2026
```

This will:
1. Parse all weekly GitHub reports for the month
2. Read your Obsidian completed tasks from `~/Documents/Obsidian Vault/Things-to-do/Things-I-did/2026/[Month].md`
3. Categorize everything by product area (WB/IDE, Connect, PPM, Chronicle, Platform, Other)
4. Remove duplicates (if a PR appears in both sources)
5. Calculate time allocation percentages
6. Generate a monthly work log at `~/Desktop/finance_percentages/[Month]/[month]-work-log.md`

### Obsidian Integration

The script expects your Obsidian completed tasks to be in this structure:

```
~/Documents/Obsidian Vault/
  Things-to-do/
    Things-I-did/
      2026/
        January.md
        February.md
        ...
```

Each file should have date headers like:
```markdown
Feb. 23
Task description here
Review PR https://github.com/...

Feb. 22
Another task...
```

## Categorization Logic

### GitHub Contributions
Automatically categorized based on the repository (from `repo-categories.yaml`).

### Obsidian Tasks
Categorized using:
1. **Repo name detection** - If a task mentions a repo, it's categorized by that repo
2. **Keyword matching** - Tasks are scanned for product-specific keywords:
   - **WB/IDE**: workbench, rstudio-pro, ide, positron
   - **Connect**: connect, rsconnect
   - **PPM**: package manager, ppm
   - **Chronicle**: chronicle
   - **Platform**: snowflake, partnership, data-sources, pro drivers
   - **Other**: docs.rstudio.com, troubleshooting, doc-reviewer, style guide, meeting, training
3. **Default**: If no match, categorized as "Other"

### Duplicate Detection

If a task in Obsidian mentions a PR number (e.g., "#12345") that also appears in the GitHub weekly reports, only the GitHub entry is kept to avoid double-counting.

## Time Allocation Percentages

Percentages are calculated by:
1. Counting total number of work items (GitHub + Obsidian)
2. Counting items per category
3. Computing percentage: `(category_items / total_items) * 100`

This gives a rough approximation of time spent in each area.

## Troubleshooting

### Workflow Fails with Authentication Error

Your token may need SSO reauthorization:
1. Go to GitHub Settings → Personal access tokens
2. Find your token and click "Configure SSO"
3. Authorize for each organization
4. Re-run the workflow

### Monthly Report Missing Obsidian Tasks

Check that:
- The Obsidian file exists at the expected path
- The file uses date headers in format: "Feb. 23" or "February 23"
- Tasks are under the date headers

### Percentages Don't Add Up to 100%

This is automatically corrected by the script - any rounding difference is added to the largest category.

## Files Overview

- **`.github/workflows/contribution-report.yml`** - GitHub Actions workflow for weekly reports
- **`repo-categories.yaml`** - Repository to product area mapping
- **`generate_monthly_report.py`** - Script to generate monthly work logs
- **`reports/`** - Directory containing weekly GitHub contribution reports
- **`SETUP.md`** - This file

## Support

For issues or questions, refer to the original workflow documentation in `HOWTO.md`.
