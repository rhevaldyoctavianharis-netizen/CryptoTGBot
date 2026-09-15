from telethon import Button
from config import COINS, ALERT_TEMPLATES

COIN_LIST = list(COINS.keys())


def main_menu():
    return [
        [Button.inline("🔔 Alerts", b"m_alerts_menu"), Button.inline("📊 Analisa", b"m_analisa_menu")],
        [Button.inline("💼 Trading", b"m_trading_menu"), Button.inline("🎁 Referral", b"m_ref")],
        [Button.inline("⚙️ Pengaturan", b"m_setting"), Button.inline("📅 Laporan", b"m_report")],
        [Button.inline("🚨 EMERGENCY", b"m_panic")],
    ]


def alerts_menu_kb():
    return [
        [Button.inline("🔔 Set Alert", b"m_set")],
        [Button.inline("📋 Status Alert", b"m_status")],
        [Button.inline("🎯 Templates", b"m_tpl")],
        [Button.inline("⬅️ Menu Utama", b"m_main")],
    ]


def analisa_menu_kb():
    return [
        [Button.inline("📈 Market", b"m_market")],
        [Button.inline("🔮 Prediksi", b"m_pred")],
        [Button.inline("📰 Berita", b"m_news")],
        [Button.inline("⬅️ Menu Utama", b"m_main")],
    ]


def trading_menu_kb():
    return [
        [Button.inline("💼 Portfolio", b"m_port")],
        [Button.inline("🎮 Paper Trading", b"m_paper")],
        [Button.inline("⬅️ Menu Utama", b"m_main")],
    ]


def coins_kb(prefix, back=b"m_main"):
    rows, row = [], []
    for i, coin in enumerate(COIN_LIST, 1):
        row.append(Button.inline(coin, f"{prefix}:{coin}".encode()))
        if i % 3 == 0:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([Button.inline("⬅️ Kembali", back)])
    return rows


def type_kb(coin):
    return [
        [Button.inline("📈 Naik", f"atype:naik:{coin}".encode())],
        [Button.inline("📉 Turun", f"atype:turun:{coin}".encode())],
        [Button.inline("📊 Trailing Stop", f"atype:trailing:{coin}".encode())],
        [Button.inline("⬅️ Kembali", b"m_set")],
    ]


def percent_kb(coin, atype):
    return [
        [Button.inline("5%", f"pct:5:{atype}:{coin}".encode()),
         Button.inline("10%", f"pct:10:{atype}:{coin}".encode()),
         Button.inline("20%", f"pct:20:{atype}:{coin}".encode())],
        [Button.inline("30%", f"pct:30:{atype}:{coin}".encode()),
         Button.inline("40%", f"pct:40:{atype}:{coin}".encode()),
         Button.inline("50%", f"pct:50:{atype}:{coin}".encode())],
        [Button.inline("✏️ Input Custom", f"pctc:{atype}:{coin}".encode())],
        [Button.inline("⬅️ Kembali", f"coin:{coin}".encode())],
    ]


def priority_kb(coin, atype, persen):
    return [
        [Button.inline("🟢 Low (chat only)", f"pr:low:{atype}:{coin}:{persen}".encode())],
        [Button.inline("🟡 Medium (chat + telfon)", f"pr:medium:{atype}:{coin}:{persen}".encode())],
        [Button.inline("🔴 Critical (telfon langsung)", f"pr:critical:{atype}:{coin}:{persen}".encode())],
        [Button.inline("⬅️ Kembali", b"m_set")],
    ]


def alert_list_kb(alerts):
    rows = []
    for a in alerts:
        pr_emoji = {"low": "🟢", "medium": "🟡", "critical": "🔴"}.get(a["priority"], "🟡")
        rows.append([Button.inline(
            f"❌ {pr_emoji} {a['coin']} {a['tipe']} {a['persen']}%",
            f"del:{a['id']}".encode())])
    rows.append([Button.inline("🗑️ Hapus Semua", b"del_all")])
    rows.append([Button.inline("⬅️ Kembali", b"m_alerts_menu")])
    return rows


def templates_kb():
    rows = [[Button.inline(t["nama"], f"tpl:{k}".encode())]
            for k, t in ALERT_TEMPLATES.items()]
    rows.append([Button.inline("⬅️ Kembali", b"m_alerts_menu")])
    return rows


def template_confirm_kb(key):
    return [
        [Button.inline("✅ Aktifkan Semua", f"tpl_go:{key}".encode())],
        [Button.inline("❌ Batal", b"m_tpl")],
    ]


def settings_kb(user):
    daily = user["report_daily"] if user else 0
    weekly = user["report_weekly"] if user else 0
    voice = user["voice_choice"] if user else "ardi"
    panic = user["panic_mode"] if user else 0
    qs = user["quiet_start"] if user else None
    qe = user["quiet_end"] if user else None

    quiet_text = "🔕 Set Quiet Hours"
    if qs is not None and qe is not None:
        quiet_text = f"🔕 Quiet: {qs:02d}:00-{qe:02d}:00"

    return [
        [Button.inline(f"{'🟢' if daily else '🔴'} Laporan Harian", b"tg_daily")],
        [Button.inline(f"{'🟢' if weekly else '🔴'} Laporan Mingguan", b"tg_weekly")],
        [Button.inline(quiet_text, b"set_quiet")],
        [Button.inline(f"🎙️ Voice: {voice.title()}", b"set_voice")],
        [Button.inline("🟢 Normal" if not panic else "🔴 PANIC AKTIF", b"tg_panic")],
        [Button.inline("⬅️ Kembali", b"m_main")],
    ]


def voice_kb():
    return [
        [Button.inline("🎙️ Ardi (Pria)", b"voice:ardi")],
        [Button.inline("🎙️ Gadis (Wanita)", b"voice:gadis")],
        [Button.inline("⬅️ Kembali", b"m_setting")],
    ]


def quiet_hours_kb():
    return [
        [Button.inline("23:00 - 07:00", b"quiet:23:7")],
        [Button.inline("22:00 - 06:00", b"quiet:22:6")],
        [Button.inline("00:00 - 08:00", b"quiet:0:8")],
        [Button.inline("✏️ Custom", b"quiet_custom")],
        [Button.inline("🔓 Matikan", b"quiet_off")],
        [Button.inline("⬅️ Kembali", b"m_setting")],
    ]


def paper_kb():
    return [
        [Button.inline("🔄 Reset", b"paper_reset")],
        [Button.inline("⬅️ Kembali", b"m_trading_menu")],
    ]


def panic_kb():
    return [
        [Button.inline("🚨 AKTIFKAN PANIC", b"panic_on")],
        [Button.inline("▶️ Resume Normal", b"panic_off")],
        [Button.inline("⬅️ Kembali", b"m_main")],
    ]


def market_kb(coin):
    return [[Button.inline("🔄 Refresh", f"mkt_refresh:{coin}".encode()),
             Button.inline("🔁 Ganti Coin", b"mkt_change")],
            [Button.inline("⬅️ Kembali", b"m_analisa_menu")]]


def prediction_kb(coin):
    return [[Button.inline("🔄 Refresh", f"pred_refresh:{coin}".encode()),
             Button.inline("🔁 Ganti Coin", b"pred_change")],
            [Button.inline("⬅️ Kembali", b"m_analisa_menu")]]


def news_kb(coin):
    return [[Button.inline("🔄 Refresh", f"news_refresh:{coin}".encode()),
             Button.inline("🔁 Ganti Coin", b"news_change")],
            [Button.inline("⬅️ Kembali", b"m_analisa_menu")]]


def back_main(dest=b"m_main", label="⬅️ Kembali ke Menu"):
    return [[Button.inline(label, dest)]]


def contact_save_kb(userbot_username):
    return [
        [Button.url("💾 Simpan Kontak Userbot", f"https://t.me/{userbot_username}")],
        [Button.inline("✅ Saya Sudah Simpan", b"contact_saved")],
    ]


def force_join_kb(channels, bot_username):
    rows = [[Button.url(f"📢 Join {c['nama']}", c["url"])] for c in channels]
    rows.append([Button.inline("✅ Saya Sudah Join", b"check_join")])
    return rows


# ── Admin ──
def admin_menu():
    return [
        [Button.inline("📊 Statistik", b"adm_stats"), Button.inline("📢 Broadcast", b"adm_bc")],
        [Button.inline("💰 Sponsors", b"adm_sp"), Button.inline("🔒 Force Join", b"adm_fj")],
        [Button.inline("📞 Test Call", b"adm_testcall"), Button.inline("📋 Riwayat Call", b"adm_calllog")],
        [Button.inline("⬅️ Menu Utama", b"m_main")],
    ]


def admin_sponsors_kb(sponsors):
    rows = [[Button.inline(f"❌ {s['nama']}", f"sp_del:{s['id']}".encode())]
            for s in sponsors]
    rows.append([Button.inline("➕ Tambah Sponsor", b"sp_add")])
    rows.append([Button.inline("⬅️ Kembali", b"adm_main")])
    return rows


def admin_force_join_kb(channels):
    rows = [[Button.inline(f"❌ {c['nama']}", f"fj_del:{c['id']}".encode())]
            for c in channels]
    rows.append([Button.inline("➕ Tambah Channel", b"fj_add")])
    rows.append([Button.inline("⬅️ Kembali", b"adm_main")])
    return rows


def admin_broadcast_confirm():
    return [[Button.inline("✅ Kirim ke Semua", b"bc_send")],
            [Button.inline("❌ Batal", b"adm_main")]]


def admin_test_call_kb():
    return [
        [Button.inline("⚡ Sekarang", b"testcall_go"),
         Button.inline("🕐 Jadwalkan", b"testcall_schedule")],
        [Button.inline("🔄 Cek Status", b"testcall_check")],
        [Button.inline("⬅️ Kembali", b"adm_main")],
    ]


def admin_test_call_schedule_kb():
    return [
        [Button.inline("⏱️ 5 Menit", b"testcall_sched:5"),
         Button.inline("⏱️ 15 Menit", b"testcall_sched:15")],
        [Button.inline("⏱️ 30 Menit", b"testcall_sched:30"),
         Button.inline("⏱️ 1 Jam", b"testcall_sched:60")],
        [Button.inline("⬅️ Kembali", b"adm_testcall")],
    ]