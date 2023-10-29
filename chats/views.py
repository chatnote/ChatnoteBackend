import concurrent.futures
import time

from chats.enums import ChatMessageEnum
from chats.schemas import ChatQueryParams, ChatReferenceSchema, ChatResponseDTO, ChatEvalParams
from chats.services import RetrievalService, ChatHistoryService, ChatService
from cores.apis import api, test_api
from cores.enums import ApiTagEnum
from cores.utils import print_execution_time


def test(chat_service, retrieval_service, query, chat_messages):
    # condense question
    condensed_query = chat_service.get_condensed_query(query)

    # retrieve docs
    search_response_schemas = retrieval_service.search(condensed_query)

    # generate response
    response = chat_service.generate_response(query, search_response_schemas, chat_messages)

    return response, search_response_schemas


@api.post(
    path="chat/",
    response={200: ChatResponseDTO},
    tags=[ApiTagEnum.chat],
)
def chat(request, params: ChatQueryParams):
    user = request.user
    session_id = params.session_id
    query = params.query
    chat_service = ChatService()
    retrieval_service = RetrievalService(user=user)
    chat_history_service = ChatHistoryService(user=user)

    chat_history_service.add_history(session_id, content=query, message_type=ChatMessageEnum.human)

    # retrieve history
    if not session_id:
        session = retrieval_service.create_session()
        session_id = session.id
    chat_messages = retrieval_service.get_chat_messages(session_id)

    # result = {}
    # with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    #     # Start the load operations and mark each future with its URL
    #     future_to_num = {
    #         executor.submit(test, chat_service, retrieval_service, query, chat_messages): 1,
    #         executor.submit(chat_service.generate_recommend_queries, query): 2
    #     }
    #     for future in concurrent.futures.as_completed(future_to_num):
    #         num = future_to_num[future]
    #
    #         result[num] = future.result()
    #
    # response = result[1][0]
    # search_response_schemas = result[1][1]
    # recommend_queries = result[2]
    # print(f"Time: {time.time() - a}")

    # condense question
    condensed_query = chat_service.get_condensed_query(query)

    # retrieve docs
    search_response_schemas = retrieval_service.search(condensed_query)

    # generate response
    response = chat_service.generate_response(query, search_response_schemas, chat_messages)

    # recommend queries
    recommend_queries = chat_service.generate_recommend_queries(query)

    chat_history_response = chat_history_service.add_history(
        session_id=session_id,
        content=response,
        message_type=ChatMessageEnum.ai,
        recommend_queries=recommend_queries,
        original_document_ids=[item.original_document_id for item in search_response_schemas]
    )

    chat_response_schema = ChatResponseDTO(
        session_id=session_id,
        chat_history_id=chat_history_response.id,
        query=query,
        response=response,
        references=[ChatReferenceSchema(
            title=item.title,
            url=item.url,
            source=item.source
        ) for item in search_response_schemas],
        recommend_queries=recommend_queries
    )

    return chat_response_schema


@api.post(
    path="chat/eval/good/",
    response={200: None},
    tags=[ApiTagEnum.chat]
)
def chat_eval_good(request, params: ChatEvalParams):
    user = request.user
    chat_history = user.chathistory_set.get(id=params.chat_history_id)
    chat_history.eval_choice = 1
    chat_history.eval_message = params.message
    chat_history.save()


@api.post(
    path="chat/eval/bad/",
    response={200: None},
    tags=[ApiTagEnum.chat]
)
def chat_eval_bad(request, params: ChatEvalParams):
    user = request.user
    chat_history = user.chathistory_set.get(id=params.chat_history_id)
    chat_history.eval_choice = -1
    chat_history.eval_message = params.message
    chat_history.save()


@test_api.post(
    path="chat/history/",
    response={200: None},
    tags=[ApiTagEnum.chat]
)
def chat(request):
    user = request.user
    session_id = None
    ChatHistoryService(user).get_history_qs(session_id)
