import os
from telethon.errors import MessageNotModifiedError
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError
import config
import database as db


def is_admin(uid):
    return config.SUPER_ADMIN_ID and uid == config.SUPER_ADMIN_ID


async def safe_delete(event):
    try:
        await event.delete()
    except Exception:
        pass


async def safe_edit(event, text, buttons=None, link_preview=True):
    try:
        await event.edit(text, buttons=buttons, link_preview=link_preview)
    except MessageNotModifiedError:
        pass
    except Exception as e:
        print(f"⚠️ edit gagal: {e}")


async def send_panel(uid, text, buttons=None, link_preview=False):
    """
    Kirim PESAN BARU (awal sebuah alur/panel) — selalu pakai thumbnail.jpg
    sebagai media, biar aesthetic dan konsisten. Ini titik krusial: karena
    Telegram tidak bisa menambah media ke pesan teks lewat edit, media
    harus sudah terpasang sejak pesan PERTAMA dibuat. Setelah itu, semua
    safe_edit()/edit_or_send() di pesan yang sama otomatis mempertahankan
    gambarnya walau cuma teksnya yang diedit.
    """
    from .client import client
    if os.path.exists(config.THUMBNAIL_FILE):
        try:
            return await client.send_file(uid, config.THUMBNAIL_FILE,
                                          caption=text, buttons=buttons)
        except Exception as e:
            print(f"⚠️ send_panel gagal pakai thumbnail: {e}")
    return await client.send_message(uid, text, buttons=buttons,
                                     link_preview=link_preview)


async def cb_msg_id(event):
    """
    Ambil message_id dari CallbackQuery secara AMAN. `event.msg_id` biasanya
    ada, tapi sebagian callback event (pesan lama/tipe khusus) bisa tidak
    punya atribut itu dan bikin bot crash. Kalau tidak ada, fallback ke
    get_message() supaya tidak pernah raise AttributeError.
    """
    mid = getattr(event, "msg_id", None)
    if mid:
        return mid
    try:
        msg = await event.get_message()
        return msg.id if msg else None
    except Exception:
        return None


async def edit_or_send(uid, msg_id, text, buttons=None, link_preview=False):
    """
    Edit pesan panel yang sudah ada di chat, bukan kirim pesan baru.
    Dipakai di alur input teks (multi-step) supaya 1 panel = 1 pesan,
    bukan numpuk pesan baru tiap langkah. Kalau edit gagal (pesan
    kadaluarsa/terhapus/dll), baru fallback kirim pesan baru.
    Return message id (dipakai buat lanjutin edit di langkah berikutnya).
    """
    from .client import client
    if msg_id:
        try:
            await client.edit_message(uid, msg_id, text, buttons=buttons,
                                      link_preview=link_preview)
            return msg_id
        except MessageNotModifiedError:
            return msg_id
        except Exception:
            pass
    sent = await client.send_message(uid, text, buttons=buttons,
                                      link_preview=link_preview)
    return sent.id


async def get_unjoined_channels(client, uid):
    channels = await db.get_force_join()
    if not channels:
        return []
    unjoined = []
    for ch in channels:
        try:
            await client(GetParticipantRequest(channel=ch["chat_id"], participant=uid))
        except UserNotParticipantError:
            unjoined.append(ch)
        except Exception:
            continue
    return unjoined


async def sponsor_footer():
    from ui.texts import LINE
    sponsors = await db.get_sponsors()
    if not sponsors:
        return ""
    lines = [f"\n\n{LINE}\n💎 **Sponsor:**"]
    for s in sponsors:
        lines.append(f"• [{s['nama']}]({s['url']})")
    return "\n".join(lines)


async def gate_check(client, event, uid):
    """
    Cek gate: force join & kontak.
    Return True jika user diblokir (sudah kirim pesan gate).
    """
    if is_admin(uid):
        return False
    from ui import texts, keyboards as kb

    unjoined = await get_unjoined_channels(client, uid)
    if unjoined:
        me = await client.get_me()
        await send_panel(uid, texts.force_join(),
                         buttons=kb.force_join_kb(unjoined, me.username))
        return True

    user = await db.get_user(uid)
    if not user or not user["contact_saved"]:
        ub = await db.get_config("userbot_username", "userbot")
        await send_panel(uid, texts.contact_gate(),
                         buttons=kb.contact_save_kb(ub))
        return True
    return False