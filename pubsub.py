import os
import asyncio

import redis.asyncio as redis
from redis.asyncio.client import PubSub
from telegram import Bot
from telegram.ext import ApplicationBuilder

redis_url = os.environ.get('REDIS_URL', 'redis://localhost')
r = redis.from_url(redis_url)

bot_token = os.environ['TELEGRAM_BOT_TOKEN']
app = ApplicationBuilder().token(bot_token).build()


def _decoded(data: dict) -> dict[str, str]:
    return {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()}


async def send_message(bot: Bot, chat_id: str, message: str) -> None:
    await bot.send_message(chat_id=chat_id, text=message)


async def reader(channel: PubSub):
    while True:
        message = await channel.get_message(ignore_subscribe_messages=True)

        if message is None:
            continue

        key = message['data'].decode()[:-3]
        data = _decoded(await r.hgetall(key))
        await r.delete(key)
        await send_message(bot=app.bot, chat_id=data['chat_id'], message='Lembrete!')
        print((key, data))


async def main():
    async with r.pubsub() as pubsub:
        await pubsub.psubscribe('__key*__:expired')

        future = asyncio.create_task(reader(pubsub))

        await future


if __name__ == '__main__':
    asyncio.run(main())
