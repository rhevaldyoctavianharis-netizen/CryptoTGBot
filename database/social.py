import aiosqlite
from config import DB_PATH
from ._core import now


# ── Sponsors ──
async def add_sponsor(nama, url):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO sponsors (nama, url, aktif, created_at) VALUES (?, ?, 1, ?)",
            (nama, url, now()))
        await db.commit()


async def get_sponsors(only_active=True):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM sponsors" + (" WHERE aktif=1" if only_active else "") \
            + " ORDER BY id DESC"
        cur = await db.execute(q)
        return await cur.fetchall()


async def delete_sponsor(sid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM sponsors WHERE id=?", (sid,))
        await db.commit()


# ── Force Join ──
async def add_force_join(nama, chat_id, url):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO force_join (nama, chat_id, url, aktif, created_at) "
            "VALUES (?, ?, ?, 1, ?)",
            (nama, chat_id, url, now()))
        await db.commit()


async def get_force_join(only_active=True):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM force_join" + (" WHERE aktif=1" if only_active else "") \
            + " ORDER BY id DESC"
        cur = await db.execute(q)
        return await cur.fetchall()


async def delete_force_join(fid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM force_join WHERE id=?", (fid,))
        await db.commit()


# ── Referrals ──
async def add_referral(referrer_id, referred_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO referrals (referrer_id, referred_id, created_at) "
            "VALUES (?, ?, ?)",
            (referrer_id, referred_id, now()))
        await db.commit()


async def count_referrals(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (uid,))
        row = await cur.fetchone()
        return row[0] if row else 0