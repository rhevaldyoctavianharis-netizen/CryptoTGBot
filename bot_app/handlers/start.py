from telethon import events, Button
import database as db
from ui import keyboards as kb, texts
from ..helpers import safe_delete, sponsor_footer, get_unjoined_channels, is_admin, send_panel
from ..client import client


def register(_c):
    @client.on(events.NewMessage(pattern=r"^/start(?:\s+(.+))?$"))
    async def on_start(event):
        uid = event.sender_id
        sender = await event.get_sender()
        uname = getattr(sender, "username", None)
        payload = event.pattern_match.group(1)

        referred_by = None
        if payload and payload.startswith("ref_"):
            ref_user = await db.get_user_by_referral_code(payload)
            if ref_user and ref_user["user_id"] != uid:
                referred_by = ref_user["user_id"]

        is_new = await db.register_user(uid, uname, referred_by)
        if is_new and referred_by:
            await db.add_referral(referred_by, uid)
            try:
                count = await db.count_referrals(referred_by)
                await client.send_message(referred_by,
                    f"🎉 **Referral Baru!**\n\nTotal: **{count}**")
            except Exception:
                pass

        await safe_delete(event)

        # Gate: force join
        if not is_admin(uid):
            unjoined = await get_unjoined_channels(client, uid)
            if unjoined:
                me = await client.get_me()
                await send_panel(uid, texts.force_join(),
                    buttons=kb.force_join_kb(unjoined, me.username))
                return

        # Onboarding user baru
        user = await db.get_user(uid)
        if user and user["onboarding_step"] == 0 and not is_admin(uid):
            ub = await db.get_config("userbot_username", "userbot")
            await send_panel(uid, texts.onboarding(sender.first_name or "User"),
                buttons=[
                    [Button.url("💾 Simpan Kontak Userbot", f"https://t.me/{ub}")],
                    [Button.inline("✅ Saya Sudah Simpan → Lanjut", b"onb_step2")],
                ])
            return

        sponsor = await sponsor_footer()
        caption = texts.welcome(sender.first_name or uname or "User") + sponsor
        await send_panel(uid, caption, buttons=kb.main_menu())
