import os
from typing import List, Union

import openai
import tiktoken
from django.db.models import When, Case, F
from langchain.callbacks import get_openai_callback
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.output_parsers import PydanticOutputParser, CommaSeparatedListOutputParser
from langchain.prompts import PromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate
from langchain.schema import AIMessage, StrOutputParser, HumanMessage, SystemMessage

from chats.enums import ChatMessageEnum
from chats.models import ChatHistory, ChatSession
from chats.prompts import SUGGESTED_QUESTIONS_AFTER_ANSWER_INSTRUCTION_PROMPT, CONDENSED_QUERY_PROMPT_v1, \
    CHAT_GENERATE_WITH_CONTEXT_SYSTEM_PROMPT, IS_PRIVATE_PROMPT, CHAT_GENERATE_SYSTEM_PROMPT, \
    ABLE_TO_KNOW_INTENT_QUERY_PROMPT, CONDENSED_QUERY_PROMPT_v2, CHAT_GENERATE_WITH_NO_CONTEXT_SYSTEM_PROMPT
from chats.schemas import SearchResponseSchema
from cores.elastics.clients import ChunkedContextClient
from cores.utils import print_token_summary, print_execution_time
from sources.enums import DataSourceEnum


openai.api_key = os.getenv("OPENAI_API_KEY")


def get_num_tokens_from_text(text: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(text))
    return num_tokens


class ChatService:
    def __init__(self):
        self.model_gpt35_turbo = ChatOpenAI(temperature=0.1)
        self.model_gpt35_turbo_16k = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=0.1)

    @print_token_summary
    @print_execution_time
    def get_condensed_query(self, query, chat_messages):
        prompt = ChatPromptTemplate.from_messages([
            ("human", CONDENSED_QUERY_PROMPT_v1),
        ])
        print(prompt)
        runnable = prompt | self.model_gpt35_turbo | StrOutputParser()
        return runnable.invoke({"query": query, "conversation": chat_messages})

    def is_intentional_of_query(self, query, chat_messages):
        chat_messages.insert(0, SystemMessage(content=ABLE_TO_KNOW_INTENT_QUERY_PROMPT))
        chat_messages.append(HumanMessage(content=query))

        runnable = self.model_gpt35_turbo | StrOutputParser()
        intentional = runnable.invoke(chat_messages)
        if intentional == "known":
            return True
        else:
            return False

    @print_token_summary
    @print_execution_time
    def is_private_of_query(self, query, chat_messages):
        # prompt = ChatPromptTemplate.from_messages([
        #     ("human", IS_PRIVATE_PROMPT)
        # ])
        #
        # runnable = prompt | self.model_gpt35_turbo | StrOutputParser()
        # result = runnable.invoke({"query": query})

        chat_messages.append(HumanMessage(content=IS_PRIVATE_PROMPT.format(query=query)))
        runnable = self.model_gpt35_turbo | StrOutputParser()
        result = runnable.invoke(chat_messages)
        if result == "private":
            return True
        else:
            return False

    @classmethod
    def _get_original_context_from_search(cls, search_response_schemas: List[SearchResponseSchema]) -> str:
        result = ""
        for i, search_response in enumerate(search_response_schemas):
            result += f"<doc id={i}>{search_response.original_text}</doc>\n"
        result = f"<context>\n{result}</context>"
        return result

    @classmethod
    def _get_chunked_context_from_search(cls, search_response_schemas: List[SearchResponseSchema]) -> str:
        result = ""
        for i, search_response in enumerate(search_response_schemas):
            result += f"<doc id={i}>{search_response.chunked_text}</doc>\n"
        result = f"<context>\n{result}</context>"
        return result

    @staticmethod
    def is_valid_token_limit(messages, counts: int):
        total_content = ""
        for message in messages:
            total_content += message.content

        total_tokens = get_num_tokens_from_text(total_content)
        print(f"total num tokens: {total_tokens}")
        if total_tokens > counts:
            # raise CustomException(error_code="invalid_token_num_limit")
            return False
        else:
            return True

    @print_token_summary
    @print_execution_time
    def generate_response_with_context(self, query, search_response_schemas, chat_messages) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", CHAT_GENERATE_WITH_CONTEXT_SYSTEM_PROMPT),
            *chat_messages,
            ("human", query)
        ])
        original_context = self._get_original_context_from_search(search_response_schemas)
        runnable = prompt | self.model_gpt35_turbo_16k | StrOutputParser()

        try:
            return runnable.invoke({"context": original_context})
        except openai.error.InvalidRequestError:
            chunked_context = self._get_chunked_context_from_search(search_response_schemas)
            prompt = ChatPromptTemplate.from_messages([
                ("system", CHAT_GENERATE_WITH_CONTEXT_SYSTEM_PROMPT),
                *chat_messages,
                ("human", query)
            ])
            runnable = prompt | self.model_gpt35_turbo_16k | StrOutputParser()
            return runnable.invoke({"context": chunked_context})

    @print_token_summary
    @print_execution_time
    def generate_response(self, query, chat_messages) -> str:
        chat_messages.insert(0, SystemMessage(content=CHAT_GENERATE_SYSTEM_PROMPT))
        chat_messages.append(HumanMessage(content=query))
        runnable = self.model_gpt35_turbo | StrOutputParser()
        return runnable.invoke(chat_messages)

    @print_execution_time
    def generate_recommend_queries(self, query: str) -> List[str]:
        output_parser = CommaSeparatedListOutputParser()
        format_instructions = output_parser.get_format_instructions()

        prompt = ChatPromptTemplate.from_messages([
            ("human", SUGGESTED_QUESTIONS_AFTER_ANSWER_INSTRUCTION_PROMPT)
        ])

        runnable = prompt | self.model_gpt35_turbo | output_parser
        return runnable.invoke({"query": query, "format_instructions": format_instructions})


class RetrievalService:
    def __init__(self, user):
        self.user = user
        self.chunked_client = ChunkedContextClient()
        self.model = OpenAI(temperature=0)

    def search(self, query: str) -> List[SearchResponseSchema]:
        chunked_documents = self.chunked_client.similarity_search(query, self.user.id)
        search_response_schemas = []
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
            for i, item in enumerate(self.user.originaldocument_set.filter(url__in=document_urls).order_by(ordering)):
                if item.source == DataSourceEnum.notion:
                    search_response_schemas.append(SearchResponseSchema(
                        title=item.title,
                        original_document_id=item.id,
                        original_text=item.text,
                        chunked_text=chunked_texts[i],
                        url=item.url,
                        source=DataSourceEnum.notion
                    ))
        return search_response_schemas

    def create_session(self):
        session = ChatSession.objects.create(user=self.user)
        return session

    def get_chat_messages(self, session_id) -> List[tuple]:
        messages = []
        chat_history_qs = self.user.chathistory_set.filter(session_id=session_id).order_by("created")

        for chat_history in chat_history_qs:
            if chat_history.message_type == ChatMessageEnum.human:
                message = ("human", chat_history.content)
            elif chat_history.message_type == ChatMessageEnum.ai:
                message = ("ai", chat_history.content)
            else:
                continue
            messages.append(message)
        return messages


class ChatHistoryService:
    def __init__(self, user):
        self.user = user

    def get_history_qs(self, session_id: int or None):
        pass

    def add_history(
            self,
            session_id: int, content: str, message_type: ChatMessageEnum,
            recommend_queries: list = None, original_document_ids: list = None
    ):
        chat_history = ChatHistory.objects.create(
            session_id=session_id,
            user=self.user,
            message_type=message_type,
            content=content,
            recommend_queries=recommend_queries,
            original_document_ids=original_document_ids
        )
        return chat_history
