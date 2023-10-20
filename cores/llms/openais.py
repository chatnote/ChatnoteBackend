import os

import openai
from django.conf import settings

from cores.utils import print_execution_time

openai.api_key = os.getenv("OPENAI_API_KEY")


class ChatCompletion:
    @staticmethod
    @print_execution_time
    def create(system_message: str, prompt: str, model: str = "gpt-3.5-turbo"):
        completion = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        return completion.choices[0].message.content

    def __init__(self) -> None:
        pass
