from dotenv import load_dotenv
import openai
from openai import ChatCompletion
import os
import time
import discord
import re
import typing
from typing import Any, List, Dict, Callable, Coroutine
import functools
import asyncio
import yaml
from enum import Enum
from db import DataBaseManager


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message:
    def __init__(self, role: MessageRole, content: str):
        self.role = role
        self.content = content

    def __str__(self):
        return f"{self.role.value}: {self.content}"

    def to_dict(self):
        return {"role": self.role.value, "content": self.content}


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
use_database = config["database"]["use_database"]

def to_thread(func: Callable[..., Any]) -> Callable[..., Coroutine[Any, Any, Any]]:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

class AssistantClient(discord.Client):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if use_database:
            self.db = DataBaseManager(openai.api_key, "discord-bot")

    async def on_ready(self) -> None:
        print(f'Logged on as {self.user}!')

    async def on_message(self, message: discord.Message) -> None:
        print(f'Message: {message}')
        print(f'Message from {message.author}: {message.content}')

        # reply to mention
        if bot_name not in [m.name for m in message.mentions]:
            return

        # ignore bot message
        if message.author.bot:
            return
        
        messages = []
        initial_prompt="あなたは有能なアシスタントです。"
        messages.append(Message(MessageRole.SYSTEM, initial_prompt))
        async with message.channel.typing():
            if isinstance(message.channel, discord.Thread):
                chat_messages = []
                async for old_message in message.channel.history(limit=10):
                    pattern = r'^<.*?>\s'
                    content = re.sub(pattern, "", old_message.content)
                    if old_message.author.bot:
                        role = MessageRole.ASSISTANT
                    else:
                        role = MessageRole.USER
                        # wrap content by user name (koiking213「hello!」)
                        content = f"{old_message.author.display_name}「{content}」"
                    new_message = Message(role, content)
                    chat_messages.append(new_message)
                    print(new_message)
                messages.extend(chat_messages[::-1])
            elif isinstance(message.channel, discord.TextChannel):
                pattern = r'^<.*?>\s'
                content = re.sub(pattern, "", message.content)
                messages.append(Message(MessageRole.USER, content))
            else:
                print("Unknown channel type")
                return

            response = await self.get_response(messages)
            print(response)
            print(len(response))
            length = len(response)
            for i in range(((length-1)//1000)+1):
                await message.channel.send(response[i*1000:(i+1)*1000])

    @to_thread
    def get_response(self, messages: List[Message]) -> str:

        start = time.time()
        stream = False
        response = create_chat_completion(
          model=chat_gpt_model,
          messages=[m.to_dict() for m in messages],
          stream=stream
        )

        full_reply_content=""

        if stream:
            pass
            #for chunk in response:
            #    # extract the message
            #    chunk_message = chunk['choices'][0]['delta'].get('content', '')
            #    full_reply_content += chunk_message
            #    #print(chunk_message)
            #    print(chunk)
        else:
            full_reply_content = response.choices[0].message['content']
            completion_tokens = response.usage['completion_tokens']
            prompt_tokens = response.usage['prompt_tokens']
            if use_database:
                self.db.insert_transaction(sent_tokens=prompt_tokens, received_tokens=completion_tokens)
            print(full_reply_content)
            print(f'{completion_tokens=}')
            print(f'{prompt_tokens=}')


        elapsed = time.time() - start
        print(f"{elapsed=}")
        return full_reply_content


    
def main() -> None:
    intents = discord.Intents.default()
    intents.message_content = True

    client = AssistantClient(intents=intents)
    client.run(discord_token)

if __name__ == "__main__":
    main()

