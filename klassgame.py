import requests
from bs4 import BeautifulSoup
import time
import random
import signal
import sys
from datetime import datetime
from urllib.parse import urljoin, urlparse

# --- COOKIE STRING ---
cookie_string = "4cb2f9b65921a3764f08be04dfcb3a44=1758353948__7Mjg5Nzc5NjU4NTFZUFpSNy0ySUpTRE4tMUJDVzRTNjhDRTVBMUNGMDJFMDE3NTgzNTM5NDg%3D;d5fe1054dca240652d5a0e04d957fa23=d30cc734ac08a2eed1ec9e298292807b;f7a278a0c9779aa260eca8138105b3eb=1;_gid=GA1.2.620554446.1758353954;3f46be58e9e603958af6956de0b91395=M;9a89e1f1a137fd1c68ba9e727856d032=soytaraga24%40gmail.com;d532c465722686b81f4a5ac1aded6fdf=rYbhu1-hypwuv-vafmev;PHPSESSID=bjcsmm943qsvnogm597tlei1fg;cbb6ed018c223b30b054b12420ecdfe7=https%3A%2F%2Fwww.google.com%2F;_gcl_au=1.1.672749043.1758353953.273195423.1758371693.1758371692;568d2c2a2914da32705508867db0b643=1;29f3203fae946d94ff2bf7428f0b61b4=138963ddf7be113df31082e06c640727;_ga=GA1.1.1236675467.1758353954;_ga_25E93VLEHL=GS2.1.s1758376791$o4$g1$t1758379642$j35$l0$h0"

# Ayarlar (saniye cinsinden)
WAIT_FIRST = 10
WAIT_RETURN = 5 * 60
WAIT_ON_ITEM = 3

CATEGORY_URL = "https://www.klasgame.com/revenger-online/revenger-online-gold"
CHECK_URL = CATEGORY_URL  # Satış aktif kontrolü yapılacak sayfa

# Telegram ayarları
TELEGRAM_TOKEN = "8350444240:AAHbhxHeI2AbPZTXCTe90qkadp7ZzE1sdtI"
USER_IDS = [5695472914,6291821880]

# Ctrl+C yakalama
stop_flag = False
def signal_handler(sig, frame):
    global stop_flag
    log("SIGINT alındı, döngü sonlandırılıyor...")
    stop_flag = True
signal.signal(signal.SIGINT, signal_handler)

# Log helper
def log(msg: str):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
    sys.stdout.flush()

# Cookie parser
def parse_cookie_string(s: str) -> dict:
    cookies = {}
    for p in s.split(';'):
        p = p.strip()
        if not p or '=' not in p:
            continue
        k, v = p.split('=', 1)
        cookies[k.strip()] = v.strip()
    return cookies

# Telegram mesaj fonksiyonu
def send_telegram_message(user_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": user_id, "text": text}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        log(f"Telegram mesaj gönderilemedi: {e}")

# Link çıkarma
def extract_candidate_links(base_url: str, html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a", href=True)
    candidates = set()
    base_parsed = urlparse(base_url)
    base_domain = f"{base_parsed.scheme}://{base_parsed.netloc}"

    for a in anchors:
        href = a["href"].strip()
        if not href:
            continue
        full = urljoin(base_domain, href)
        if "/ilan/" in full or "/oyuncu-pazari/" in full or "/revenger-online/" in full:
            if urlparse(full).netloc == base_parsed.netloc:
                candidates.add(full)
    if not candidates:
        for a in anchors:
            href = a["href"].strip()
            if not href:
                continue
            full = urljoin(base_domain, href)
            if urlparse(full).netloc == base_parsed.netloc and not full.startswith(("javascript:", "#")):
                candidates.add(full)
    return sorted(candidates)

# Main loop
def main_loop():
    cookies = parse_cookie_string(cookie_string)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    for k, v in cookies.items():
        session.cookies.set(k, v)

    iteration = 0
    while not stop_flag:
        iteration += 1
        log(f"--- DÖNGÜ #{iteration} BAŞLADI ---")
        try:
            log(f"Kategori sayfasına istek atılıyor: {CATEGORY_URL}")
            resp = session.get(CATEGORY_URL, allow_redirects=True, timeout=30)
            log(f"Kategori HTTP status: {resp.status_code}")
            if resp.status_code != 200:
                log("⚠️ Kategori sayfası 200 dönmedi. 10s bekleniyor...")
                time.sleep(10)
                continue

            log(f"{WAIT_FIRST}s bekleniyor...")
            time.sleep(WAIT_FIRST)

            candidates = extract_candidate_links(CATEGORY_URL, resp.text)
            log(f"Aday link sayısı: {len(candidates)}")
            if not candidates:
                log("⚠️ Aday link bulunamadı, 30s bekleniyor...")
                time.sleep(30)
                continue

            chosen = random.choice(candidates)
            log(f"Rastgele seçilen link: {chosen}")

            # Sadece CHECK_URL kontrolü
            if chosen == CHECK_URL:
                log(f"{CHECK_URL} sayfası için Satış aktif kontrolü başlatılıyor...")
                while not stop_flag:
                    r = session.get(CHECK_URL, timeout=20)
                    kontrol_mesaji = "message('Şu an için alış aktif görünmüyor, lütfen daha sonra tekrar deneyiniz.', 'danger'); return false;"
                    if kontrol_mesaji not in r.text:
                        log("Satış aktif! Telegram mesajı gönderiliyor...")
                        for uid in USER_IDS:
                            send_telegram_message(uid, f"{CHECK_URL} sayfasında Satış aktif!")
                        break
                    else:
                        log("Alış aktif değil, 2s beklenip tekrar kontrol edilecek...")
                        time.sleep(2)
            else:
                log(f"{chosen} sayfasına gidiliyor...")
                try:
                    r2 = session.get(chosen, timeout=20)
                    log(f"HTTP status: {r2.status_code}")
                    log(f"{WAIT_ON_ITEM}s bekleniyor...")
                    time.sleep(WAIT_ON_ITEM)
                except Exception as e:
                    log(f"Hata: {e}")

            # Kategoriye geri dönüş
            log(f"{CATEGORY_URL} sayfasına geri dönülüyor...")
            try:
                resp_back = session.get(CATEGORY_URL, timeout=20)
                log(f"Geri dönüş status: {resp_back.status_code}")
            except Exception as e:
                log(f"Hata: {e}")

            log(f"{WAIT_RETURN}s bekleniyor...")
            time.sleep(WAIT_RETURN)

        except Exception as e:
            log(f"Beklenmeyen hata: {e}")
            time.sleep(5)

    log("Döngü sonlandırıldı.")

if __name__ == "__main__":
    main_loop()