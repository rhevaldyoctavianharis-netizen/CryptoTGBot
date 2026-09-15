import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = (os.getenv("API_HASH") or "").strip()
BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0") or "0")
USERBOT_SESSION = (os.getenv("USERBOT_SESSION") or "").strip()
CRYPTOPANIC_KEY = (os.getenv("CRYPTOPANIC_KEY") or "").strip()

# ── Database ──
DB_PATH = "alerts.db"

# ── Timing ──
CHECK_INTERVAL = 30
COOLDOWN_SECONDS = 300
READ_TIMEOUT = 30
MAX_CONCURRENT_CALLS = 3

# ── Call ──
CALL_DURATION = 30
TTS_REPEAT = 2
MUSIC_FILE = "music.mp3"
MUSIC_VOLUME = 0.4
FADE_IN = 3
FADE_OUT = 3

# ── UI ──
THUMBNAIL_FILE = "thumbnail.jpg"

# ── Coins ──
COINS = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "BNB": "binancecoin", "XRP": "ripple", "ADA": "cardano",
    "DOGE": "dogecoin", "AVAX": "avalanche-2", "DOT": "polkadot",
    "MATIC": "matic-network",
}
BINANCE_SYMBOLS = {c: f"{c}USDT" for c in COINS}

COINPAPRIKA_IDS = {
    "BTC": "btc-bitcoin", "ETH": "eth-ethereum", "SOL": "sol-solana",
    "BNB": "bnb-binance-coin", "XRP": "xrp-xrp", "ADA": "ada-cardano",
    "DOGE": "doge-dogecoin", "AVAX": "avax-avalanche", "DOT": "dot-polkadot",
    "MATIC": "matic-polygon",
}

# ── News Keywords ──
NEWS_KEYWORDS_BULLISH = [
    "approve", "partnership", "adoption", "etf", "listing",
    "upgrade", "launch", "integration", "halving", "all-time high",
]
NEWS_KEYWORDS_BEARISH = [
    "hack", "ban", "lawsuit", "sec", "crash", "delist",
    "shutdown", "exploit", "rug", "bankruptcy",
]

# ── Templates ──
ALERT_TEMPLATES = {
    "whale": {
        "nama": "🐋 Whale Entry",
        "desc": "Beli saat dump besar",
        "alerts": [
            ("BTC", "turun", 5.0, "medium"),
            ("ETH", "turun", 7.0, "medium"),
            ("SOL", "turun", 10.0, "medium"),
        ],
    },
    "moon": {
        "nama": "🚀 Moon Shot",
        "desc": "Tangkap momentum pump",
        "alerts": [
            ("BTC", "naik", 10.0, "medium"),
            ("ETH", "naik", 12.0, "medium"),
            ("SOL", "naik", 15.0, "medium"),
        ],
    },
    "safety": {
        "nama": "🛡️ Safety Net",
        "desc": "Lindungi profit dengan trailing stop",
        "alerts": [
            ("BTC", "trailing", 3.0, "critical"),
            ("ETH", "trailing", 5.0, "critical"),
        ],
    },
    "scalp": {
        "nama": "📈 Scalping",
        "desc": "Profit kecil tapi cepat",
        "alerts": [
            ("BTC", "naik", 2.0, "low"),
            ("ETH", "naik", 2.0, "low"),
        ],
    },
}

VOICE_OPTIONS = {
    "ardi": "id-ID-ArdiNeural",
    "gadis": "id-ID-GadisNeural",
}