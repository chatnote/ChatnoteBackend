import requests
from django.conf import settings


class GoogleDriveLoader:
    def __init__(self, user):
        # scope: https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/drive.metadata.readonly
        self.user = user
        self.headers = {
            'Authorization': f'Bearer {user.google_drive_access_token}',
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

    def