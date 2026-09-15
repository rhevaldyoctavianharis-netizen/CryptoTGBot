from telethon import TelegramClient
import config

client = TelegramClient("bot_session", config.API_ID, config.API_HASH)


async def start_bot():
    from .handlers import register_all
    await client.start(bot_token=config.BOT_TOKEN)
    register_all(client)
    me = await client.get_me()
    return me