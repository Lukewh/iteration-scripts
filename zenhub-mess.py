import requests
import json
from dotenv import load_dotenv

import flask

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


def update_estimates(issues_dict):
    for issue in issues_dict:
        single_issue = issues_dict[issue]

        if not single_issue["estimate"]:
            single_issue["estimate"] = 0

        if not "complete" in single_issue:
            single_issue["complete"] = 0

        if single_issue["children"]:
            for child in single_issue["children"]:
                if child["estimate"]:
                    single_issue["estimate"] += child["estimate"]
                    if child["state"] == "closed":
                        single_issue["complete"] += child["estimate"]


def simpler_issues(issues):
    new_issues = []

    for issue in issues:
        is_master_epic = False

        for label in issue["labels"]:
            if "name" in label and label["name"] == "Master Epic":
                is_master_epic = True

        new_issues.append(
            {
                "estimate": issue["estimate"],
                "html_url": issue["html_url"],
                "labels": issue["labels"],
                "milestone": issue["milestone"],
                "issue_number": issue["number"],
                "organization_name": issue["organization_name"],
                "parent_epics": issue["parent_epics"],
                "releases": issue["releases"],
                "repo_id": issue["repo_id"],
                "repo_name": issue["repo_name"],
                "state": issue["state"],
                "is_epic": issue["is_epic"],
                "title": issue["title"],
                "is_master_epic": is_master_epic,
            }
        )

    return new_issues


def get_complete(issues, master_epic_key, milestone):
    epics = []

    data = {"estimate": 0, "complete": 0}

    for issue in issues:
        if (
            issue["milestone"]
            and issue["milestone"]["title"]
            and issue["milestone"]["title"] == milestone
        ):
            if issue["is_epic"] and issue["parent_epics"]:
                for epic in issue["parent_epics"]:
                    temp_key = (
                        str(epic["repo_id"]) + ":" + str(epic["issue_number"])
                    )
                    if temp_key == master_epic_key:
                        epics.append(
                            str(issue["repo_id"])
                            + ":"
                            + str(issue["issue_number"])
                        )

    for issue in issues:
        if issue["parent_epics"]:
            for epic in issue["parent_epics"]:
                temp_key = (
                    str(epic["repo_id"]) + ":" + str(epic["issue_number"])
                )

                if temp_key in epics:
                    if issue["estimate"]:
                        data["estimate"] += issue["estimate"]
                        if issue["state"] == "closed":
                            data["complete"] += issue["estimate"]
    return data


def get_nested_data():
    r = requests.get(URL, headers=headers)

    issues = simpler_issues(r.json())

    releases = []

    the_data = []

    for issue in issues:
        for release in issue["releases"]:
            if "state" in release and release["state"] == "open":
                title = release["title"]
                the_release = None
                if not title in releases:
                    releases.append(release["title"])
                    the_release = {
                        "title": release["title"],
                        "master_epics": [],
                    }
                    the_data.append(the_release)
                else:
                    the_release = [
                        release
                        for release in the_data
                        if release["title"] == title
                    ][0]

                the_release["master_epics"].append(issue)

    milestones = []

    releases = {}

    for issue in issues:
        release_title = None
        master_epic = None
        issue_key = str(issue["repo_id"]) + ":" + str(issue["issue_number"])

        for release in issue["releases"]:
            if "state" in release and release["state"] == "open":
                release_title = release["title"]
                if not release_title in releases:
                    releases[release_title] = {"epic_keys": []}

        if release_title:
            for label in issue["labels"]:
                if "name" in label and label["name"] == "Master Epic":
                    master_epic = issue["title"]
                    if not master_epic in releases[release_title]:
                        releases[release_title][master_epic] = {
                            "epic_key": issue_key,
                            "milestones": {},
                        }
                        releases[release_title]["epic_keys"].append(issue_key)

    for issue in issues:
        master_epic = None
        epic_keys = []
        add_to = None
        milestone = None

        for epic in issue["parent_epics"]:
            epic_keys.append(
                str(epic["repo_id"]) + ":" + str(epic["issue_number"])
            )

        if (
            "milestone" in issue
            and issue["milestone"]
            and "title" in issue["milestone"]
        ):
            milestone = issue["milestone"]["title"]

        if len(epic_keys) > 0:
            for epic_key in epic_keys:
                for release in releases:
                    for master_epic_title in releases[release]:
                        if (
                            "epic_key" in releases[release][master_epic_title]
                            and releases[release][master_epic_title][
                                "epic_key"
                            ]
                            == epic_key
                        ):
                            add_to = releases[release][master_epic_title]

        if add_to and milestone and not milestone in add_to:
            add_to["milestones"][milestone] = {}

    for release in releases:
        for master_epic in releases[release]:
            if master_epic != "epic_key":
                if "milestones" in releases[release][master_epic]:
                    epic_key = releases[release][master_epic]["epic_key"]
                    for milestone in releases[release][master_epic][
                        "milestones"
                    ]:
                        releases[release][master_epic]["milestones"][
                            milestone
                        ] = get_complete(issues, epic_key, milestone)

    for release in releases:
        del releases[release]["epic_keys"]

        for master_epic in releases[release]:
            releases[release][master_epic] = releases[release][master_epic][
                "milestones"
            ]

    return releases


if __name__ == "__main__":
    import sys
    args = sys.argv

    is_flask = False
    
    for arg in args:
        if arg == "--web":
            is_flask = True

    if is_flask:
        app = flask.Flask(__name__)

        @app.route("/original")
        def get_the_data_big_boy():
            milestone = flask.request.args.get("milestone")

            r = requests.get(URL, headers=headers)

            issues = simpler_issues(r.json())

            issues_dict = add_to_parents(issues, issues_as_dict(issues))

            update_estimates(issues_dict)

            issues_list = []

            for issue in issues_dict.items():
                if issue[1]["is_epic"] or len(issue[1]["children"]) > 0:
                    issues_list.append(issue[1])

            if milestone:
                return flask.jsonify(filter_by_milestone(issues_list, milestone))
            else:
                return flask.jsonify(issues_list)

        @app.route("/")
        def get_more_data_big_boy():
            data = get_nested_data()
            return flask.jsonify(data)
 
        app.run()
    else:
        releases = get_nested_data()
        
        for release in releases:
            print(release)
            for master_epic in releases[release]:
                estimate = 0
                complete = 0
                for iteration in releases[release][master_epic]:
                    estimate += releases[release][master_epic][iteration]["estimate"]
                    complete += releases[release][master_epic][iteration]["complete"]

                percentage = 0
                if estimate > 0 and complete > 0:
                    percentage = round((complete / estimate) * 100)
                print("\t" + master_epic + " - " + str(percentage) + "%")
                for iteration in releases[release][master_epic]:
                    print("\t\t" + iteration)
                    print("\t\t\tEstimate: " + str(releases[release][master_epic][iteration]["estimate"]))
                    print("\t\t\tComplete: " + str(releases[release][master_epic][iteration]["complete"]))
