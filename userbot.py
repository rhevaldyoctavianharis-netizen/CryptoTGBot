import asyncio
import config
import database as db
from userbot_app.client import userbot, _AVAILABLE, PyTgCalls
from userbot_app import monitor, reports, testcall
from userbot_app import client as uc


async def main():
    await db.init_db()
    await userbot.start()
    me = await userbot.get_me()

    if me.username:
        await db.set_config("userbot_username", me.username)
        print(f"📛 @{me.username}")

    if _AVAILABLE:
        try:
            uc.pytg = PyTgCalls(userbot)
            await uc.pytg.start()
            uc.HAS_CALLS = True
            print("✅ PyTgCalls AKTIF")
        except Exception as e:
            print(f"⚠️ PyTgCalls: {e}")
    else:
        print("⚠️ chat-only")

    monitor.register_read_handler()
    print(f"✅ {me.first_name} | TTS {config.TTS_REPEAT}x | {config.CALL_DURATION}s")

    try:
        await asyncio.gather(
            monitor.price_monitor(),
            reports.scheduler(),
            testcall.monitor(),
        )
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        await monitor.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋")