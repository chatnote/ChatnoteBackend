from cores.enums import CustomEnum


class DataSourceEnum(CustomEnum):
    notion = 'notion'


class NotionValidErrorEnum(CustomEnum):
    notion_page_limit = 'notion_page_limit'
