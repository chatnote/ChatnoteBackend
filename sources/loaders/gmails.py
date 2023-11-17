import base64

import requests
from django.conf import settings


class GoogleGmailService:
    def __init__(self, user):
        # scope: https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.email
        self.user = user
        self.headers = {
            'Authorization': f'Bearer {user.gmail_access_token}',
            'Content-type': 'application/x-www-form-urlencoded',
            'charset': 'utf-8'
        }

    @staticmethod
    def get_token(code: str, redirect_url: str) -> str:
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
        access_token = response.json()["access_token"]
        return access_token

    def get_account_info(self) -> str:
        response = requests.get(
            url="https://www.googleapis.com/oauth2/v2/userinfo",
            headers=self.headers
        )
        return response.json()

    def get_messages(self, page_token=None):
        # https://support.google.com/mail/answer/7190?hl=ko
        q_date = "q=category:primary newer_than:7d 'ddr04014@gmail.com'"

        if page_token:
            q_page_token = f"pageToken={page_token}"
        else:
            q_page_token = ""
        response = requests.get(
            url=f"https://gmail.googleapis.com/gmail/v1/users/{self.user.gmail_google_user_id}/messages?{q_date}&{q_page_token}",
            headers=self.headers
        )
        import json
        print(json.dumps(response.json()))
        return response.json()

    def get_message(self, message_id):
        response = requests.get(
            url=f"https://gmail.googleapis.com/gmail/v1/users/{self.user.gmail_google_user_id}/messages/{message_id}",
            headers=self.headers
        )

        message = response.json()
        import json
        print(json.dumps(message))

        snippet = message["snippet"]
        # mime_type = message["payload"]["mimeType"]
        subject = self._get_subject(message)
        html_data = base64.urlsafe_b64decode(message["payload"]["body"]["data"]).decode("utf-8")

        return subject, snippet, html_data

    @staticmethod
    def _get_subject(message):
        headers = message["payload"]["headers"]
        for header in headers:
            if header["name"] == "Subject":
                return header["value"]
