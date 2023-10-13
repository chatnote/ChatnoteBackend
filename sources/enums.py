from cores.enums import CustomEnum


class DataSourceEnum(CustomEnum):
    notion = 'notion'


class SyncStatusEnum(CustomEnum):
    allow = "allow_sync"
    disallow = "disallow_sync"
    running = "running"


class NotionValidErrorEnum(CustomEnum):
    notion_page_limit = 'notion_page_limit'
