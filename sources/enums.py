from cores.enums import CustomEnum


class DataSourceEnum(CustomEnum):
    notion = 'notion'
    google_calendar = 'google_calendar'
    gmail = 'gmail'
    google_drive = 'google_drive'
    slack = 'slack'
    github = 'github'


class NotionValidErrorEnum(CustomEnum):
    notion_page_limit = 'notion_page_limit'
