from typing_extensions import List
from zappa.asynchronous import task

from sources.loaders.notion import NotionLoader
from sources.services import NotionSyncStatusService, NotionSync
from users.models import User


@task
def sync_notion_task(pages: List[dict], user_id: int, total_page_urls: list):
    user = User.objects.get(id=user_id)
    notion_document_schemas = NotionLoader(user).overall_process(pages)

    notion_sync = NotionSync(user, notion_document_schemas)
    try:
        notion_sync.overall_process(total_page_urls)
        NotionSyncStatusService(user).save_current_page_count(len(pages))
    except Exception:
        NotionSyncStatusService(user).save_current_page_count(len(pages))
