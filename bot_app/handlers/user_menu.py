import asyncio
from telethon import events, Button
import config
import database as db
from services import market, prediction
from ui import keyboards as kb
from ui.texts import (LINE, alert_created, main_menu_text, alerts_menu_text,
                      analisa_menu_text, trading_menu_text, settings_text)
from ..helpers import safe_edit, is_admin, cb_msg_id
from ..client import client

# State lokal user (in-memory)
user_states = {}


async def _do_create_alert(uid, coin, atype, persen, priority="medium"):
    if persen <= 0 or persen > 100:
        return "❌ Persentase harus 0-100.", None
    try:
        p = await market.get_price(coin)
        baseline = p.get("usd") or 0
    except Exception:
        baseline = 0
    await db.add_alert(uid, coin, atype, persen, baseline, priority)
    text = alert_created(coin, atype, persen, priority, baseline)
    buttons = [
        [Button.inline("➕ Buat Lagi", b"m_set"), Button.inline("📋 Status", b"m_status")],
        [Button.inline("🏠 Menu Utama", b"m_main")],
    ]
    return text, buttons


def register(_c):
    @client.on(events.CallbackQuery())
    async def on_cb(event):
        uid = event.sender_id
        data = event.data.decode()
        try:
            admin_only = (data.startswith("adm_") or data.startswith("sp_")
                          or data.startswith("fj_") or data.startswith("bc_")
                          or data.startswith("testcall_"))
            if admin_only and not is_admin(uid):
                await event.answer("⛔ Admin only", alert=True)
                return
            if not admin_only and not is_admin(uid):
                from ..helpers import get_unjoined_channels
                unjoined = await get_unjoined_channels(client, uid)
                if unjoined:
                    me = await client.get_me()
                    from ui.texts import force_join
                    await safe_edit(event, force_join(),
                                    buttons=kb.force_join_kb(unjoined, me.username))
                    return
            await _handle_user(event, uid, data)
        except Exception as e:
            print(f"⚠️ cb error: {e}")
        finally:
            try:
                await event.answer()
            except Exception:
                pass


async def _handle_user(event, uid, data):
    # Onboarding
    if data == "onb_step2":
        await db.set_user_setting(uid, "onboarding_step", 2)
        await safe_edit(event, "🪙 **Pilih coin favoritmu:**", buttons=kb.coins_kb("onb"))
        return
    if data.startswith("onb:"):
        coin = data.split(":", 1)[1]
        await db.set_user_setting(uid, "onboarding_step", 3)
        user_states[uid] = {"coin": coin}
        await safe_edit(event, f"🎯 **{coin}** dipilih!\n\nPilih tipe:", buttons=kb.type_kb(coin))
        return

    if data == "contact_saved":
        await db.set_user_contact_saved(uid, 1)
        await safe_edit(event, main_menu_text(), buttons=kb.main_menu())
        return

    if data == "check_join":
        from ..helpers import get_unjoined_channels
        unjoined = await get_unjoined_channels(client, uid)
        if unjoined:
            me = await client.get_me()
            from ui.texts import force_join
            await safe_edit(event, force_join(), buttons=kb.force_join_kb(unjoined, me.username))
        else:
            user = await db.get_user(uid)
            if not user or not user["contact_saved"]:
                from ui.texts import contact_gate
                ub = await db.get_config("userbot_username", "userbot")
                await safe_edit(event, contact_gate(), buttons=kb.contact_save_kb(ub))
            else:
                await safe_edit(event, main_menu_text(), buttons=kb.main_menu())
        return

    # Navigation
    if data == "m_main":
        user_states.pop(uid, None)
        await safe_edit(event, main_menu_text(), buttons=kb.main_menu())
    elif data == "m_alerts_menu":
        await safe_edit(event, alerts_menu_text(), buttons=kb.alerts_menu_kb())
    elif data == "m_analisa_menu":
        await safe_edit(event, analisa_menu_text(), buttons=kb.analisa_menu_kb())
    elif data == "m_trading_menu":
        await safe_edit(event, trading_menu_text(), buttons=kb.trading_menu_kb())
    elif data == "m_set":
        await safe_edit(event, "🪙 **Pilih Coin**:", buttons=kb.coins_kb("coin", back=b"m_alerts_menu"))
    elif data.startswith("coin:"):
        coin = data.split(":", 1)[1]
        user_states[uid] = {"coin": coin}
        await safe_edit(event, f"🎯 Coin: **{coin}**\n\nPilih tipe:", buttons=kb.type_kb(coin))
    elif data.startswith("atype:"):
        _, atype, coin = data.split(":")
        user_states[uid] = {"coin": coin, "atype": atype}
        await safe_edit(event, f"🎯 **{coin}**/{atype}\n\nPilih persen:",
                        buttons=kb.percent_kb(coin, atype))
    elif data.startswith("pct:"):
        _, n, atype, coin = data.split(":")
        await safe_edit(event, f"🎯 **{coin}**/{atype}/{n}%\n\nPilih priority:",
                        buttons=kb.priority_kb(coin, atype, n))
    elif data.startswith("pr:"):
        _, priority, atype, coin, pct = data.split(":")
        text, buttons = await _do_create_alert(uid, coin, atype, float(pct), priority)
        user_states.pop(uid, None)
        await safe_edit(event, text, buttons=buttons)
    elif data.startswith("pctc:"):
        _, atype, coin = data.split(":")
        user_states[uid] = {"await": "pct", "coin": coin, "atype": atype,
                            "prompt_msg_id": await cb_msg_id(event)}
        await safe_edit(event,
            f"✏️ **Input Custom**\n\nKetik persentase untuk **{coin}** ({atype}):",
            buttons=kb.back_main())

    elif data == "m_status":
        alerts = await db.get_user_alerts(uid)
        if not alerts:
            await safe_edit(event, "📋 Belum ada alert.", buttons=kb.back_main(b"m_alerts_menu"))
        else:
            await safe_edit(event, "📋 **Alert Aktif:**", buttons=kb.alert_list_kb(alerts))
    elif data.startswith("del:"):
        await db.delete_alert(int(data.split(":")[1]), uid)
        alerts = await db.get_user_alerts(uid)
        if not alerts:
            await safe_edit(event, "📋 Kosong.", buttons=kb.back_main(b"m_alerts_menu"))
        else:
            await safe_edit(event, "📋 **Alert Aktif:**", buttons=kb.alert_list_kb(alerts))
    elif data == "del_all":
        await db.delete_all_alerts(uid)
        await safe_edit(event, "🗑️ Semua alert dihapus.", buttons=kb.back_main(b"m_alerts_menu"))

    # Templates
    elif data == "m_tpl":
        await safe_edit(event, "🎯 **Templates:**", buttons=kb.templates_kb())
    elif data.startswith("tpl:"):
        key = data.split(":", 1)[1]
        tpl = config.ALERT_TEMPLATES.get(key)
        if not tpl:
            return
        lines = [f"{tpl['nama']}\n_{tpl['desc']}_\n\n{LINE}\n"]
        for coin, tipe, persen, pr in tpl["alerts"]:
            emoji = {"naik": "📈", "turun": "📉", "trailing": "📊"}[tipe]
            pr_e = {"low": "🟢", "medium": "🟡", "critical": "🔴"}[pr]
            lines.append(f"{pr_e} {emoji} **{coin}** {tipe} {persen}%")
        await safe_edit(event, "\n".join(lines), buttons=kb.template_confirm_kb(key))
    elif data.startswith("tpl_go:"):
        key = data.split(":", 1)[1]
        tpl = config.ALERT_TEMPLATES.get(key)
        if not tpl:
            return
        created = 0
        for coin, tipe, persen, pr in tpl["alerts"]:
            try:
                p = await market.get_price(coin)
                await db.add_alert(uid, coin, tipe, persen, p.get("usd") or 0, pr)
                created += 1
            except Exception:
                pass
        await safe_edit(event,
            f"✅ **{tpl['nama']}** aktif! {created} alert dibuat.",
            buttons=[[Button.inline("📋 Lihat", b"m_status"),
                      Button.inline("🏠 Menu", b"m_main")]])

    # Portfolio
    elif data == "m_port":
        await _show_portfolio(event, uid)
    elif data == "port_reset":
        await db.clear_portfolio(uid)
        await safe_edit(event, "🗑️ Dikosongkan.", buttons=kb.back_main(b"m_trading_menu"))

    # Paper
    elif data == "m_paper":
        await _show_paper(event, uid)
    elif data == "paper_reset":
        await db.paper_reset(uid)
        await safe_edit(event, "✅ Reset ke $10,000.", buttons=kb.paper_kb())

    # Referral
    elif data == "m_ref":
        user = await db.get_user(uid)
        count = await db.count_referrals(uid)
        me = await client.get_me()
        link = f"https://t.me/{me.username}?start={user['referral_code']}"
        text = (f"🎁 **Referral**\n\n{LINE}\n\n"
                f"📊 Total: **{count}**\n\n"
                f"🔗 `{link}`\n\n{LINE}\n\n"
                f"Reward: 1 ref = +1 slot, 5 = critical, 10 = support")
        await safe_edit(event, text, buttons=kb.back_main())

    # Panic
    elif data == "m_panic":
        user = await db.get_user(uid)
        status = "🔴 AKTIF" if (user and user["panic_mode"]) else "🟢 Normal"
        text = (f"🚨 **EMERGENCY**\n\n{LINE}\n\n"
                f"Status: **{status}**\n\n"
                f"Panic mode: hentikan semua telfon, alert tetap masuk via chat.")
        await safe_edit(event, text, buttons=kb.panic_kb())
    elif data == "panic_on":
        await db.set_user_setting(uid, "panic_mode", 1)
        await safe_edit(event, "🚨 Panic mode AKTIF", buttons=kb.panic_kb())
    elif data == "panic_off":
        await db.set_user_setting(uid, "panic_mode", 0)
        await safe_edit(event, "✅ Normal", buttons=kb.panic_kb())

    # Market / Pred / News
    elif data == "m_market":
        await safe_edit(event, "📈 Pilih coin:", buttons=kb.coins_kb("mkt", back=b"m_analisa_menu"))
    elif data.startswith("mkt:") or data.startswith("mkt_refresh:"):
        await _show_market(event, data.split(":", 1)[1])
    elif data == "mkt_change":
        await safe_edit(event, "📈 Pilih coin:", buttons=kb.coins_kb("mkt", back=b"m_analisa_menu"))
    elif data == "m_pred":
        await safe_edit(event, "🔮 Pilih coin:", buttons=kb.coins_kb("pred", back=b"m_analisa_menu"))
    elif data.startswith("pred:") or data.startswith("pred_refresh:"):
        await _show_pred(event, data.split(":", 1)[1])
    elif data == "pred_change":
        await safe_edit(event, "🔮 Pilih coin:", buttons=kb.coins_kb("pred", back=b"m_analisa_menu"))
    elif data == "m_news":
        await safe_edit(event, "📰 Pilih coin:", buttons=kb.coins_kb("news", back=b"m_analisa_menu"))
    elif data.startswith("news:") or data.startswith("news_refresh:"):
        await _show_news(event, data.split(":", 1)[1])
    elif data == "news_change":
        await safe_edit(event, "📰 Pilih coin:", buttons=kb.coins_kb("news", back=b"m_analisa_menu"))

    # Settings
    elif data == "m_setting":
        user = await db.get_user(uid)
        await safe_edit(event, settings_text(user), buttons=kb.settings_kb(user))
    elif data == "tg_daily":
        user = await db.get_user(uid)
        await db.set_user_setting(uid, "report_daily",
            0 if (user and user["report_daily"]) else 1)
        user = await db.get_user(uid)
        await safe_edit(event, settings_text(user), buttons=kb.settings_kb(user))
    elif data == "tg_weekly":
        user = await db.get_user(uid)
        await db.set_user_setting(uid, "report_weekly",
            0 if (user and user["report_weekly"]) else 1)
        user = await db.get_user(uid)
        await safe_edit(event, settings_text(user), buttons=kb.settings_kb(user))
    elif data == "set_quiet":
        user = await db.get_user(uid)
        cur = "Tidak diatur"
        if user["quiet_start"] is not None:
            cur = f"{user['quiet_start']:02d}:00 - {user['quiet_end']:02d}:00"
        await safe_edit(event,
            f"🔕 **QUIET HOURS**\n\n{LINE}\n\nSaat ini: **{cur}**\n\n"
            f"Selama jam ini, telfon diblokir. Alert tetap masuk via chat.\n\n"
            f"{LINE}\n\nPilih jadwal:",
            buttons=kb.quiet_hours_kb())
    elif data.startswith("quiet:"):
        _, s, e = data.split(":")
        await db.set_user_setting(uid, "quiet_start", int(s))
        await db.set_user_setting(uid, "quiet_end", int(e))
        user = await db.get_user(uid)
        await safe_edit(event, settings_text(user), buttons=kb.settings_kb(user))
    elif data == "quiet_off":
        await db.set_user_setting(uid, "quiet_start", None)
        await db.set_user_setting(uid, "quiet_end", None)
        user = await db.get_user(uid)
        await safe_edit(event, settings_text(user), buttons=kb.settings_kb(user))
    elif data == "quiet_custom":
        user_states[uid] = {"await": "quiet_custom", "prompt_msg_id": await cb_msg_id(event)}
        await safe_edit(event,
            f"✏️ **INPUT CUSTOM**\n\n{LINE}\n\nKetik jam mulai & selesai, contoh: `23 7`",
            buttons=[[Button.inline("❌ Batal", b"set_quiet")]])
    elif data == "set_voice":
        await safe_edit(event, f"🎙️ **PILIH VOICE**\n\n{LINE}\n\nSuara yang dipakai saat telfon:",
                        buttons=kb.voice_kb())
    elif data.startswith("voice:"):
        v = data.split(":")[1]
        await db.set_user_setting(uid, "voice_choice", v)
        user = await db.get_user(uid)
        await safe_edit(event, settings_text(user), buttons=kb.settings_kb(user))
    elif data == "cd_info":
        await event.answer("Cooldown di config", alert=True)

    # Report
    elif data == "m_report":
        await _show_report(event, uid)

    # Delegasi ke admin handler
    elif data.startswith("adm_") or data.startswith("sp_") \
         or data.startswith("fj_") or data.startswith("bc_") \
         or data.startswith("testcall_"):
        from . import admin_menu
        await admin_menu.handle_admin(event, uid, data)


# ── Sub-show functions ──
async def _show_market(event, coin):
    try:
        results = await asyncio.gather(
            market.get_price(coin), market.get_rsi(coin, "4h", 14),
            market.get_ma_cross(coin, "4h"), market.get_funding(coin),
            market.get_fear_greed(), return_exceptions=True)
        price, rsi, ma, funding, fg = results

        def fmt(v, f="{:.2f}"):
            return "—" if isinstance(v, Exception) or v is None else f.format(v)

        if isinstance(price, Exception):
            usd = idr = ch = vol = "—"; ce = ""
        else:
            usd = fmt(price.get("usd")); idr = fmt(price.get("idr"), "{:,.0f}")
            ch = price.get("change_24h")
            ce = "🟢" if (ch or 0) >= 0 else "🔴"
            ch = fmt(ch); vol = fmt(price.get("vol_24h"), "{:,.0f}")

        rsi_s = fmt(rsi)
        m20 = m50 = m200 = "—"
        if not isinstance(ma, Exception):
            m20 = fmt(ma.get("ma20")); m50 = fmt(ma.get("ma50")); m200 = fmt(ma.get("ma200"))
        fund_s = "—" if isinstance(funding, Exception) else fmt(funding.get("funding"), "{:.4f}")
        fg_s = "—" if isinstance(fg, Exception) else f"{fg.get('value')} ({fg.get('label')})"

        text = (f"📈 **Market {coin}**\n\n{LINE}\n"
                f"💵 Harga: **${usd}** / Rp{idr}\n"
                f"{ce} 24h: {ch}%\n📊 Vol: ${vol}\n{LINE}\n"
                f"📉 RSI: {rsi_s}\n📊 MA20: {m20}\n📊 MA50: {m50}\n📊 MA200: {m200}\n{LINE}\n"
                f"💰 Funding: {fund_s}%\n😨 F&G: {fg_s}")
        await safe_edit(event, text, buttons=kb.market_kb(coin))
    except Exception as e:
        await safe_edit(event, f"❌ {e}", buttons=kb.market_kb(coin))


async def _show_pred(event, coin):
    try:
        await safe_edit(event, "🔮 Menganalisis...")
        r = await asyncio.wait_for(prediction.predict(coin), timeout=20)
        reasons = "\n".join(f"• {x}" for x in r["reasons"])
        text = (f"{r['emoji']} **{r['verdict']} — {coin}**\n\n{LINE}\n"
                f"🎯 Skor: {r['score']}\n💪 Keyakinan: {r['confidence']}\n{LINE}\n\n"
                f"**Alasan:**\n{reasons}\n\n⚠️ _Bukan saran finansial._")
        await safe_edit(event, text, buttons=kb.prediction_kb(coin))
    except Exception as e:
        await safe_edit(event, f"❌ {e}", buttons=kb.prediction_kb(coin))


async def _show_news(event, coin):
    try:
        news = await market.get_news(coin, 5)
        if not news:
            text = f"📰 **{coin}**\n\nTidak ada berita."
        else:
            lines = [f"📰 **Berita {coin}**\n\n{LINE}\n"]
            for n in news:
                tl = n["title"].lower()
                impact = "⚪"
                for kw in config.NEWS_KEYWORDS_BULLISH:
                    if kw in tl: impact = "🟢 Bullish"; break
                for kw in config.NEWS_KEYWORDS_BEARISH:
                    if kw in tl: impact = "🔴 Bearish"; break
                lines.append(f"• [{n['title']}]({n['url']})\n  {impact} _{n['src']}_\n")
            text = "\n".join(lines)
        await safe_edit(event, text, buttons=kb.news_kb(coin), link_preview=False)
    except Exception as e:
        await safe_edit(event, f"❌ {e}", buttons=kb.news_kb(coin))


async def _show_portfolio(event, uid):
    portfolio = await db.get_portfolio(uid)
    if not portfolio:
        await safe_edit(event, "💼 Kosong.\n\n`/add COIN AMOUNT BUY_PRICE`",
                        buttons=kb.back_main(b"m_trading_menu"))
        return
    lines = [f"💼 **Portfolio**\n\n{LINE}\n"]
    tv = tc = 0.0
    for p in portfolio:
        try:
            pd = await market.get_price(p["coin"])
            cur = pd.get("usd") or 0
        except Exception:
            cur = 0
        val = cur * p["amount"]; cost = p["buy_price"] * p["amount"]
        pl = val - cost; plp = (pl / cost * 100) if cost else 0
        tv += val; tc += cost
        emoji = "🟢" if pl >= 0 else "🔴"
        lines.append(f"{emoji} **{p['coin']}** {p['amount']}\n"
                     f"   ${p['buy_price']:,.2f} → ${cur:,.2f} | P/L ${pl:,.2f} ({plp:+.2f}%)")
    tpl = tv - tc; tplp = (tpl / tc * 100) if tc else 0
    lines.append(f"\n{LINE}\n💰 Total: ${tv:,.2f}\n📊 P/L: ${tpl:,.2f} ({tplp:+.2f}%)")
    await safe_edit(event, "\n".join(lines), buttons=[
        [Button.inline("🗑️ Reset", b"port_reset")],
        [Button.inline("⬅️ Kembali", b"m_trading_menu")]])


async def _show_paper(event, uid):
    bal = await db.paper_get_balance(uid)
    holdings = await db.paper_get_holdings(uid)
    total = bal["balance"]
    lines = [f"🎮 **Paper Trading**\n\n{LINE}\n",
             f"💵 Cash: ${bal['balance']:,.2f}",
             f"📊 Initial: ${bal['initial']:,.2f}"]
    if holdings:
        lines.append(f"\n**Holdings:**")
        for h in holdings:
            try:
                p = await market.get_price(h["coin"])
                cur = p.get("usd") or 0
            except Exception:
                cur = 0
            val = cur * h["amount"]
            total += val
            pl = val - (h["buy_price"] * h["amount"])
            emoji = "🟢" if pl >= 0 else "🔴"
            lines.append(f"{emoji} {h['coin']} {h['amount']} @ ${h['buy_price']:,.2f} | P/L ${pl:,.2f}")
    lines.append(f"\n{LINE}\n💰 Total: ${total:,.2f}")
    roi = (total - bal["initial"]) / bal["initial"] * 100
    lines.append(f"📈 ROI: {roi:+.2f}%")
    lines.append(f"\n`/paper buy BTC 0.1` / `/paper sell BTC 0.1`")
    await safe_edit(event, "\n".join(lines), buttons=kb.paper_kb())


async def _show_report(event, uid):
    alerts = await db.get_user_alerts(uid)
    portfolio = await db.get_portfolio(uid)
    logs = await db.get_alert_logs(uid, 10)
    tv = 0.0
    for p in portfolio:
        try:
            pd = await market.get_price(p["coin"])
            tv += (pd.get("usd") or 0) * p["amount"]
        except Exception:
            pass
    lines = [f"📅 **Laporan**\n\n{LINE}\n",
             f"🔔 Alert: {len(alerts)}",
             f"  ├ 🟢 {sum(1 for a in alerts if a['priority']=='low')}",
             f"  ├ 🟡 {sum(1 for a in alerts if a['priority']=='medium')}",
             f"  └ 🔴 {sum(1 for a in alerts if a['priority']=='critical')}",
             f"📊 Triggered: {len(logs)}",
             f"💼 Portfolio: {len(portfolio)}",
             f"💰 Nilai: ${tv:,.2f}\n{LINE}\n",
             "**Top Coins:**"]
    for c in ["BTC", "ETH", "SOL", "BNB"]:
        try:
            p = await market.get_price(c)
            ch = p.get("change_24h") or 0
            e = "🟢" if ch >= 0 else "🔴"
            lines.append(f"{e} {c}: ${p.get('usd'):,.2f} ({ch:+.2f}%)")
        except Exception:
            lines.append(f"⚪ {c}: —")
    if logs:
        lines.append(f"\n{LINE}\n**🔥 5 Trigger:**")
        for l in logs[:5]:
            e = {"naik": "📈", "turun": "📉", "trailing": "📊"}.get(l["tipe"], "•")
            lines.append(f"{e} {l['coin']} {l['tipe']} @ ${l['harga']:,.2f}")
    await safe_edit(event, "\n".join(lines), buttons=kb.back_main())