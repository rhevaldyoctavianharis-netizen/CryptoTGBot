from services import market
import config
import database as db


async def handle_paper(event):
    uid = event.sender_id
    args = event.pattern_match.group(1).strip().split()
    if not args:
        return
    action = args[0].lower()

    if action == "buy" and len(args) >= 3:
        coin = args[1].upper()
        if coin not in config.COINS:
            await event.reply(f"❌ Coin {coin} tidak didukung.")
            return
        try:
            amount = float(args[2])
        except ValueError:
            await event.reply("❌ Jumlah tidak valid.")
            return
        p = await market.get_price(coin)
        price = p.get("usd") or 0
        cost = price * amount
        bal = await db.paper_get_balance(uid)
        if bal["balance"] < cost:
            await event.reply(f"❌ Saldo kurang. Butuh ${cost:,.2f}")
            return
        await db.paper_set_balance(uid, bal["balance"] - cost)
        await db.paper_add_holding(uid, coin, amount, price)
        await event.reply(
            f"✅ **BUY** {amount} {coin} @ ${price:,.2f}\n"
            f"Total: ${cost:,.2f}\nSisa: ${bal['balance'] - cost:,.2f}")

    elif action == "sell" and len(args) >= 3:
        coin = args[1].upper()
        try:
            amount = float(args[2])
        except ValueError:
            await event.reply("❌ Jumlah tidak valid.")
            return
        holdings = await db.paper_get_holdings(uid)
        target = next((h for h in holdings
                       if h["coin"] == coin and abs(h["amount"] - amount) < 0.0001), None)
        if not target:
            await event.reply(f"❌ Tidak ada holding {coin} {amount}.")
            return
        p = await market.get_price(coin)
        price = p.get("usd") or 0
        revenue = price * amount
        bal = await db.paper_get_balance(uid)
        await db.paper_set_balance(uid, bal["balance"] + revenue)
        await db.paper_remove_holding(target["id"], uid)
        pl = revenue - (target["buy_price"] * amount)
        emoji = "🟢" if pl >= 0 else "🔴"
        await event.reply(
            f"✅ **SELL** {amount} {coin} @ ${price:,.2f}\n"
            f"Revenue: ${revenue:,.2f}\nP/L: {emoji} ${pl:,.2f}")