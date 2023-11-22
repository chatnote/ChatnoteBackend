import base64
from concurrent.futures import ThreadPoolExecutor
from typing import List

import requests
from django.conf import settings

from sources.schemas import GmailMessageSchema


class GoogleGmailLoader:
    def __init__(self, user):
        # scope: https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.email
        self.user = user
        self.headers = {
            'Authorization': f'Bearer {user.gmail_access_token}',
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
                "refresh_token": self.user.gmail_refresh_token,
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

    def keyword_search(self, keyword: str, offset: int = 0, limit: int = 15, next_page_token=None) -> List[GmailMessageSchema]:
        if not self.user.gmail_access_token:
            return []
        # https://support.google.com/mail/answer/7190?hl=ko
        q_date = "q=category:primary newer_than:7d 'ddr04014@gmail.com'"

        if next_page_token:
            q_page_token = f"pageToken={next_page_token}"
        else:
            q_page_token = ""

        if keyword:
            q_subject = f"subject:{keyword}"
        else:
            q_subject = ""

        response = requests.get(
            url=f"""https://gmail.googleapis.com/gmail/v1/users/{self.user.gmail_google_user_id}/messages?q="{keyword}" """.strip(),
            # url=f"https://gmail.googleapis.com/gmail/v1/users/{self.user.gmail_google_user_id}/messages?{q_date}&{q_page_token}&{q_subject}".strip(),
            headers=self.headers
        )
        if "error" in response.json():
            if response.json()["error"]["status"] == "UNAUTHENTICATED":
                tokens = self.get_tokens_by_refresh()
                self.user.gmail_access_token = tokens["access_token"]
                self.user.save()
                self.headers['Authorization'] = f'Bearer {self.user.gmail_access_token}'

                response = requests.get(
                    url=f"""https://gmail.googleapis.com/gmail/v1/users/{self.user.gmail_google_user_id}/messages?q="{keyword}" """.strip(),
                    # url=f"https://gmail.googleapis.com/gmail/v1/users/{self.user.gmail_google_user_id}/messages?{q_date}&{q_page_token}&{q_subject}".strip(),
                    headers=self.headers
                )

        messages = []
        if "messages" in response.json():
            messages = response.json()["messages"]

        message_ids = [message["id"] for message in messages[offset: offset+limit]]
        with ThreadPoolExecutor(max_workers=5) as pool:
            message_schemas = list(pool.map(self.get_message_schema, message_ids))
        return message_schemas

    def get_message_schema(self, message_id) -> GmailMessageSchema:
        response = requests.get(
            url=f"https://gmail.googleapis.com/gmail/v1/users/{self.user.gmail_google_user_id}/messages/{message_id}",
            headers=self.headers
        )
        message = response.json()

        snippet = message["snippet"]
        message_part = self._get_message_part(message)
        subject = self._get_subject(message_part)

        return GmailMessageSchema(
            title=subject,
            description=snippet,
            url=f"https://mail.google.com/mail?authuser={self.user.gmail_email}#all/{message_id}"
        )

    @staticmethod
    def _get_message_part(message):
        return message["payload"]

    @staticmethod
    def _get_subject(message_part):
        subject = ""
        headers = message_part["headers"]
        for header in headers:
            if header["name"] == "Subject":
                subject = header["value"]
        return subject

    def _get_data(self, message_part):
        data = ""
        if "parts" in message_part:
            for sub_message_part in message_part["parts"]:
                data += self._get_html(sub_message_part)
        return data

    @staticmethod
    def _get_html(message_part):
        html_data = ""
        if "body" in message_part:
            if "data" in message_part["body"]:
                html_data = base64.urlsafe_b64decode(message_part["body"]["data"]).decode("utf-8")
        return html_data
