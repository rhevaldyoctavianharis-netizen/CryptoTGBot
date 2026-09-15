import aiosqlite
from config import DB_PATH
from ._core import now


# ── Bot config (KV) ──
async def set_config(key, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO bot_config VALUES (?, ?)", (key, value))
        await db.commit()


async def get_config(key, default=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT value FROM bot_config WHERE key=?", (key,))
        row = await cur.fetchone()
        return row[0] if row else default


# ── Pending notifications (fallback chat) ──
async def add_pending_notification(uid, coin, tipe, persen, harga, pct_change, reason=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO pending_notifications "
            "(user_id, coin, tipe, persen, harga, pct_change, reason, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (uid, coin, tipe, persen, harga, pct_change, reason, now()))
        await db.commit()


async def get_pending_notifications():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM pending_notifications WHERE sent=0 ORDER BY id ASC")
        return await cur.fetchall()


async def mark_notification_sent(nid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE pending_notifications SET sent=1 WHERE id=?", (nid,))
        await db.commit()


# ── Test calls ──
async def create_test_call(admin_id, scheduled_at=None):
    """Buat permintaan test call baru.

    scheduled_at=None  -> mode "sekarang", langsung diproses oleh monitor.
    scheduled_at=<str> -> mode "jadwal", baru diproses saat waktunya tiba.
    """
    mode = "schedule" if scheduled_at else "now"
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO test_calls (admin_id, status, mode, scheduled_at, created_at) "
            "VALUES (?, 'pending', ?, ?, ?)",
            (admin_id, mode, scheduled_at, now()))
        await db.commit()
        return cur.lastrowid


async def get_pending_test_call():
    """Ambil test call pending yang sudah waktunya dieksekusi.

    - Mode "sekarang": langsung diambil.
    - Mode "jadwal": hanya diambil begitu scheduled_at <= waktu sekarang.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM test_calls WHERE status='pending' "
            "AND (scheduled_at IS NULL OR scheduled_at <= ?) "
            "ORDER BY id ASC LIMIT 1", (now(),))
        return await cur.fetchone()


async def complete_test_call(tcid, status="completed"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE test_calls SET status=?, completed_at=? WHERE id=?",
            (status, now(), tcid))
        await db.commit()


async def get_recent_test_calls(limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM test_calls ORDER BY id DESC LIMIT ?", (limit,))
        return await cur.fetchall()


# ── Channel posts ──
async def log_channel_post(channel_id, message_id, alert_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO channel_posts (channel_id, message_id, alert_id, created_at) "
            "VALUES (?, ?, ?, ?)",
            (channel_id, message_id, alert_id, now()))
        await db.commit()