LINE = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


def welcome(name):
    return (
        f"🚀 **CRYPTO ALERT BOT** 🚀\n{LINE}\n\n"
        f"👋 Halo, **{name}**!\n\n"
        f"Bot ini memantau harga crypto 24/7 dan akan "
        f"menelfon Anda saat target tercapai.\n\n"
        f"📋 **MENU UTAMA**\nPilih menu di bawah untuk mulai 👇"
    )


def contact_gate():
    return (
        f"💾 **SIMPAN KONTAK** 💾\n{LINE}\n\n"
        f"Untuk mengaktifkan fitur telfon, simpan kontak userbot.\n\n"
        f"📝 **Tanpa simpan kontak:**\n"
        f"• Alert tetap masuk via chat ✅\n"
        f"• Tapi TIDAK bisa ditelfon ❌\n\n"
        f"1️⃣ Klik tombol di bawah\n"
        f"2️⃣ Pilih **Simpan Kontak**\n"
        f"3️⃣ Klik **✅ Saya Sudah Simpan**"
    )


def force_join():
    return (
        f"🔒 **AKSES TERBATAS** 🔒\n{LINE}\n\n"
        f"Silakan join channel berikut terlebih dahulu 👇"
    )


def onboarding(name):
    return (
        f"👋 **Selamat datang, {name}!**\n\n{LINE}\n\n"
        f"Saya Crypto Alert Bot. Saya akan memantau harga crypto "
        f"24/7 dan **menelfon Anda** saat target tercapai.\n\n"
        f"📚 **Setup 3 Langkah:**\n\n"
        f"**1️⃣ Simpan Kontak Userbot**\n    Agar bisa ditelfon\n\n"
        f"**2️⃣ Set Alert Pertama**\n    Pilih coin + persen\n\n"
        f"**3️⃣ Selesai!**\n    Bot akan bekerja otomatis\n\n"
        f"{LINE}\n\nMulai dari langkah 1:"
    )


def test_call_panel():
    return (
        f"📞 **PUSAT TEST CALL** 📞\n{LINE}\n\n"
        f"Uji koneksi voice call userbot kapan saja Anda butuhkan.\n\n"
        f"⚡ **Sekarang** — panggilan diproses dalam hitungan detik\n"
        f"🕐 **Jadwalkan** — tentukan sendiri waktu panggilannya\n\n"
        f"Silakan pilih salah satu opsi di bawah 👇"
    )


def test_call_schedule_menu():
    return (
        f"🕐 **JADWALKAN TEST CALL** 🕐\n{LINE}\n\n"
        f"Pilih kapan panggilan uji ingin dijalankan.\n"
        f"Bot akan menghubungi secara otomatis tepat waktu."
    )


def test_call_queued_now():
    return (
        f"⚡ **Test Call Diproses** ⚡\n{LINE}\n\n"
        f"📞 Panggilan akan segera berlangsung dalam beberapa saat.\n"
        f"Pantau hasilnya lewat tombol **Cek Status** di bawah."
    )


def test_call_queued_schedule(when):
    return (
        f"🕐 **Test Call Terjadwal** 🕐\n{LINE}\n\n"
        f"📅 Waktu   : **{when}**\n"
        f"📞 Panggilan akan berjalan otomatis begitu waktunya tiba.\n\n"
        f"Pantau hasilnya lewat tombol **Cek Status** di bawah."
    )


def test_call_history(rows):
    icon = {"pending": "⏳", "completed": "✅", "failed": "❌"}
    mode_icon = {"schedule": "🕐", "now": "⚡"}
    header = f"📋 **RIWAYAT TEST CALL** 📋\n{LINE}\n\n"
    if not rows:
        return header + "Belum ada riwayat test call."
    lines = []
    for r in rows:
        st = r["status"] if r["status"] in icon else "pending"
        mode = r["mode"] if "mode" in r.keys() and r["mode"] in mode_icon else "now"
        waktu = r["scheduled_at"] if (mode == "schedule" and r["scheduled_at"]) else r["created_at"]
        lines.append(
            f"{icon[st]} #{r['id']}  {mode_icon[mode]} {mode.title():<8}  "
            f"**{st.title()}**\n     🕰️ {waktu}"
        )
    return header + "\n\n".join(lines)


def alert_created(coin, atype, persen, priority, baseline):
    label = {"naik": "📈 Naik", "turun": "📉 Turun", "trailing": "📊 Trailing"}[atype]
    pr_emoji = {"low": "🟢", "medium": "🟡", "critical": "🔴"}.get(priority, "🟡")
    return (
        f"✅ **Alert dibuat!**\n\n{LINE}\n"
        f"🪙 Coin       : **{coin}**\n"
        f"{label}      : **{persen}%**\n"
        f"{pr_emoji} Priority   : **{priority.title()}**\n"
        f"💵 Baseline   : ${baseline:,.2f}\n{LINE}\n\n"
        f"Userbot akan menelfon Anda jika target tercapai."
    )


def main_menu_text():
    return (
        f"🏠 **MENU UTAMA**\n{LINE}\n\n"
        f"Pilih kategori di bawah untuk mulai 👇"
    )


def alerts_menu_text():
    return (
        f"🔔 **ALERTS**\n{LINE}\n\n"
        f"Atur notifikasi harga & kelola alert yang sedang aktif."
    )


def analisa_menu_text():
    return (
        f"📊 **ANALISA MARKET**\n{LINE}\n\n"
        f"Cek harga real-time, indikator teknikal, prediksi AI, "
        f"dan berita terbaru."
    )


def trading_menu_text():
    return (
        f"💼 **TRADING**\n{LINE}\n\n"
        f"Kelola portfolio asli atau latihan strategi lewat paper trading."
    )


def settings_text(user):
    daily = "🟢 Aktif" if (user and user["report_daily"]) else "⚪ Nonaktif"
    weekly = "🟢 Aktif" if (user and user["report_weekly"]) else "⚪ Nonaktif"
    voice = (user["voice_choice"] if user else "ardi").title()
    panic = "🔴 AKTIF" if (user and user["panic_mode"]) else "🟢 Normal"
    qs = user["quiet_start"] if user else None
    qe = user["quiet_end"] if user else None
    quiet = f"{qs:02d}:00 - {qe:02d}:00" if qs is not None and qe is not None else "Tidak diatur"
    return (
        f"⚙️ **PENGATURAN**\n{LINE}\n\n"
        f"📅 Laporan Harian    : {daily}\n"
        f"📅 Laporan Mingguan  : {weekly}\n"
        f"🔕 Quiet Hours       : {quiet}\n"
        f"🎙️ Voice             : {voice}\n"
        f"🚨 Panic Mode        : {panic}\n\n"
        f"{LINE}\n\nTap tombol di bawah untuk ubah:"
    )