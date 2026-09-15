import asyncio
from collections import defaultdict
import database as db
from ui.texts import LINE
from ..helpers import sponsor_footer
from ..client import client


def _format_one(n):
    emoji = {"naik": "📈", "turun": "📉", "trailing": "📊"}.get(n["tipe"], "🚨")
    label = {"naik": "NAIK", "turun": "TURUN",
             "trailing": "TRAILING STOP"}.get(n["tipe"], "")
    reason = f"\n💡 _{n['reason']}_" if n["reason"] else ""
    return (f"{emoji} **{label} — {n['coin']}**\n"
            f"💵 ${n['harga']:,.2f}  |  📊 {n['pct_change']:+.2f}%{reason}")


async def notification_poller():
    while True:
        try:
            notifs = await db.get_pending_notifications()
            # Gabung semua notif per user jadi 1 pesan, biar chat gak
            # kebanjiran pesan satu-satu kalau beberapa alert nyala barengan.
            by_user = defaultdict(list)
            for n in notifs:
                by_user[n["user_id"]].append(n)

            sponsor = await sponsor_footer()
            for uid, items in by_user.items():
                try:
                    if len(items) == 1:
                        header = f"🚨 **ALERT — {items[0]['coin']}**\n\n"
                        body = _format_one(items[0])
                    else:
                        header = f"🚨 **{len(items)} ALERT BARU**\n\n{LINE}\n\n"
                        body = f"\n{LINE}\n\n".join(_format_one(n) for n in items)
                    text = (f"{header}{body}\n\n{LINE}\n\n"
                            f"🔇 Notifikasi suara tidak tersedia{sponsor}")
                    await client.send_message(uid, text, link_preview=False)
                    for n in items:
                        await db.mark_notification_sent(n["id"])
                except Exception as e:
                    print(f"❌ Poller [{uid}]: {e}")
        except Exception as e:
            print(f"❌ Poller error: {e}")
        await asyncio.sleep(10)


def start_poller():
    asyncio.create_task(notification_poller())