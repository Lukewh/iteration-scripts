import requests
import json
from dotenv import load_dotenv

load_dotenv()
import os

"""
Master epic
  - title
  - estimate
  - complete
  - url
  - release
  - status
Epic
  - title
  - estimate
  - complete
  - url
  - milestone
  - status
Issue
  - title
  - estimate
  - status
  - url
  - milestone
"""

URL = os.getenv("ZENHUB_URL")
TOKEN = os.getenv("ZENHUB_TOKEN")

headers = {
    "authority": "api.zenhub.com",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "origin": "https://app.zenhub.com",
    "x-authentication-token": TOKEN,
    "x-zenhub-agent": "webapp/2.38.189",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "cors",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
}

r = requests.get(URL, headers=headers)

issues = r.json()


def get_epics(issues):
    return [issue for issue in issues if issue["is_epic"]]


def filter_by_milestone(issues, milestone):
    return [
        issue
        for issue in issues
        if "milestone" in issue
        and issue["milestone"]
        and "title" in issue["milestone"]
        and issue["milestone"]["title"] == milestone
    ]


def get_master_epics(issues):
    master_epics = []

    for issue in issues:
        if issue["is_epic"]:
            for label in issue["labels"]:
                if label["name"] == "Master Epic":
                    issue["epics"] = []
                    master_epics.append(issue)

    return master_epics


def issues_as_dict(issues):
    issues_dict = {}
    for issue in issues:
        issue["children"] = []
        issue_key = ":".join(
            [str(issue["repo_id"]), str(issue["issue_number"])]
        )
        issues_dict[issue_key] = issue

    return issues_dict


issues_dict = issues_as_dict(issues)


def add_to_parents(issues, issues_dict):
    for issue in issues:
        parents = issue["parent_epics"]
        issue_key = ":".join(
            [str(issue["repo_id"]), str(issue["issue_number"])]
        )
        for parent in parents:
            key = ":".join(
                [str(parent["repo_id"]), str(parent["issue_number"])]
            )
            if key in issues_dict:
                issues_dict[key]["children"].append(issue)

    return issues_dict


issues_dict = add_to_parents(issues, issues_dict)

issues_list = []

for issue in issues_dict.items():
    if issue[1]["is_epic"] or len(issue[1]["children"]) > 0:
        issues_list.append(issue[1])

print(
    json.dumps(
        filter_by_milestone(
            issues_list, "Iteration 20-08 (17 February - 28 February)"
        ),
        indent=2,
    )
)
