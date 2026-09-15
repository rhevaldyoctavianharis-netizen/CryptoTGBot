import aiosqlite
from config import DB_PATH
from ._core import now


async def add_alert(uid, coin, tipe, persen, baseline, priority="medium"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO alerts (user_id, coin, tipe, persen, priority, "
            "baseline_price, peak_price, aktif, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
            (uid, coin, tipe, persen, priority, baseline, baseline, now()))
        await db.commit()


async def get_user_alerts(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM alerts WHERE user_id=? AND aktif=1 ORDER BY id DESC", (uid,))
        return await cur.fetchall()


async def get_all_active_alerts():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM alerts WHERE aktif=1")
        return await cur.fetchall()


async def delete_alert(aid, uid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM alerts WHERE id=? AND user_id=?", (aid, uid))
        await db.commit()


async def delete_all_alerts(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM alerts WHERE user_id=?", (uid,))
        await db.commit()


async def update_alert_price(aid, baseline=None, peak=None):
    sets, vals = [], []
    if baseline is not None:
        sets.append("baseline_price=?"); vals.append(baseline)
    if peak is not None:
        sets.append("peak_price=?"); vals.append(peak)
    if not sets:
        return
    vals.append(aid)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE alerts SET {', '.join(sets)} WHERE id=?", vals)
        await db.commit()


async def verify_alert_owner(aid, uid):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM alerts WHERE id=? AND user_id=? AND aktif=1", (aid, uid))
        return await cur.fetchone() is not None


async def is_alert_called(aid):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT called FROM alerts WHERE id=?", (aid,))
        row = await cur.fetchone()
        return bool(row and row[0])


async def mark_notified(aid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE alerts SET notified_at=? WHERE id=?", (now(), aid))
        await db.commit()


async def mark_called(aid, status):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE alerts SET called=1, call_status=?, last_triggered=? WHERE id=?",
            (status, now(), aid))
        await db.commit()


async def reset_alert_called(aid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE alerts SET called=0, call_status=NULL WHERE id=?", (aid,))
        await db.commit()


async def log_alert(uid, coin, tipe, persen, harga):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO alert_log (user_id, coin, tipe, persen, harga, waktu) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (uid, coin, tipe, persen, harga, now()))
        await db.commit()


async def get_alert_logs(uid, limit=50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM alert_log WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (uid, limit))
        return await cur.fetchall()