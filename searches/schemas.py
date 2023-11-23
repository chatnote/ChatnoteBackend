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
    url: str
    description: str

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


class SearchResponseDTO(Schema):
    notion: List[NotionSearchResponseDTO]
    gmail: List[GmailSearchResponseDTO]