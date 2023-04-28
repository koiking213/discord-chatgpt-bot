from dotenv import load_dotenv
import openai
from openai import ChatCompletion
import os
import time
import discord
import re
import typing
from typing import Any, List, Dict
import functools
import asyncio
import yaml

# wrapper
@typing.no_type_check
def create_chat_completion(model: str, messages: List[Dict[str, str]], stream: bool) -> Any:
    return ChatCompletion.create(model=model, messages=messages, stream=stream)


load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]
discord_token = os.environ["DISCORD_BOT_TOKEN"]
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
chat_gpt_model = config["chat_gpt_model"]
bot_name = config["bot_name"]

def to_thread(func: typing.Callable[..., Any]) -> typing.Callable[..., typing.Coroutine[Any, Any, Any]]:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

@to_thread
def get_response(content: str) -> str:
    initial_prompt="あなたは有能なアシスタントです。"

    start = time.time()
    response = create_chat_completion(
      model=chat_gpt_model,
      messages=[
            {"role": "system", "content": initial_prompt},
            {"role": "user", "content": content},
        ],
      stream=True
    )

    full_reply_content=""
    for chunk in response:
        chunk_message = chunk['choices'][0]['delta'].get('content', '')  # extract the message
        full_reply_content += chunk_message
        print(chunk_message)

    elapsed = time.time() - start
    print(f"{elapsed=}")
    return full_reply_content

class AssistantClient(discord.Client):
    async def on_ready(self) -> None:
        print(f'Logged on as {self.user}!')

    async def on_message(self, message: discord.Message) -> None:
        print(f'Message from {message.author}: {message.content}')
        if bot_name in [m.name for m in message.mentions]:
            async with message.channel.typing():
                pattern = r'^<.*?>\s'
                content = re.sub(pattern, "", message.content)
                response = await get_response(content)
                print(response)
                print(len(response))
                length = len(response)
                for i in range(((length-1)//1000)+1):
                    await message.channel.send(response[i*1000:(i+1)*1000])

def main() -> None:
    intents = discord.Intents.default()
    intents.message_content = True

    client = AssistantClient(intents=intents)
    client.run(discord_token)

if __name__ == "__main__":
    main()

