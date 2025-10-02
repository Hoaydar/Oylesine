import json
import time
import pyautogui
import pyperclip

# JSON dosyasını oku
with open("members.json", "r", encoding="utf-8") as f:
    users = json.load(f)

# Sadece username dolu olanları al
usernames = [user["username"] for user in users if user.get("username")]

# Çok satırlı mesaj
message = """🎁 Yatırım Şartsız 50 Freespin Kod!

💸 Sınırsız çekim fırsatıyla hemen kullan!

-------------- AYRICA ----------------

🎰 500 Freespin Deneme Bonusu!

🚀 Şimdi dene, şansını katla!

HEPSİ İÇERDE: @piranakod"""

# Telegram Web açık olmalı
time.sleep(5)

for username in usernames:
    # Arama kutusuna tıkla
    pyautogui.click(200, 170)
    time.sleep(1)

    # Eski aramayı temizle
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")

    # Username yaz
    pyautogui.write(username)
    time.sleep(2)

    # İlk çıkan kullanıcıya tıkla
    pyautogui.press("enter")
    time.sleep(2)

    # Mesaj kutusuna odaklan
    pyautogui.click(600, 1000)
    time.sleep(1)

    # Mesajı panoya kopyala ve yapıştır
    pyperclip.copy(message)
    pyautogui.hotkey("ctrl", "v")

    # Gönder
    pyautogui.press("enter")

    time.sleep(3)
