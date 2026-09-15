import asyncio
import os
import tempfile
import traceback
import edge_tts
import config
from . import client   # <-- import modul, bukan nama

CALL_SEMAPHORE = asyncio.Semaphore(config.MAX_CONCURRENT_CALLS)

# Error MTProto yang sifatnya TRANSIENT (server Telegram lagi flaky pas
# handshake DH untuk voice call) — retry otomatis, bukan langsung gagal.
TRANSIENT_CALL_ERRORS = (
    "DH_G_A_HASH_INVALID",
    "CALL_ALREADY_ACCEPTED",
    "CALL_ALREADY_DECLINED",
    "PARTICIPANT_VERSION_OUTDATED",
    "CALL_PROTOCOL_LAYER_INVALID",
)
MAX_CALL_RETRIES = 2


async def _tts(text, path, voice="ardi"):
    v = config.VOICE_OPTIONS.get(voice, config.VOICE_OPTIONS["ardi"])
    c = edge_tts.Communicate(text, v)
    await c.save(path)


async def _prepare_music(src):
    if src and os.path.exists(src):
        return src, False
    tmp = tempfile.mktemp(suffix=".mp3")
    cmd = (f'ffmpeg -f lavfi -i "sine=frequency=523:duration=25" '
           f'-af "volume=0.15" -c:a libmp3lame "{tmp}" -y -loglevel quiet')
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: os.system(cmd))
    return tmp, True


async def _play_with_retry(user_id, stream):
    """
    Mulai voice call dengan retry otomatis kalau gagal karena error
    handshake yang transient (mis. DH_G_A_HASH_INVALID). Ini masalah umum
    di sisi Telegram/pytgcalls saat negosiasi kunci enkripsi call gagal
    sesaat — biasanya berhasil kalau dicoba ulang.
    """
    last_err = None
    for attempt in range(1, MAX_CALL_RETRIES + 2):
        try:
            await client.pytg.play(user_id, stream)
            return
        except Exception as e:
            last_err = e
            msg = str(e)
            transient = any(code in msg for code in TRANSIENT_CALL_ERRORS)
            if not transient or attempt > MAX_CALL_RETRIES:
                raise
            print(f"⚠️ Handshake call gagal ({msg}), retry {attempt}/"
                  f"{MAX_CALL_RETRIES} untuk {user_id}...")
            await asyncio.sleep(1.5 * attempt)
    raise last_err


async def call_user(user_id, text, voice="ardi"):
    # Baca status TERKINI dari modul client
    if not client.HAS_CALLS or client.pytg is None:
        print(f"⚠️ call_user: pytgcalls belum siap "
              f"(HAS_CALLS={client.HAS_CALLS}, pytg={client.pytg})")
        return False

    async with CALL_SEMAPHORE:
        tts_mp3 = tempfile.mktemp(suffix=".mp3")
        final_ogg = tempfile.mktemp(suffix=".ogg")
        music_src = None
        generated = False
        try:
            loop = asyncio.get_running_loop()
            await _tts(text, tts_mp3, voice)
            music_src, generated = await _prepare_music(config.MUSIC_FILE)

            repeat = max(1, int(config.TTS_REPEAT))
            dur = config.CALL_DURATION
            vol = config.MUSIC_VOLUME
            fi = config.FADE_IN
            fo = config.FADE_OUT
            fo_start = max(0, dur - fo)

            tts_streams = "".join(
                f"[{i}:a]aformat=sample_rates=48000:sample_fmts=fltp[tts{i}];"
                for i in range(repeat))
            m_idx = repeat
            music_stream = (
                f"[{m_idx}:a]aformat=sample_rates=48000:sample_fmts=fltp,"
                f"aloop=loop=-1:size=2e9,volume={vol},"
                f"afade=t=in:st=0:d={fi}[music];")
            concat = "".join(f"[tts{i}]" for i in range(repeat)) + "[music]"
            fc = (f"{tts_streams}{music_stream}{concat}"
                  f"concat=n={repeat + 1}:v=0:a=1,atrim=0:{dur},"
                  f"asetpts=PTS-STARTPTS,afade=t=out:st={fo_start}:d={fo}[out]")
            inputs = " ".join([f'-i "{tts_mp3}"'] * repeat + [f'-i "{music_src}"'])
            cmd = (f'ffmpeg {inputs} -filter_complex "{fc}" '
                   f'-map "[out]" -c:a libopus -b:a 48k "{final_ogg}" '
                   f'-y -loglevel quiet')
            ret = await loop.run_in_executor(None, lambda: os.system(cmd))
            if ret != 0:
                raise RuntimeError(f"ffmpeg failed (exit={ret})")

            if not os.path.exists(final_ogg) or os.path.getsize(final_ogg) == 0:
                raise RuntimeError("output ogg kosong")

            # pakai MediaStream dari modul client, dengan retry handshake
            await _play_with_retry(user_id, client.MediaStream(final_ogg))
            print(f"📞 Call {user_id} ({repeat}x TTS, {dur}s)")
            await asyncio.sleep(dur)
            try:
                await client.pytg.leave_call(user_id)
            except Exception as e:
                print(f"⚠️ leave_call {user_id}: {e}")
            print(f"📴 Done {user_id}")
            return True

        except Exception as e:
            msg = str(e)
            known_transient = any(code in msg for code in TRANSIENT_CALL_ERRORS)
            print(f"❌ Call fail {user_id}: {msg}")
            if not known_transient:
                traceback.print_exc()
            return False

        finally:
            for f in (tts_mp3, final_ogg):
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass
            if generated and music_src and os.path.exists(music_src):
                try:
                    os.remove(music_src)
                except Exception:
                    pass