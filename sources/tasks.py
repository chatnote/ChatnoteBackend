from typing_extensions import List
from zappa.asynchronous import task

from sources.loaders.notion import NotionLoader
from sources.services import NotionSyncStatusService, NotionSync, NotionPageService
from users.models import User


@task
def sync_notion_task(user_id: int, pages: List[dict]):
    user = User.objects.get(id=user_id)

    notion_document_schemas = NotionLoader(user).overall_process(pages)
    notion_sync = NotionSync(user, notion_document_schemas)
    notion_sync.overall_process()

    NotionSyncStatusService(user).save_current_page_count(len(pages))
