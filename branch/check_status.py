import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import requests


def get_inputs() -> tuple[str, ...]:
    # Get the inputs from the GitHub Actions environment or local .env
    import dotenv

    dotenv.load_dotenv()
    defaults = defaultdict(str)
    defaults["INPUT_VALID_BRANCH_NAMES"] = "task|test|bugfix|feature|hotfix|epic"
    defaults["INPUT_PR_TITLE"] = "None"
    env_keys = (
        "INPUT_BRANCH_TO_CHECK",
        "INPUT_VALID_BRANCH_NAMES",
        "INPUT_JIRA_USERNAME",
        "INPUT_JIRA_PASSWORD",
        "INPUT_PR_TITLE",
    )

    values = {key: os.environ.get(key, defaults[key]) for key in env_keys}
    for key in env_keys:
        if not values[key]:
            msg = f"Missing input '{key}'"
            raise RuntimeError(msg)
    return tuple(values.values())


def extract_issue_key_branch(branch_to_check: str, valid_branch_names: str):
    """
    :param branch_to_check: `refs/heads/` is prefixed if the action is triggered by a branch.
    :param valid_branch_names: a partial regex string to match the branch name
    :return: the extracted issue key
    """
    match = re.match(
        rf"^(refs/heads/)?({valid_branch_names})/([a-zA-Z0-9]+-[0-9]+)",
        branch_to_check,
    )
    if not match:
        msg = f"Could not extract issue key from branch name '{branch_to_check}'"
        raise RuntimeError(msg)
    return match.group(3)


def extract_issue_key_pr_title(pr_title: str):
    """
    :param pr_title: The full PR title string from GitHub
    :return: the extracted issue key
    """
    match = re.match(
        r"^([a-zA-Z0-9]+-[0-9]+)\s?[|:]\s\w.*$",
        pr_title,
    )
    if not match:
        msg = f"Could not extract issue key from PR title '{pr_title}'\nThe expected format is 'PROJ-123 | Title'"
        raise RuntimeError(msg)
    return match.group(1)


def extract_project_key(issue_key: str) -> str:
    return issue_key.split("-")[0]


def check_project_access(project_key: str, jira_username: str, jira_password: str):
    url = f"https://ovearup.atlassian.net/rest/api/3/project/{project_key}"
    return jira_request(jira_password, jira_username, url)


def query_jira_api(issue_key: str, jira_username: str, jira_password: str) -> dict:
    url = f"https://ovearup.atlassian.net/rest/api/3/issue/{issue_key}"
    return jira_request(jira_password, jira_username, url)


def jira_request(jira_password, jira_username, url):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    response = requests.get(
        url,
        headers=headers,
        auth=(jira_username, jira_password),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def check_status_category(response_json: dict) -> dict:
    try:
        status_cat = response_json["fields"]["status"]["statusCategory"]
        status_cat_id = status_cat["id"]
        status_cat_name = status_cat["name"]
    except KeyError as e:
        msg = f"Status category is missing from JSON response\n{response_json}"
        raise RuntimeError(msg) from e
    in_progress = 4
    if status_cat_id != in_progress:
        msg = f"Status category is not 'In Progress', but {status_cat_name}"
        raise RuntimeError(
            msg,
        )
    return status_cat


def check_branch_name(branch_name: str, valid_branch_names: str) -> bool:
    return bool(re.match(rf"^(refs/heads/)?({valid_branch_names})/([a-zA-Z0-9]+-[0-9]+)", branch_name))


def check_pr_title(pr_title: str, issue_key: str):
    if pr_title == "None":
        return
    title_issue_key = extract_issue_key_pr_title(pr_title)
    if issue_key != title_issue_key:
        msg = f"JIRA key '{issue_key}' extracted from branch does not match the one extracted from the PR title '{title_issue_key}'"
        raise RuntimeError(msg)


def main():
    try:
        branch_to_check, valid_branch_names, jira_username, jira_password, pr_title = get_inputs()
    except RuntimeError as e:
        print(f"::error::Missing inputs. Checks Action setup.\n{e}")  # noqa: T201
        sys.exit(1)
    if not check_branch_name(branch_to_check, valid_branch_names):
        print(f"::error::Branch name '{branch_to_check}' does not match the valid branch names ({valid_branch_names}).")  # noqa: T201
        sys.exit(1)
    try:
        issue_key = extract_issue_key_branch(branch_to_check, valid_branch_names)
    except RuntimeError as e:
        print(f"::error::Could not extract issue key from branch name. Check branch name.\n{e}")  # noqa: T201
        sys.exit(1)
    try:
        check_pr_title(pr_title, issue_key)
    except RuntimeError as e:
        print(f"::error::JIRA key in PR title is incorrect.\n{e}")  # noqa: T201
        sys.exit(1)
    project_key = extract_project_key(issue_key)
    try:
        check_project_access(project_key, jira_username, jira_password)
    except requests.exceptions.HTTPError as e:
        print(f"::error::Could not access project {project_key} in Jira. Check credentials and project access.\n{e}")  # noqa: T201
        sys.exit(1)
    try:
        response = query_jira_api(issue_key, jira_username, jira_password)
    except requests.exceptions.HTTPError as e:
        print(f"::error::Could not access issue {issue_key} in Jira. Does the issue really exist?.\n{e}")  # noqa: T201
        sys.exit(1)
    try:
        cat = check_status_category(response)
    except RuntimeError as e:
        print(f"::error::Issue {issue_key} is not in progress. Check issue status.\n{e}")  # noqa: T201
        sys.exit(1)
    with Path(os.environ.get("GITHUB_OUTPUT")).open(mode="a") as out_file:
        out_file.write(f"jira_issue_key={issue_key}\n")
        cat_repr = json.dumps(cat)
        out_file.write(f"jira_issue_category={cat_repr}\n")
        out_file.write(f"jira_project_key={project_key}\n")


if __name__ == "__main__":
    main()
