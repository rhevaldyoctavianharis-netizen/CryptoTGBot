import asyncio
from collections import defaultdict
from datetime import datetime
import config
import database as db
from services import market
from .caller import call_user
from .gate import can_call
from .client import userbot

USER_LOCKS = defaultdict(asyncio.Lock)
RUNNING_TASKS = set()
pending_reads = {}


def spawn(coro, name=None):
    t = asyncio.create_task(coro, name=name)
    RUNNING_TASKS.add(t)
    t.add_done_callback(RUNNING_TASKS.discard)
    return t


def register_read_handler():
    from telethon import events

    @userbot.on(events.MessageRead)
    async def on_read(event):
        uid = None
        for attr in ("user_id", "chat_id", "peer_id"):
            v = getattr(event, attr, None)
            if v is not None:
                uid = getattr(v, "user_id", v); break
        if uid is None:
            return
        try:
            uid = int(uid)
        except (TypeError, ValueError):
            return
        evt = pending_reads.get(uid)
        if evt and not evt.is_set():
            evt.set()


async def _post_context(coin, price, pct):
    try:
        rsi, fg = await asyncio.gather(
            market.get_rsi(coin, "4h", 14), market.get_fear_greed(),
            return_exceptions=True)
        rsi_s = f"{rsi:.1f}" if not isinstance(rsi, Exception) and rsi else "—"
        fg_s = "—" if isinstance(fg, Exception) else f"{fg['value']} ({fg['label']})"
        return (f"\n📊 **Konteks:** RSI {rsi_s} | F&G {fg_s}")
    except Exception:
        return ""


async def notify_and_call(alert, price, pct):
    uid = alert["user_id"]; aid = alert["id"]
    coin = alert["coin"]; tipe = alert["tipe"]
    async with USER_LOCKS[uid]:
        try:
            if not await db.verify_alert_owner(aid, uid): return
            if await db.is_alert_called(aid): return
            if alert["last_triggered"]:
                try:
                    lt = datetime.strptime(alert["last_triggered"], "%Y-%m-%d %H:%M:%S")
                    if (datetime.now() - lt).total_seconds() < config.COOLDOWN_SECONDS:
                        return
                except Exception:
                    pass

            can, reason = await can_call(uid, alert)
            if not can:
                print(f"📭 Call blocked [{uid}]: {reason}")
                await db.add_pending_notification(uid, coin, tipe, alert["persen"],
                                                  price, pct, reason)
                await db.log_alert(uid, coin, tipe, alert["persen"], price)
                await db.update_alert_price(aid, baseline=price, peak=price)
                return

            user = await db.get_user(uid)
            voice = user["voice_choice"] if user else "ardi"
            context = await _post_context(coin, price, pct)

            sponsors = await db.get_sponsors()
            sponsor_txt = ""
            if sponsors:
                sponsor_txt = ("\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💎 **Sponsor:**\n"
                               + "\n".join(f"• [{s['nama']}]({s['url']})" for s in sponsors))

            emoji = {"naik": "🚨📈", "turun": "🚨📉", "trailing": "🚨📊"}[tipe]
            label = {"naik": "NAIK", "turun": "TURUN", "trailing": "TRAILING STOP"}[tipe]
            text = (f"{emoji} **ALERT {label} — {coin}**\n\n"
                    f"💵 Harga : **${price:,.2f}**\n"
                    f"📌 Base  : ${alert['baseline_price']:,.2f}\n"
                    f"📊 Δ     : **{pct:+.2f}%**\n{context}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"⏳ Anda punya **{config.READ_TIMEOUT} detik**.\n"
                    f"Jika tidak dibaca, userbot akan menelfon.{sponsor_txt}")

            try:
                await userbot.send_message(uid, text, link_preview=False)
                await db.mark_notified(aid)
            except Exception as e:
                print(f"❌ send fail {uid}: {e}")
                await db.mark_called(aid, "send_failed")
                return

            priority = alert["priority"] if "priority" in alert.keys() else "medium"
            if priority != "critical":
                evt = asyncio.Event()
                pending_reads[uid] = evt
                try:
                    await asyncio.wait_for(evt.wait(), config.READ_TIMEOUT)
                    await db.mark_called(aid, "read")
                    return
                except asyncio.TimeoutError:
                    pass
                finally:
                    pending_reads.pop(uid, None)

            if tipe == "naik":
                tts = f"Peringatan. {coin} naik {pct:.2f} persen. Harga {price:.0f} dolar."
            elif tipe == "turun":
                tts = f"Peringatan. {coin} turun {abs(pct):.2f} persen. Harga {price:.0f} dolar."
            else:
                tts = f"Peringatan. {coin} turun {abs(pct):.2f} persen dari puncak. Harga {price:.0f} dolar."

            ok = await call_user(uid, tts, voice)
            await db.mark_called(aid, "called" if ok else "call_failed")
            await db.reset_alert_called(aid)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"❌ notify: {e}")


async def price_monitor():
    while True:
        try:
            alerts = await db.get_all_active_alerts()
            if alerts:
                coins = list({a["coin"] for a in alerts})
                try:
                    prices = await market.get_prices_bulk(coins)
                except Exception as e:
                    print(f"❌ price: {e}"); prices = {}
                for a in alerts:
                    if a["called"]: continue
                    cp = prices.get(a["coin"])
                    if not cp or cp.get("usd") is None: continue
                    cur = cp["usd"]
                    base = a["baseline_price"] or cur
                    peak = a["peak_price"] or base
                    if base == 0: continue
                    pct = (cur - base) / base * 100
                    trail = (cur - peak) / peak * 100 if peak else 0
                    triggered = False
                    if a["tipe"] == "naik" and pct >= a["persen"]: triggered = True
                    elif a["tipe"] == "turun" and pct <= -a["persen"]: triggered = True
                    elif a["tipe"] == "trailing":
                        if cur > peak:
                            await db.update_alert_price(a["id"], peak=cur)
                        elif trail <= -a["persen"]:
                            triggered = True
                    if triggered:
                        spawn(notify_and_call(a, cur, pct), name=f"a-{a['id']}")
                        await db.log_alert(a["user_id"], a["coin"], a["tipe"],
                                           a["persen"], cur)
                        await db.update_alert_price(a["id"], baseline=cur, peak=cur)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"❌ monitor: {e}")
        await asyncio.sleep(config.CHECK_INTERVAL)


async def shutdown():
    for t in list(RUNNING_TASKS):
        t.cancel()
    if RUNNING_TASKS:
        await asyncio.gather(*RUNNING_TASKS, return_exceptions=True)