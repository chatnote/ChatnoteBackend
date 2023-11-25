from concurrent.futures import ThreadPoolExecutor
from typing import List

import requests
from django.conf import settings

from sources.schemas import GoogleDriveFileSchema


class GoogleDriveLoader:
    def __init__(self, user):
        # scope: https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/drive.metadata.readonly https://www.googleapis.com/auth/drive.file
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
                "refresh_token": self.user.google_drive_refresh_token,
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

    def keyword_search(self, keyword: str, offset: int = 0, limit: int = 10, next_page_token=None) -> List[
        GoogleDriveFileSchema]:
        if not self.user.google_drive_access_token:
            return []

        query = f"q=fullText contains '{keyword}'&fields=files(mimeType,id,name,modifiedTime,description,webViewLink)"
        response = requests.get(
            url=f"https://www.googleapis.com/drive/v3/files?{query}",
            headers=self.headers
        )

        if "error" in response.json():
            if response.json()["error"]["status"] == "UNAUTHENTICATED":
                tokens = self.get_tokens_by_refresh()
                self.user.google_drive_access_token = tokens["access_token"]
                self.user.save()
                self.headers['Authorization'] = f'Bearer {self.user.google_drive_access_token}'

                response = requests.get(
                    url=f"https://www.googleapis.com/drive/v3/files?{query}",
                    headers=self.headers
                )

        files = []
        if "files" in response.json():
            files = response.json()["files"]

        return [
            GoogleDriveFileSchema(
                id=file["id"],
                name=file["name"],
                mime_type=file["mimeType"],
                modified_time=file["modifiedTime"],
                webview_link=file["webViewLink"]
            ) for file in files[offset: offset + limit]
        ]
