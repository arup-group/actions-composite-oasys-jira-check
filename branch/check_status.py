import os
import re
import requests
import json


def get_inputs():
    # Get the inputs from the GitHub Actions environment or local .env
    import dotenv

    dotenv.load_dotenv()
    branch_to_check = os.getenv("INPUT_BRANCH_TO_CHECK")
    valid_branch_names = os.getenv(
        "INPUT_VALID_BRANCH_NAMES", "task|test|bugfix|feature|hotfix|epic"
    )
    jira_username = os.getenv("INPUT_JIRA_USERNAME")
    jira_password = os.getenv("INPUT_JIRA_PASSWORD")
    return branch_to_check, valid_branch_names, jira_username, jira_password


def check_branch_format(branch_to_check, valid_branch_names):
    # Check the branch format
    match = re.match(
        rf"^refs/heads/({valid_branch_names})/([a-zA-Z0-9]+-[0-9]+)", branch_to_check
    )
    if not match:
        raise RuntimeError("Branch format is incorrect")
    return match.group(2)


def query_jira_api(issue_key, jira_username, jira_password):
    # Query the Jira API
    response = requests.get(
        f"https://ovearup.atlassian.net/rest/api/3/issue/{issue_key}",
        auth=(jira_username, jira_password),
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    return response


def check_status_category(response):
    # Check the status category
    issue_status_cat = json.loads(response.text)["fields"]["status"]["statusCategory"][
        "id"
    ]
    if issue_status_cat != "4":
        sys.exit('Status category is not "In Progress"')


def main():
    branch_to_check, valid_branch_names, jira_username, jira_password = get_inputs()
    issue_key = check_branch_format(branch_to_check, valid_branch_names)
    response = query_jira_api(issue_key, jira_username, jira_password)
    check_status_category(response)


if __name__ == "__main__":
    main()
