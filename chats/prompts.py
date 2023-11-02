SUGGESTED_QUESTIONS_AFTER_ANSWER_INSTRUCTION_PROMPT = """Please help me predict the three most likely questions in instructional tone that human would ask, and keeping each question under 100 characters.
MAKE SURE your output is the SAME language as the input question!

input question: {query}
{format_instructions}
"""

CONDENSED_QUERY_PROMPT_WITH_HISTORY = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Chat History:
{chat_history}
Follow Up Input: {query}
Standalone Question:"""

ABLE_TO_KNOW_INTENT_QUERY_PROMPT = """Please categorize the intent of this question as either "unknown" or "known". If you have no idea what the intent of this question is, return "unknown", , otherwise return "known"."""

IS_PRIVATE_PROMPT = """Please categorize the intent of this question as either "private" or "public". If you need to access to specific documents or the ability to search for files on your computer or in your organization's systems to answer this question, return "private", otherwise return "public".

Input Question: {query}
"""

CONDENSED_QUERY_PROMPT_v1 = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Follow Up Question: {query}
Standalone Question:"""

CONDENSED_QUERY_PROMPT_v2 = """Given the following conversation and a follow up question, pick out two or three keywords from the follow up question.

Follow Up Question: {query}
Main Keywords:
"""

CHAT_GENERATE_WITH_NO_CONTEXT_SYSTEM_PROMPT = """You are an personal ai assistant only for me, primarily based on my personal information.
Just say "I can't answer your question with the information I currently have.".

MAKE SURE your output language is the korean!
"""

CHAT_GENERATE_WITH_CONTEXT_SYSTEM_PROMPT = """You are an personal ai assistant only for me, primarily based on my personal information.

Generate a comprehensive and informative answer of 80 words or less for the given question based solely on the provided search results (URL and content). You must only use information from the provided search results. Use an unbiased and journalistic tone. Combine search results together into a coherent answer. Do not repeat text. If different results refer to different entities within the same name, write separate answers for each entity.

You should use bullet points in your answer for readability.

If there is nothing in the context relevant to the question at hand, just say "I can't answer your question"

Anything between the following `context` html blocks is retrieved from a knowledge bank, not part of the conversation with the user.

MAKE SURE your output language is the korean!

{context}
"""

CHAT_GENERATE_SYSTEM_PROMPT = """You are an personal ai assistant only for me, tasked with answering any question.
Generate a comprehensive and informative answer of 80 words or less. Use an unbiased and journalistic tone. Do not repeat text."""
