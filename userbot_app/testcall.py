import asyncio
import database as db
from .caller import call_user


async def monitor():
    while True:
        try:
            req = await db.get_pending_test_call()
            if req:
                aid = req["admin_id"]; tid = req["id"]
                mode = req["mode"] if "mode" in req.keys() else "now"
                label = "terjadwal" if mode == "schedule" else "instan"
                print(f"📞 Test call #{tid} ({label}) → admin {aid}")
                user = await db.get_user(aid)
                voice = user["voice_choice"] if user else "ardi"
                text = ("Tes panggilan dari Crypto Alert Bot. "
                        "Jika Anda mendengar suara ini, userbot berjalan normal.")
                ok = await call_user(aid, text, voice)
                await db.complete_test_call(tid, "completed" if ok else "failed")
                print(f"🏁 Test #{tid}: {'OK' if ok else 'FAILED'}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"❌ test: {e}")
        await asyncio.sleep(5)