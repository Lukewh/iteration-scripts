import requests

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

    def get_epic_data(self, repo_id, epic_id):
          endpoint = "p1/repositories/{repo_id}/epics/{epic_id}".format(repo_id=repo_id, epic_id=epic_id)
          request = self.get(
                endpoint=endpoint
          )

          return request.json()

    def get_issue_data(self, repo_id, issue_number):
          endpoint = "p1/repositories/{repo_id}/issues/{issue_number}".format(repo_id=repo_id, issue_number=issue_number)

          request = self.get(endpoint=endpoint)

          return request.json()
