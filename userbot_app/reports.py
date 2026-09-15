import asyncio
from datetime import datetime
import aiosqlite
import config
import database as db
from services import market
from .client import userbot

_last_daily = None
_last_weekly = None


async def _send(kind):
    try:
        top = ["BTC", "ETH", "SOL", "BNB"]
        lines = [f"📅 **Laporan {'Harian' if kind=='daily' else 'Mingguan'}**\n\n"
                 f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
        try:
            prices = await market.get_prices_bulk(top)
        except Exception:
            prices = {}
        for c in top:
            p = prices.get(c)
            if p and p.get("usd") is not None:
                ch = p.get("usd_24h_change") or 0
                e = "🟢" if ch >= 0 else "🔴"
                lines.append(f"{e} {c}: ${p['usd']:,.2f} ({ch:+.2f}%)")
            else:
                lines.append(f"⚪ {c}: —")
        try:
            fg = await market.get_fear_greed()
            lines.append(f"\n😨 F&G: {fg['value']} ({fg['label']})")
        except Exception:
            pass
        lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        text = "\n".join(lines)

        field = "report_daily" if kind == "daily" else "report_weekly"
        async with aiosqlite.connect(config.DB_PATH) as conn:
            cur = await conn.execute(f"SELECT user_id FROM users WHERE {field}=1")
            rows = await cur.fetchall()
        ids = [r[0] for r in rows]
        sem = asyncio.Semaphore(5)

        async def one(uid):
            async with sem:
                try:
                    await userbot.send_message(uid, text, link_preview=False)
                except Exception as e:
                    print(f"❌ report {uid}: {e}")

        await asyncio.gather(*(one(u) for u in ids), return_exceptions=True)
    except Exception as e:
        print(f"❌ report err: {e}")


async def scheduler():
    global _last_daily, _last_weekly
    from .monitor import spawn
    while True:
        try:
            now = datetime.now()
            if now.hour == 8 and now.minute < 2:
                if not _last_daily or (now - _last_daily).total_seconds() > 3600:
                    spawn(_send("daily"), name="rep-daily")
                    _last_daily = now
            if now.weekday() == 0 and now.hour == 8 and 5 <= now.minute < 7:
                if not _last_weekly or (now - _last_weekly).total_seconds() > 3600:
                    spawn(_send("weekly"), name="rep-weekly")
                    _last_weekly = now
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"❌ sched: {e}")
        await asyncio.sleep(60)