from typing import List

from django.shortcuts import render

from chats.schemas import ChatQueryParams, ChatResponseSchema
from chats.services import SearchClient, ChatHistoryService
from cores.apis import api
from cores.enums import ApiTagEnum


# Create your views here.


@api.post(
    path="chat/",
    response={200: ChatResponseSchema},
    tags=[ApiTagEnum.chat],
)
def chat(request, params: ChatQueryParams):
    user = request.user
    chat_response_schema = SearchClient(user).search(params.query)
    ChatHistoryService(user).add_history(chat_response_schema)
    return chat_response_schema


@api.post(
    path="chat/history/",
    response={200: List[ChatResponseSchema]},
    tags=[ApiTagEnum.chat],
)
def chat(request):
    user = request.user
    results = ChatHistoryService(user).get_history()
    return results
