from telethon import TelegramClient
from telethon.sessions import StringSession
import config

if not config.USERBOT_SESSION:
    raise RuntimeError("USERBOT_SESSION kosong")

userbot = TelegramClient(
    StringSession(config.USERBOT_SESSION), config.API_ID, config.API_HASH)

try:
    from pytgcalls import PyTgCalls
    from pytgcalls.types import MediaStream
    _AVAILABLE = True
except ImportError:
    PyTgCalls = None
    MediaStream = None
    _AVAILABLE = False
    print("⚠️ pytgcalls tidak tersedia")

pytg = None
HAS_CALLS = False