import aiosqlite
from datetime import datetime, timedelta
from config import DB_PATH


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def future(minutes):
    """Kembalikan timestamp string N menit dari sekarang, untuk penjadwalan."""
    return (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.execute("PRAGMA busy_timeout=5000")

        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT,
            cooldown INTEGER DEFAULT 300, report_daily INTEGER DEFAULT 0,
            report_weekly INTEGER DEFAULT 0, contact_saved INTEGER DEFAULT 0,
            call_available INTEGER DEFAULT 1, call_private INTEGER DEFAULT 0,
            privacy_checked_at TEXT, quiet_start INTEGER, quiet_end INTEGER,
            panic_mode INTEGER DEFAULT 0, voice_choice TEXT DEFAULT 'ardi',
            custom_voice_file TEXT, referral_code TEXT, referred_by INTEGER,
            onboarding_step INTEGER DEFAULT 0, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, coin TEXT,
            tipe TEXT, persen REAL, baseline_price REAL, peak_price REAL,
            aktif INTEGER DEFAULT 1, last_triggered TEXT, called INTEGER DEFAULT 0,
            call_status TEXT, notified_at TEXT,
            priority TEXT DEFAULT 'medium', created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, coin TEXT,
            amount REAL, buy_price REAL, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS alert_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, coin TEXT,
            tipe TEXT, persen REAL, harga REAL, waktu TEXT
        );
        CREATE TABLE IF NOT EXISTS sponsors (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, url TEXT,
            aktif INTEGER DEFAULT 1, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS force_join (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, chat_id TEXT,
            url TEXT, aktif INTEGER DEFAULT 1, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS test_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER,
            status TEXT DEFAULT 'pending', mode TEXT DEFAULT 'now',
            scheduled_at TEXT, created_at TEXT, completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS bot_config (
            key TEXT PRIMARY KEY, value TEXT
        );
        CREATE TABLE IF NOT EXISTS pending_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, coin TEXT,
            tipe TEXT, persen REAL, harga REAL, pct_change REAL,
            reason TEXT, created_at TEXT, sent INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS paper_portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, coin TEXT,
            amount REAL, buy_price REAL, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS paper_balance (
            user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 10000,
            initial REAL DEFAULT 10000
        );
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, referrer_id INTEGER,
            referred_id INTEGER, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS channel_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id TEXT,
            message_id INTEGER, alert_id INTEGER, created_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_aktif ON alerts(aktif);
        CREATE INDEX IF NOT EXISTS idx_pending_sent ON pending_notifications(sent);
        CREATE INDEX IF NOT EXISTS idx_ref_referrer ON referrals(referrer_id);
        """)
        await db.commit()

        # Migrasi ringan untuk database lama (kolom baru fitur jadwal test call)
        for ddl in (
            "ALTER TABLE test_calls ADD COLUMN mode TEXT DEFAULT 'now'",
            "ALTER TABLE test_calls ADD COLUMN scheduled_at TEXT",
        ):
            try:
                await db.execute(ddl)
                await db.commit()
            except Exception:
                pass  # kolom sudah ada, aman diabaikan