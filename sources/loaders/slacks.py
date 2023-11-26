import requests
from django.conf import settings


class SlackLoader:
    def __init__(self, user):
        self.user = user
        self.headers = {
            'Authorization': f'Bearer {user.slack_access_token}',
            'Content-type': 'application/x-www-form-urlencoded',
            'charset': 'utf-8'
        }

    @staticmethod
    def get_tokens(code: str, redirect_url: str) -> dict:
        response = requests.post(
            url=f"https://slack.com/api/oauth.v2.access",
            headers={
                'Content-type': 'application/x-www-form-urlencoded',
                'charset': 'utf-8'
            },
            data={
                "client_id": settings.SLACK_CLIENT_ID,
                "client_secret": settings.SLACK_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_url
            }
        )
        return response.json()

    def get_account_info(self):
        response = requests.get(
            url="https://slack.com/api/users.profile.get",
            headers=self.headers
        )
        return response.json()

    def keyword_search(self, keyword: str):
        response = requests.get(
            url=f"https://slack.com/api/search.all?query={keyword}",
            headers=self.headers
        )
        import json
        print(json.dumps(response.json()))
        # return response.json()
