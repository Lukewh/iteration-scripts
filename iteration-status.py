#!/usr/bin/python3

from __future__ import print_function, unicode_literals
import os
import json
import sys

VERBOSE = True
if len(sys.argv) == 2:
    VERBOSE = False

from github import Github

from zenhub import Zenhub

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
ZENHUB_ACCESS_TOKEN = os.getenv("ZENHUB_ACCESS_TOKEN")

g = Github(GITHUB_ACCESS_TOKEN)
z = Zenhub(ZENHUB_ACCESS_TOKEN)

if VERBOSE:
    print("Getting data...")

repo = g.get_organization("canonical-web-and-design").get_repo("snap-squad")

milestones = repo.get_milestones()

milestone = milestones[0]

search_term = " ".join([
    "type:issue",
    "repo:canonical-web-and-design/snap-squad",
    "repo:canonical-web-and-design/snapcraft.io",
    "repo:canonical-web-and-design/build.snapcraft.io",
    "repo:canonical-web-and-design/charmhub.io",
    "milestone:\"" + milestone.title + "\""
])

gh_issues = g.search_issues(search_term)

maintenance_term = " ".join([
    "label:\"Master Epic\"",
    "repo:canonical-web-and-design/snap-squad",
    "Maintenance"
])

maintenance_issue = g.search_issues(maintenance_term)[0]
maintenance_epic = z.get_epic_data(repo_id=maintenance_issue.repository.id, epic_id=maintenance_issue.number)

epics = [{"github": maintenance_issue, "zenhub": maintenance_epic}]
issues = []

for issue in gh_issues:
    zenhub_details = z.get_issue_data(repo_id=issue.repository.id, issue_number=issue.number)
    if zenhub_details["is_epic"]:
        epic_details = z.get_epic_data(repo_id=repo.id, epic_id=issue.number)
        epics.append({"github": issue, "zenhub": epic_details})
    else:
        issues.append({"github": issue, "zenhub": zenhub_details})

orphan_issues = []

for issue in issues:
    is_orphan = True

    repo_id = issue["github"].repository.id
    issue_number = issue["github"].number

    for epic in epics:
        issue_matches = []
        if "zenhub" in epic and "issues" in epic["zenhub"]:
            issue_matches = [
                zh_issue
                for zh_issue in epic["zenhub"]["issues"]
                if zh_issue["repo_id"] == repo_id
                and zh_issue["issue_number"] == issue_number
            ]

        if len(issue_matches) > 0:
            is_orphan = False
    
    if is_orphan:
        orphan_issues.append(issue)

total_points = 0
complete_points = 0

for epic in epics:
    if VERBOSE:
        print(epic["github"].title + " - " + epic["github"].html_url)
    epic_total_points = 0
    epic_complete_points = 0
    if "issues" in epic["zenhub"]:
        for issue in epic["zenhub"]["issues"]:
            found_issues = [
                _issue
                for _issue in issues
                if _issue["github"].repository.id == issue["repo_id"]
                and _issue["github"].number == issue["issue_number"]
            ]
            for found_issue in found_issues:
                output = ["\t"]
                points = 0
                if "estimate" in found_issue["zenhub"]:
                    points = found_issue["zenhub"]["estimate"]["value"]

                if found_issue["github"].state == "closed":
                    output.append("◼")
                    complete_points = complete_points + points
                    epic_complete_points = epic_complete_points + points
                else:
                    output.append("◻")
                total_points = total_points + points
                epic_total_points = epic_total_points + points
                output.append(" " + found_issue["github"].title)
                if VERBOSE:
                    print("".join(output) + " - " + str(points))
        if VERBOSE:
            print("\t-----------------------")
        percentage = 0
        if epic_complete_points > 0 and epic_total_points > 0:
            percentage = round((epic_complete_points / epic_total_points) * 100)
        if VERBOSE:
            print("\t" + "Total: " + str(epic_total_points) + "\tComplete: " + str(epic_complete_points) + "\t" + str(percentage) + "%\n")
    else:
        if VERBOSE:
            print("\t Not part of the iteration - for some reason\n")
                
if len(orphan_issues) > 0:
    if VERBOSE:
        print("Orphan issues")
    for issue in orphan_issues:
        output = ["\t"]
        points = 0
        if "estimate" in issue["zenhub"]:
            points = issue["zenhub"]["estimate"]["value"]
            total_points = total_points + points
            
        if issue["github"].state == "closed":
            output.append("◼")
            complete_points = complete_points + points
        else:
            output.append("◻")
            
        output.append(" " + issue["github"].title + " - " + str(issue["zenhub"]["estimate"]["value"]))

        if VERBOSE:
            print("".join(output))
            print("\t\t" + issue["github"].html_url)

if VERBOSE:
    print("")
    print("=======================")
percentage_points = (complete_points / total_points) * 100
if VERBOSE:
    print(milestone.title)
    print("Total: " + str(total_points) + "\tComplete: " + str(complete_points) + "\t" + str(round(percentage_points)) + "%")
else:
    print("".join([
        str(complete_points),
        "/",
        str(total_points),
        " ",
        str(round(percentage_points)),
        "%"
    ]))
