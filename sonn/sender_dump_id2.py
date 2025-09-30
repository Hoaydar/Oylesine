# collect_message_senders_streaming.py
import asyncio
import json
import time
import os
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from telethon.tl.types import PeerUser, PeerChannel, PeerChat

# ===== AYARLAR =====
API_ID = 28488268
API_HASH = "c3a2afe710010a5636adac325d977a8f"
STRING_SESSION = None   # varsa koyabilirsin
TARGET = '@bahissikayetimvar'   # grup id'si veya @kullaniciadi
JSONL_OUT = "message_senders.ndjson"   # NDJSON (her satır 1 JSON)
RESOLVE_USERS = True    # True: her id için get_entity ile username/isim al (yavaş olabilir)
SAVE_EVERY = 1          # her yeni kullanıcıyı anında kaydet (1 = hemen)
# ===================

def load_seen_and_count(filepath):
    """Var olan NDJSON dosyasından daha önce kaydedilmiş id'leri oku."""
    seen = set()
    count = 0
    if not os.path.exists(filepath):
        return seen, count
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for _line in f:
                line = _line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    uid = obj.get("id")
                    if uid is not None:
                        seen.add(int(uid))
                        count += 1
                except Exception:
                    # bozuk satır atla
                    continue
    except Exception:
        pass
    return seen, count

async def safe_get_entity(client, uid):
    """get_entity ile FloodWait'i yönet."""
    try:
        return await client.get_entity(uid)
    except errors.FloodWaitError as fe:
        wait = int(fe.seconds) + 2
        print(f"[resolve] FloodWait: {wait}s bekleniyor...")
        time.sleep(wait)
        try:
            return await client.get_entity(uid)
        except Exception as e:
            # başarısız olursa None dön
            return None
    except Exception:
        return None

async def gather_and_stream(client, entity, out_path, resolve_users=True):
    seen, start_count = load_seen_and_count(out_path)
    print(f"Önceden kaydedilmiş gönderici sayısı: {len(seen)} (dosyadan okundu).")
    order = start_count

    # aç append modunda; her yazdıktan sonra flush ile dosyada kalıcı olsun
    out_f = open(out_path, "a", encoding="utf-8")

    try:
        print("Mesajlar taranıyor... (yeni -> eski sırasıyla iter_messages çalışır).")
        async for msg in client.iter_messages(entity, limit=None):
            # from_id olabilir: PeerUser(user_id=...), PeerChannel, PeerChat veya None
            fid = None
            if getattr(msg, "from_id", None) is not None:
                fid_obj = msg.from_id
                if hasattr(fid_obj, "user_id"):
                    fid = int(fid_obj.user_id)
                else:
                    try:
                        fid = int(fid_obj)
                    except Exception:
                        fid = None

            if fid is None:
                continue

            if fid in seen:
                continue  # zaten kaydedilmiş
            # yeni kullanıcı
            seen.add(fid)
            order += 1
            entry = {
                "order": order,
                "id": fid,
                "username": None,
                "first_name": None,
                "last_name": None,
                "is_bot": None,
                "first_seen_msg_id": getattr(msg, "id", None),
                "first_seen_date": getattr(msg, "date", None).isoformat() if getattr(msg, "date", None) else None
            }

            if resolve_users:
                user = await safe_get_entity(client, fid)
                if user is not None:
                    entry["username"] = getattr(user, "username", None)
                    entry["first_name"] = getattr(user, "first_name", None)
                    entry["last_name"] = getattr(user, "last_name", None)
                    entry["is_bot"] = bool(getattr(user, "bot", False))

            # NDJSON: her satıra bir JSON objesi
            out_f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            out_f.flush()
            # opsiyonel: küçük gecikme ile flood önleme (çok küçük)
            # time.sleep(0.01)

            if order % 100 == 0:
                print(f"{order} benzersiz gönderici (toplam) kaydedildi...")

    except errors.FloodWaitError as fe:
        wait = int(fe.seconds) + 2
        print(f"[messages] FloodWait: {wait}s bekleniyor...")
        time.sleep(wait)
    except KeyboardInterrupt:
        print("Kullanıcı tarafından durduruldu (CTRL+C). Kaydedildiği kadar kayıt dosyaya yazıldı.")
    except Exception as e:
        print("Beklenmeyen hata:", e)
    finally:
        out_f.close()
        print(f"Dosya kapatıldı. Toplam kayıt: {order} (dosyada bulunanlar da dahil).")

async def main():
    if STRING_SESSION:
        client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    else:
        client = TelegramClient("session", API_ID, API_HASH)

    await client.start()
    me = await client.get_me()
    print(f"Giriş yapıldı: @{me.username or me.first_name} (id={me.id})")

    # entity al
    try:
        entity = await client.get_entity(TARGET)
    except Exception as e:
        print("Hedef entity bulunamadı veya erişim yok:", e)
        await client.disconnect()
        return

    # stream ve kaydet
    await gather_and_stream(client, entity, JSONL_OUT, resolve_users=RESOLVE_USERS)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
