import time
import openai
from loguru import logger
from openai import OpenAI

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.LLMSetting import LLMSetting

# TODO: Modify the api_key and api_base
api_key = ""
api_base = ""

def invoke(prompt: str, temp: float, maxTokens: int = 4096, topP: float = 1.0, api: str = 'openai', model: str = 'gpt-3.5-turbo', sys_prompt: str = '', n = 1):
    while True:
        if api == 'openai':
            openai.api_key = api_key
            openai.api_base = api_base
            logger.debug(f'Chosen API key: {openai.api_key}')
            client = openai.OpenAI(api_key=openai.api_key, base_url=openai.api_base)
            logger.debug(f'API({api}) start... temp={temp}, Top_p={topP}, Max_tokens={maxTokens}, model={model}')
            start_time = time.time()
            try:
                completion = client.chat.completions.create(
                    model=model,
                    temperature=temp,
                    top_p=topP,
                    n = n,
                    max_tokens=maxTokens,
                    messages=[
                        {"role": "system",
                         "content": sys_prompt},
                        {"role": "user",
                         "content": prompt}
                    ]
                )
                logger.debug(f'LLM({api}) Done in {time.time() - start_time:.2f}s')
                if n == 1:
                    response = completion.choices[0].message.content
                elif n > 1:
                    response = [choice.message.content for choice in completion.choices]
                break
            except Exception as e:
                logger.error(f'LLM({api}) Exception {e}')
                time.sleep(20)


    return response

def invoke_deepseek(prompt: str,
           temp: float,
           maxTokens: int = 4096,
           topP: float = 1.0,
           sys_prompt: str = '',
           n: int = 1):
    while True:
        model: str = 'deepseek'
        engine: str = 'deepseek-ai/deepseek-r1'
        api_key: str = ""
        api_base: str = ""
        try:
            client = OpenAI(api_key=api_key, base_url=api_base)
            logger.debug(f'Chosen API key: {api_key}')
            logger.debug(
                f'LLM({model}) start... temp={temp}, Top_p={topP}, Max_tokens={maxTokens}, engine={engine}')

            start_time = time.time()
            completion = client.chat.completions.create(
                model=engine,
                temperature=temp,
                top_p=topP,
                n=n,
                max_tokens=maxTokens,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            logger.debug(f'LLM({model}) Done in {time.time() - start_time:.2f}s')

            if n == 1:
                response = completion.choices[0].message.content
            elif n > 1:
                response = [choice.message.content for choice in completion.choices]

            break

        except Exception as e:
            logger.error(f'LLM({model}) Exception: {e}')
            time.sleep(20)

    return response


def get_text_embedding(text, model='text-embedding-ada-002'):
    try:
        openai.api_key = api_key
        openai.api_base = api_base
        client = openai.OpenAI(api_key=openai.api_key, base_url=openai.api_base)
        response = client.embeddings.create(
            model=model,
            input=text
        )

        embedding = response.data[0].embedding
        return embedding

    except Exception as e:
        print(f"Failed to get text embedding: {e}")
        return None