from chats.enums import ChatMessageEnum
from chats.schemas import ChatQueryParams, ChatReferenceSchema, ChatResponseDTO
from chats.services import RetrievalService, ChatHistoryService, ChatService
from cores.apis import api, test_api
from cores.enums import ApiTagEnum


# Create your views here.


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

    # condense question
    condensed_query = chat_service.get_condensed_query(query)

    # retrieve docs
    search_response_schemas = retrieval_service.search(condensed_query)

    # retrieve history
    if not session_id:
        session = retrieval_service.create_session()
        session_id = session.id
    chat_messages = retrieval_service.get_chat_messages(session_id)

    # generate response
    response = chat_service.generate_response(query, search_response_schemas, chat_messages)
    recommend_queries = chat_service.generate_recommend_queries(query)

    chat_response_schema = ChatResponseDTO(
        session_id=session_id,
        query=query,
        response=response,
        references=[ChatReferenceSchema(
            title=item.title,
            url=item.url,
            source=item.source
        ) for item in search_response_schemas],
        recommend_queries=recommend_queries
    )

    chat_history_service.add_history(
        session_id=session_id,
        content=query,
        message_type=ChatMessageEnum.ai,
        recommend_queries=recommend_queries,
        original_document_ids=[item.original_document_id for item in search_response_schemas]
    )

    return chat_response_schema


@test_api.post(
    path="chat/history/",
    tags=[ApiTagEnum.chat]
)
def chat(request):
    user = request.user
    session_id = None
    ChatHistoryService(user).get_history(session_id)
