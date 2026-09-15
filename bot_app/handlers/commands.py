from telethon import events
import config
import database as db
from ui import keyboards as kb
from ..helpers import safe_delete, is_admin, send_panel
from ..client import client
import re

ADD_RE = re.compile(r"^/add\s+([A-Za-z]+)\s+([\d.]+)\s+([\d.]+)$")
PAPER_RE = re.compile(r"^/paper\s+(.+)$")


def register(_c):
    @client.on(events.NewMessage(pattern="/add"))
    async def on_add(event):
        uid = event.sender_id
        m = ADD_RE.match(event.raw_text.strip())
        if not m:
            await safe_delete(event)
            await client.send_message(uid,
                "❌ Format: `/add COIN AMOUNT BUY_PRICE`\nContoh: `/add BTC 0.5 60000`")
            return
        coin = m.group(1).upper()
        if coin not in config.COINS:
            await safe_delete(event)
            await client.send_message(uid, f"❌ Coin {coin} tidak didukung.")
            return
        await db.add_portfolio(uid, coin, float(m.group(2)), float(m.group(3)))
        await safe_delete(event)
        await client.send_message(uid,
            f"✅ Ditambahkan: {m.group(2)} {coin} @ ${float(m.group(3)):,.2f}")

    @client.on(events.NewMessage(pattern="/portfolio"))
    async def on_portfolio(event):
        await safe_delete(event)
        await send_panel(event.sender_id,
            "💼 Gunakan `/add COIN AMOUNT BUY_PRICE` untuk menambah portfolio.",
            buttons=kb.main_menu())

    @client.on(events.NewMessage(pattern="/panic"))
    async def on_panic(event):
        uid = event.sender_id
        await db.set_user_setting(uid, "panic_mode", 1)
        await safe_delete(event)
        await send_panel(uid,
            "🚨 **PANIC MODE AKTIF**\n\n"
            "• Semua telfon dari userbot dihentikan\n"
            "• Alert tetap masuk via chat\n"
            "• Kirim /resume untuk mengaktifkan kembali",
            buttons=kb.panic_kb())

    @client.on(events.NewMessage(pattern="/resume"))
    async def on_resume(event):
        uid = event.sender_id
        await db.set_user_setting(uid, "panic_mode", 0)
        await safe_delete(event)
        await send_panel(uid,
            "✅ **Mode Normal Aktif**\n\nUserbot akan menelfon Anda.",
            buttons=kb.main_menu())

    @client.on(events.NewMessage(pattern=PAPER_RE))
    async def on_paper(event):
        from ..handlers.paper_helper import handle_paper
        await handle_paper(event)

    @client.on(events.NewMessage(pattern="/admin"))
    async def on_admin(event):
        uid = event.sender_id
        if not config.SUPER_ADMIN_ID or uid != config.SUPER_ADMIN_ID:
            return
        await safe_delete(event)
        await send_panel(uid, "🎛️ **Admin Dashboard**", buttons=kb.admin_menu())