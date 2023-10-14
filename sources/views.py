from typing import List

import requests
from django.conf import settings

from cores.apis import api, test_api
from cores.enums import ApiTagEnum
from cores.exception import CustomException
from sources.services import NotionDocumentService, NotionSync, NotionValidator, PAGE_LIMIT
from sources.enums import NotionValidErrorEnum
from sources.exceptions import NotionValidErrorSchema, NotionValidPayloadSchema
from sources.loaders.notion import NotionLoader
from sources.schemas import NotionCallbackParams, SyncStatusSchema, NotionPageSchema, NotionPageDTO
import base64

from sources.services import NotionSyncStatusService


@test_api.get(
    path="notion/callback/",
    auth=None,
    description=f"""NOTION AUTH_URL: {settings.NOTION_AUTH_URL}""",
    tags=[ApiTagEnum.test]
)
def code_notion(request, code: str):
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
            'redirect_uri': settings.NOTION_REDIRECT_URL
        }
    )
    return response.json()


@api.post(
    path="source/notion/access_token/",
    tags=[ApiTagEnum.source]
)
def save_notion_access_token(request, params: NotionCallbackParams):
    user = request.user
    user.notion_access_token = params.access_token
    user.save()


@api.post(
    path="source/notion/sync/",
    response={200: None, 400: NotionValidErrorSchema},
    tags=[ApiTagEnum.source]
)
def notion_sync(request):
    user = request.user

    NotionSyncStatusService(user).to_running()
    notion_loader = NotionLoader(user)
    pages = notion_loader.get_all_page

    # page count save
    is_valid = NotionValidator.validate(user, pages)
    if not is_valid:
        NotionSyncStatusService(user).to_stop()

        raise CustomException(
            **NotionValidErrorSchema(
                error_code=NotionValidErrorEnum.notion_page_limit,
                payload=NotionValidPayloadSchema(
                    page_limit_counts=PAGE_LIMIT,
                    page_counts=len(pages),
                    notion_page_schemas=notion_loader.get_workspace_pages_and_counts()
                )
            ).dict()
        )

    # background sync
    try:
        NotionSyncStatusService(user).save_total_page_count(len(pages))
        notion_document_schemas = NotionLoader(user).overall_process(pages)
        NotionSync(user, notion_document_schemas).overall_process()
        NotionSyncStatusService(user).to_stop()
    except Exception as e:
        print(e)
        NotionSyncStatusService(user).to_stop()


@api.post(
    path="source/notion/delete/",
    tags=[ApiTagEnum.source]
)
def notion_delete(request):
    user = request.user
    NotionDocumentService(user).delete_all_documents()


@api.get(
    path="source/notion/pages/",
    response={200: List[NotionPageDTO]},
    tags=[ApiTagEnum.source]
)
def get_pages(request):
    user = request.user
    notion_page_qs = user.notionpage_set.filter(is_workspace=True).order_by("-modified").all()
    return NotionPageDTO.from_notion_page_qs(notion_page_qs)


@api.get(
    path="source/status/",
    response={200: List[SyncStatusSchema]},
    tags=[ApiTagEnum.source]
)
def source_status(request):
    user = request.user
    data_sync_status_qs = user.datasyncstatus_set.all()
    return SyncStatusSchema.from_instances(data_sync_status_qs)
