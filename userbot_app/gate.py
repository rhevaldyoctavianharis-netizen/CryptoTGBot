from datetime import datetime
from telethon.tl.functions.users import GetFullUserRequest
import database as db
from .client import userbot


async def _check_privacy(user_id):
    try:
        r = await userbot(GetFullUserRequest(user_id))
        uf = r.full_user
        return (bool(getattr(uf, "phone_calls_available", False)),
                bool(getattr(uf, "phone_calls_private", False)))
    except Exception as e:
        print(f"⚠️ privacy {user_id}: {e}")
        return False, True


async def can_call(user_id, alert):
    """
    Return (can_call: bool, reason: str).
    """
    user = await db.get_user(user_id)
    if not user:
        return False, "User tidak terdaftar"

    if user["panic_mode"]:
        return False, "Anda mengaktifkan PANIC MODE. Kirim /resume untuk normal."

    priority = alert["priority"] if "priority" in alert.keys() else "medium"
    if priority == "low":
        return False, "Alert priority Low (chat only)"

    if not user["contact_saved"]:
        return False, "Kontak userbot belum disimpan"

    available, private = await _check_privacy(user_id)
    await db.set_user_call_privacy(user_id, available, private)

    if not available:
        return False, "Privasi Anda memblokir panggilan dari non-kontak"

    if private and not user["contact_saved"]:
        return False, "Privasi: hanya kontak yang bisa menelfon"

    if priority != "critical":
        qs, qe = user["quiet_start"], user["quiet_end"]
        if qs is not None and qe is not None:
            h = datetime.now().hour
            in_q = (qs <= h < qe) if qs < qe else (h >= qs or h < qe)
            if in_q:
                return False, f"Quiet hours aktif ({qs:02d}:00-{qe:02d}:00)"

    return True, ""