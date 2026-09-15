import aiosqlite
from config import DB_PATH
from ._core import now


# ── Portfolio (real) ──
async def add_portfolio(uid, coin, amount, buy):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO portfolio (user_id, coin, amount, buy_price, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (uid, coin, amount, buy, now()))
        await db.commit()


async def get_portfolio(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM portfolio WHERE user_id=?", (uid,))
        return await cur.fetchall()


async def clear_portfolio(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM portfolio WHERE user_id=?", (uid,))
        await db.commit()


# ── Paper trading ──
async def paper_get_balance(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM paper_balance WHERE user_id=?", (uid,))
        row = await cur.fetchone()
        if not row:
            await db.execute(
                "INSERT INTO paper_balance (user_id, balance, initial) VALUES (?, 10000, 10000)",
                (uid,))
            await db.commit()
            cur = await db.execute("SELECT * FROM paper_balance WHERE user_id=?", (uid,))
            row = await cur.fetchone()
        return row


async def paper_set_balance(uid, balance):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE paper_balance SET balance=? WHERE user_id=?", (balance, uid))
        await db.commit()


async def paper_reset(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO paper_balance (user_id, balance, initial) "
            "VALUES (?, 10000, 10000)", (uid,))
        await db.execute("DELETE FROM paper_portfolio WHERE user_id=?", (uid,))
        await db.commit()


async def paper_add_holding(uid, coin, amount, buy_price):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO paper_portfolio (user_id, coin, amount, buy_price, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (uid, coin, amount, buy_price, now()))
        await db.commit()


async def paper_get_holdings(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM paper_portfolio WHERE user_id=?", (uid,))
        return await cur.fetchall()


async def paper_remove_holding(hid, uid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM paper_portfolio WHERE id=? AND user_id=?", (hid, uid))
        await db.commit()