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


if __name__ == "__main__":
    pytest.main()
