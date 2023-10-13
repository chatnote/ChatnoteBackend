from typing import List

from django.db.models import When, Case, F
from langchain.llms import OpenAI
from langchain.output_parsers import PydanticOutputParser, CommaSeparatedListOutputParser
from langchain.prompts import PromptTemplate

from chats.models import ChatHistory, ChatHistoryReference
from chats.prompts import SUGGESTED_QUESTIONS_AFTER_ANSWER_INSTRUCTION_PROMPT
from chats.schemas import ChatResponseSchema, ChatReferenceSchema
from cores.elastics.clients import OriginalContextClient, ChunkedContextClient
from cores.llms.openais import ChatCompletion
from sources.enums import DataSourceEnum


class SearchClient:
    def __init__(self, user):
        self.user = user
        self.original_client = OriginalContextClient()
        self.chunked_client = ChunkedContextClient()
        self.model = OpenAI(temperature=0)

    def generate_recommend_queries(self, query: str) -> List[str]:
        output_parser = CommaSeparatedListOutputParser()

        format_instructions = output_parser.get_format_instructions()
        system_message = "".join(SUGGESTED_QUESTIONS_AFTER_ANSWER_INSTRUCTION_PROMPT)
        prompt = PromptTemplate(
            template="{system_message}\n{format_instructions}\nquery: {query}",
            input_variables=["query"],
            partial_variables={"system_message": system_message, "format_instructions": format_instructions}
        )
        _input = prompt.format(query=query)
        output = self.model(_input)

        return output_parser.parse(output)
        # response = ChatCompletion.create(
        #     system_message="".join(SUGGESTED_QUESTIONS_AFTER_ANSWER_INSTRUCTION_PROMPT),
        #     prompt=f"""질문: {query}"""
        # )
        # return response

    @staticmethod
    def generate_response(query, chunked_texts):
        if chunked_texts:
            response = ChatCompletion.create(
                system_message="""질문과 관련있는 문서의 일부와 출처를 전달해줄거야. 문서의 일부가 질문과 관련있다면 핵심내용을 정리해주고 없으면 정리할 내용이 없다고 최대한 간략하게 응답해줘""",
                prompt=f"""질문: {query}\n관련 문서 일부들: {str(chunked_texts)}\n사용자 질문을 반복하지말고 가장 관련있는 핵심내용을 정리해줘."""
            )
        else:
            response = "질문과 관련있는 문서를 찾지 못했습니다. 다른 방법으로 질문 해주시겠어요?"

        return response

    def search(self, query: str) -> ChatResponseSchema:
        chunked_documents = self.chunked_client.similarity_search(query, self.user.id)
        chat_references = []
        document_urls = []
        chunked_texts = []

        for document in chunked_documents:
            if document.metadata["data_source_type"] == DataSourceEnum.notion:
                document_url = document.metadata["url"]

                if document_url in document_urls:
                    for idx, exist_url in enumerate(document_urls):
                        if document_url == exist_url:
                            chunked_texts[idx] = chunked_texts[idx] + f" {document.page_content}"
                else:
                    document_urls.append(document_url)
                    chunked_texts.append(document.page_content)

        if document_urls:
            ordering = Case(*[When(url=_url, then=_idx) for _idx, _url in enumerate(document_urls)])

            for item in self.user.originaldocument_set.filter(url__in=document_urls).order_by(ordering):
                if item.source == DataSourceEnum.notion:
                    chat_references.append(ChatReferenceSchema(
                        id=item.id,
                        title=item.title,
                        url=item.url,
                        source=DataSourceEnum.notion
                    ))

        response = self.generate_response(query, chunked_texts)
        recommend_queries = self.generate_recommend_queries(query)

        return ChatResponseSchema(
            query=query,
            references=chat_references,
            response=response,
            recommend_queries=recommend_queries
        )


class ChatHistoryService:
    def __init__(self, user):
        self.user = user

    def get_history(self) -> List[ChatResponseSchema]:
        chat_history_qs = self.user.chathistory_set.order_by("-created")
        chat_history_ids = list(chat_history_qs.values_list("id", flat=True))

        chat_history_2_reference_schema = {}
        chat_history_reference_qs = ChatHistoryReference.objects.filter(chat_history_id__in=chat_history_ids).annotate(
            title=F("original_document__title"),
            url=F("original_document__url"),
            source=F("original_document__source"),
        ).all()

        for item in chat_history_reference_qs:
            if item.chat_history_id in chat_history_2_reference_schema:
                chat_history_2_reference_schema[item.chat_history_id].append(
                    ChatReferenceSchema(
                        id=item.original_document_id,
                        title=item.title,
                        url=item.url,
                        source=item.source,
                    )
                )
            else:
                chat_history_2_reference_schema[item.chat_history_id] = [
                    ChatReferenceSchema(
                        id=item.original_document_id,
                        title=item.title,
                        url=item.url,
                        source=item.source,
                    )
                ]

        return [ChatResponseSchema(
            query=item.query,
            response=item.response,
            recommend_queries=item.recommend_queries,
            references=chat_history_2_reference_schema[item.id]
        ) for item in chat_history_qs]

    def add_history(self, chat_response_schema: ChatResponseSchema):
        chat_history = ChatHistory.objects.create(
            user=self.user,
            query=chat_response_schema.query,
            response=chat_response_schema.response,
            recommend_queries=chat_response_schema.recommend_queries
        )
        for reference in chat_response_schema.references:
            ChatHistoryReference.objects.create(
                chat_history=chat_history,
                original_document_id=reference.id
            )
