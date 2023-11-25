from concurrent.futures import ThreadPoolExecutor
from typing import List

from django.shortcuts import render

from cores.apis import api_v2
from cores.enums import ApiTagEnum
from cores.utils import print_execution_time
from searches.schemas import SearchResponseDTO, NotionSearchResponseDTO, GmailSearchResponseDTO, GoogleDriveResponseDTO, \
    GoogleCalendarResponseDTO
from sources.loaders.drives import GoogleDriveLoader
from sources.loaders.gmails import GoogleGmailLoader
from sources.loaders.google_calendars import GoogleCalendarLoader
from sources.loaders.notion import NotionLoader
from sources.schemas import GmailMessageSchema


# Create your views here.


@api_v2.get(
    path="search/",
    response={200: SearchResponseDTO},
    tags=[ApiTagEnum.search]
)
def search(request, keyword: str):
    user = request.user
    offset = 0
    limit = 10

    with ThreadPoolExecutor(max_workers=4) as executor:
        future1 = executor.submit(NotionLoader(user).keyword_search, keyword, offset, limit)
        future2 = executor.submit(GoogleGmailLoader(user).keyword_search, keyword, offset, limit)
        future3 = executor.submit(GoogleDriveLoader(user).keyword_search, keyword, offset, limit)
        future4 = executor.submit(GoogleCalendarLoader(user).keyword_search, keyword, offset, limit)

        notion_search_page_schemas = future1.result()
        gmail_message_schemas = future2.result()
        google_drive_file_schemas = future3.result()
        google_calendar_event_schemas = future4.result()

    return SearchResponseDTO(
        notion=NotionSearchResponseDTO.from_notion_search_page_schemas(notion_search_page_schemas),
        gmail=GmailSearchResponseDTO.from_gmail_message_schemas(gmail_message_schemas),
        google_drive=GoogleDriveResponseDTO.from_google_drive_file_schemas(google_drive_file_schemas),
        google_calendar=GoogleCalendarResponseDTO.from_google_calendar_event_schemas(google_calendar_event_schemas)
    )
