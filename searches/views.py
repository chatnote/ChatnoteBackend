from concurrent.futures import ThreadPoolExecutor
from typing import List

from django.shortcuts import render

from cores.apis import api_v2
from cores.enums import ApiTagEnum
from cores.utils import print_execution_time
from searches.schemas import SearchResponseDTO, NotionSearchResponseDTO, GmailSearchResponseDTO
from sources.loaders.gmails import GoogleGmailLoader
from sources.loaders.notion import NotionLoader
from sources.schemas import GmailMessageSchema


# Create your views here.


@api_v2.get(
    path="search/",
    response={200: SearchResponseDTO},
    tags=[ApiTagEnum.search]
)
def search(request, keyword: str, offset: int, limit: int):
    user = request.user

    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(NotionLoader(user).search, keyword, offset, limit)
        future2 = executor.submit(GoogleGmailLoader(user).get_message_schemas, keyword, offset, limit)

        notion_search_page_schemas = future1.result()
        gmail_message_schemas = future2.result()

    # notion_search_page_schemas = NotionLoader(user).search(keyword, offset, limit)
    # gmail_message_schemas = GoogleGmailLoader(user).get_message_schemas(keyword, offset, limit)

    return SearchResponseDTO(
        notion=NotionSearchResponseDTO.from_notion_search_page_schemas(notion_search_page_schemas),
        gmail=GmailSearchResponseDTO.from_gmail_message_schemas(gmail_message_schemas)
    )


@api_v2.get(
    path="search/gmail/",
    response={200: List[GmailSearchResponseDTO]},
    tags=[ApiTagEnum.search]
)
def gmail_search(request, keyword: str, offset: int, limit: int):
    user = request.user
    gmail_message_schemas = GoogleGmailLoader(user).get_message_schemas(keyword, offset, limit)

    return GmailSearchResponseDTO.from_gmail_message_schemas(gmail_message_schemas)


@api_v2.get(
    path="search/notion/",
    response={200: List[NotionSearchResponseDTO]},
    tags=[ApiTagEnum.search]
)
def notion_search(request, keyword: str, offset: int, limit: int):
    user = request.user
    notion_search_page_schemas = NotionLoader(user).search(keyword, offset, limit)
    return NotionSearchResponseDTO.from_notion_search_page_schemas(notion_search_page_schemas)
