from telethon import events, Button
import database as db
from ui import keyboards as kb
from ui.texts import LINE, settings_text
from ..helpers import safe_delete, edit_or_send
from ..client import client
from .user_menu import user_states, _do_create_alert


def register(_c):
    @client.on(events.NewMessage())
    async def on_text(event):
        if event.raw_text.startswith("/"):
            return
        uid = event.sender_id
        state = user_states.get(uid)
        if not state:
            return
        t = state.get("await")
        pmid = state.get("prompt_msg_id")

        if t == "pct":
            raw = event.raw_text.strip().replace(",", ".")
            await safe_delete(event)
            try:
                persen = float(raw)
                if persen <= 0 or persen > 100:
                    raise ValueError
            except ValueError:
                await edit_or_send(uid, pmid, "❌ Angka tidak valid (0-100).")
                return
            coin = state["coin"]; atype = state["atype"]
            pmid = await edit_or_send(uid, pmid,
                f"🎯 **{coin}**/{atype}/{persen}%\n\nPilih priority:",
                buttons=kb.priority_kb(coin, atype, persen))
            state["prompt_msg_id"] = pmid

        elif t == "quiet_custom":
            await safe_delete(event)
            try:
                parts = event.raw_text.strip().split()
                s, e = int(parts[0]), int(parts[1])
                if not (0 <= s <= 23 and 0 <= e <= 23):
                    raise ValueError
                await db.set_user_setting(uid, "quiet_start", s)
                await db.set_user_setting(uid, "quiet_end", e)
                user_states.pop(uid, None)
                user = await db.get_user(uid)
                pmid = await edit_or_send(uid, pmid, settings_text(user),
                                          buttons=kb.settings_kb(user))
            except Exception:
                await edit_or_send(uid, pmid,
                    f"❌ **Format salah**\n\n{LINE}\n\nKetik jam mulai & selesai, contoh: `23 7`",
                    buttons=[[Button.inline("❌ Batal", b"set_quiet")]])

        elif t == "sp_nama":
            state["sp_nama"] = event.raw_text.strip()
            state["await"] = "sp_url"
            await safe_delete(event)
            await edit_or_send(uid, pmid, "🔗 URL sponsor:",
                               buttons=[[Button.inline("❌", b"adm_sp")]])

        elif t == "sp_url":
            await db.add_sponsor(state.get("sp_nama", ""), event.raw_text.strip())
            user_states.pop(uid, None)
            await safe_delete(event)
            sp = await db.get_sponsors(only_active=False)
            await edit_or_send(uid, pmid, "✅ Ditambahkan.",
                               buttons=kb.admin_sponsors_kb(sp))

        elif t == "fj_chat_id":
            state["fj_chat_id"] = event.raw_text.strip()
            state["await"] = "fj_url"
            await safe_delete(event)
            await edit_or_send(uid, pmid, "🔗 URL invite:",
                               buttons=[[Button.inline("❌", b"adm_fj")]])

        elif t == "fj_url":
            state["fj_url"] = event.raw_text.strip()
            state["await"] = "fj_nama"
            await safe_delete(event)
            await edit_or_send(uid, pmid, "📝 Nama:",
                               buttons=[[Button.inline("❌", b"adm_fj")]])

        elif t == "fj_nama":
            await db.add_force_join(event.raw_text.strip(),
                                    state.get("fj_chat_id", ""),
                                    state.get("fj_url", ""))
            user_states.pop(uid, None)
            await safe_delete(event)
            fj = await db.get_force_join(only_active=False)
            await edit_or_send(uid, pmid, "✅ Ditambahkan.",
                               buttons=kb.admin_force_join_kb(fj))

        elif t == "bc_msg":
            state["bc_text"] = event.raw_text
            state["await"] = None
            total = await db.count_users()
            preview = event.raw_text[:200] + ("..." if len(event.raw_text) > 200 else "")
            await safe_delete(event)
            await edit_or_send(uid, pmid,
                f"📢 Konfirmasi ke **{total} user**:\n\n{preview}",
                buttons=kb.admin_broadcast_confirm())
