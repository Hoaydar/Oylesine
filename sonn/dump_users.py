import asyncio
import json
import time
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from telethon.tl.types import User

# ===== AYARLAR =====
API_ID = 28488268      # my.telegram.org'dan aldığın api_id
API_HASH = "c3a2afe710010a5636adac325d977a8f"  # api_hash
STRING_SESSION = None   # istersen buraya string session koy
TARGET = -1002924465335  # veya "-1001234567890"
JSON_OUT = "members.json"
# ===================

def member_to_dict(user):
    return {
        "id": user.id,
        "username": getattr(user, "username", None),
        "first_name": getattr(user, "first_name", None),
        "last_name": getattr(user, "last_name", None),
        "phone": getattr(user, "phone", None),
        "is_bot": bool(getattr(user, "bot", False)),
    }

async def fetch_group_members(client, target):
    entity = await client.get_entity(target)

    print("JSON dosyasına yazılıyor:", JSON_OUT)
    f = open(JSON_OUT, "w", encoding="utf-8")
    f.write("[\n")
    first = True
    count = 0

    async for user in client.iter_participants(entity, aggressive=True):
        if not isinstance(user, User):
            continue
        obj = member_to_dict(user)
        j = json.dumps(obj, ensure_ascii=False)
        if not first:
            f.write(",\n")
        f.write(j)
        first = False
        count += 1
        if count % 100 == 0:
            print(f"{count} üye yazıldı...")

    f.write("\n]\n")
    f.close()
    print(f"Tamamlandı — toplam {count} üye kaydedildi. Dosya: {JSON_OUT}")

async def main():
    if STRING_SESSION:
        client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    else:
        client = TelegramClient("session", API_ID, API_HASH)

    await client.start()
    me = await client.get_me()
    print(f"Giriş yapıldı: @{me.username or me.first_name} (id={me.id})")

    while True:
        try:
            await fetch_group_members(client, TARGET)
            break
        except errors.FloodWaitError as fe:
            wait = int(fe.seconds) + 5
            print(f"FloodWait: {wait} saniye bekleniyor...")
            time.sleep(wait)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
