import json

import pytest
import requests_mock

from branch import check_status


def test_status_category_in_progress():
    with requests_mock.Mocker() as m:
        issue_key = "TEST-1"
        m.get(
            f"https://ovearup.atlassian.net/rest/api/3/issue/{issue_key}",
            text=json.dumps({"fields": {"status": {"statusCategory": {"id": 4}}}}),
        )
        response = check_status.query_jira_api(issue_key, "username", "password")
        check_status.check_status_category(response)


def test_status_category_not_in_progress():
    with requests_mock.Mocker() as m:
        issue_key = "TEST-1"
        m.get(
            f"https://ovearup.atlassian.net/rest/api/3/issue/{issue_key}",
            text=json.dumps({"fields": {"status": {"statusCategory": {"id": 5}}}}),
        )
        response = check_status.query_jira_api(issue_key, "username", "password")
        with pytest.raises(RuntimeError):
            check_status.check_status_category(response)


def test_status_category_missing():
    with requests_mock.Mocker() as m:
        issue_key = "TEST-1"
        m.get(
            f"https://ovearup.atlassian.net/rest/api/3/issue/{issue_key}",
            text=json.dumps({"fields": {"status": {"statusCategory": {}}}}),
        )
        response = check_status.query_jira_api(issue_key, "username", "password")
        with pytest.raises(RuntimeError):
            check_status.check_status_category(response)


def test_status_category_garbled_response():
    with requests_mock.Mocker() as m:
        issue_key = "TEST-1"
        m.get(
            f"https://ovearup.atlassian.net/rest/api/3/issue/{issue_key}",
            text=json.dumps({"nothing": {"Status": {"foo": {}}}}),
        )
        response = check_status.query_jira_api(issue_key, "username", "password")
        with pytest.raises(RuntimeError):
            check_status.check_status_category(response)


def test_extract_issue_key_with_valid_input():
    branch_to_check = "refs/heads/feature/TEST-123"
    valid_branch_names = "task|test|bugfix|feature|hotfix|epic"
    assert check_status.extract_issue_key(branch_to_check, valid_branch_names) == "TEST-123"


def test_extract_issue_key_without_refs_heads_prefix():
    branch_to_check = "feature/TEST-123"
    valid_branch_names = "task|test|bugfix|feature|hotfix|epic"
    assert check_status.extract_issue_key(branch_to_check, valid_branch_names) == "TEST-123"


def test_extract_issue_key_with_invalid_branch_name():
    branch_to_check = "invalid/TEST-123"
    valid_branch_names = "task|test|bugfix|feature|hotfix|epic"
    with pytest.raises(RuntimeError):
        check_status.extract_issue_key(branch_to_check, valid_branch_names)


def test_extract_issue_key_with_invalid_issue_key_format():
    branch_to_check = "feature/INVALID"
    valid_branch_names = "task|test|bugfix|feature|hotfix|epic"
    with pytest.raises(RuntimeError):
        check_status.extract_issue_key(branch_to_check, valid_branch_names)


def test_extract_issue_key_with_custom_names_fail():
    branch_to_check = "feature/OQS-123"
    valid_branch_names = "YOU_SHALL_NOT_PASS"
    with pytest.raises(RuntimeError):
        check_status.extract_issue_key(branch_to_check, valid_branch_names)


def test_extract_issue_key_with_custom_names_pass():
    branch_to_check = "YOU_SHALL_NOT_PASS/OQS-123"
    valid_branch_names = "YOU_SHALL_NOT_PASS"
    check_status.extract_issue_key(branch_to_check, valid_branch_names)


def test_get_inputs_with_all_inputs(monkeypatch):
    monkeypatch.setenv("INPUT_BRANCH_TO_CHECK", "refs/heads/feature/TEST-123")
    monkeypatch.setenv("INPUT_VALID_BRANCH_NAMES", "task|test|bugfix|feature|hotfix|epic")
    monkeypatch.setenv("INPUT_JIRA_USERNAME", "username")
    monkeypatch.setenv("INPUT_JIRA_PASSWORD", "password")
    assert check_status.get_inputs() == (
        "refs/heads/feature/TEST-123",
        "task|test|bugfix|feature|hotfix|epic",
        "username",
        "password",
    )


def test_get_inputs_with_missing_input(monkeypatch):
    monkeypatch.setenv("INPUT_BRANCH_TO_CHECK", "refs/heads/feature/TEST-123")
    monkeypatch.setenv("INPUT_VALID_BRANCH_NAMES", "task|test|bugfix|feature|hotfix|epic")
    monkeypatch.setenv("INPUT_JIRA_USERNAME", "username")
    monkeypatch.delenv("INPUT_JIRA_PASSWORD", raising=False)
    with pytest.raises(RuntimeError):
        check_status.get_inputs()


def test_get_inputs_with_missing_input_2(monkeypatch):
    monkeypatch.setenv("INPUT_BRANCH_TO_CHECK", "refs/heads/feature/TEST-123")
    monkeypatch.setenv("INPUT_VALID_BRANCH_NAMES", "")
    monkeypatch.setenv("INPUT_JIRA_USERNAME", "username")
    with pytest.raises(RuntimeError):
        check_status.get_inputs()


def test_get_inputs_with_default_valid_branch_names(monkeypatch):
    monkeypatch.setenv("INPUT_BRANCH_TO_CHECK", "refs/heads/feature/TEST-123")
    monkeypatch.delenv("INPUT_VALID_BRANCH_NAMES", raising=False)
    monkeypatch.setenv("INPUT_JIRA_USERNAME", "username")
    monkeypatch.setenv("INPUT_JIRA_PASSWORD", "password")
    assert check_status.get_inputs() == (
        "refs/heads/feature/TEST-123",
        "task|test|bugfix|feature|hotfix|epic",
        "username",
        "password",
    )


if __name__ == "__main__":
    pytest.main()
