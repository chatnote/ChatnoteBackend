from typing import List

from django.conf import settings
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.vectorstores import ElasticsearchStore

from cores.elastics.mappings import original_index_mappings, chunk_index_mappings
from cores.schemas import OriginalContext


class OriginalContextClient:
    def __init__(self):
        self.search_client = ElasticsearchStore.connect_to_elasticsearch(
            cloud_id=settings.ES_CLOUD_ID,
            username=settings.ES_USER,
            password=settings.ES_PASSWORD
        )
        self.index = settings.ORIGINAL_DOCUMENT_INDEX

    def create_index(self, index=None):
        if index:
            self.index = index
        is_index = self.search_client.indices.exists(index=self.index).body
        if not is_index:
            return self.search_client.indices.create(index=self.index, mappings=original_index_mappings)

    def delete_index(self):
        self.search_client.indices.delete(index=self.index)

    def add_documents(self, original_contexts: List[OriginalContext]):
        for context in original_contexts:
            self.search_client.index(
                index=settings.ORIGINAL_DOCUMENT_INDEX,
                id=context.id,  # url 을 document id 로 설정
                document=context.dict()
            )

    def delete_all_documents(self, user):
        delete_query = {
            "query": {
                "match": {
                    "user_id": user.id
                }
            }
        }
        self.search_client.delete_by_query(index=self.index, body=delete_query)

    def refresh_index(self):
        self.search_client.indices.refresh(index=self.index)

    def search_by_ids(self, document_ids: List[str]) -> List[OriginalContext]:
        response = self.search_client.search(
            index=self.index,
            query={
                "ids": {
                    "values": document_ids
                },
            },
            sort=[
                {
                    "_doc": "asc"
                }
            ]
        )

        original_contexts = []
        for item in response.body['hits']['hits']:
            original_contexts.append(OriginalContext.from_dict(item['_source']))
        return original_contexts

    def get_document_ids(self, user):
        document_ids = []
        while True:
            response = self.search_client.search(
                index=self.index,
                source_includes=[],
                size=5,
                query={
                    "bool": {
                        "filter": {
                            "term": {"user_id": user.id}
                        }
                    }
                },
                sort=[
                    {"id": "asc"}
                ],
                search_after=[document_ids[-1]] if document_ids else None
            )
            if not response.body["hits"]["hits"]:
                break
            for item in response.body["hits"]["hits"]:
                document_ids.append(item["_id"])
        return document_ids

    def unchanged_document_ids(self, user, document_ids: List[str], text_hashes: List[str]):
        return self.search_client.search(
            index=self.index,
            query={
                "ids": {
                    "values": document_ids
                },
                "bool": {
                    "filter": [
                        {"term": {"user_id": user.id}},
                        {"terms": {"text_hash": text_hashes}},
                    ],
                }
            }
        )


class ChunkedContextClient:
    def __init__(self):
        self.embedding = OpenAIEmbeddings()
        self.index = settings.CHUNKED_DOCUMENT_INDEX
        self.vector_client = ElasticsearchStore(
            es_cloud_id=settings.ES_CLOUD_ID,
            index_name=self.index,
            embedding=self.embedding,
            es_user=settings.ES_USER,
            es_password=settings.ES_PASSWORD
        )
        self.search_client = ElasticsearchStore.connect_to_elasticsearch(
            cloud_id=settings.ES_CLOUD_ID,
            username=settings.ES_USER,
            password=settings.ES_PASSWORD
        )

    def create_index(self):
        is_index = self.search_client.indices.exists(index=self.index).body
        if not is_index:
            self.search_client.indices.create(index=self.index, mappings=chunk_index_mappings)

    def delete_index(self):
        self.search_client.indices.delete(index=self.index)

    def create_documents(self, chunked_documents: List[Document]):
        ElasticsearchStore.from_documents(
            chunked_documents,
            self.embedding,
            es_cloud_id=settings.ES_CLOUD_ID,
            es_user=settings.ES_USER,
            es_password=settings.ES_PASSWORD,
            index_name=self.index
        )

    def delete_documents(self, user, document_urls=None):
        if document_urls:
            query = {
                "bool": {
                    "filter": [
                        {
                            "match": {
                                "metadata.user_id": user.id
                            }
                        },
                        {
                            "terms": {
                                "metadata.url": document_urls
                            }
                        }
                    ]
                }
            }
        else:
            query = {
                "term": {
                    "metadata.user_id": user.id
                }
            }

        return self.search_client.delete_by_query(
            index=self.index,
            query=query
        )

    def refresh_index(self):
        self.search_client.indices.refresh(index=self.index)

    def similarity_search(self, query: str, user_id: int) -> List[Document]:
        results = self.vector_client.similarity_search_with_score(
            query,
            filter=[{"match": {"metadata.user_id": str(user_id)}}],
            k=4
        )

        return [doc for doc, score in results if score > 0.9]
