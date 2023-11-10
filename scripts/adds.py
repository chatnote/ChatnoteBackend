from sources.enums import DataSourceEnum
from sources.models import DataSource


def create_data_source():
    DataSource.objects.create(
        source=DataSourceEnum.notion,
        name="Notion",
        description="노션의 정보를 연동해보세요. 노션의 파일과 AI를 통해 소통할 수 있습니다.",
        icon="",
        limit_count=500,
        is_available=True
    )
    DataSource.objects.create(
        source=DataSourceEnum.google_calendar,
        name="Google Calendar",
        description="구글 캘린더를 연동해보세요. 캘린더 내 일정과 메모 등에 대해 AI와 소통할 수 있습니다.",
        icon="",
        is_available=False
    )
    DataSource.objects.create(
        source=DataSourceEnum.gmail,
        name="Gmail",
        description="지메일을 연동해보세요. 메일 내용을 바탕으로 AI와 소통할 수 있습니다.",
        icon="",
        is_available=False
    )
    DataSource.objects.create(
        source=DataSourceEnum.google_drive,
        name="Gmail",
        description="구글 드라이브를 연동해보세요. 드라이브 내 파일과 AI를 통해 소통할 수 있습니다.",
        icon="",
        is_available=False
    )
