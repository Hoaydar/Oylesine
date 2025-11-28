from unittest import result
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.error import BadRequest
import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
import mysql.connector # Artık kullanılmasa da korunuyor
from datetime import datetime, timedelta
import mariadb

# ================== Telegram ==================
TOKEN = "8277717807:AAH7ECeQnOzMrIs7bUkODB99YoBiIBwlzKc" 
CHANNEL_USERNAME = "@goneresminew"

# ================== Betco API ==================
BETCO_TOKEN = "caa44f6274c3479fc69f8f1219227053c0e19492ff63f6f3a0194eb51661f234"
BETCO_GET_CLIENTS_URL = "https://backofficewebadmin.betcostatic.com/api/tr/Client/GetClients"
BETCO_ADD_CLIENT_BONUS_URL = "https://backofficewebadmin.betcostatic.com/api/tr/Client/AddClientToBonus"

# Bonus tipleri -> PartnerBonusId ve Amount
BONUS_MAP = {
    "freespin": {"PartnerBonusId": 604382, "Amount": "500"},
    "freebet": {"PartnerBonusId": 604383, "Amount": "50"}
}

# ================== Token Yönetimi ve DB Config ==================

ADMIN_IDS = [5695472914, 5947341902, 805254965, 1782604827]
SPECIAL_GROUP_ID = -4876211377 

# Token değişim zamanı (başlangıçta None)
last_token_change = None

# ✅ DB Bağlantı Bilgileri (Global bağlantı denemesi kaldırıldı)
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "root",
    "database": "101m"
}

# ---- Bonus Alan Kullanıcılar (telegram kontrol)----
BONUS_USERS_FILE = "bonus_users.json"
USERS_FILE = "users.json"
print("🚀 Kod başladı")

def has_taken_bonus(user_id: int) -> bool:
    """Kullanıcı daha önce bonus almış mı kontrol et"""
    try:
        with open(BONUS_USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return user_id in data
    except FileNotFoundError:
        return False

def mark_bonus_given(user_id: int):
    """Kullanıcıya bonus verildiyse kaydet"""
    try:
        with open(BONUS_USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []

    if user_id not in data:
        data.append(user_id)
        with open(BONUS_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def save_user(user_id: int):
    """Kullanıcının ID'sini JSON dosyasına kaydeder."""
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = []

    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

# ================== /settoken Komutu ==================
async def set_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BETCO_TOKEN, last_token_change

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Yetki kontrolü
    if chat_id != SPECIAL_GROUP_ID and (update.effective_chat.type != "private" or user_id not in ADMIN_IDS):
        await update.message.reply_text("❌ Bu komutu kullanmaya yetkiniz yok!")
        return

    if not context.args:
        await update.message.reply_text("❌ Kullanım: /settoken <yeni_token>")
        return

    # ✅ Tokeni güncelle
    BETCO_TOKEN = context.args[0].strip()
    last_token_change = datetime.utcnow()
    await update.message.reply_text("✅ Betco token başarıyla güncellendi!")

# ================== 10 Saat Sonra Hatırlatma Task ==================
async def token_reminder_task(app):
    global last_token_change
    while True:
        if last_token_change:
            now = datetime.utcnow()
            # 10 saat geçmiş mi kontrol et
            if now - last_token_change >= timedelta(hours=10):
                for admin_id in ADMIN_IDS:
                    try:
                        await app.bot.send_message(admin_id, "⚠️ Betco token 10 saat oldu, güncellemeniz gerekebilir!")
                    except Exception as e:
                        print(f"Mesaj gönderilemedi: {e}")
                last_token_change = None 
        await asyncio.sleep(60 * 60) 

# ---- Yardımcı: Betco API çağrısı
async def betco_post(url: str, payload: dict):
    headers = {
        "authentication": BETCO_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://backoffice.betcostatic.com",
        "Referer": "https://backoffice.betcostatic.com/",
        "User-Agent": "Mozilla/5.0 TelegramBot"
    }
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(url, headers=headers, json=payload) as resp:
                text = await resp.text()
                status = resp.status

                print("BETCO POST", url, "STATUS:", status)
                print("REQUEST PAYLOAD:", json.dumps(payload, ensure_ascii=False))
                print("RESPONSE TEXT (first 800 chars):", text[:800])

                if status == 401:
                    return {"HasError": True, "AlertMessage": "401 Unauthorized (Token geçersiz/expired)"}
                if status == 403:
                    return {"HasError": True, "AlertMessage": "403 Forbidden (Yetki/Origin/Referer reddedildi)"}
                if status >= 500:
                    return {"HasError": True, "AlertMessage": f"Sunucu hatası: {status}"}

                try:
                    return json.loads(text)
                except Exception:
                    return {"HasError": True, "AlertMessage": "JSON parse edilemedi", "_raw": text, "_status": status}
        except Exception as e:
            return {"HasError": True, "AlertMessage": f"Request exception: {e}"}

# ---- Kullanıcı arama fonksiyonları ----
def extract_users(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "Data" in data and isinstance(data["Data"], dict):
            if "Objects" in data["Data"] and isinstance(data["Data"]["Objects"], list):
                return data["Data"]["Objects"]
        for key in ("Items", "Rows", "Clients"):
            if key in data and isinstance(data[key], list):
                return data[key]
        for key in ("Login", "UserName", "NickName"):
            if key in data:
                return [data]
    return []

async def betco_find_user(username: str):
    base_payload = {
        "Login": username,
        "IsOrderedDesc": True,
        "MaxRows": 20,
        "SkeepRows": 0,
        "IsStartWithSearch": False,
    }
    data1 = await betco_post(BETCO_GET_CLIENTS_URL, base_payload)
    users = extract_users(data1)
    if not users:
        payload2 = dict(base_payload)
        payload2["IsStartWithSearch"] = True
        data2 = await betco_post(BETCO_GET_CLIENTS_URL, payload2)
        users = extract_users(data2)

    uname = username.strip().lower()
    exact = [
        u for u in users if any(
            isinstance(u.get(k), str) and u.get(k).strip().lower() == uname
            for k in ("Login", "UserName", "NickName")
        )
    ]
    if exact:
        return {"ok": True, "user": exact[0], "raw": users}

    partial = [
        u for u in users if any(
            isinstance(u.get(k), str) and uname in u.get(k).strip().lower()
            for k in ("Login", "UserName", "NickName")
        )
    ]
    if partial:
        return {"ok": True, "user": partial[0], "raw": users}

# ================== Telegram Bot Mantığı ==================
async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except BadRequest:
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await check_membership(user_id, context):
        await update.message.reply_text(
            f"🎉 Tebrikler {update.effective_user.first_name}! Kanalımıza başarıyla katıldınız.\n"
            "Artık bonusunuzu alabilmek için bana Betco kullanıcı adınızı yazınız."
        )
    else:
        await send_invite_message(update)

async def send_invite_message(update: Update):
    user_name = update.effective_user.first_name
    photo_url = "https://r.resimlink.com/wcgRmJG.jpg"
    caption_text = f"""Sayın {user_name}, Telegram kanalımızı henüz takibe almadığınız için etkinliğimizden yararlanamamaktasınız. 

📢 Kanalımıza katılmak için lütfen aşağıdaki butona tıklayınız """
    keyboard = [
        [InlineKeyboardButton("🎯 Kanala katılmak için hemen tıkla", url="https://t.me/goneresminew")],
        [InlineKeyboardButton("🎯 Kanala katıldım", callback_data="joined")]
    ]
    await update.message.reply_photo(photo=photo_url, caption=caption_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "joined":
        if await check_membership(user_id, context):
            await query.edit_message_caption(
                caption=f"🎉 Tebrikler {query.from_user.first_name}! Kanalımıza başarıyla katıldınız.\n"
                        "Artık bonusunuzu alabilmek için bana Betco kullanıcı adınızı yazınız."
            )
        else:
            await query.answer("❌ Hâlâ kanala katılmamışsınız!", show_alert=True)

# ================== Bonus Verme Fonksiyonu ==================
async def give_bonus(client_id: int, bonus_type: str):
    bonus_cfg = BONUS_MAP.get(bonus_type)
    if not bonus_cfg:
        return {"HasError": True, "AlertMessage": f"Bilinmeyen bonus tipi: {bonus_type}"}

    payload = {
        "ClientId": client_id,
        "MessageChannel": None,
        "Amount": bonus_cfg["Amount"],
        "MessageSubject": None,
        "MessageContent": None,
        "Count": None,
        "PartnerBonusId": bonus_cfg["PartnerBonusId"]
    }

    print(f"[BONUS REQUEST] client_id={client_id}, type={bonus_type}, payload={payload}")
    resp = await betco_post(BETCO_ADD_CLIENT_BONUS_URL, payload)
    return resp

# ================== FreeBet Yükleme Fonksiyonu (Korundu) ==================
async def give_freebet(client_id: int):
    payload = {
        "ClientId": client_id,
        "MessageChannel": None,
        "Amount": "50",
        "MessageSubject": None,
        "MessageContent": None,
        "Count": None,
        "PartnerBonusId": 604383 
    }

    print(f"[FREEBET REQUEST] client_id={client_id}, payload={payload}")
    resp = await betco_post(BETCO_ADD_CLIENT_BONUS_URL, payload)
    return resp

# ---- Betco: GetClientById ----
async def betco_get_user_by_id(client_id: int):
    url = f"https://backofficewebadmin.betcostatic.com/api/tr/Client/GetClientById?id={client_id}"
    headers = {
        "authentication": BETCO_TOKEN,
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 TelegramBot"
    }
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as resp:
            text = await resp.text()
            try:
                return json.loads(text)
            except Exception:
                return {"HasError": True, "AlertMessage": "JSON parse edilemedi", "_raw": text}

async def betco_get_last_login_ip(client_id: int):
    url = "https://backofficewebadmin.betcostatic.com/api/tr/Client/GetLogins"
    payload = {
        "ClientId": client_id,
        "StartDate": None,
        "EndDate": None,
        "MaxRows": 10,
        "SkipRows": 0
    }
    result = await betco_post(url, payload)
    try:
        objects = result.get("Data", {}).get("Objects", [])
        if objects and "LoginIP" in objects[0]:
            return objects[0]["LoginIP"]
    except Exception:
        pass
    return None

# --- IP çakışması kontrol fonksiyonu ---
async def check_ip_conflict(ip: str):
    url = "https://backofficewebadmin.betcostatic.com/api/tr/Client/GetClientsByIPAddress"
    payload = {
        "LoginIP": ip,
        "SkeepRows": 0,
        "MaxRows": 10
    }

    result = await betco_post(url, payload)

    try:
        count = result.get("Data", {}).get("Count", 0)
        objects = result.get("Data", {}).get("Objects", [])

        # --- Terminal log ---
        print(f"\n[IP KONTROL] {ip} adresi {count} kullanıcı tarafından kullanılıyor.")
        for obj in objects:
            cid = obj.get("ClientId")
            uname = obj.get("Login") or obj.get("Username")
            print(f"   → KullanıcıID: {cid}, Username: {uname}")

        ip_conflict = count > 1
        return ip_conflict, objects
    except Exception as e:
        print(f"[HATA][check_ip_conflict] {e}")
        return False, []

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user_id = update.effective_user.id
    
    # ✅ Kullanıcı daha önce bonus almış mı kontrol et
    if has_taken_bonus(tg_user_id):
        await update.message.reply_text("⚠️ Bu Telegram hesabı üzerinden daha önce bonus alındı!")
        return
    
    username = (update.message.text or "").strip()
    if not username:
        return

    tg_user_id = update.effective_user.id
    save_user(tg_user_id)
    await update.message.reply_text("🔍 Kullanıcı adı sorgulanıyor, lütfen bekleyin...")

    # --- 1) Betco'da kullanıcı ara (varsa) ---
    api_result = None
    try:
        api_result = await betco_find_user(username)
    except Exception:
        api_result = None

    user = (api_result.get("user") if api_result else {}) or {}
    client_id = user.get("Id")
    detail = {}
    if client_id:
        try:
            detail_resp = await betco_get_user_by_id(client_id)
            if detail_resp and not detail_resp.get("HasError"):
                detail = detail_resp.get("Data") or {}
        except Exception:
            detail = {}

     # --- 2) Veritabanı sorgusu için gerekli veriler ---
    FirstName = (detail.get("FirstName") or user.get("FirstName") or "") or ""
    MiddleName = (detail.get("MiddleName") or user.get("MiddleName") or "") or ""
    LastName = (detail.get("LastName") or user.get("LastName") or "") or ""
    DocNumber = (detail.get("DocNumber") or user.get("DocNumber") or "") or ""
    BirthDate = (detail.get("BirthDate") or user.get("BirthDate") or "") or ""

    conn = None
    rows = []

    try:
        # TC numarası → zorunlu
        if not DocNumber:
            await update.message.reply_text("❌ Kullanıcının TC bilgisi bulunamadı, doğrulama yapılamıyor.")
            return
        
        # Doğum Tarihi → zorunlu
        birth_year = None
        if not BirthDate:
            await update.message.reply_text("❌ Kullanıcının doğum tarihi bulunamadı, doğrulama yapılamıyor.")
            return
        try:
            birthdate_obj = datetime.fromisoformat(BirthDate.split("T")[0])
            birth_year = birthdate_obj.year
        except Exception:
            await update.message.reply_text("❌ Doğum tarihi formatı okunamadı.")
            return
            
        # ✅ BAĞLANTIYI KUR
        conn = mariadb.connect(**DB_CONFIG)
        print("✅ Database bağlantısı kuruldu.")
        
        cursor = conn.cursor()
        clauses = []
        params = []

        clauses.append("TC = %s")
        params.append(DocNumber)

        # DOGUMTARIHI = '9.5.1973' formatında olduğundan LIKE kullanıyoruz
        clauses.append("DOGUMTARIHI LIKE %s")
        params.append(f"%{birth_year}")
        

        # ADI kolonu (FirstName + MiddleName)
        full_name = FirstName
        if MiddleName:
            full_name += f" {MiddleName}"
        if full_name:
            clauses.append("UPPER(ADI) = %s")
            params.append(full_name.upper())

        # Soyadı
        if LastName:
            clauses.append("UPPER(SOYADI) = %s")
            params.append(LastName.upper())

        if clauses:
            sql = "SELECT * FROM 101m WHERE " + " AND ".join(clauses)
            print("DEBUG SQL:", sql, "PARAMS:", params)
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            
        cursor.close()
    
    except mariadb.Error as e:
        await update.message.reply_text(f"❌ Veritabanı sorgusunda hata: {e}")
        return
    except Exception as e:
        await update.message.reply_text(f"❌ Beklenmedik bir hata oluştu: {e}")
        return
    finally:
        # ✅ BAĞLANTIYI KAPAT
        if conn and conn.open:
            conn.close()
            print("Database bağlantısı kapatıldı.")

    # --- DB eşleşmesi kontrolü ---
    if not rows:
        await update.message.reply_text("❌ TC veya diğer bilgiler doğrulanmadı. \n \nEğer yanlış kullanıcı adı yazdıysanız tekrar deneyin. \n \n Eğer bilgileriniz size ait ise lütfen destek ile iletişime geçin.")
        return
    
    # --- 3) DB eşleşmesi varsa --- 
    if rows:
        await update.message.reply_text("✅ TC doğrulandı, diğer filtrelere geçiliyor...")

        # Eğer ilk sorguda kullanıcı bulunamadıysa tekrar Betco'da arama
        if not (api_result and api_result.get("ok")):
            try:
                api_result = await betco_find_user(username)
            except Exception as e:
                await update.message.reply_text(f"❌ Betco sorgusunda hata oluştu: {e}")
                return

        if not api_result or not api_result.get("ok"):
            await update.message.reply_text(
                "⚠️ Veritabanında eşleşme bulundu fakat Betco sisteminde kullanıcı bulunamadı. "
                "Lütfen destek ile iletişime geçin."
            )
            return

        user = api_result.get("user", {}) or {}
        client_id = user.get("Id")
        if not client_id:
            await update.message.reply_text("⚠️ Kullanıcı ID bulunamadı, işlem yapılamıyor.")
            return

        # Kullanıcı detaylarını tekrar çek (ClientById)
        detail = {}
        try:
            detail_resp = await betco_get_user_by_id(client_id)
            if not detail_resp or detail_resp.get("HasError"):
                await update.message.reply_text("❌ Kullanıcı detayları alınamadı.")
                return
            detail = detail_resp.get("Data", {}) or {}
        except Exception:
            await update.message.reply_text("❌ Kullanıcı detayları alınamadı.")
            return
            
        # --- Kayıt tarihi filtresi (Son 7 gün) ---
        created_date_str = detail.get("CreatedLocalDate") or user.get("CreatedLocalDate")
        if created_date_str:
            try:
                created_date = datetime.fromisoformat(created_date_str.split("T")[0])
                today = datetime.now().date()
                cutoff = datetime.combine(today - timedelta(days=7), datetime.min.time())
                cutoff_date_str_fmt = cutoff.strftime("%d.%m.%Y")

                if created_date < cutoff:
                    await update.message.reply_text(
                        f"❌ {cutoff_date_str_fmt} tarihinden önce kayıt olduğunuz için bonus hakkınız bulunmamaktadır."
                    )
                    return
            except Exception as e:
                print(f"CreatedLocalDate parse hatası: {e}, value={created_date_str}")
                
        # Daha önce casino oynamış mı?
        last_casino_bet = detail.get("LastCasinoBetLocalDate") or detail.get("LastCasinoBetTime")
        if last_casino_bet:
            await update.message.reply_text(
                "⚠️ Daha önceden casino oynamış olduğunuz için bonus hakkınız bulunmamaktadır."
            )
            return
            
        # Daha önce yatırım yapmış mı?
        first_deposit = detail.get("FirstDepositLocalDate") or detail.get("FirstDepositTime")
        if first_deposit:
            await update.message.reply_text(
                "⚠️ Daha önceden yatırım yaptığınız için bonus hakkınız bulunmamaktadır."
            )
            return

        
        # Bonus geçmişi kontrolü
        try:
            bonuses_payload = {
                "StartDateLocal": None, "EndDateLocal": None, "BonusType": None,
                "AcceptanceType": None, "ClientBonusId": "", "PartnerBonusId": "", 
                "PartnerExternalBonusId": "", "ClientId": client_id
            }
            bonuses_resp = await betco_post(
                "https://backofficewebadmin.betcostatic.com/api/tr/Client/GetClientBonuses",
                bonuses_payload
            )
        except Exception:
            await update.message.reply_text("❌ Bonus geçmişi sorgulanırken hata oluştu.")
            return

        if not bonuses_resp or bonuses_resp.get("HasError"):
            await update.message.reply_text("❌ Bonus geçmişi alınamadı, işlem iptal edildi.")
            return

        bonuses_data = bonuses_resp.get("Data", [])

        def has_active_noncancelled_bonus(bonus_items):
            items = []
            if isinstance(bonus_items, dict):
                items = bonus_items.get("Objects", []) or []
            elif isinstance(bonus_items, list):
                items = bonus_items
            for b in items:
                if b and b.get("CancellationNote") is None and b.get("Status") not in ("Cancelled", "Deleted", "Expired"):
                    return True
            return False

        if has_active_noncancelled_bonus(bonuses_data):
            await update.message.reply_text("⚠️ Üzgünüz, daha önce bonus alma hakkınızı kullanmış bulunmaktasınız.")
            return

        if user.get("HasReceivedBonus"):
            await update.message.reply_text("⚠️ Daha önce bonus almışsınız. Tekrar bonus alamazsınız.")
            return
        
        # Kayıt tarihi kontrolü (15.09.2025 cutoff - korunuyor)
        created_date_str = detail.get("CreatedLocalDate") or user.get("CreatedLocalDate")
        if created_date_str:
            try:
                created_date = datetime.fromisoformat(created_date_str.split("T")[0])
                cutoff = datetime(2025, 9, 15)

                if created_date < cutoff:
                    await update.message.reply_text(
                        f"❌ 15.09.2025 tarihinden önce kayıt olduğunuz için bonus hakkınız bulunmamaktadır."
                    )
                    return
            except Exception as e:
                print(f"CreatedLocalDate parse hatası: {e}, value={created_date_str}")

    # ---- IP çakışması kontrolü ----
    if client_id:
        last_ip = await betco_get_last_login_ip(client_id)
        if last_ip:
            ip_conflict, users_with_same_ip = await check_ip_conflict(last_ip)
            if ip_conflict:
                await update.message.reply_text(
                    f"❌ IP çakışması tespit edildi! Bu IP {len(users_with_same_ip)} kullanıcı tarafından kullanılıyor.\n"
                    "⚠️ Bu nedenle bonus alamazsınız."
                )
                return
                
        # Bonus seçenekleri
        keyboard = [
            [InlineKeyboardButton("🎰 500 FreeSpin", callback_data=f"bonus_freespin_{client_id}")],
            [InlineKeyboardButton("⚽ 50 FreeBet", callback_data=f"bonus_freebet_{client_id}")]
        ]
        await update.message.reply_text(
            "🎉 Bonusunuzu seçiniz:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # --- 4) DB eşleşmesi yok ama API’de kullanıcı varsa ---
    if api_result and api_result.get("ok") and api_result.get("user"):
        # Bu blok, DB'den geçemeyen ancak Betco'da olan kullanıcılar için.
        # İhtiyacınız olan mesajı yayınlayıp bitiriyoruz.
        await update.message.reply_text( "❌ TC’niz doğrulanamadı!\n \nEğer yanlış kullanıcı adı yazdıysanız lütfen tekrar deneyin.\n\nEğer bilgileriniz size ait ise lütfen destek ile iletişime geçin."
        )
        return

    # Hiçbir yerde bulunamadı
    await update.message.reply_text("❌ Kullanıcı bulunamadı veya yanıt boş.")
# ================== Callback ile Bonus İşlemi ==================
async def bonus_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id 

    # Daha önce bu Telegram hesabından bonus alınmış mı?
    if has_taken_bonus(user_id):
        await query.answer("⚠️ Bu Telegram hesabı üzerinden daha önce bonus alındı!", show_alert=True)
        return

    if data.startswith("bonus_"):
        _, bonus_type, client_id_str = data.split("_")
        client_id = int(client_id_str)

        # ✅ İlk defa alıyorsa API’ye istek atıyoruz
        resp = await give_bonus(client_id, bonus_type)

        if resp.get("HasError"):
            await query.edit_message_text(f"❌ {bonus_type} yüklenemedi: {resp.get('AlertMessage')}")
        else:
            if bonus_type == "freespin":
                await query.edit_message_text("✅ 500 FreeSpin hesabınıza başarıyla yüklendi!")
            elif bonus_type == "freebet":
                await query.edit_message_text("✅ 50 FreeBet hesabınıza başarıyla yüklendi!")
            else:
                await query.edit_message_text("✅ Bonus hesabınıza başarıyla yüklendi!")

            # ✅ Bonus verildi → artık bu Telegram hesabı kilitlendi
            mark_bonus_given(user_id)

# ================== /duyuru Komutu (Resimli) ==================
async def broadcast_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Bu komutu kullanmaya yetkiniz yok!")
        return

    # Komut bir fotoğraf mesajına cevap olarak kullanılmalı
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("❌ Kullanım: /duyuru komutunu bir fotoğraf mesajına cevap olarak gönderiniz.")
        return

    photo = update.message.reply_to_message.photo[-1].file_id
    caption = update.message.reply_to_message.caption or "📢 Yeni duyuru!"

    # users.json içinden kullanıcıları oku
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = []

    if not users:
        await update.message.reply_text("⚠️ Hiç kullanıcı bulunamadı.")
        return

    sent_count = 0
    failed_count = 0

    for uid in users:
        try:
            await context.bot.send_photo(chat_id=uid, photo=photo, caption=caption)
            sent_count += 1
        except Exception as e:
            print(f"❌ {uid} kullanıcısına resimli mesaj gönderilemedi: {e}")
            failed_count += 1

    await update.message.reply_text(
        f"✅ Resimli duyuru gönderildi.\n"
        f"📨 Başarılı: {sent_count}\n"
        f"⚠️ Başarısız: {failed_count}"
    )
# ================== Runner ==================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # 10 saatlik hatırlatmayı başlat
    app.job_queue.run_repeating(token_reminder_task, interval=3600, first=0, name="token_reminder_task")

    app.add_handler(CallbackQueryHandler(bonus_button_handler, pattern="^bonus_"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("settoken", set_token)) 
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))
    app.add_handler(CommandHandler("duyuru", broadcast_photo))
    print("Bot çalışmaya başladı...")
    app.run_polling()