from datetime import datetime
from typing import List

from ninja import Schema


class NotionSearchResponseDTO(Schema):
    title: str
    url: str

    @classmethod
    def from_notion_search_page_schemas(cls, notion_search_page_schemas):
        return [
            cls(
                title=f"{page.icon} {page.title}",
                url=page.url
            )
            for page in notion_search_page_schemas
        ]


class GmailSearchResponseDTO(Schema):
    title: str
    description: str
    url: str

    @classmethod
    def from_gmail_message_schemas(cls, gmail_message_schemas):
        return [
            cls(
                title=message.title,
                description=message.description,
                url=message.url
            )
            for message in gmail_message_schemas
        ]


class GoogleDriveResponseDTO(Schema):
    title: str
    description: str
    url: str

    @classmethod
    def from_google_drive_file_schemas(cls, google_drive_file_schemas):
        return [
            cls(
                title=file.name,
                description=f"수정된 날짜: {file.modified_time.split('T')[0]}",
                url=file.webview_link
            )
            for file in google_drive_file_schemas
        ]


class GoogleCalendarResponseDTO(Schema):
    title: str
    description: str
    url: str

    @classmethod
    def from_google_calendar_event_schemas(cls, google_calendar_event_schemas):
        return [
            cls(
                title=cls.get_title(event),
                description=cls.get_description(event),
                url=event.html_link
            )
            for event in google_calendar_event_schemas
        ]

    @classmethod
    def get_title(cls, event):
        start_date = event.start_date.split("T")[0]
        end_date = event.end_date.split("T")[0]
        if start_date == end_date:
            return f"({start_date}) {event.summary}"
        else:
            return f"({start_date} ~ {end_date}) {event.summary}"

    @classmethod
    def get_description(cls, event):
        if event.creator_display_name:
            return f"작성자: {event.creator_email} ({event.creator_display_name})"
        else:
            return f"작성자: {event.creator_email}"


class SlackResponseDTO(Schema):
    title: str
    description: str
    url: str

    @classmethod
    def from_slack_schemas(cls, slack_schemas):
        return [
            cls(
                title=slack_schema.text[:100],
                description=cls.get_description(slack_schema),
                url=slack_schema.permalink
            )
            for slack_schema in slack_schemas
        ]

    @classmethod
    def get_description(cls, slack_schema):
        _datetime = datetime.fromtimestamp(float(slack_schema.timestamp))
        return f"채널: #{slack_schema.channel_name} | 작성자: @{slack_schema.username} | 작성날짜: {datetime.strftime(_datetime, '%Y-%m-%d %H:%M')}"

class SearchResponseDTO(Schema):
    notion: List[NotionSearchResponseDTO]
    gmail: List[GmailSearchResponseDTO]
    google_drive: List[GoogleDriveResponseDTO]
    google_calendar: List[GoogleCalendarResponseDTO]
    slack: List[SlackResponseDTO]
