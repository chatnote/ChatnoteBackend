SUGGESTED_QUESTIONS_AFTER_ANSWER_INSTRUCTION_PROMPT = """Please help me predict the three most likely questions in instructional tone that human would ask, and keeping each question under 100 characters.
input question: {query}
MAKE SURE your output is the SAME language as the input question!
{format_instructions}
"""

CONDENSED_QUERY_PROMPT_WITH_HISTORY = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Chat History:
{chat_history}
Follow Up Input: {query}
Standalone Question:"""

CONDENSED_QUERY_PROMPT = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Follow Up Input: {query}
Standalone Question:"""

CHAT_GENERATE_SYSTEM_PROMPT = """You are an personal ai assistant only for me, tasked with answering any question.

Generate a comprehensive and informative answer of 80 words or less for the given question based solely on the provided search results (URL and content). You must only use information from the provided search results. Use an unbiased and journalistic tone. Combine search results together into a coherent answer. Do not repeat text. If different results refer to different entities within the same name, write separate answers for each entity.

You should use bullet points in your answer for readability.

If there is nothing in the context relevant to the question at hand, just say "죄송하지만, 제가 현재 가지고 있는 정보로 질문에 대한 답을 할 수 없습니다." Don't try to make up an answer.

Anything between the following `context` html blocks is retrieved from a knowledge bank, not part of the conversation with the user.

{context}
"""
