import asyncio
from telethon import Button
import config
import database as db
from ui import keyboards as kb
from ui.texts import LINE, test_call_panel, test_call_schedule_menu, \
    test_call_queued_now, test_call_queued_schedule, test_call_history
from ..helpers import safe_edit, sponsor_footer, cb_msg_id
from ..client import client


async def handle_admin(event, uid, data):
    if not (config.SUPER_ADMIN_ID and uid == config.SUPER_ADMIN_ID):
        return

    if data in ("adm_main", "adm_dash"):
        await safe_edit(event, "🎛️ **Admin Dashboard**", buttons=kb.admin_menu())
    elif data == "adm_stats":
        tu = await db.count_users()
        al = await db.get_all_active_alerts()
        sp = await db.get_sponsors()
        fj = await db.get_force_join()
        text = (f"📊 **Statistik**\n\n{LINE}\n"
                f"👥 Users: **{tu}**\n🔔 Alert: **{len(al)}**\n"
                f"💰 Sponsor: **{len(sp)}**\n🔒 Force Join: **{len(fj)}**")
        await safe_edit(event, text, buttons=[[Button.inline("⬅️", b"adm_main")]])
    elif data == "adm_sp":
        sp = await db.get_sponsors(only_active=False)
        await safe_edit(event, "💰 **Sponsors**", buttons=kb.admin_sponsors_kb(sp))
    elif data == "sp_add":
        from .user_menu import user_states
        user_states[uid] = {"await": "sp_nama", "prompt_msg_id": await cb_msg_id(event)}
        await safe_edit(event, "➕ Nama sponsor:",
                        buttons=[[Button.inline("❌", b"adm_sp")]])
    elif data.startswith("sp_del:"):
        await db.delete_sponsor(int(data.split(":")[1]))
        sp = await db.get_sponsors(only_active=False)
        await safe_edit(event, "💰 **Sponsors**", buttons=kb.admin_sponsors_kb(sp))
    elif data == "adm_fj":
        fj = await db.get_force_join(only_active=False)
        await safe_edit(event, "🔒 **Force Join**", buttons=kb.admin_force_join_kb(fj))
    elif data == "fj_add":
        from .user_menu import user_states
        user_states[uid] = {"await": "fj_chat_id", "prompt_msg_id": await cb_msg_id(event)}
        await safe_edit(event, "➕ Chat ID (`@username` / `-100...`):",
                        buttons=[[Button.inline("❌", b"adm_fj")]])
    elif data.startswith("fj_del:"):
        await db.delete_force_join(int(data.split(":")[1]))
        fj = await db.get_force_join(only_active=False)
        await safe_edit(event, "🔒 **Force Join**", buttons=kb.admin_force_join_kb(fj))
    elif data == "adm_bc":
        from .user_menu import user_states
        user_states[uid] = {"await": "bc_msg", "prompt_msg_id": await cb_msg_id(event)}
        total = await db.count_users()
        await safe_edit(event, f"📢 Pesan untuk **{total} user**:",
                        buttons=[[Button.inline("❌", b"adm_main")]])
    elif data == "bc_send":
        from .user_menu import user_states
        state = user_states.get(uid)
        if not state or "bc_text" not in state:
            return
        await safe_edit(event, "📢 Mengirim...")
        users = await db.get_all_users()
        sent = failed = 0
        sponsor = await sponsor_footer()
        msg = state["bc_text"] + sponsor
        for u in users:
            try:
                await client.send_message(u["user_id"], msg, link_preview=False)
                sent += 1
            except Exception:
                failed += 1
            await asyncio.sleep(0.05)
        user_states.pop(uid, None)
        await safe_edit(event, f"✅ Sent: {sent} | Failed: {failed}",
                        buttons=[[Button.inline("⬅️", b"adm_main")]])
    elif data == "adm_testcall":
        await safe_edit(event, test_call_panel(),
                        buttons=kb.admin_test_call_kb())
    elif data == "testcall_go":
        await db.create_test_call(uid)
        await safe_edit(event, test_call_queued_now(),
                        buttons=[[Button.inline("🔄 Cek Status", b"testcall_check")],
                                 [Button.inline("⬅️ Kembali", b"adm_main")]])
    elif data == "testcall_schedule":
        await safe_edit(event, test_call_schedule_menu(),
                        buttons=kb.admin_test_call_schedule_kb())
    elif data.startswith("testcall_sched:"):
        minutes = int(data.split(":")[1])
        when = db.future(minutes)
        await db.create_test_call(uid, scheduled_at=when)
        await safe_edit(event, test_call_queued_schedule(when),
                        buttons=[[Button.inline("🔄 Cek Status", b"testcall_check")],
                                 [Button.inline("⬅️ Kembali", b"adm_main")]])
    elif data == "testcall_check":
        recent = await db.get_recent_test_calls(5)
        await safe_edit(event, test_call_history(recent),
                        buttons=kb.admin_test_call_kb())
    elif data == "adm_calllog":
        recent = await db.get_recent_test_calls(10)
        await safe_edit(event, test_call_history(recent),
                        buttons=[[Button.inline("⬅️ Kembali", b"adm_main")]])