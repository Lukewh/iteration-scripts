#!/usr/bin/python3

'''
in your i3block configuration to update every hour
# Prs
[open_prs]
command=PATH_TO_THIS_SCRIPT/new-prs.py $button
label=
interval=3600
'''

from __future__ import print_function, unicode_literals
import os
import json
from urllib import parse
import webbrowser
import sys

from github import Github

from zenhub import Zenhub

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

g = Github(GITHUB_ACCESS_TOKEN)

search_term = " ".join([
    "type:pr",
    "repo:canonical-web-and-design/snap-squad",
    "repo:canonical-web-and-design/snapcraft.io",
    "repo:canonical-web-and-design/build.snapcraft.io",
    "repo:canonical-web-and-design/charmhub.io",
    "is:open",
    "is:unmerged"
])

safe_term = parse.quote_plus(search_term)

url = f"https://github.com/search?q={safe_term}"

if len(sys.argv) == 2:
    webbrowser.open(url)

gh_issues = g.search_issues(search_term)

unmerged = []

for issue in gh_issues:
    if issue.state == "open":
        unmerged.append(issue)

count = len(unmerged)

count_str = ""

if count < 10:
    count_str += " " + str(count)
else:
    count_str = str(count)

print(f" {count_str}")
