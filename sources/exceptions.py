from typing import List

from ninja import Schema

from cores.exception import ExceptionSchema
from sources.enums import NotionValidErrorEnum


class NotionValidPageSchema(Schema):
    title: str
    icon: str


class NotionValidErrorDTO(ExceptionSchema):
    error_code: NotionValidErrorEnum
