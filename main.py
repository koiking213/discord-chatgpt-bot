from dotenv import load_dotenv
import openai
import os
import time
import discord
import re
import typing
import functools
import asyncio

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
discord_token = os.getenv("DISCORD_BOT_TOKEN")

def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

@to_thread
def get_response(content: str):
    initial_prompt="あなたは有能なアシスタントです。"
    
    start = time.time()
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
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

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        if "chatgpt-bot" in [m.name for m in message.mentions]:
            async with message.channel.typing():
                pattern = r'^<.*?>\s'
                content = re.sub(pattern, "", message.content)
                response = await get_response(content)
                print(response)
                print(len(response))
                length = len(response)
                for i in range(((length-1)//1000)+1):
                    await message.channel.send(response[i*1000:(i+1)*1000])

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(discord_token)


