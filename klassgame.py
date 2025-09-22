from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import random
import signal
import sys
from datetime import datetime

# --- COOKIE STRING ---
cookie_string = "4cb2f9b65921a3764f08be04dfcb3a44=1758353948__7Mjg5Nzc5NjU4NTFZUFpSNy0ySUpTRE4tMUJDVzRTNjhDRTVBMUNGMDJFMDE3NTgzNTM5NDg%3D;d5fe1054dca240652d5a0e04d957fa23=d30cc734ac08a2eed1ec9e298292807b;f7a278a0c9779aa260eca8138105b3eb=1;3f46be58e9e603958af6956de0b91395=M;9a89e1f1a137fd1c68ba9e727856d032=soytaraga24%40gmail.com;d532c465722686b81f4a5ac1aded6fdf=rYbhu1-hypwuv-vafmev;568d2c2a2914da32705508867db0b643=1;_gid=GA1.2.810185186.1758547130;cbb6ed018c223b30b054b12420ecdfe7=https%3A%2F%2Fwww.klasgame.com%2Fgiris-yap%2F;PHPSESSID=tvratei5ju0g6bihstglga0e5a;_gcl_au=1.1.672749043.1758353953.1319774559.1758560162.1758560161;_gat_gtag_UA_111439643_1=1;29f3203fae946d94ff2bf7428f0b61b4=8278d939b2e7db7a81d2d40219d9fc5d;_ga_25E93VLEHL=GS2.1.s1758569325$o7$g1$t1758569714$j60$l0$h0;_ga=GA1.1.1236675467.1758353954"

# --- AYARLAR ---
WAIT_FIRST = 10
WAIT_RETURN = 5 * 10
WAIT_ON_ITEM = 3

CATEGORY_URL = "https://www.klasgame.com/revenger-online/revenger-online-gold"
CHECK_URL = CATEGORY_URL  # Satış aktif kontrolü yapılacak sayfa

# Telegram ayarları
import requests
TELEGRAM_TOKEN = "8350444240:AAHbhxHeI2AbPZTXCTe90qkadp7ZzE1sdtI"
USER_IDS = [5695472914,6291821880]

# --- STOP FLAG ---
stop_flag = False
def signal_handler(sig, frame):
    global stop_flag
    log("SIGINT alındı, döngü sonlandırılıyor...")
    stop_flag = True
signal.signal(signal.SIGINT, signal_handler)

# --- LOG ---
def log(msg: str):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
    sys.stdout.flush()

# --- Cookie parser ---
def parse_cookie_string(s: str):
    cookies = []
    for p in s.split(";"):
        p = p.strip()
        if not p or "=" not in p:
            continue
        k, v = p.split("=", 1)
        cookies.append({"name": k.strip(), "value": v.strip()})
    return cookies

# --- Telegram ---
def send_telegram_message(user_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": user_id, "text": text}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        log(f"Telegram mesaj gönderilemedi: {e}")

# --- Selenium başlat ---
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")
options.add_argument("--window-size=800,600")  # Küçük pencere boyutu
driver = webdriver.Chrome(options=options)

# İlk siteyi aç
driver.get(CATEGORY_URL)
time.sleep(3)

# Cookie ekle
for c in parse_cookie_string(cookie_string):
    try:
        driver.add_cookie(c)
    except Exception as e:
        log(f"Cookie eklenemedi: {e}")

driver.refresh()
time.sleep(3)

# --- Main loop ---
# --- Main loop ---
iteration = 0
while not stop_flag:
    iteration += 1
    log(f"--- DÖNGÜ #{iteration} BAŞLADI ---")
    try:
        # Ana sayfayı aç
        driver.get(CHECK_URL)
        log(f"{WAIT_FIRST}s bekleniyor...")
        time.sleep(WAIT_FIRST)

        # Ana sayfada satış kontrolü
        page_src = driver.page_source
        kontrol_mesaji = "Şu an için alış aktif görünmüyor"

        if kontrol_mesaji not in page_src:
            log("✅ Satış aktif bulundu! Telegram mesajı gönderiliyor...")
            for uid in USER_IDS:
                send_telegram_message(uid, f"{CHECK_URL} sayfasında Satış aktif!")
        else:
            log("❌ Satış aktif değil.")

        # Ana sayfadaki linkleri topla ama sadece rastgele gezinme için kullan
        anchors = driver.find_elements(By.TAG_NAME, "a")
        candidates = []
        for a in anchors:
            href = a.get_attribute("href")
            if href and ("/ilan/" in href or "/oyuncu-pazari/" in href or "/revenger-online/" in href):
                candidates.append(href)

        log(f"Aday link sayısı: {len(candidates)}")
        if candidates:
            chosen = random.choice(candidates)
            log(f"Rastgele seçilen link: {chosen} (sadece 3sn kalınıyor)")
            driver.get(chosen)
            time.sleep(3)  # sadece 3 saniye kal
        else:
            log("⚠️ Aday link bulunamadı, bekleniyor...")
            time.sleep(5)

        # Ana sayfaya dön
        driver.get(CATEGORY_URL)
        log(f"{WAIT_RETURN}s bekleniyor...")
        time.sleep(WAIT_RETURN)

    except Exception as e:
        log(f"Beklenmeyen hata: {e}")
        time.sleep(5)

        page_src = driver.page_source
        kontrol_mesaji = "Şu an için alış aktif görünmüyor"

        if kontrol_mesaji not in page_src:
            log("✅ Satış aktif bulundu! Telegram mesajı gönderiliyor...")
            for uid in USER_IDS:
                send_telegram_message(uid, f"{chosen} sayfasında Satış aktif!")
        else:
            log("❌ Bu sayfada satış aktif değil.")

        # Sonraki döngü için bekleme
        log(f"{WAIT_RETURN}s bekleniyor...")
        time.sleep(WAIT_RETURN)

    except Exception as e:
        log(f"Beklenmeyen hata: {e}")
        time.sleep(5)

log("Döngü sonlandırıldı.")
driver.quit()
