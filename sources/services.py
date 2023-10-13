from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.utils.functional import cached_property

from sources.loaders.notion import NotionLoader
from sources.models import DataSyncStatus, NotionPage

from typing import List

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from cores.elastics.clients import ChunkedContextClient
from sources.schemas import OriginalDocumentSchema
from sources.enums import DataSourceEnum
from sources.models import OriginalDocument


PAGE_LIMIT = 200


class NotionSplitter:
    @staticmethod
    def split_by_token(notion_chunked_schemas: [OriginalDocumentSchema]) -> List[Document]:

        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=500, chunk_overlap=0)

        documents = [Document(
            page_content=document.text,
            metadata=document.dict(exclude={"text"})
        ) for document in notion_chunked_schemas]

        docs = text_splitter.split_documents(documents)
        return docs


class NotionValidator:
    @staticmethod
    def validate(user, pages: List[dict]):
        # if user.email in settings.ACCESS_ALLOWED_EMAILS:
        #     return True
        if len(pages) <= PAGE_LIMIT:
            return True
        else:
            return False


class NotionDocumentService:
    def __init__(self, user):
        self.user = user
        self.chunked_client = ChunkedContextClient()

    def create_documents(self, notion_document_schemas: List[OriginalDocumentSchema]):
        notion_document_list = [OriginalDocument(
            user_id=document.user_id,
            url=document.url,
            title=document.title,
            text=document.text,
            text_hash=document.text_hash,
            source=DataSourceEnum.notion
        ) for document in notion_document_schemas]
        OriginalDocument.objects.bulk_create(notion_document_list)

        self.create_chunked_documents(notion_document_schemas)

    def update_documents(self, notion_document_schemas: List[OriginalDocumentSchema]):
        url_2_document = {}
        for document in notion_document_schemas:
            url_2_document[document.url] = document

        notion_document_qs = self.user.originaldocument_set.filter(url__in=url_2_document.keys())

        for notion_document in notion_document_qs:
            notion_document.title = url_2_document[notion_document.url].title
            notion_document.text = url_2_document[notion_document.url].text
            notion_document.text_hash = url_2_document[notion_document.url].text_hash

        OriginalDocument.objects.bulk_update(notion_document_qs, ["title", "text", "text_hash"])
        self.update_chunked_documents(notion_document_schemas)

    def delete_documents(self, document_urls: List[str]):
        self.user.originaldocument_set.filter(url__in=document_urls).all().delete()
        self.chunked_client.delete_documents(self.user, document_urls)

    def delete_all_documents(self):
        self.user.originaldocument_set.all().delete()
        self.user.notionpage_set.all().delete()
        self.chunked_client.delete_documents(self.user)

    def create_chunked_documents(self, notion_document_schemas: List[OriginalDocumentSchema]):
        chunked_documents = NotionSplitter.split_by_token(notion_document_schemas)

        self.chunked_client.create_documents(chunked_documents)

    def update_chunked_documents(self, notion_document_schemas: List[OriginalDocumentSchema]):
        document_urls = [document.url for document in notion_document_schemas]
        if document_urls:
            self.chunked_client.delete_documents(self.user, document_urls)
        self.create_chunked_documents(notion_document_schemas)


class NotionPageService:
    def __init__(self, user):
        self.user = user

    @transaction.atomic
    def create_or_update_pages(self):
        self.user.notionpage_set.all().delete()

        notion_page_schemas = NotionLoader(self.user).get_pages_and_counts()
        notion_page_for_create = []

        for item in notion_page_schemas:
            notion_page_for_create.append(NotionPage(
                user=self.user,
                url=item.url,
                page_id=item.page_id,
                title=item.title,
                icon=item.icon,
                is_workspace=item.is_workspace
            ))

        NotionPage.objects.bulk_create(notion_page_for_create)


class NotionSync:
    def __init__(self, user, notion_document_schemas: List[OriginalDocumentSchema]):
        self.user = user
        self.notion_document_schemas = notion_document_schemas
        self.notion_document_service = NotionDocumentService(self.user)
        self.new_document_urls = [notion_document.url for notion_document in notion_document_schemas]
        self.new_text_hashes = [notion_document.text_hash for notion_document in notion_document_schemas]
        self.chunked_client = ChunkedContextClient()

    def overall_process(self):
        # notion text update
        self.create_documents()
        self.update_documents()
        self.delete_documents()
        self.chunked_client.refresh_index()

        # notion page update
        NotionPageService(self.user).create_or_update_pages()

    def create_documents(self):
        documents_for_create = [document for document in self.notion_document_schemas if document.url not in self.saved_document_urls]
        if documents_for_create:
            self.notion_document_service.create_documents(documents_for_create)
        print(f"documents_for_create: {len(documents_for_create)}개")

    def update_documents(self):
        existed_document_urls = list(set(self.saved_document_urls) & set(self.new_document_urls))
        changed_text_hashes = list(set(self.new_text_hashes) - set(self.saved_text_hashes))

        document_urls_for_update = list(self.user.originaldocument_set.filter(
            url__in=existed_document_urls,
            text_hash__in=changed_text_hashes
        ).values_list("url", flat=True))

        documents_for_update = [document for document in self.notion_document_schemas if document.url in document_urls_for_update]
        if documents_for_update:
            self.notion_document_service.update_documents(documents_for_update)
        print(f"documents for exists: {len(existed_document_urls)}개")
        print(f"documents_for_update: {len(documents_for_update)}개")

    def delete_documents(self):
        document_urls = list(set(self.saved_document_urls) - set(self.new_document_urls))
        if document_urls:
            self.notion_document_service.delete_documents(document_urls)
        print(f"documents_for_delete: {len(document_urls)}개")

    @cached_property
    def saved_document_urls(self):
        return list(self.user.originaldocument_set.values_list("url", flat=True))

    @cached_property
    def saved_text_hashes(self):
        return list(self.user.originaldocument_set.values_list("text_hash", flat=True))


class NotionSyncStatusService:
    def __init__(self, user):
        self.user = user

    def get_or_create_sync_status(self):
        try:
            sync_status = self.user.datasyncstatus_set.get(source=DataSourceEnum.notion)
        except DataSyncStatus.DoesNotExist:
            sync_status = DataSyncStatus.objects.create(
                user=self.user,
                source=DataSourceEnum.notion,
                is_running=True
            )
        return sync_status

    def save_current_page_count(self, count: int):
        sync_status = self.get_or_create_sync_status()
        sync_status.cur_page_count = count
        sync_status.save()

    def save_total_page_count(self, count: int):
        sync_status = self.get_or_create_sync_status()
        sync_status.total_page_count = count
        sync_status.save()

    def to_running(self):
        sync_status = self.get_or_create_sync_status()
        sync_status.is_running = True
        sync_status.save()

    def to_stop(self):
        sync_status = self.get_or_create_sync_status()
        sync_status.last_sync_datetime = datetime.now()
        sync_status.total_page_count = None
        sync_status.cur_page_count = None
        sync_status.is_running = False
        sync_status.save()
