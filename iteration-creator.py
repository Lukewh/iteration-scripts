from __future__ import print_function, unicode_literals
import os
import sys
import signal
from github import Github
from dateutil import parser
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
from PyInquirer import prompt, print_json, Validator, ValidationError

load_dotenv()
from zenhub import Zenhub

def signal_handler(signal, frame):
    print("You want to quit? Fine, see if I care 🤷‍")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
ZENHUB_ACCESS_TOKEN = os.getenv("ZENHUB_ACCESS_TOKEN")

g = Github(GITHUB_ACCESS_TOKEN)


class Zenhub:
    def __init__(self, access_token):
        self.ACCESS_TOKEN = access_token

    def post(self, endpoint, data):
        url = "".join(
            [
                "https://api.zenhub.io/",
                endpoint,
                "?access_token=",
                self.ACCESS_TOKEN,
            ]
        )
        return requests.post(url, json=data)

    def get(self, endpoint):
        url = "".join(
            [
                "https://api.zenhub.io/",
                endpoint,
                "?access_token=",
                self.ACCESS_TOKEN,
            ]
        )

        return requests.get(url)

    def get_milestone_start(self, repo_id, milestone_number):
        endpoint = "p1/repositories/{repo_id}/milestones/{milestone_number}/start_date".format(
            repo_id=repo_id, milestone_number=milestone_number
        )

        request = self.get(endpoint=endpoint)

    def get_workspace(self, repo_id):
        endpoint = "p2/repositories/{repo_id}/workspaces".format(
            repo_id=repo_id
        )

        request = self.get(endpoint=endpoint)

        return request.json()

    def set_milestone_start(self, start, repo_id, milestone_number):
        endpoint = "p1/repositories/{repo_id}/milestones/{milestone_number}/start_date".format(
            repo_id=repo_id, milestone_number=milestone_number
        )
        request = self.post(
            endpoint=endpoint, data={"start_date": start.isoformat()}
        )

        return request.status_code == 200

    def convert_issue_to_epic(self, repo_id, issue_number):
        endpoint = "p1/repositories/{repo_id}/issues/{issue_number}/convert_to_epic".format(
            repo_id=repo_id, issue_number=issue_number
        )
        request = self.post(
            endpoint=endpoint,
            data=[{"repo_id": repo_id, "issue_number": issue_number}],
        )

        return request.status_code == 200

    def add_issue_to_epic(self, repo_id, epic_issue_number, issue_to_add):
        endpoint = "p1/repositories/{repo_id}/epics/{epic_issue_number}/update_issues".format(
            repo_id=repo_id, epic_issue_number=epic_issue_number
        )
        request = self.post(
            endpoint=endpoint,
            data={"add_issues": [{"repo_id": issue_to_add["repo_id"], "issue_number": issue_to_add["issue_number"]}]},
        )

        return request.status_code == 200


z = Zenhub(ZENHUB_ACCESS_TOKEN)


def create_milestone(due_date, length_in_weeks, repos):
    primary_repo = g.get_repo(repos[0])
    other_repos = [g.get_repo(repo) for repo in repos[1:]]

    questions = [
        {
            "type": "checkbox",
            "name": "repos_to_create_milestone",
            "message": "Milestone will be created for {primary_name}.\nWhich repos should the milestone be created for?".format(
                primary_name=primary_repo.full_name
            ),
            "choices": [{"name": repo.full_name} for repo in other_repos],
        }
    ]

    answers = prompt(questions)

    repos_to_create_milestone = [
        repo
        for repo in other_repos
        if repo.full_name in answers["repos_to_create_milestone"]
    ]

    end_date = parser.isoparse(due_date)
    week_of_year = end_date.isocalendar()[1]
    start_days_earlier = 5
    if length_in_weeks == 2:
        week_of_year = week_of_year - 1
        start_days_earlier = 11
    start_date = end_date - timedelta(days=start_days_earlier)
    start_year = start_date.strftime("%y")
    if week_of_year < 10:
        week_of_year = "0" + str(week_of_year)
    title_format = "{year}-{week} ({start_date} - {end_date})".format(
        year=start_year,
        week=week_of_year,
        start_date=start_date.strftime("%-d %B"),
        end_date=end_date.strftime("%-d %B"),
    )
    title = "Iteration " + title_format

    print("Creating:")
    print(title)

    end_iso = end_date + timedelta(days=1)
    milestone = primary_repo.create_milestone(title, due_on=end_iso)
    for repo in repos_to_create_milestone:
        repo.create_milestone(title, due_on=end_iso)

    z.set_milestone_start(start_date, primary_repo.id, milestone.number)

    print("Done")

    questions = [
        {
            "type": "confirm",
            "name": "create_small_task",
            "message": "Create Small Tasks Epic on {primary_name}".format(
                primary_name=primary_repo.full_name
            ),
            "default": True,
        }
    ]

    answers = prompt(questions)

    if answers["create_small_task"]:
        print("Creating small tasks")
        small_tasks_title = "Maintenance " + title_format
        print(small_tasks_title)
        issue = primary_repo.create_issue(
            small_tasks_title, milestone=milestone
        )
        z.convert_issue_to_epic(primary_repo.id, issue.number)
        z.add_issue_to_epic(primary_repo.id, 987, {"repo_id": primary_repo.id, "issue_number": issue.number})

    print("All done 🤜🤛")


class DateValidator(Validator):
    def validate(self, document):
        try:
            parsed = parser.isoparse(document.text)
            return isinstance(parsed, datetime)
        except ValueError:
            raise ValidationError(
                message="Please enter a date in the format YYYY-MM-DD",
                cursor_position=len(document.text),
            )


print("HIYA! Just getting the list of repos. Hold tight... 🕵")

repos = g.get_organization("canonical-web-and-design").get_repos(type="private")
squad_repos = []
for repo in repos:
    if "squad" in repo.name:
        squad_repos.append(repo.name)

print("FOUND THEM! 👏")

questions = [
    {
        "type": "rawlist",
        "name": "squad-repo",
        "message": "Which squad?",
        "choices": squad_repos,
    }
]

answers = prompt(questions)

squad_repo = g.get_repo("canonical-web-and-design/" + answers["squad-repo"])
squad_repos = [squad_repo.id] + [
    repo
    for repo in z.get_workspace(squad_repo.id)[0]["repositories"]
    if repo != squad_repo.id
]

questions = [
    {
        "type": "input",
        "name": "due_date",
        "message": "What date will the iteration end (YYYY-MM-DD format)",
        "validate": DateValidator,
    },
    {
        "type": "list",
        "name": "iteration_length",
        "message": "How long is the iteration (weeks)",
        "choices": ["1", "2"],
    },
]


answers = prompt(questions)
create_milestone(
    answers["due_date"],
    length_in_weeks=int(answers["iteration_length"]),
    repos=squad_repos,
)
