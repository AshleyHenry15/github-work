# How to use this action

This GitHub Action scans the specified repositories for your contributions every seven days (it runs on Friday afternoon). The contributions are added to a file within the `reports` directory.
The action triggers an update to the README file with a link to each file within the `report` directory and is published as a GitHub pages site. The `Generate GitHub Contribution Report` runs automatically when a change merges into `main` but you can also manually run the workflow against `main` or the branch of your choosing.
## Prework

Before you begin:

- Your repo must be public (GitHub pages is only available for public repositories unless you pay an additional fee).
- Configure tokens:
    - You need to add a **Tokens (classic)** personal access token named "WEEKLY_TOKEN".
      - The token needs **repo** and **workflow** scopes. The choice to use Token (classic) is intentional since many repositories are private and require SSO (Okta) authentication.
      - You should copy the token and add it to an `.env` file within the `github-work` directory (locally) for potential troubleshooting authentication issues.
    - Now, select the **Configure SSO** dropdown menu to configure SSO organizations for your token. You must authorize the token for all organizations that the weekly report workflow checks.
  
- Configure pages:
    - Navigate to **Settings** > **Pages** and in **Branches**, select `main` from the **None** dropdown and click **Save**.
    - Add a custom domain.

## Setup

In the `README` file, edit the title and remove existing file entries.

In the `.github/workflows/contribution-report.yml` file:

- Update the `REPOS` entry with the specific repos for your workflow to scan for your contributions.
- Replace AshleyHenry15 with your GitHub username:

  ```
   user = "AshleyHenry15"
  ```


## Common issues and troubleshooting

Sometimes, the workflow fails, and most of the time it is due to SSO authentication issues.

To test your token, replace `YOUR_REAL_TOKEN_VALUE` and then run:

```
curl -s -H "Authorization: token <YOUR_REAL_TOKEN_VALUE>" \
  https://api.github.com/orgs/rstudio/repos | jq '.[].full_name'
```

If authorized and working, it returns the list of repos.

To reauthenticate with GitHub, from the terminal run `gh auth refresh` and follow the prompts.

Once it's finished, rerun the Generate GitHub Contribution Report workflow.
