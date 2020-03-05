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


def filter_by_release(issues, release_title):
    issues_with_releases = []

    for issue in issues:
        if "releases" in issue and len(issue["releases"]) > 0:
            for release in issue["releases"]:
                if release["title"] == release_title:
                    issues_with_releases.append(issue)
    return issues_with_releases


epics = get_epics(issues)

master_epics = filter_by_release(epics, "Focal Fossa - 20.04")

for master_epic in master_epics:
    master_epic["epics"] = []

for epic in epics:
    for parent_epic in epic["parent_epics"]:
        repo_id = parent_epic["repo_id"]
        issue_number = parent_epic["issue_number"]

        for master_epic in master_epics:
            if (
                master_epic["repo_id"] == repo_id
                and master_epic["issue_number"] == issue_number
            ):
                master_epic["epics"].append(epic)

issues_in_milestone = filter_by_milestone(
    issues, "Iteration 20-08 (17 February - 28 February)"
)

epics_in_milestone = get_epics(issues_in_milestone)

for epic in epics_in_milestone:
    epic["issues"] = []
    epic["estimate"] = 0
    epic["completed"] = 0

for issue in issues_in_milestone:
    if not issue["is_epic"]:
        for parent_epic in issue["parent_epics"]:
            repo_id = parent_epic["repo_id"]
            issue_number = parent_epic["issue_number"]

            for epic in epics_in_milestone:
                if (
                    epic["repo_id"] == repo_id
                    and epic["issue_number"] == issue_number
                ):
                    epic["issues"].append(issue)
                    if issue["estimate"]:
                        epic["estimate"] += issue["estimate"]
                        if issue["state"] == "closed":
                            epic["completed"] += issue["estimate"]


# print(json.dumps(epics_in_milestone[3], indent=2))

print(epics_in_milestone[0]["milestone"]["title"] + "\n")

for epic in epics_in_milestone:
    print(epic["title"])
    for issue in epic["issues"]:
        print("\t" + issue["title"] + " - " + str(issue["estimate"]))
    print("\t" + str(round((epic["completed"] / epic["estimate"]) * 100)))
    print("")

print(json.dumps(master_epics[1], indent=2))
# print(json.dumps(epics_in_milestone[0], indent=2))
