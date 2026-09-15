import asyncio
import os
import config
from bot_app.client import start_bot, client


async def main():
    import database as db
    await db.init_db()
    me = await start_bot()
    mode = "Admin" if config.SUPER_ADMIN_ID else "Publik"
    print(f"✅ Bot: {me.first_name} (@{me.username}) | {mode}")
    print(f"🖼️ Thumbnail: {'ADA' if os.path.exists(config.THUMBNAIL_FILE) else 'TIDAK ADA'}")
    try:
        await client.run_until_disconnected()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋")