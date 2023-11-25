from typing import List

import requests
from django.conf import settings

from sources.schemas import GoogleCalendarEventSchema


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

    def keyword_search(self, keyword: str, offset: int = 0, limit: int = 10, next_page_token=None) -> List[GoogleCalendarEventSchema]:
        if not self.user.google_calendar_access_token:
            return []

        calendar_id = "primary"
        params = f"q={keyword}"
        response = requests.get(
            url=f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events?{params}",
            headers=self.headers
        )
        # import json
        # print(json.dumps(response.json()))
        if "error" in response.json():
            if response.json()["error"]["status"] == "UNAUTHENTICATED":
                tokens = self.get_tokens_by_refresh()
                self.user.google_calendar_access_token = tokens["access_token"]
                self.user.save()
                self.headers['Authorization'] = f'Bearer {self.user.google_calendar_access_token}'

                response = requests.get(
                    url=f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events?{params}",
                    headers=self.headers
                )

        google_calendar_event_schemas = []
        for item in list(reversed(response.json()["items"]))[offset: offset + limit]:
            creator = item.get("creator")
            start = item.get("start")
            end = item.get("end")
            if item.get("summary"):
                google_calendar_event_schemas.append(
                    GoogleCalendarEventSchema(
                        creator_email=creator.get("email") if creator else None,
                        creator_display_name=creator.get("displayName") if creator else None,
                        start_date=start.get("dateTime") or start.get("date") if start else None,
                        end_date=end.get("dateTime") or end.get("date") if end else None,
                        summary=item.get("summary"),
                        html_link=item.get("htmlLink")
                    )
                )
        return google_calendar_event_schemas
