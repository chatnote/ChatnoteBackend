import requests
from django.conf import settings


class GoogleCalendarLoader:
    def __init__(self, user):
        self.user = user
        self.headers = {
            'Authorization': f'Bearer {user.google_calendar_access_token}',
            'Content-type': 'application/x-www-form-urlencoded',
            'charset': 'utf-8'
        }

    @staticmethod
    def get_tokens(code: str, redirect_url: str) -> dict:
        response = requests.post(
            url=f"https://oauth2.googleapis.com/token",
            headers={
                'Content-type': 'application/x-www-form-urlencoded',
                'charset': 'utf-8'
            },
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_url,
                "grant_type": "authorization_code",
            }
        )
        return response.json()

    def get_tokens_by_refresh(self):
        response = requests.post(
            url=f"https://oauth2.googleapis.com/token",
            headers={
                'Content-type': 'application/x-www-form-urlencoded',
                'charset': 'utf-8'
            },
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": self.user.google_calendar_refresh_token,
                "grant_type": "refresh_token",
            }
        )
        return response.json()

    def get_account_info(self) -> dict:
        response = requests.get(
            url="https://www.googleapis.com/oauth2/v2/userinfo",
            headers=self.headers
        )
        return response.json()

    def keyword_search(self, keyword: str, offset: int = 0, limit: int = 10, next_page_token=None):
        pass
