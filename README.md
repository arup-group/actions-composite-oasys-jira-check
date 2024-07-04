# Usage

In both cases you will need the JIRA_PASSWORD secret to be set in the repository secrets. This is the password for the automation account.

## Pull request workflow

To use this action from a PR workflow, add the following to your workflow file:

```yml
on:
  pull_request:

jobs:
  check-jira:
    runs-on: ubuntu-22.04

    steps:
      - uses: arup-group/actions-composite-oasys-jira-check/branch@main
        with:
          valid-branch-names: task|test|bugfix|feature|hotfix|epic
          jira-username: automation@arup.com
          jira-password: ${{ secrets.JIRA_PASSWORD }}
          branch_to_check: refs/heads/${{ github.event.pull_request.head.ref }}
          # Optional. If not provided, pr title is not checked for JIRA key
          # If provided, checks PR title is formatted as `JIRA-1234 | My PR title`
          pr_title: ${{ github.event.pull_request.title }}
```

## Push to branch workflow

If you want to add this action to a workflow that runs on push to a branch, you can use the following:

```yml
on:
  push:

jobs:
  check-jira:
    runs-on: ubuntu-22.04

    steps:
      - uses: arup-group/actions-composite-oasys-jira-check/branch@main
        with:
          valid-branch-names: task|test|bugfix|feature|hotfix|epic
          jira-username: automation@arup.com
          jira-password: ${{ secrets.JIRA_PASSWORD }}
```


## Development

For local debug and development, you can run the python scripts directly.
Copy `.env.example` to `.env` and fill in the values.


### Note:

This repo is public so other public Arup projects (GSA-Grasshopper) can use it.
