import aiosqlite
import secrets
from config import DB_PATH
from ._core import now


async def register_user(uid, uname, referred_by=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
        if await cur.fetchone():
            return False
        code = f"ref_{secrets.token_hex(4)}"
        await db.execute(
            "INSERT INTO users (user_id, username, referral_code, referred_by, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (uid, uname, code, referred_by, now()))
        await db.commit()
        return True


async def get_user(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (uid,))
        return await cur.fetchone()


async def set_user_setting(uid, field, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, uid))
        await db.commit()


async def set_user_contact_saved(uid, val=1):
    await set_user_setting(uid, "contact_saved", val)


async def set_user_call_privacy(uid, available, private):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET call_available=?, call_private=?, privacy_checked_at=? "
            "WHERE user_id=?",
            (1 if available else 0, 1 if private else 0, now(), uid))
        await db.commit()


async def count_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        row = await cur.fetchone()
        return row[0] if row else 0


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT user_id, username FROM users")
        return await cur.fetchall()


async def get_user_by_referral_code(code):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE referral_code=?", (code,))
        return await cur.fetchone()