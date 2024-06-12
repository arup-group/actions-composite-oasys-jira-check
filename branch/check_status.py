import os
import re
from collections import defaultdict

import requests


def get_inputs() -> tuple[str, ...]:
    # Get the inputs from the GitHub Actions environment or local .env
    import dotenv

    dotenv.load_dotenv()
    defaults = defaultdict(str)
    defaults["INPUT_VALID_BRANCH_NAMES"] = "task|test|bugfix|feature|hotfix|epic"
    env_keys = ("INPUT_BRANCH_TO_CHECK", "INPUT_VALID_BRANCH_NAMES", "INPUT_JIRA_USERNAME", "INPUT_JIRA_PASSWORD")

    values = {key: os.environ.get(key, defaults[key]) for key in env_keys}
    for key in env_keys:
        if not values[key]:
            msg = f"Missing input '{key}'"
            raise RuntimeError(msg)
    return tuple(values.values())


def extract_issue_key(branch_to_check: str, valid_branch_names: str):
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


def query_jira_api(issue_key: str, jira_username: str, jira_password: str) -> dict:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    response = requests.get(
        f"https://ovearup.atlassian.net/rest/api/3/issue/{issue_key}",
        headers=headers,
        auth=(jira_username, jira_password),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def check_status_category(response_json: dict):
    try:
        issue_status_cat = response_json["fields"]["status"]["statusCategory"]["id"]
    except KeyError as e:
        msg = f"Status category is missing from JSON response\n{response_json}"
        raise RuntimeError(msg) from e
    in_progress = 4
    if issue_status_cat != in_progress:
        msg = f"Status category is not 'In Progress', but {issue_status_cat}"
        raise RuntimeError(
            msg,
        )


def main():
    branch_to_check, valid_branch_names, jira_username, jira_password = get_inputs()
    issue_key = extract_issue_key(branch_to_check, valid_branch_names)
    response = query_jira_api(issue_key, jira_username, jira_password)
    check_status_category(response)


if __name__ == "__main__":
    main()
