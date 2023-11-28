import urllib.parse
from datetime import timedelta
from typing import List

import requests
from django.conf import settings

from cores.apis import api, api_v2
from cores.elastics.clients import ChunkedContextClient
from cores.enums import ApiTagEnum
from cores.exception import CustomException
from cores.utils import split_list_and_run
from sources.constants import NOTION_PAGE_LIMIT
from sources.loaders.drives import GoogleDriveLoader
from sources.loaders.gmails import GoogleGmailLoader
from sources.loaders.google_calendars import GoogleCalendarLoader
from sources.loaders.slacks import SlackLoader
from sources.models import DataSource, DataSourceUpvote
from sources.services import NotionService, NotionValidator, GmailSyncStatusService, GoogleDriveSyncStatusService, \
    GoogleCalendarSyncStatusService, SlackSyncStatusService
from sources.enums import NotionValidErrorEnum, DataSourceEnum
from sources.exceptions import NotionValidErrorDTO
from sources.loaders.notion import NotionLoader
from sources.schemas import SyncStatusSchema, NotionPageDTO, NotionPagePayloadDTO, MyDataSourceDTO, DataSourceDTO, \
    PostUpvoteParams
import base64

from sources.services import NotionSyncStatusService
from sources.tasks import sync_notion_task


@api_v2.get(
    path="source/",
    response={200: List[DataSourceDTO]},
    tags=[ApiTagEnum.source]
)
def all_sources(request):
    user = request.user
    data_source_qs = DataSource.objects.all().order_by("sort_order")
    return DataSourceDTO.from_instances(user, data_source_qs)


@api_v2.get(
    path="source/my_integration/",
    response={200: List[MyDataSourceDTO]},
    tags=[ApiTagEnum.source]
)
def my_integrations(request):
    user = request.user
    data_sync_status_qs = user.datasyncstatus_set.all()
    return MyDataSourceDTO.from_instances(data_sync_status_qs)


@api_v2.post(
    path="source/upvote/",
    tags=[ApiTagEnum.source]
)
def update_upvote(request, params: PostUpvoteParams):
    DataSourceUpvote.objects.get_or_create(user=request.user, data_source_id=params.data_source_id)


@api.get(
    path="source/notion/callback/",
    tags=[ApiTagEnum.source]
)
@api_v2.get(
    path="source/notion/callback/",
    tags=[ApiTagEnum.source]
)
def notion_callback(request, code: str, redirect_url: str):
    code = urllib.parse.unquote(code)
    credentials = f"{settings.NOTION_CLIENT_ID}:{settings.NOTION_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    response = requests.post(
        url="https://api.notion.com/v1/oauth/token",
        headers={
            'Authorization': f"Basic {encoded_credentials}",
            'Notion-Version': '2022-06-28',
            'Content-type': 'application/json',
        },
        json={
            "grant_type": "authorization_code",
            "code": code,
            'redirect_uri': redirect_url
        }
    )
    if "access_token" not in response.json():
        print(response.json())
    access_token = response.json()["access_token"]
    user = request.user
    user.notion_access_token = access_token
    user.save()


@api.post(
    path="source/notion/sync/",
    response={200: None, 400: NotionValidErrorDTO},
    tags=[ApiTagEnum.source]
)
@api_v2.post(
    path="source/notion/sync/",
    response={200: None, 400: NotionValidErrorDTO},
    tags=[ApiTagEnum.source]
)
def sync_notion(request):
    user = request.user

    notion_loader = NotionLoader(user)
    pages = notion_loader.get_all_page()

    # page count save
    is_valid = NotionValidator.validate(user, pages)
    if not is_valid:
        raise CustomException(
            NotionValidErrorDTO(
                error_code=NotionValidErrorEnum.notion_page_limit
            )
        )

    if pages:
        NotionSyncStatusService(user).to_running(len(pages))
        total_page_urls = [page["url"] for page in pages]  # for delete

        split_list_and_run(pages, 30, sync_notion_task, user.id, total_page_urls)


@api.post(
    path="source/notion/delete/",
    tags=[ApiTagEnum.source]
)
@api_v2.post(
    path="source/notion/delete/",
    tags=[ApiTagEnum.source]
)
def notion_delete(request):
    user = request.user
    NotionService(user).delete_all_documents()
    user.datasyncstatus_set.filter(data_source__source=DataSourceEnum.notion).delete()
    user.notion_access_token = None
    user.save()


@api_v2.get(
    path="source/gmail/callback/",
    description="- scope : https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.email",
    tags=[ApiTagEnum.source]
)
def gmail_callback(request, code: str, redirect_url: str):
    user = request.user
    code = urllib.parse.unquote(code)
    tokens = GoogleGmailLoader(user).get_tokens(code, redirect_url)
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    user.gmail_access_token = access_token
    user.gmail_refresh_token = refresh_token
    user.save()

    GmailSyncStatusService(user).get_or_create_sync_status()


@api_v2.post(
    path="source/gmail/delete/",
    tags=[ApiTagEnum.source]
)
def gmail_delete(request):
    user = request.user
    user.datasyncstatus_set.filter(data_source__source=DataSourceEnum.gmail).delete()
    user.gmail_access_token = None
    user.save()


@api_v2.get(
    path="source/google_drive/callback/",
    description="- scope : https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/drive.metadata.readonly https://www.googleapis.com/auth/drive.file",
    tags=[ApiTagEnum.source]
)
def google_drive_callback(request, code: str, redirect_url: str):
    user = request.user
    code = urllib.parse.unquote(code)
    tokens = GoogleDriveLoader(user).get_tokens(code, redirect_url)
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    user.google_drive_access_token = access_token
    user.google_drive_refresh_token = refresh_token
    user.save()

    GoogleDriveSyncStatusService(user).get_or_create_sync_status()


@api_v2.post(
    path="source/google_drive/delete/",
    tags=[ApiTagEnum.source]
)
def google_drive_delete(request):
    user = request.user
    user.datasyncstatus_set.filter(data_source__source=DataSourceEnum.google_drive).delete()
    user.google_drive_access_token = None
    user.save()


@api_v2.get(
    path="source/google_calendar/callback/",
    description="- scope : https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/calendar.readonly",
    tags=[ApiTagEnum.source]
)
def google_calendar_callback(request, code: str, redirect_url: str):
    user = request.user
    code = urllib.parse.unquote(code)
    tokens = GoogleCalendarLoader(user).get_tokens(code, redirect_url)
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    user.google_calendar_access_token = access_token
    user.google_calendar_refresh_token = refresh_token
    user.save()

    GoogleCalendarSyncStatusService(user).get_or_create_sync_status()


@api_v2.post(
    path="source/google_calendar/delete/",
    tags=[ApiTagEnum.source]
)
def google_calendar_delete(request):
    user = request.user
    user.datasyncstatus_set.filter(data_source__source=DataSourceEnum.google_calendar).delete()
    user.google_calendar_access_token = None
    user.save()


@api_v2.get(
    path="source/slack/callback/",
    description="- scope : channels:history channels:read files:read search:read users.profile:read",
    tags=[ApiTagEnum.source]
)
def slack_callback(request, code: str, redirect_url: str):
    user = request.user
    code = urllib.parse.unquote(code)
    tokens = SlackLoader(user).get_tokens(code, redirect_url)
    access_token = tokens["authed_user"]["access_token"]
    user.slack_access_token = access_token
    user.save()

    SlackSyncStatusService(user).get_or_create_sync_status()


@api_v2.post(
    path="source/slack/delete/",
    tags=[ApiTagEnum.source]
)
def slack_delete(request):
    user = request.user
    user.datasyncstatus_set.filter(data_source__source=DataSourceEnum.slack).delete()
    user.slack_access_token = None
    user.save()


# TODO: DELETE
@api.get(
    path="source/notion/pages/",
    response={200: NotionPageDTO},
    tags=[ApiTagEnum.source]
)
def get_pages(request):
    user = request.user
    page_counts = user.notionpage_set.count()
    workspace_notion_page_qs = user.notionpage_set.filter(is_workspace=True).order_by("-modified").all()

    return NotionPageDTO(
        page_limit_counts=NOTION_PAGE_LIMIT,
        page_counts=page_counts,
        notion_page_schemas=[NotionPagePayloadDTO(
            title=item.title,
            icon=item.icon
        ) for item in workspace_notion_page_qs],
        update_datetime=workspace_notion_page_qs.first().modified + timedelta(
            hours=9) if workspace_notion_page_qs else None
    )


# TODO: DELETE
@api.get(
    path="source/status/",
    response={200: List[SyncStatusSchema]},
    tags=[ApiTagEnum.source]
)
def source_status(request):
    user = request.user

    data_sync_status_qs = user.datasyncstatus_set.all()
    if not data_sync_status_qs.get(data_source__source=DataSourceEnum.notion).is_running:
        ChunkedContextClient().refresh_index()
        NotionSyncStatusService(user).to_stop()
    return SyncStatusSchema.from_instances(data_sync_status_qs)
