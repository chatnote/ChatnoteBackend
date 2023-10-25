from typing import List

from ninja import Schema

from sources.enums import DataSourceEnum


class ChatQueryParams(Schema):
    session_id: int | None
    query: str


class SearchResponseSchema(Schema):
    title: str
    original_document_id: int
    original_text: str
    chunked_text: str
    url: str | None
    source: DataSourceEnum


class ChatReferenceSchema(Schema):
    title: str
    url: str
    source: DataSourceEnum


class ChatResponseDTO(Schema):
    session_id: int
    chat_history_id: int
    query: str
    response: str
    recommend_queries: List[str] | None
    references: List[ChatReferenceSchema] | None


class ChatEvalParams(Schema):
    chat_history_id: int
    message: str | None
