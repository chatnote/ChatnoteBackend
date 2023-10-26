from datetime import timedelta
from typing import List

import requests
from django.conf import settings

from cores.apis import api, test_api
from cores.enums import ApiTagEnum
from cores.exception import CustomException
from cores.utils import split_list_and_run
from sources.constants import PAGE_LIMIT
from sources.services import NotionDocumentService, NotionValidator, NotionPageService
from sources.enums import NotionValidErrorEnum, DataSourceEnum
from sources.exceptions import NotionValidErrorDTO, NotionValidPayloadSchema, NotionValidPageSchema
from sources.loaders.notion import NotionLoader
from sources.schemas import SyncStatusSchema, NotionPageDTO, NotionPagePayloadDTO
import base64

from sources.services import NotionSyncStatusService
from sources.tasks import sync_notion_task


@api.get(
    path="source/notion/callback/",
    tags=[ApiTagEnum.source]
)
def notion_callback(request, code: str, redirect_url: str):
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
    access_token = response.json()["access_token"]

    user = request.user
    user.notion_access_token = access_token
    user.save()


@api.post(
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
        workspace_notion_page_schemas = [item for item in notion_loader.get_all_page_schemas(pages) if item.is_workspace]
        raise CustomException(
            **NotionValidErrorDTO(
                error_code=NotionValidErrorEnum.notion_page_limit,
                payload=NotionValidPayloadSchema(
                    page_limit_counts=PAGE_LIMIT,
                    page_counts=len(pages),
                    notion_page_schemas=[NotionValidPageSchema(
                        title=notion_page.title,
                        icon=notion_page.icon
                    ) for notion_page in workspace_notion_page_schemas]
                )
            ).dict()
        )

    if pages:
        NotionSyncStatusService(user).to_running(len(pages))

    split_list_and_run(pages, 50, sync_notion_task, user.id)


@api.post(
    path="source/notion/delete/",
    tags=[ApiTagEnum.source]
)
def notion_delete(request):
    user = request.user
    NotionDocumentService(user).delete_all_documents()


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
        page_limit_counts=PAGE_LIMIT,
        page_counts=page_counts,
        notion_page_schemas=[NotionPagePayloadDTO(
            title=item.title,
            icon=item.icon
        ) for item in workspace_notion_page_qs],
        update_datetime=workspace_notion_page_qs.first().modified + timedelta(hours=9) if workspace_notion_page_qs else None
    )


@api.get(
    path="source/status/",
    response={200: List[SyncStatusSchema]},
    tags=[ApiTagEnum.source]
)
def source_status(request):
    user = request.user

    data_sync_status_qs = user.datasyncstatus_set.all()
    if data_sync_status_qs.get(source=DataSourceEnum.notion).is_done:
        NotionPageService(user).create_or_update_pages()
        NotionSyncStatusService(user).to_stop()
    return SyncStatusSchema.from_instances(data_sync_status_qs)
