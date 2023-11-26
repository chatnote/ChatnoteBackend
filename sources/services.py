from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.utils.functional import cached_property

from chats.services import get_num_tokens_from_text
from sources.constants import NOTION_PAGE_LIMIT
from sources.loaders.drives import GoogleDriveLoader
from sources.loaders.gmails import GoogleGmailLoader
from sources.loaders.google_calendars import GoogleCalendarLoader
from sources.loaders.notion import NotionUserLoader
from sources.loaders.slacks import SlackLoader
from sources.models import DataSyncStatus, NotionPage, DataSource

from typing import List

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from cores.elastics.clients import ChunkedContextClient, OriginalContextClient
from sources.schemas import OriginalDocumentSchema, NotionPageSchema
from sources.enums import DataSourceEnum
from sources.models import OriginalDocument


class NotionSplitter:
    @classmethod
    def splitter_by_len(cls):
        return RecursiveCharacterTextSplitter(
            chunk_size=200,
            chunk_overlap=30,
            length_function=len,
        )

    @classmethod
    def splitter_by_token(cls):
        # 한글과 영어에 포함된 문장 개수가 차이남. 영어 임베딩 성능이 떨어짐.
        return RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=500, chunk_overlap=0)

    @classmethod
    def split(cls, notion_chunked_schemas: [OriginalDocumentSchema]) -> List[Document]:
        text_splitter = cls.splitter_by_len()

        documents = [Document(
            page_content=document.text,
            metadata=document.dict(exclude={"text"})
        ) for document in notion_chunked_schemas]

        docs = text_splitter.split_documents(documents)
        return docs


class NotionValidator:
    @staticmethod
    def validate(user, pages: List[dict]):
        if len(pages) <= NOTION_PAGE_LIMIT:
            return True
        else:
            return False


class NotionService:
    def __init__(self, user):
        self.user = user
        self.original_client = OriginalContextClient()
        self.chunked_client = ChunkedContextClient()
        self.data_source = DataSource.objects.get(source=DataSourceEnum.notion)

    @staticmethod
    def _url_2_notion_page_schema(notion_page_schemas: List[NotionPageSchema]):
        url_2_notion_page_schema = {}
        for page_schema in notion_page_schemas:
            url_2_notion_page_schema[page_schema.url] = page_schema
        return url_2_notion_page_schema

    def _notion_page_schemas_2_original_document_schemas(self, notion_page_schemas: List[NotionPageSchema]):
        return [
            OriginalDocumentSchema(
                user_id=self.user.id,
                data_source_type=DataSourceEnum.notion,
                url=document.url,
                title=document.title,
                text=document.text,
                text_hash=document.text_hash
            ) for document in notion_page_schemas
        ]

    def create_documents(self, notion_page_schemas: List[NotionPageSchema]):
        original_document_qs_list = [OriginalDocument(
            user_id=self.user.id,
            url=page.url,
            title=page.title,
            text=page.text,
            text_hash=page.text_hash,
            source=DataSourceEnum.notion,
            data_source=self.data_source
        ) for page in notion_page_schemas]
        OriginalDocument.objects.bulk_create(original_document_qs_list)

        original_document_schemas = self._notion_page_schemas_2_original_document_schemas(notion_page_schemas)
        self.create_original_contexts(original_document_schemas)
        self.create_chunked_contexts(original_document_schemas)

        notion_page_qs_list = [
            NotionPage(
                user=self.user,
                url=item.url,
                page_id=item.page_id,
                title=item.title,
                icon=item.icon,
                is_workspace=item.is_workspace
            ) for item in notion_page_schemas]
        NotionPage.objects.bulk_create(notion_page_qs_list)

    def update_documents(self, notion_page_schemas: List[NotionPageSchema]):
        url_2_notion_page_schema = self._url_2_notion_page_schema(notion_page_schemas)
        notion_document_qs = self.user.originaldocument_set.filter(url__in=url_2_notion_page_schema.keys())
        for notion_document in notion_document_qs:
            notion_document.title = url_2_notion_page_schema[notion_document.url].title
            notion_document.text = url_2_notion_page_schema[notion_document.url].text
            notion_document.text_hash = url_2_notion_page_schema[notion_document.url].text_hash
        OriginalDocument.objects.bulk_update(notion_document_qs, ["title", "text", "text_hash"])

        original_document_schemas = self._notion_page_schemas_2_original_document_schemas(notion_page_schemas)
        self.update_original_contexts(original_document_schemas)
        self.update_chunked_contexts(original_document_schemas)

        notion_page_for_update_qs = self.user.notionpage_set.filter(url=url_2_notion_page_schema.keys()).all()
        for notion_page in notion_page_for_update_qs:
            notion_page.title = url_2_notion_page_schema[notion_page.url].title
            notion_page.icon = url_2_notion_page_schema[notion_page.url].icon
            notion_page.is_workspace = url_2_notion_page_schema[notion_page.url].is_workspace
        NotionPage.objects.bulk_update(notion_page_for_update_qs, ['title', 'icon', 'is_workspace'])

    def delete_documents(self, document_urls: List[str]):
        self.user.originaldocument_set.filter(url__in=document_urls).all().delete()
        self.original_client.delete_documents(self.user, document_urls)
        self.chunked_client.delete_documents(self.user, document_urls)
        self.user.notionpage_set.filter(url__in=document_urls).all().delete()

    def delete_all_documents(self):
        self.user.originaldocument_set.all().delete()
        self.user.notionpage_set.all().delete()
        self.original_client.delete_documents(self.user)
        self.chunked_client.delete_documents(self.user)

    def create_chunked_contexts(self, original_document_schemas: List[OriginalDocumentSchema]):
        original_document_schemas = [item for item in original_document_schemas if get_num_tokens_from_text(item.text) > 10]
        chunked_documents = NotionSplitter.split(original_document_schemas)

        self.chunked_client.create_documents(chunked_documents)

    def update_chunked_contexts(self, original_document_schemas: List[OriginalDocumentSchema]):
        document_urls = [document.url for document in original_document_schemas]
        if document_urls:
            self.chunked_client.delete_documents(self.user, document_urls)
        self.create_chunked_contexts(original_document_schemas)

    def create_original_contexts(self, original_document_schemas: List[OriginalDocumentSchema]):
        self.original_client.bulk_create(original_document_schemas)

    def update_original_contexts(self, original_document_schemas: List[OriginalDocumentSchema]):
        document_urls = [document.url for document in original_document_schemas]
        if document_urls:
            self.original_client.delete_documents(self.user, document_urls)
        self.create_original_contexts(original_document_schemas)


class NotionSync:
    def __init__(self, user, notion_page_schemas: List[NotionPageSchema]):
        self.user = user
        self.notion_page_schemas = notion_page_schemas
        self.notion_document_service = NotionService(self.user)
        self.new_document_urls = [notion_document.url for notion_document in notion_page_schemas]
        self.new_text_hashes = [notion_document.text_hash for notion_document in notion_page_schemas]
        self.original_client = OriginalContextClient()
        self.chunked_client = ChunkedContextClient()

    def overall_process(self, total_page_urls):
        # notion text update
        self.create_documents()
        self.update_documents()
        self.delete_documents(total_page_urls)

    def create_documents(self):
        documents_for_create = [
            document for document in self.notion_page_schemas if document.url not in self.saved_document_urls
        ]
        if documents_for_create:
            self.notion_document_service.create_documents(documents_for_create)
        print(f"documents for create: {len(documents_for_create)}개")
        return documents_for_create

    def update_documents(self):
        existed_document_urls = list(set(self.saved_document_urls) & set(self.new_document_urls))
        changed_text_hashes = list(set(self.new_text_hashes) - set(self.saved_text_hashes))

        document_urls_for_update = list(self.user.originaldocument_set.filter(
            url__in=existed_document_urls,
            text_hash__in=changed_text_hashes
        ).values_list("url", flat=True))

        documents_for_update = [
            document for document in self.notion_page_schemas if document.url in document_urls_for_update
        ]
        if documents_for_update:
            self.notion_document_service.update_documents(documents_for_update)
            print(f"documents for update: {len(documents_for_update)}개")
        else:
            print(f"documents for exists: {len(existed_document_urls)}개")
        return documents_for_update

    def delete_documents(self, total_page_urls: list):
        document_urls = list(set(self.saved_document_urls) - set(total_page_urls))
        if document_urls:
            self.notion_document_service.delete_documents(document_urls)
        print(f"documents_for_delete: {len(document_urls)}개")
        return document_urls

    @cached_property
    def saved_document_urls(self):
        return list(self.user.originaldocument_set.values_list("url", flat=True))

    @cached_property
    def saved_text_hashes(self):
        return list(self.user.originaldocument_set.values_list("text_hash", flat=True))


class NotionSyncStatusService:
    def __init__(self, user):
        self.user = user

    @transaction.atomic
    def get_or_create_sync_status(self):
        try:
            sync_status = self.user.datasyncstatus_set.get(data_source__source=DataSourceEnum.notion)
        except DataSyncStatus.DoesNotExist:
            email = NotionUserLoader(self.user).get_email()
            sync_status = DataSyncStatus.objects.create(
                user=self.user,
                account_name=email,
                data_source=DataSource.objects.get(source=DataSourceEnum.notion)
            )
        return sync_status

    @transaction.atomic
    def save_current_page_count(self, count: int):
        sync_status = self.get_or_create_sync_status()
        sync_status.cur_page_count = sync_status.cur_page_count + count
        sync_status.save()

    @transaction.atomic
    def to_running(self, count: int):
        sync_status = self.get_or_create_sync_status()
        sync_status.total_page_count = count
        sync_status.cur_page_count = 0
        sync_status.save()

    @transaction.atomic
    def to_stop(self):
        sync_status = self.get_or_create_sync_status()
        sync_status.last_sync_datetime = datetime.now()
        sync_status.save()


class GmailSyncStatusService:
    def __init__(self, user):
        self.user = user

    @transaction.atomic
    def get_or_create_sync_status(self):
        try:
            sync_status = self.user.datasyncstatus_set.get(data_source__source=DataSourceEnum.gmail)
        except DataSyncStatus.DoesNotExist:
            account = GoogleGmailLoader(self.user).get_account_info()
            email = account["email"]
            sync_status = DataSyncStatus.objects.create(
                user=self.user,
                account_name=email,
                data_source=DataSource.objects.get(source=DataSourceEnum.gmail),
                last_sync_datetime=datetime.now()
            )
        return sync_status


class GoogleDriveSyncStatusService:
    def __init__(self, user):
        self.user = user

    @transaction.atomic
    def get_or_create_sync_status(self):
        try:
            sync_status = self.user.datasyncstatus_set.get(data_source__source=DataSourceEnum.google_drive)
        except DataSyncStatus.DoesNotExist:
            account = GoogleDriveLoader(self.user).get_account_info()
            email = account["email"]
            sync_status = DataSyncStatus.objects.create(
                user=self.user,
                account_name=email,
                data_source=DataSource.objects.get(source=DataSourceEnum.google_drive),
                last_sync_datetime=datetime.now()
            )
        return sync_status


class GoogleCalendarSyncStatusService:
    def __init__(self, user):
        self.user = user

    @transaction.atomic
    def get_or_create_sync_status(self):
        try:
            sync_status = self.user.datasyncstatus_set.get(data_source__source=DataSourceEnum.google_calendar)
        except DataSyncStatus.DoesNotExist:
            account = GoogleCalendarLoader(self.user).get_account_info()
            email = account["email"]
            sync_status = DataSyncStatus.objects.create(
                user=self.user,
                account_name=email,
                data_source=DataSource.objects.get(source=DataSourceEnum.google_calendar),
                last_sync_datetime=datetime.now()
            )
        return sync_status


class SlackSyncStatusService:
    def __init__(self, user):
        self.user = user

    @transaction.atomic
    def get_or_create_sync_status(self):
        try:
            sync_status = self.user.datasyncstatus_set.get(data_source__source=DataSourceEnum.slack)
        except DataSyncStatus.DoesNotExist:
            account = SlackLoader(self.user).get_account_info()
            real_name = account["profile"]["real_name"]
            sync_status = DataSyncStatus.objects.create(
                user=self.user,
                account_name=real_name,
                data_source=DataSource.objects.get(source=DataSourceEnum.slack),
                last_sync_datetime=datetime.now()
            )
        return sync_status
