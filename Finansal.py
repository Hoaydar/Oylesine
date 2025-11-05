import os
import time
import requests
import matplotlib.pyplot as plt
import numpy as np
import json
import pandas as pd
import math
from scipy.signal import find_peaks
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from yahooquery import Ticker
from thefuzz import process

# Lütfen bu TOKEN'ı kendi bot tokeniniz ile değiştirin
BOT_TOKEN = "7932037979:AAHyz8Lay8tDl7nwb4L4WFXfPihn3NjTRW4" 

# --- YÖNETİM DEĞİŞKENLERİ ---
USER_LOG_FILE = "users.txt"
CHANNEL_LOG_FILE = "channel_logs.txt" # Kanal Kayıt Dosyası

# DUYURU VE KANAL YÖNETİMİ İÇİN YETKİLİ KULLANICILARIN TELEGRAM ID'leri
# LÜTFEN KENDİ ID'NİZİ BURAYA YAZINIZ! (Örn: 123456789)
AUTHORIZED_USERS = [5695472914, 5624868688] 
# ----------------------------

BILINEN_HISSELER = {
    "QNBTR": "QNB Bank AS",
    "ASELS": "ASELSAN ELEKTRONİK SANAYİ VE TİCARET A.Ş.",
    "GARAN": "TÜRKİYE GARANTİ BANKASI A.Ş.",
    "ENKAI": "ENKA İNŞAAT VE SANAYİ A.Ş.",
    "KCHOL": "KOÇ HOLDİNG A.Ş.",
    "THYAO": "TÜRK HAVA YOLLARI A.O.",
    "TUPRS": "TÜPRAŞ-TÜRKİYE PETROL RAFİNERİLERİ A.Ş.",
    "ISCTR": "TÜRKİYE İŞ BANKASI A.Ş.",
    "FROTO": "FORD OTOMOTİV SANAYİ A.Ş.",
    "AKBNK": "AKBANK T.A.Ş.",
    "BIMAS": "BİM BİRLEŞİK MAĞAZALAR A.Ş.",
    "YKBNK": "YAPI VE KREDİ BANKASI A.Ş.",
    "VAKBN": "TÜRKİYE VAKIFLAR BANKASI T.A.O.",
    "KLRHO": "KİLER HOLDİNG A.Ş.",
    "DSTKF": "DESTEK FAKTORİNG A.Ş.",
    "TCELL": "TURKCELL İLETİŞİM HİZMETLERİ A.Ş.",
    "EREGL": "EREĞLİ DEMİR VE ÇELİK FABRİKALARI T.A.Ş.",
    "HALKB": "TÜRKİYE HALK BANKASI A.Ş.",
    "TTKOM": "TÜRK TELEKOMÜNİKASYON A.Ş.",
    "SAHOL": "HACI ÖMER SABANCI HOLDİNG A.Ş.",
    "HEDEF": "HEDEF HOLDİNG A.Ş.",
    "TERA": "TERA YATIRIM MENKUL DEĞERLER A.Ş.",
    "CCOLA": "COCA-COLA İÇECEK A.Ş.",
    "SASA": "SASA POLYESTER SANAYİ A.Ş.",
    "TURSG": "TÜRKİYE SİGORTA A.Ş.",
    "KLNMA": "TÜRKİYE KALKINMA VE YATIRIM BANKASI A.Ş.",
    "TOASO": "TOFAŞ TÜRK OTOMOBİL FABRİKASI A.Ş.",
    "QNBFK": "QNB Finansal Kiralama A.S.",
    "ISDMR": "İSKENDERUN DEMİR VE ÇELİK A.Ş.",
    "SISE": "TÜRKİYE ŞİŞE VE CAM FABRİKALARI A.Ş.",
    "ZRGYO": "ZİRAAT GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.",
    "PGSUS": "PEGASUS HAVA TAŞIMACILIĞI A.Ş.",
    "OYAKC": "OYAK ÇİMENTO FABRİKALARI A.Ş.",
    "ASTOR": "ASTOR ENERJİ A.Ş.",
    "GUBRF": "GÜBRE FABRİKALARI T.A.Ş.",
    "TAVHL": "TAV HAVALİMANLARI HOLDİNG A.Ş.",
    "UFUK": "UFUK YATIRIM YÖNETİM VE GAYRİMENKUL A.Ş.",
    "PASEU": "Pasifik Eurasia Lojistik dis Ticaret AS",
    "ENJSA": "ENERJİSA ENERJİ A.Ş.",
    "ENERY": "Enerya Enerji A.S.",
    "KOZAL": "KOZA ALTIN İŞLETMELERİ A.Ş.",
    "AEFES": "ANADOLU EFES BİRACILIK VE MALT SANAYİİ A.Ş.",
    "MAGEN": "MARGÜN ENERJİ ÜRETİM SANAYİ VE TİCARET A.Ş.",
    "MGROS": "MİGROS TİCARET A.Ş.",
    "ARCLK": "ARÇELİK A.Ş.",
    "AHGAZ": "AHLATCI DOĞAL GAZ DAĞITIM ENERJİ VE YATIRIM A.Ş.",
    "DMLKT": "Emlak Konut Gayrimenkul Yatirim Ortakligi A.S. 0 % Certificates 2025-31.12.2199",
    "AKSEN": "AKSA ENERJİ ÜRETİM A.Ş.",
    "BRSAN": "BORUSAN MANNESMANN BORU SANAYİ VE TİCARET A.Ş.",
    "TBORG": "TÜRK TUBORG BİRA VE MALT SANAYİİ A.Ş.",
    "BRYAT": "BORUSAN YATIRIM VE PAZARLAMA A.Ş.",
    "RALYH": "RAL YATIRIM HOLDİNG A.Ş.",
    "ISMEN": "İŞ YATIRIM MENKUL DEĞERLER A.Ş.",
    "MPARK": "MLP SAĞLIK HİZMETLERİ A.Ş.",
    "GLRMK": "Gulermak Agir Sanayi Insaat Ve Taahhut A.S.",
    "TABGD": "TAB Gida Sanayi ve Ticaret A.S.",
    "AGHOL": "AG ANADOLU GRUBU HOLDİNG A.Ş.",
    "ECILC": "EİS ECZACIBAŞI İLAÇ SINAİ VE FİNANSAL YATIRIMLAR SANAYİ VE TİCARET A.Ş.",
    "INVES": "INVESTCO HOLDİNG A.Ş.",
    "PEKGY": "PEKER GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.",
    "GENIL": "GEN İLAÇ VE SAĞLIK ÜRÜNLERİ SANAYİ VE TİCARET A.Ş.",
    "OTKAR": "OTOKAR OTOMOTİV VE SAVUNMA SANAYİ A.Ş.",
    "TTRAK": "TÜRK TRAKTÖR VE ZİRAAT MAKİNELERİ A.Ş.",
    "LIDER": "LDR TURİZM A.Ş.",
    "EFOR": "Efor Yatirim Sanayi Ticaret A.S.",
    "RGYAS": "RÖNESANS GAYRİMENKUL YATIRIM A.Ş.",
    "GRTHO": "Grainturk Holding A.S.",
    "SELEC": "SELÇUK ECZA DEPOSU TİCARET VE SANAYİ A.Ş.",
    "ANSGR": "ANADOLU ANONİM TÜRK SİGORTA ŞİRKETİ",
    "AKSA": "AKSA AKRİLİK KİMYA SANAYİİ A.Ş.",
    "ANHYT": "ANADOLU HAYAT EMEKLİLİK A.Ş.",
    "DOHOL": "DOĞAN ŞİRKETLER GRUBU HOLDİNG A.Ş.",
    "PETKM": "PETKİM PETROKİMYA HOLDİNG A.Ş.",
    "AYGAZ": "AYGAZ A.Ş.",
    "SMRVA": "Sumer Varlik Yonetim A.S.",
    "RAYSG": "RAY SİGORTA A.Ş.",
    "CIMSA": "ÇİMSA ÇİMENTO SANAYİ VE TİCARET A.Ş.",
    "LYDHO": "Lydia Holding A.S.",
    "ULKER": "ÜLKER BİSKÜVİ SANAYİ A.Ş.",
    "CLEBI": "ÇELEBİ HAVA SERVİSİ A.Ş.",
    "AGESA": "AGESA HAYAT VE EMEKLİLİK A.Ş.",
    "NUHCM": "NUH ÇİMENTO SANAYİ A.Ş.",
    "DOAS": "DOĞUŞ OTOMOTİV SERVİS VE TİCARET A.Ş.",
    "TSKB": "TÜRKİYE SINAİ KALKINMA BANKASI A.Ş.",
    "ALARK": "ALARKO HOLDİNG A.Ş.",
    "GRSEL": "GÜR-SEL TURİZM TAŞIMACILIK VE SERVİS TİCARET A.Ş.",
    "DAPGM": "DAP GAYRİMENKUL GELİŞTİRME A.Ş.",
    "ECZYT": "ECZACIBAŞI YATIRIM HOLDİNG ORTAKLIĞI A.Ş.",
    "POLTK": "POLİTEKNİK METAL SANAYİ VE TİCARET A.Ş.",
    "KOZAA": "KOZA ANADOLU METAL MADENCİLİK İŞLETMELERİ A.Ş.",
    "YGGYO": "YENİ GİMAT GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.",
    "MAVI": "MAVİ GİYİM SANAYİ VE TİCARET A.Ş.",
    "LYDYE": "Lydia Yesil Enerji kaynaklari A.S.",
    "HEKTS": "HEKTAŞ TİCARET T.A.Ş.",
    "KRDMD": "KARDEMİR KARABÜK DEMİR ÇELİK SANAYİ VE TİCARET A.Ş.",
    "KRDMA": "KARDEMİR KARABÜK DEMİR ÇELİK SANAYİ VE TİCARET A.Ş.",
    "KRDMB": "KARDEMİR KARABÜK DEMİR ÇELİK SANAYİ VE TİCARET A.Ş.",
    "TKFEN": "TEKFEN HOLDİNG A.Ş.",
    "RYSAS": "REYSAŞ TAŞIMACILIK VE LOJİSTİK TİCARET A.Ş.",
    "CVKMD": "CVK MADEN İŞLETMELERİ SANAYİ VE TİCARET A.Ş.",
    "KTLEV": "KATILIMEVIM TASARRUF FINANSMAN A.S.",
    "BASGZ": "BAŞKENT DOĞALGAZ DAĞITIM GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.",
    "BRISA": "BRİSA BRIDGESTONE SABANCI LASTİK SANAYİ VE TİCARET A.Ş.",
    "CWENE": "CW ENERJİ MÜHENDİSLİK TİCARET VE SANAYİ A.Ş.",
    "BSOKE": "BATISÖKE SÖKE ÇİMENTO SANAYİİ T.A.Ş.",
    "SOKM": "ŞOK MARKETLER TİCARET A.Ş.",
    "KCAER": "KOCAER ÇELİK SANAYİ VE TİCARET A.Ş.",
    "BTCIM": "BATIÇİM BATI ANADOLU ÇİMENTO SANAYİİ A.Ş.",
    "EGEEN": "EGE ENDÜSTRİ VE TİCARET A.Ş.",
    "AKCNS": "AKÇANSA ÇİMENTO SANAYİ VE TİCARET A.Ş.",
    "KONYA": "KONYA ÇİMENTO SANAYİİ A.Ş.",
    "IZENR": "Izdemir Enerji Elektrik Uretim A.S.",
    "KLYPV": "Kalyon Gunes Teknolojileri Uretim Anonim Sirketi",
    "NTHOL": "NET HOLDİNG A.Ş.",
    "ODINE": "Odine Solutions Teknoloji Ticaret ve Sanayi AS",
    "MOGAN": "Mogan Enerji Yatirim Holding",
    "QUAGR": "QUA GRANITE HAYAL YAPI VE ÜRÜNLERİ SANAYİ TİCARET A.Ş.",
    "AVPGY": "Avrupakent Gayrimenkul Yatirim Ortakligi SA",
    "TATEN": "Tatlipinar Enerji Uretim A.S.",
    "VERUS": "VERUSA HOLDİNG A.Ş.",
    "BALSU": "Balsu Gida Sanayi ve Ticaret Anonim Sirketi",
    "GESAN": "GİRİŞİM ELEKTRİK SANAYİ TAAHHÜT VE TİCARET A.Ş.",
    "GLYHO": "GLOBAL YATIRIM HOLDİNG A.Ş.",
    "ENTRA": "IC Enterra Yenilenebilir Enerji AS",
    "OBAMS": "Oba Makarnacilik Sanayi Ve Ticaret A. S.",
    "AKFYE": "AKFEN YENİLENEBİLİR ENERJİ A.Ş.",
    "ALBRK": "ALBARAKA TÜRK KATILIM BANKASI A.Ş.",
    "BFREN": "BOSCH FREN SİSTEMLERİ SANAYİ VE TİCARET A.Ş.",
    "KONTR": "KONTROLMATİK TEKNOLOJİ ENERJİ VE MÜHENDİSLİK A.Ş.",
    "SKBNK": "ŞEKERBANK T.A.Ş.",
    "SUNTK": "SUN TEKSTİL SANAYİ VE TİCARET A.Ş.",
    "CEMZY": "CEM ZEYTIN ANONIM SIRKETI",
    "GSRAY": "GALATASARAY SPORTİF SINAİ VE TİCARİ YATIRIMLAR A.Ş.",
    "BINBN": "Bin Ulasim Ve Akilli Sehir Teknolojileri AS",
    "IPEKE": "İPEK DOĞAL ENERJİ KAYNAKLARI ARAŞTIRMA VE ÜRETİM A.Ş.",
    "MRSHL": "MARSHALL BOYA VE VERNİK SANAYİİ A.Ş.",
    "GZNMI": "GEZİNOMİ SEYAHAT TURİZM TİCARET A.Ş.",
    "MIATK": "MİA TEKNOLOJİ A.Ş.",
    "KZBGY": "KIZILBÜK GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.",
    "EUPWR": "EUROPOWER ENERJİ VE OTOMASYON TEKNOLOJİLERİ SANAYİ TİCARET A.Ş.",
    "PATEK": "Pasifik Teknoloji AS",
    "ADESE": "ADESE GAYRİMENKUL YATIRIM A.Ş.",
    "BMSTL": "BMS BİRLEŞİK METAL SANAYİ VE TİCARET A.Ş.",
    "ZOREN": "ZORLU ENERJİ ELEKTRİK ÜRETİM A.Ş.",
    "BANVT": "BANVİT BANDIRMA VİTAMİNLİ YEM SANAYİİ A.Ş.",
    "OYYAT": "OYAK YATIRIM MENKUL DEĞERLER A.Ş.",
    "FZLGY": "FUZUL GAYRIMENKUL YATIRIM ORTAKLIGI A.S.",
    "CANTE": "ÇAN2 TERMİK A.Ş.",
    "LILAK": "Lila Kagit Sanayi Ve Ticaret Anonim Sirketi",
    "IEYHO": "IŞIKLAR ENERJİ VE YAPI HOLDİNG A.Ş.",
    "DOFRB": "DOF Robotik Sanayi Anonim Sirketi",
    "BORLS": "Borlease Otomotiv AS",
    "AKFIS": "Akfen insaat Turizm ve Ticaret AS",
    "EUREN": "EUROPEN ENDÜSTRİ İNŞAAT SANAYİ VE TİCARET A.Ş.",
    "SMRTG": "SMART GÜNEŞ ENERJİSİ TEKNOLOJİLERİ ARAŞTIRMA GELİŞTİRME ÜRETİM SANAYİ VE TİCARET A.Ş.",
    "KLSER": "Kaleseramik Canakkale Kalebodur Seramik A.S.",
    "KLKIM": "KALEKİM KİMYEVİ MADDELER SANAYİ VE TİCARET A.Ş.",
    "ULUSE": "ULUSOY ELEKTRİK İMALAT TAAHHÜT VE TİCARET A.Ş.",
    "ALFAS": "ALFA SOLAR ENERJİ SANAYİ VE TİCARET A.Ş.",
    "SARKY": "SARKUYSAN ELEKTROLİTİK BAKIR SANAYİ VE TİCARET A.Ş.",
    "VSNMD": "Visne Madencilik Uretim Sanayi ve Ticaret AS",
    "ALTNY": "Altinay Savunma Teknolojileri A.S.",
    "LOGO": "LOGO YAZILIM SANAYİ VE TİCARET A.Ş.",
    "OZATD": "OZATA DENIZCILIK SANAYI VE TICARET AS",
    "EGPRO": "EGE PROFİL TİCARET VE SANAYİ A.Ş.",
    "ADGYO": "Adra Gayrimenkul Yatirim Ortakligi A.S.",
    "LMKDC": "Limak Dogu Anadolu Cimento Sanayi Ve Ticaret AS",
    "JANTS": "JANTSA JANT SANAYİ VE TİCARET A.Ş.",
    "KOTON": "KOTON MAĞAZACILIK TEKSTİL SANAYİ VE TİCARET A.Ş.",
    "HTTBT": "HİTİT BİLGİSAYAR HİZMETLERİ A.Ş.",
    "CRFSA": "CARREFOURSA CARREFOUR SABANCI TİCARET MERKEZİ A.Ş.",
    "ISKPL": "IŞIK PLASTİK SANAYİ VE DIŞ TİCARET PAZARLAMA A.Ş.",
    "BIENY": "BİEN YAPI ÜRÜNLERİ SANAYİ TURİZM VE TİCARET A.Ş.",
    "ARASE": "DOĞU ARAS ENERJİ YATIRIMLARI A.Ş.",
    "ASUZU": "ANADOLU ISUZU OTOMOTİV SANAYİ VE TİCARET A.Ş.",
    "VESBE": "VESTEL BEYAZ EŞYA SANAYİ VE TİCARET A.Ş.",
    "BINHO": "1000 Yatirimlar Holding AS",
    "POLHO": "POLİSAN HOLDİNG A.Ş.",
    "DEVA": "DEVA HOLDİNG A.Ş.",
    "ISFIN": "İŞ FİNANSAL KİRALAMA A.Ş.",
    "GWIND": "GALATA WIND ENERJİ A.Ş.",
    "TRHOL": "Tera Financial Investments Holding A.S.",
    "AYDEM": "AYDEM YENİLENEBİLİR ENERJİ A.Ş.",
    "TUKAS": "TUKAŞ GIDA SANAYİ VE TİCARET A.Ş.",
    "ENSRI": "ENSARİ DERİ GIDA SANAYİ VE TİCARET A.Ş.",
    "KAYSE": "KAYSERİ ŞEKER FABRİKASI A.Ş.",
    "ESEN": "ESENBOĞA ELEKTRİK ÜRETİM A.Ş.",
    "ICBCT": "ICBC TURKEY BANK A.Ş.",
    "FENER": "FENERBAHÇE FUTBOL A.Ş.",
    "BERA": "BERA HOLDİNG A.Ş.",
    "TMSN": "TÜMOSAN MOTOR VE TRAKTÖR SANAYİ A.Ş.",
    "YYLGD": "YAYLA AGRO GIDA SANAYİ VE TİCARET A.Ş.",
    "YEOTK": "YEO TEKNOLOJİ ENERJİ VE ENDÜSTRİ A.Ş.",
    "BULGS": "Bulls Girisim Sermayesi Yatirim Ortakligi Anonim Sirketi",
    "GEDIK": "GEDİK YATIRIM MENKUL DEĞERLER A.Ş.",
    "GIPTA": "Gipta Ofis Kirtasiye ve Promosyon Urunleri Imalat Sanayi A.S.",
    "AKGRT": "AKSİGORTA A.Ş.",
    "VESTL": "VESTEL ELEKTRONİK SANAYİ VE TİCARET A.Ş.",
    "BIOEN": "BİOTREND ÇEVRE VE ENERJİ YATIRIMLARI A.Ş.",
    "AHSGY": "Ahes Gayrimenkul Yatirim Ortakligi AS",
    "AYCES": "ALTIN YUNUS ÇEŞME TURİSTİK TESİSLER A.Ş.",
    "SDTTR": "SDT UZAY VE SAVUNMA TEKNOLOJİLERİ A.Ş.",
    "VAKKO": "VAKKO TEKSTİL VE HAZIR GİYİM SANAYİ İŞLETMELERİ A.Ş.",
    "INVEO": "INVEO YATIRIM HOLDİNG A.Ş.",
    "EGGUB": "EGE GÜBRE SANAYİİ A.Ş.",
    "SRVGY": "SERVET GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.",
    "KORDS": "KORDSA TEKNİK TEKSTİL A.Ş.",
    "MEGMT": "Mega Metal Sanayi Ve Ticaret A.S.",
    "INGRM": "INGRAM MİCRO BİLİŞİM SİSTEMLERİ A.Ş.",
    "GARFA": "GARANTİ FAKTORİNG A.Ş.",
    "HATSN": "Hat-San Gemi Insaa Bakim Onarim Deniz Nakliyat Sanayi ve Ticaret A.S.",
    "OFSYM": "Ofis Yem Gida Sanayi ve Ticaret A.S.",
    "SONME": "SÖNMEZ FİLAMENT SENTETİK İPLİK VE ELYAF SANAYİ A.Ş.",
    "ESCAR": "ESCAR FİLO KİRALAMA HİZMETLERİ A.Ş.",
    "ALCAR": "ALARKO CARRIER SANAYİ VE TİCARET A.Ş.",
    "VAKFN": "VAKIF FİNANSAL KİRALAMA A.Ş.",
    "SNPAM": "SÖNMEZ PAMUKLU SANAYİİ A.Ş.",
    "TRCAS": "TURCAS PETROL A.Ş.",
    "ALKLC": "Altinkilic Gida ve Sut Sanayi Ticaret AS",
    "TSPOR": "TRABZONSPOR SPORTİF YATIRIM VE FUTBOL İŞLETMECİLİĞİ TİCARET A.Ş.",
    "IZMDC": "İZMİR DEMİR ÇELİK SANAYİ A.Ş.",
    "GLCVY": "GELECEK VARLIK YÖNETİMİ A.Ş.",
    "BUCIM": "BURSA ÇİMENTO FABRİKASI A.Ş.",
    "MOPAS": "Mopas Marketcilik Gida Sanayi Ve Ticaret A.S.",
    "BASCM": "BAŞTAŞ BAŞKENT ÇİMENTO SANAYİ VE TİCARET A.Ş.",
    "BESLR": "Besler Gida Ve Kimya Sanayi Ve Ticaret AS",
    "KAPLM": "KAPLAMİN AMBALAJ SANAYİ VE TİCARET A.Ş.",
    "ARMGD": "Armada Gida Ticaret ve Sanayi Anonim Sirketi",
    "BLUME": "Blume Metal Kimya Anonim Sirketi",
    "REEDR": "Reeder Teknoloji Sanayi ve Ticaret A.S.",
    "KARSN": "KARSAN OTOMOTİV SANAYİİ VE TİCARET A.Ş.",
    "KMPUR": "KİMTEKS POLİÜRETAN SANAYİ VE TİCARET A.Ş.",
    "BOSSA": "BOSSA TİCARET VE SANAYİ İŞLETMELERİ T.A.Ş.",
    "AGROT": "Agrotech Yuksek Teknoloji ve Yatirim AS",
    "EMKEL": "EMEK ELEKTRİK ENDÜSTRİSİ A.Ş.",
    "KBORU": "Kuzey Boru A.S.",
    "ATATP": "ATP YAZILIM VE TEKNOLOJİ A.Ş.",
    "KOPOL": "KOZA POLYESTER SANAYİ VE TİCARET A.Ş.",
    "A1CAP": "A1 Capital Yatitim Menkul Degerler A.S.",
    "MNDTR": "MONDİ TURKEY OLUKLU MUKAVVA KAĞIT VE AMBALAJ SANAYİ A.Ş.",
    "PRKAB": "TÜRK PRYSMİAN KABLO VE SİSTEMLERİ A.Ş.",
    "TUREX": "TUREKS TURİZM TAŞIMACILIK A.Ş.",
    "TNZTP": "TAPDİ OKSİJEN ÖZEL SAĞLIK VE EĞİTİM HİZMETLERİ SANAYİ TİCARET A.Ş.",
    "HRKET": "Hareket Proje Tasimaciligi ve Yuk Muhendisligi AS",
    "EBEBK": "EBEBEK MAGAZACILIK ANONIM SIRKETI",
    "GOZDE": "GÖZDE GİRİŞİM SERMAYESİ YATIRIM ORTAKLIĞI A.Ş.",
    "AKENR": "AKENERJİ ELEKTRİK ÜRETİM A.Ş.",
    "BJKAS": "BEŞİKTAŞ FUTBOL YATIRIMLARI SANAYİ VE TİCARET A.Ş.",
    "ADEL": "ADEL KALEMCİLİK TİCARET VE SANAYİ A.Ş.",
    "SURGY": "Sur Tatil Evleri Gayrimenkul Yatirim Ortakligi A.S.",
    "TCKRC": "Kirac Galvaniz Telekominikasyon Metal Makine Insaat Elektrik Sanayi Ve Ticaret AS",
    "IZFAS": "İZMİR FIRÇA SANAYİ VE TİCARET A.Ş.",
    "DOKTA": "DÖKTAŞ DÖKÜMCÜLÜK TİCARET VE SANAYİ A.Ş.",
    "PARSN": "PARSAN MAKİNA PARÇALARI SANAYİİ A.Ş.",
    "MOBTL": "MOBİLTEL İLETİŞİM HİZMETLERİ SANAYİ VE TİCARET A.Ş.",
    "TARKM": "Tarkim Bitki Koruma Sanayi ve Ticaret A.S.",
    "ODAS": "ODAŞ ELEKTRİK ÜRETİM SANAYİ TİCARET A.Ş.",
    "PAGYO": "PANORA GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.",
    "YIGIT": "Yigit Aku Malzemeleri Nakliyat Turizm Insaat Sanayi Ve Ticaret",
    "KAREL": "KAREL ELEKTRONİK SANAYİ VE TİCARET A.Ş.",
    "AYEN": "AYEN ENERJİ A.Ş.",
    "GOKNR": "GÖKNUR GIDA MADDELERİ ENERJİ İMALAT İTHALAT İHRACAT TİCARET VE SANAYİ A.Ş.",
    "NTGAZ": "NATURELGAZ SANAYİ VE TİCARET A.Ş.",
    "ALKA": "ALKİM KAĞIT SANAYİ VE TİCARET A.Ş.",
    "EKOS": "Ekos Teknoloji ve Elektrik AS",
    "BOBET": "BOĞAZİÇİ BETON SANAYİ VE TİCARET A.Ş.",
    "KATMR": "KATMERCİLER ARAÇ ÜSTÜ EKİPMAN SANAYİ VE TİCARET A.Ş.",
    "ATAKP": "Atakey Patates Gida Sanayi ve Ticaret AS",
    "BIGCH": "BÜYÜK ŞEFLER GIDA TURİZM TEKSTİL DANIŞMANLIK ORGANİZASYON EĞİTİM SANAYİ VE TİCARET A.Ş.",
    "YBTAS": "YİBİTAŞ YOZGAT İŞÇİ BİRLİĞİ İNŞAAT MALZEMELERİ TİCARET VE SANAYİ A.Ş.",
    "MERIT": "MERİT TURİZM YATIRIM VE İŞLETME A.Ş.",
    "GENTS": "GENTAŞ DEKORATİF YÜZEYLER SANAYİ VE TİCARET A.Ş.",
    "NATEN": "NATUREL YENİLENEBİLİR ENERJİ TİCARET A.Ş.",
    "DESA": "DESA DERİ SANAYİ VE TİCARET A.Ş.",
    "ENDAE": "Enda Enerji Holding Anonim Sirketi",
    "MAALT": "MARMARİS ALTINYUNUS TURİSTİK TESİSLER A.Ş.",
    "GEREL": "GERSAN ELEKTRİK TİCARET VE SANAYİ A.Ş.",
    "KOCMT": "Koc Metalurji AS",
    "PKENT": "PETROKENT TURİZM A.Ş.",
    "IHAAS": "İHLAS HABER AJANSI A.Ş.",
    "LINK": "LİNK BİLGİSAYAR SİSTEMLERİ YAZILIMI VE DONANIMI SANAYİ VE TİCARET A.Ş.",
    "SUWEN": "SUWEN TEKSTİL SANAYİ PAZARLAMA A.Ş.",
    "TEZOL": "EUROPAP TEZOL KAĞIT SANAYİ VE TİCARET A.Ş.",
    "PLTUR": "PLATFORM TURİZM TAŞIMACILIK GIDA İNŞAAT TEMİZLİK HİZMETLERİ SANAYİ VE TİCARET A.Ş.",
    "CGCAM": "Cagdas Cam Sanayi ve Ticaret AS",
    "BIGEN": "Birlesim Grup Enerji Yatirimlari AS",
    "GMTAS": "GİMAT MAĞAZACILIK SANAYİ VE TİCARET A.Ş.",
    "KARTN": "KARTONSAN KARTON SANAYİ VE TİCARET A.Ş.",
    "INDES": "İNDEKS BİLGİSAYAR SİSTEMLERİ MÜHENDİSLİK SANAYİ VE TİCARET A.Ş.",
    "PENTA": "PENTA TEKNOLOJİ ÜRÜNLERİ DAĞITIM TİCARET A.Ş.",
    "KONKA": "KONYA KAĞIT SANAYİ VE TİCARET A.Ş.",
    "DARDL": "DARDANEL ÖNENTAŞ GIDA SANAYİ A.Ş.",
    "HDFGS": "HEDEF GİRİŞİM SERMAYESİ YATIRIM ORTAKLIĞI A.Ş.",
    "INTEM": "İNTEMA İNŞAAT VE TESİSAT MALZEMELERİ YATIRIM VE PAZARLAMA A.Ş.",
    "GOLTS": "GÖLTAŞ GÖLLER BÖLGESİ ÇİMENTO SANAYİ VE TİCARET A.Ş.",
    "ERCB": "ERCİYAS ÇELİK BORU SANAYİ A.Ş.",
    "CATES": "Cates Elektrik Uretim Anonim Sirketi",
    "ULUUN": "ULUSOY UN SANAYİ VE TİCARET A.Ş.",
    "BORSK": "Bor Seker Anonim Sirketi",
    "ALKIM": "ALKİM ALKALİ KİMYA A.Ş.",
    "KRVGD": "KERVAN GIDA SANAYİ VE TİCARET A.Ş.",
    "CEMTS": "ÇEMTAŞ ÇELİK MAKİNA SANAYİ VE TİCARET A.Ş.",
    "HOROZ": "Horoz Lojistik Kargo Hizmetleri Ve Ticaret AS",
    "EGEGY": "Egeyapi Avrupa Gayrimenkul Yatirim Ortakligi A.S.",
    "ORGE": "ORGE ENERJİ ELEKTRİK TAAHHÜT A.Ş.",
    "TKNSA": "TEKNOSA İÇ VE DIŞ TİCARET A.Ş.",
    "KZGYO": "Kuzugrup Gayrimenkul Yatirim Ortakligi AS",
    "YATAS": "YATAŞ YATAK VE YORGAN SANAYİ TİCARET A.Ş.",
    "SAFKR": "SAFKAR EGE SOĞUTMACILIK KLİMA SOĞUK HAVA TESİSLERİ İHRACAT İTHALAT SANAYİ VE TİCARET A.Ş.",
    "BARMA": "BAREM AMBALAJ SANAYİ VE TİCARET A.Ş.",
    "ARSAN": "ARSAN TEKSTİL TİCARET VE SANAYİ A.Ş.",
    "AFYON": "AFYON ÇİMENTO SANAYİ T.A.Ş.",
    "IMASM": "İMAŞ MAKİNA SANAYİ A.Ş.",
    "ALCTL": "ALCATEL LUCENT TELETAŞ TELEKOMÜNİKASYON A.Ş.",
    "AZTEK": "AZTEK TEKNOLOJİ ÜRÜNLERİ TİCARET A.Ş.",
    "FMIZP": "FEDERAL-MOGUL İZMİT PİSTON VE PİM ÜRETİM TESİSLERİ A.Ş.",
    "DMRGD": "DMR Unlu Mamuller Uretim Gida Toptan Perakende Ihracat A.S.",
    "ONRYT": "Onur Yuksek Teknoloji AS",
    "ONCSM": "ONCOSEM ONKOLOJİK SİSTEMLER SANAYİ VE TİCARET A.Ş.",
    "FORTE": "FORTE BILGI ILETISIM TEKNOLOJILERI VE SAVUNMA SANAYI A.S.",
    "BVSAN": "BÜLBÜLOĞLU VİNÇ SANAYİ VE TİCARET A.Ş.",
    "YYAPI": "YEŞİL YAPI ENDÜSTRİSİ A.Ş.",
    "BRKVY": "BİRİKİM VARLIK YÖNETİM A.Ş.",
    "ORMA": "ORMA ORMAN MAHSULLERİ İNTEGRE SANAYİ VE TİCARET A.Ş.",
    "MHRGY": "MHR Gayrimenkul Yatirim Ortakligi Anonim Sirketi",
    "ARDYZ": "ARD GRUP BİLİŞİM TEKNOLOJİLERİ A.Ş.",
    "IHLAS": "İHLAS HOLDİNG A.Ş.",
    "NETAS": "NETAŞ TELEKOMÜNİKASYON A.Ş.",
    "BEGYO": "Bati Ege Gayrimenkul Yatirim Ortakligi A.S.",
    "TEKTU": "TEK-ART İNŞAAT TİCARET TURİZM SANAYİ VE YATIRIMLAR A.Ş.",
    "INFO": "İNFO YATIRIM MENKUL DEĞERLER A.Ş.",
    "LRSHO": "Loras Holding Anonim Sirketi",
    "ELITE": "ELİTE NATUREL ORGANİK GIDA SANAYİ VE TİCARET A.Ş.",
    "ALVES": "Alves Kablo Sanayi ve Ticaret A. S.",
    "CRDFA": "CREDITWEST FAKTORİNG A.Ş.",
    "BAGFS": "BAGFAŞ BANDIRMA GÜBRE FABRİKALARI A.Ş.",
    "SEGYO": "ŞEKER GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.",
    "GSDHO": "GSD HOLDİNG A.Ş.",
    "DUNYH": "Dunya Holding Anonim Sirketi",
    "SOKE": "SÖKE DEĞİRMENCİLİK SANAYİ VE TİCARET A.Ş.",
    "MERCN": "MERCAN KİMYA SANAYİ VE TİCARET A.Ş.",
    "KUTPO": "KÜTAHYA PORSELEN SANAYİ A.Ş.",
    "USAK": "UŞAK SERAMİK SANAYİ A.Ş.",
    "GOODY": "GOODYEAR LASTİKLERİ T.A.Ş.",
    "CEMAS": "ÇEMAŞ DÖKÜM SANAYİ A.Ş.",
    "DYOBY": "DYO BOYA FABRİKALARI SANAYİ VE TİCARET A.Ş.",
    "FORMT": "FORMET METAL VE CAM SANAYİ A.Ş.",
    "DCTTR": "DCT Trading Dis Ticaret Anonim Sirketi",
    "SERNT": "Seranit Granit Seramik Sanayi ve Ticaret A.S.",
    "ANELE": "ANEL ELEKTRİK PROJE TAAHHÜT VE TİCARET A.Ş.",
    "KUVVA": "KUVVA GIDA TİCARET VE SANAYİ YATIRIMLARI A.Ş.",
    "MACKO": "MACKOLİK İNTERNET HİZMETLERİ TİCARET A.Ş.",
    "SAYAS": "SAY YENİLENEBİLİR ENERJİ EKİPMANLARI SANAYİ VE TİCARET A.Ş.",
    "CMBTN": "ÇİMBETON HAZIRBETON VE PREFABRİK YAPI ELEMANLARI SANAYİ VE TİCARET A.Ş.",
    "RUZYE": "Ruzy Madencilik Ve Enerji Yatirimlari Sanayi Ve Ticaret A.S.",
    "OSMEN": "OSMANLI YATIRIM MENKUL DEĞERLER A.Ş.",
    "MNDRS": "MENDERES TEKSTİL SANAYİ VE TİCARET A.Ş.",
    "PINSU": "PINAR SU VE İÇECEK SANAYİ VE TİCARET A.Ş.",
    "YUNSA": "YÜNSA YÜNLÜ SANAYİ VE TİCARET A.Ş.",
    "ERBOS": "ERBOSAN ERCİYAS BORU SANAYİİ VE TİCARET A.Ş.",
    "YAPRK": "YAPRAK SÜT VE BESİ ÇİFTLİKLERİ SANAYİ VE TİCARET A.Ş.",
    "PETUN": "PINAR ENTEGRE ET VE UN SANAYİİ A.Ş.",
    "HUNER": "HUN YENİLENEBİLİR ENERJİ ÜRETİM A.Ş.",
    "MEKAG": "Meka Global Makine Imalat Sanayi Ve Ticaret A.S.",
    "EGEPO": "NASMED ÖZEL SAĞLIK HİZMETLERİ TİCARET A.Ş.",
    "PNSUT": "PINAR SÜT MAMULLERİ SANAYİİ A.Ş.",
    "SEGMN": "Segmen Kardesler Gida Uretim ve Ambalaj Sanayi AS",
    "EKSUN": "EKSUN GIDA TARIM SANAYİ VE TİCARET A.Ş.",
    "KIMMR": "ERSAN ALIŞVERİŞ HİZMETLERİ VE GIDA SANAYİ TİCARET A.Ş.",
    "TURGG": "TÜRKER PROJE GAYRİMENKUL VE YATIRIM GELİŞTİRME A.Ş.",
    "GUNDG": "Gundogdu Gida Sut Urunleri Sanayi Ve Dis Ticaret AS",
    "OZYSR": "Ozyasar Tel ve Galvanizleme Sanayi Anonim Sirketi",
    "KNFRT": "KONFRUT GIDA SANAYİ VE TİCARET A.Ş.",
    "HURGZ": "HÜRRİYET GAZETECİLİK VE MATBAACILIK A.Ş.",
    "LKMNH": "LOKMAN HEKİM ENGÜRÜSAĞ SAĞLIK TURİZM EĞİTİM HİZMETLERİ VE İNŞAAT TAAHHÜT A.Ş.",
    "PAPIL": "PAPİLON SAVUNMA TEKNOLOJİ VE TİCARET A.Ş.",
    "TATGD": "TAT GIDA SANAYİ A.Ş.",
    "MEDTR": "MEDİTERA TIBBİ MALZEME SANAYİ VE TİCARET A.Ş.",
    "SANKO": "SANKO PAZARLAMA İTHALAT İHRACAT A.Ş.",
    "TRILC": "TURK İLAÇ VE SERUM SANAYİ A.Ş.",
    "LUKSK": "LÜKS KADİFE TİCARET VE SANAYİİ A.Ş.",
    "OTTO": "OTTO HOLDİNG A.Ş.",
    "ISSEN": "İŞBİR SENTETİK DOKUMA SANAYİ A.Ş.",
    "TMPOL": "TEMAPOL POLİMER PLASTİK VE İNŞAAT SANAYİ TİCARET A.Ş.",
    "KTSKR": "KÜTAHYA ŞEKER FABRİKASI A.Ş.",
    "DOFER": "Dofer Yapi Maizemeleri Sanayi ve Ticaret A.S.",
    "BRLSM": "BİRLEŞİM MÜHENDİSLİK ISITMA SOĞUTMA HAVALANDIRMA SANAYİ VE TİCARET A.Ş.",
    "BEYAZ": "BEYAZ FİLO OTO KİRALAMA A.Ş.",
    "ARTMS": "Artemis Hali A. S.",
    "DERHL": "DERLÜKS YATIRIM HOLDİNG A.Ş.",
    "DAGI": "DAGİ GİYİM SANAYİ VE TİCARET A.Ş.",
    "BURCE": "BURÇELİK BURSA ÇELİK DÖKÜM SANAYİİ A.Ş.",
    "PNLSN": "PANELSAN ÇATI CEPHE SİSTEMLERİ SANAYİ VE TİCARET A.Ş.",
    "MARBL": "Tureks Turunc Madencilik Ic ve Dis Ticaret A.S.",
    "METRO": "METRO TİCARİ VE MALİ YATIRIMLAR HOLDİNG A.Ş.",
    "ARENA": "ARENA BİLGİSAYAR SANAYİ VE TİCARET A.Ş.",
    "MAKTK": "MAKİNA TAKIM ENDÜSTRİSİ A.Ş.",
    "TGSAS": "TGS DIŞ TİCARET A.Ş.",
    "KLMSN": "KLİMASAN KLİMA SANAYİ VE TİCARET A.Ş.",
    "PAMEL": "PAMEL YENİLENEBİLİR ELEKTRİK ÜRETİM A.Ş.",
    "BAHKM": "Bahadir Kimya Sanayi Ve Ticaret Anonim Sirketi",
    "SNICA": "SANİCA ISI SANAYİ A.Ş.",
    "KRONT": "KRON TELEKOMÜNİKASYON HİZMETLERİ A.Ş.",
    "FONET": "FONET BİLGİ TEKNOLOJİLERİ A.Ş.",
    "BAKAB": "BAK AMBALAJ SANAYİ VE TİCARET A.Ş.",
    "IHLGM": "İHLAS GAYRİMENKUL PROJE GELİŞTİRME VE TİCARET A.Ş.",
    "GLRYH": "GÜLER YATIRIM HOLDİNG A.Ş.",
    "INTEK": "Innosa Teknoloji Anonim Sirketi",
    "MTRKS": "MATRİKS BİLGİ DAĞITIM HİZMETLERİ A.Ş.",
    "VRGYO": "Vera Konsept Gayrimenkul Yatirim Ortakligi A.S.",
    "DZGYO": "DENİZ GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.",
    "PCILT": "PC İLETİŞİM VE MEDYA HİZMETLERİ SANAYİ TİCARET A.Ş.",
    "UNLU": "ÜNLÜ YATIRIM HOLDİNG A.Ş.",
    "SANFM": "SANİFOAM ENDÜSTRİ VE TÜKETİM ÜRÜNLERİ SANAYİ TİCARET A.Ş.",
    "CELHA": "ÇELİK HALAT VE TEL SANAYİİ A.Ş.",
    "ANGEN": "ANATOLİA TANI VE BİYOTEKNOLOJİ ÜRÜNLERİ ARAŞTIRMA GELİŞTİRME SANAYİ VE TİCARET A.Ş.",
    "PRKME": "PARK ELEKTRİK ÜRETİM MADENCİLİK SANAYİ VE TİCARET A.Ş.",
    "CONSE": "CONSUS ENERJİ İŞLETMECİLİĞİ VE HİZMETLERİ A.Ş.",
    "SKTAS": "SÖKTAŞ TEKSTİL SANAYİ VE TİCARET A.Ş.",
    "ISBIR": "İŞBİR HOLDİNG A.Ş.",
    "DNISI": "DİNAMİK ISI MAKİNA YALITIM MALZEMELERİ SANAYİ VE TİCARET A.Ş.",
    "KLSYN": "KOLEKSİYON MOBİLYA SANAYİ A.Ş.",
    "EGSER": "EGE SERAMİK SANAYİ VE TİCARET A.Ş.",
    "DGATE": "DATAGATE BİLGİSAYAR MALZEMELERİ TİCARET A.Ş.",
    "BLCYT": "BİLİCİ YATIRIM SANAYİ VE TİCARET A.Ş.",
    "ESCOM": "ESCORT TEKNOLOJİ YATIRIM A.Ş.",
    "LIDFA": "LİDER FAKTORİNG A.Ş.",
    "DITAS": "DİTAŞ DOĞAN YEDEK PARÇA İMALAT VE TEKNİK A.Ş.",
    "OZSUB": "ÖZSU BALIK ÜRETİM A.Ş.",
    "EDATA": "E-DATA TEKNOLOJİ PAZARLAMA A.Ş.",
    "EDIP": "EDİP GAYRİMENKUL YATIRIM SANAYİ VE TİCARET A.Ş.",
    "BIZIM": "BİZİM TOPTAN SATIŞ MAĞAZALARI A.Ş.",
    "ULUFA": "ULUSAL FAKTORİNG A.Ş.",
    "BURVA": "BURÇELİK VANA SANAYİ VE TİCARET A.Ş.",
    "KRSTL": "KRİSTAL KOLA VE MEŞRUBAT SANAYİ TİCARET A.Ş.",
    "TLMAN": "TRABZON LİMAN İŞLETMECİLİĞİ A.Ş.",
    "VBTYZ": "VBT YAZILIM A.Ş.",
    "DGNMO": "DOĞANLAR MOBİLYA GRUBU İMALAT SANAYİ VE TİCARET A.Ş.",
    "SELVA": "SELVA GIDA SANAYİ A.Ş.",
    "DERIM": "DERİMOD KONFEKSİYON AYAKKABI DERİ SANAYİ VE TİCARET A.Ş.",
    "AYES": "AYES ÇELİK HASIR VE ÇİT SANAYİ A.Ş.",
    "EUHOL": "EURO YATIRIM HOLDİNG A.Ş.",
    "BAYRK": "BAYRAK EBT TABAN SANAYİ VE TİCARET A.Ş.",
    "MARTI": "MARTI OTEL İŞLETMELERİ A.Ş.",
    "BMSCH": "BMS ÇELİK HASIR SANAYİ VE TİCARET A.Ş.",
    "RTALB": "RTA LABORATUVARLARI BİYOLOJİK ÜRÜNLER İLAÇ VE MAKİNE SANAYİ TİCARET A.Ş.",
    "DENGE": "DENGE YATIRIM HOLDİNG A.Ş.",
    "DURKN": "Durukan Sekerleme Sanayi ve Ticaret AS",
    "SKYMD": "Seker Yatirim Menkul Degerler A.S.",
    "DOGUB": "DOĞUSAN BORU SANAYİİ VE TİCARET A.Ş.",
    "MAKIM": "MAKİM MAKİNA TEKNOLOJİLERİ SANAYİ VE TİCARET A.Ş.",
    "AVGYO": "AVRASYA GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.",
    "YESIL": "YEŞİL YATIRIM HOLDİNG A.Ş.",
    "DURDO": "DURAN DOĞAN BASIM VE AMBALAJ SANAYİ A.Ş.",
    "OSTIM": "OSTİM ENDÜSTRİYEL YATIRIMLAR VE İŞLETME A.Ş.",
    "KFEIN": "KAFEİN YAZILIM HİZMETLERİ TİCARET A.Ş.",
    "ATEKS": "AKIN TEKSTİL A.Ş.",
    "TDGYO": "TREND GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.",
    "SODSN": "SODAŞ SODYUM SANAYİİ A.Ş.",
    "DMSAS": "DEMİSAŞ DÖKÜM EMAYE MAMÜLLERİ SANAYİİ A.Ş.",
    "ARZUM": "ARZUM ELEKTRİKLİ EV ALETLERİ SANAYİ VE TİCARET A.Ş.",
    "BYDNR": "Baydoner Restoranlari A.S.",
    "CUSAN": "ÇUHADAROĞLU METAL SANAYİ VE PAZARLAMA A.Ş.",
    "OBASE": "OBASE BİLGİSAYAR VE DANIŞMANLIK HİZMETLERİ TİCARET A.Ş.",
    "PKART": "PLASTİKKART AKILLI KART İLETİŞİM SİSTEMLERİ SANAYİ VE TİCARET A.Ş.",
    "TUCLK": "TUĞÇELİK ALÜMİNYUM VE METAL MAMÜLLERİ SANAYİ VE TİCARET A.Ş.",
    "SKYLP": "Skyalp Finansal Teknolojiler ve Danismanlik A.S",
    "FRIGO": "FRİGO-PAK GIDA MADDELERİ SANAYİ VE TİCARET A.Ş.",
    "A1YEN": "A1 Yenilenebilir Enerji Uretim AS",
    "MERKO": "MERKO GIDA SANAYİ VE TİCARET A.Ş.",
    "RUBNS": "RUBENİS TEKSTİL SANAYİ TİCARET A.Ş.",
    "AVHOL": "AVRUPA YATIRIM HOLDİNG A.Ş.",
    "SNKRN": "SENKRON SİBER GÜVENLİK YAZILIM VE BİLİŞİM ÇÖZÜMLERİ A.Ş.",
    "BNTAS": "BANTAŞ BANDIRMA AMBALAJ SANAYİ TİCARET A.Ş.",
    "GLBMD": "GLOBAL MENKUL DEĞERLER A.Ş.",
    "ZEDUR": "ZEDUR ENERJİ ELEKTRİK ÜRETİM A.Ş.",
    "GSDDE": "GSD DENİZCİLİK GAYRİMENKUL İNŞAAT SANAYİ VE TİCARET A.Ş.",
    "PENGD": "PENGUEN GIDA SANAYİ A.Ş.",
    "YKSLN": "YÜKSELEN ÇELİK A.Ş.",
    "YAYLA": "YAYLA ENERJİ ÜRETİM TURİZM VE İNŞAAT TİCARET A.Ş.",
    "KRPLS": "KOROPLAST TEMİZLİK AMBALAJ ÜRÜNLERİ SANAYİ VE DIŞ TİCARET A.Ş.",
    "IHGZT": "İHLAS GAZETECİLİK A.Ş.",
    "KERVN": "KERVANSARAY YATIRIM HOLDİNG A.Ş.",
    "VKING": "VİKİNG KAĞIT VE SELÜLOZ A.Ş.",
    "PRDGS": "PARDUS GİRİŞİM SERMAYESİ YATIRIM ORTAKLIĞI A.Ş.",
    "MMCAS": "MMC SANAYİ VE TİCARİ YATIRIMLAR A.Ş.",
    "DESPC": "DESPEC BİLGİSAYAR PAZARLAMA VE TİCARET A.Ş.",
    "NIBAS": "NİĞBAŞ NİĞDE BETON SANAYİ VE TİCARET A.Ş.",
    "GEDZA": "GEDİZ AMBALAJ SANAYİ VE TİCARET A.Ş.",
    "HKTM": "HİDROPAR HAREKET KONTROL TEKNOLOJİLERİ MERKEZİ SANAYİ VE TİCARET A.Ş.",
    "PSDTC": "PERGAMON STATUS DIŞ TİCARET A.Ş.",
    "AVOD": "A.V.O.D. KURUTULMUŞ GIDA VE TARIM ÜRÜNLERİ SANAYİ TİCARET A.Ş.",
    "FADE": "FADE GIDA YATIRIM SANAYİ TİCARET A.Ş.",
    "MEGAP": "MEGA POLİETİLEN KÖPÜK SANAYİ VE TİCARET A.Ş.",
    "SEYKM": "SEYİTLER KİMYA SANAYİ A.Ş.",
    "IZINV": "İZ YATIRIM HOLDİNG A.Ş.",
    "MEPET": "MEPET METRO PETROL VE TESİSLERİ SANAYİ TİCARET A.Ş.",
    "ACSEL": "ACISELSAN ACIPAYAM SELÜLOZ SANAYİ VE TİCARET A.Ş.",
    "CEOEM": "CEO EVENT MEDYA A.Ş.",
    "RNPOL": "RAİNBOW POLİKARBONAT SANAYİ TİCARET A.Ş.",
    "MANAS": "MANAS ENERJİ YÖNETİMİ SANAYİ VE TİCARET A.Ş.",
    "COSMO": "COSMOS YATIRIM HOLDİNG A.Ş.",
    "EPLAS": "EGEPLAST EGE PLASTİK TİCARET VE SANAYİ A.Ş.",
    "AKSUE": "AKSU ENERJİ VE TİCARET A.Ş.",
    "ICUGS": "ICU Girisim Sermayesi Yatirim Ortakligi A.S.",
    "IHYAY": "İHLAS YAYIN HOLDİNG A.Ş.",
    "ETILR": "ETİLER GIDA VE TİCARİ YATIRIMLAR SANAYİ VE TİCARET A.Ş.",
    "YONGA": "YONGA MOBİLYA SANAYİ VE TİCARET A.Ş.",
    "BRKO": "BİRKO BİRLEŞİK KOYUNLULULAR MENSUCAT TİCARET VE SANAYİ A.Ş.",
    "SILVR": "SİLVERLİNE ENDÜSTRİ VE TİCARET A.Ş.",
    "ORCAY": "ORÇAY ORTAKÖY ÇAY SANAYİ VE TİCARET A.Ş.",
    "HUBVC": "HUB GİRİŞİM SERMAYESİ YATIRIM ORTAKLIĞI A.Ş.",
    "VANGD": "VANET GIDA SANAYİ İÇ VE DIŞ TİCARET A.Ş.",
    "KRTEK": "KARSU TEKSTİL SANAYİİ VE TİCARET A.Ş.",
    "BRMEN": "BİRLİK MENSUCAT TİCARET VE SANAYİ İŞLETMESİ A.Ş.",
    "PRZMA": "PRİZMA PRES MATBAACILIK YAYINCILIK SANAYİ VE TİCARET A.Ş.",
    "HATEK": "HATEKS HATAY TEKSTİL İŞLETMELERİ A.Ş.",
    "BALAT": "BALATACILAR BALATACILIK SANAYİ VE TİCARET A.Ş.",
    "MARKA": "MARKA YATIRIM HOLDİNG A.Ş.",
    "OYAYO": "OYAK YATIRIM ORTAKLIĞI A.Ş.",
    "FLAP": "FLAP KONGRE TOPLANTI HİZMETLERİ OTOMOTİV VE TURİZM A.Ş.",
    "IHEVA": "İHLAS EV ALETLERİ İMALAT SANAYİ VE TİCARET A.Ş.",
    "OYLUM": "OYLUM SINAİ YATIRIMLAR A.Ş.",
    "SEKFK": "ŞEKER FİNANSAL KİRALAMA A.Ş.",
    "SMART": "SMARTİKS YAZILIM A.Ş.",
    "OZRDN": "ÖZERDEN PLASTİK SANAYİ VE TİCARET A.Ş.",
    "ULAS": "ULAŞLAR TURİZM YATIRIMLARI VE DAYANIKLI TÜKETİM MALLARI TİCARET PAZARLAMA A.Ş.",
    "AKYHO": "AKDENİZ YATIRIM HOLDİNG A.Ş.",
    "EKIZ": "EKİZ KİMYA SANAYİ VE TİCARET A.Ş.",
    "BRKSN": "BERKOSAN YALITIM VE TECRİT MADDELERİ ÜRETİM VE TİCARET A.Ş.",
    "SEKUR": "SEKURO PLASTİK AMBALAJ SANAYİ A.Ş.",
    "SAMAT": "SARAY MATBAACILIK KAĞITÇILIK KIRTASİYECİLİK TİCARET VE SANAYİ A.Ş.",
    "ERSU": "ERSU MEYVE VE GIDA SANAYİ A.Ş.",
    "MZHLD": "MAZHAR ZORLU HOLDİNG A.Ş.",
    "VKFYO": "VAKIF MENKUL KIYMET YATIRIM ORTAKLIĞI A.Ş.",
    "RODRG": "RODRİGO TEKSTİL SANAYİ VE TİCARET A.Ş.",
    "ATSYH": "ATLANTİS YATIRIM HOLDİNG A.Ş.",
    "GRNYO": "GARANTİ YATIRIM ORTAKLIĞI A.Ş.",
    "SANEL": "SAN-EL MÜHENDİSLİK ELEKTRİK TAAHHÜT SANAYİ VE TİCARET A.Ş.",
    "ETYAT": "EURO TREND YATIRIM ORTAKLIĞI A.Ş.",
    "CASA": "CASA EMTİA PETROL KİMYEVİ VE TÜREVLERİ SANAYİ TİCARET A.Ş.",
    "ATLAS": "ATLAS MENKUL KIYMETLER YATIRIM ORTAKLIĞI A.Ş.",
    "MTRYO": "METRO YATIRIM ORTAKLIĞI A.Ş.",
    "EUKYO": "EURO KAPİTAL YATIRIM ORTAKLIĞI A.Ş.",
    "EUYO": "EURO MENKUL KIYMET YATIRIM ORTAKLIĞI A.Ş.",
    "DIRIT": "DİRİTEKS DİRİLİŞ TEKSTİL SANAYİ VE TİCARET A.Ş.",
    "ALTIN": "DARPHANE ALTIN SERTİFİKASI",
    "MARMR": "Marmara Holding AS"
}

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}.IS"

# --- TRADINGVIEW TARAMA AYARLARI (1/4: BIST Dip) ---
TRADINGVIEW_PAYLOAD_BIST_DIP = {
    "columns": [
        "name", "description", "logoid", "update_mode", "type", "typespecs",
        "close", "pricescale", "minmov", "fractional", "minmove2", "currency",
        "change", "volume", "relative_volume_10d_calc", "market_cap_basic",
        "fundamental_currency_code", "price_earnings_ttm",
        "earnings_per_share_diluted_ttm", "earnings_per_share_diluted_yoy_growth_ttm",
        "dividends_yield_current", "sector.tr", "market", "sector",
        "AnalystRating", "AnalystRating.tr", "exchange"
    ],
    "filter": [
        {"left": "RSI", "operation": "less", "right": 30},
        {"left": "Stoch.RSI.K", "operation": "less", "right": 20}
    ],
    "markets": ["turkey"],
    "options": {"lang": "en"},
    "range": [0, 5000],
    "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"}
}

# --- TRADINGVIEW TARAMA AYARLARI (2/4: NASDAQ Dip - Gelişmiş Filtre) ---
TRADINGVIEW_PAYLOAD_NASDAQ_DIP = {
    "columns": [
        "name", "close", "description", "logoid", "update_mode", "type", "typespecs", 
        "TechRating_1D", "TechRating_1D.tr", "MARating_1D", "MARating_1D.tr", 
        "OsRating_1D", "OsRating_1D.tr", "RSI", "Mom", "pricescale", "minmov", 
        "fractional", "minmove2", "AO", "CCI20", "Stoch.K", "Stoch.D", 
        "Candle.3BlackCrows", "Candle.3WhiteSoldiers", "Candle.AbandonedBaby.Bearish", 
        "Candle.AbandonedBaby.Bullish", "Candle.Doji", "Candle.Doji.Dragonfly", 
        "Candle.Doji.Gravestone", "Candle.Engulfing.Bearish", "Candle.Engulfing.Bullish", 
        "Candle.EveningStar", "Candle.Hammer", "Candle.HangingMan", 
        "Candle.Harami.Bearish", "Candle.Harami.Bullish", "Candle.InvertedHammer", 
        "Candle.Kicking.Bearish", "Candle.Kicking.Bullish", "Candle.LongShadow.Lower", 
        "Candle.LongShadow.Upper", "Candle.Marubozu.Black", "Candle.Marubozu.White", 
        "Candle.MorningStar", "Candle.ShootingStar", "Candle.SpinningTop.Black", 
        "Candle.SpinningTop.White", "Candle.TriStar.Bearish", "Candle.TriStar.Bullish", 
        "exchange"
    ],
    "filter": [
        {"left": "RSI", "operation": "less", "right": 35},
        {"left": "Stoch.RSI.K", "operation": "less", "right": 20},
        {"left": "Stoch.RSI.K", "operation": "greater", "right": "Stoch.RSI.D"},
        {"left": "SMA50", "operation": "greater", "right": "close"},
        {"left": "close", "operation": "greater", "right": 10},
        {"left": "average_volume_30d_calc", "operation": "greater", "right": 1000000},
        {"left": "OsRating_1D", "operation": "in_range", "right": ["Buy", "StrongBuy", "Neutral"]}
    ],
    "filter2": {
        "operator": "and",
        "operands": [
            {
                "operation": {
                    "operator": "or",
                    "operands": [
                         { "operation": { "operator": "and", "operands": [{"expression": {"left": "type", "operation": "equal", "right": "stock"}}, {"expression": {"left": "typespecs", "operation": "has", "right": ["common"]}}]}},
                         { "operation": { "operator": "and", "operands": [{"expression": {"left": "type", "operation": "equal", "right": "stock"}}, {"expression": {"left": "typespecs", "operation": "has", "right": ["preferred"]}}]}},
                         { "operation": { "operator": "and", "operands": [{"expression": {"left": "type", "operation": "equal", "right": "dr"}}]}},
                         { "operation": { "operator": "and", "operands": [{"expression": {"left": "type", "operation": "equal", "right": "fund"}}, {"expression": {"left": "typespecs", "operation": "has_none_of", "right": ["etf"]}}]}}
                    ]
                }
            },
            {"expression": {"left": "typespecs", "operation": "has_none_of", "right": ["pre-ipo"]}}
        ]
    },
    "ignore_unknown_fields": False, 
    "markets": ["america"],
    "options": {"lang": "en"},
    "range": [0, 5000],
    "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
    "symbols": {}
}

# --- TRADINGVIEW TARAMA AYARLARI (3/4: BIST Düşen Trend Kırılımı) ---
TRADINGVIEW_PAYLOAD_BIST_TREND = {
    "columns": [
        "name", "description", "logoid", "update_mode", "type", "typespecs", 
        "close", "pricescale", "minmov", "fractional", "minmove2", "currency", 
        "change", "volume", "relative_volume_10d_calc", "market_cap_basic", 
        "fundamental_currency_code", "price_earnings_ttm", 
        "earnings_per_share_diluted_ttm", "earnings_per_share_diluted_yoy_growth_ttm", 
        "dividends_yield_current", "sector.tr", "market", "sector", 
        "AnalystRating", "AnalystRating.tr", "exchange"
    ],
    "filter": [
        {"left": "EMA12|1M", "operation": "greater", "right": "EMA26|1M"},
        {"left": "MACD.macd|1M", "operation": "greater", "right": 0},
        {"left": "MACD.signal|1M", "operation": "greater", "right": "MACD.macd|1M"},
        {"left": "RSI|1M", "operation": "greater", "right": 60},
        {"left": "EMA20|1M", "operation": "greater", "right": "EMA50|1M"},
        {"left": "AnalystRating", "operation": "in_range", "right": ["Buy", "StrongBuy"]}
    ],
    "filter2": {
        "operator": "and",
        "operands": [
            {
                "operation": {
                    "operator": "or",
                    "operands": [
                        {"operation": {"operator": "and", "operands": [
                            {"expression": {"left": "type", "operation": "equal", "right": "stock"}},
                            {"expression": {"left": "typespecs", "operation": "has", "right": ["common"]}}
                        ]}},
                        {"operation": {"operator": "and", "operands": [
                            {"expression": {"left": "type", "operation": "equal", "right": "stock"}},
                            {"expression": {"left": "typespecs", "operation": "has", "right": ["preferred"]}}
                        ]}},
                        {"operation": {"operator": "and", "operands": [
                            {"expression": {"left": "type", "operation": "equal", "right": "dr"}}
                        ]}},
                        {"operation": {"operator": "and", "operands": [
                            {"expression": {"left": "type", "operation": "equal", "right": "fund"}},
                            {"expression": {"left": "typespecs", "operation": "has_none_of", "right": ["etf"]}}
                        ]}}
                    ]
                }
            },
            {"expression": {"left": "typespecs", "operation": "has_none_of", "right": ["pre-ipo"]}}
        ]
    },
    "ignore_unknown_fields": False,
    "markets": ["turkey"],
    "options": {"lang": "en"},
    "range": [0, 5000],
    "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
    "symbols": {}
}

# --- TRADINGVIEW TARAMA AYARLARI (4/4: BIST Potansiyelli Kağıtlar) ---
TRADINGVIEW_PAYLOAD_BIST_POTANSIYEL = {
    "columns": [
        "name", "description", "logoid", "update_mode", "type", "typespecs", "close",
        "pricescale", "minmov", "fractional", "minmove2", "currency", "change",
        "volume", "relative_volume_10d_calc", "market_cap_basic", "fundamental_currency_code",
        "price_earnings_ttm", "earnings_per_share_diluted_ttm", "earnings_per_share_diluted_yoy_growth_ttm",
        "dividends_yield_current", "sector.tr", "market", "sector", "AnalystRating",
        "AnalystRating.tr", "exchange"
    ],
    "filter": [
        {"left": "EMA20", "operation": "greater", "right": "EMA50"},
        {"left": "EMA50", "operation": "less", "right": "close"},
        {"left": "EMA200", "operation": "less", "right": "close"},
        {"left": "RSI", "operation": "greater", "right": 60},
        {"left": "MACD.macd", "operation": "greater", "right": 1},
        {"left": "TechRating_1M", "operation": "in_range", "right": ["StrongBuy"]},
        {"left": "AnalystRating", "operation": "in_range", "right": ["Buy", "StrongBuy"]}
    ],
    "filter2": {
        "operator": "and",
        "operands": [
            {
                "operation": {
                    "operator": "or",
                    "operands": [
                        {"operation": {"operator": "and", "operands": [
                            {"expression": {"left": "type", "operation": "equal", "right": "stock"}},
                            {"expression": {"left": "typespecs", "operation": "has", "right": ["common"]}}
                        ]}},
                        {"operation": {"operator": "and", "operands": [
                            {"expression": {"left": "type", "operation": "equal", "right": "stock"}},
                            {"expression": {"left": "typespecs", "operation": "has", "right": ["preferred"]}}
                        ]}},
                        {"operation": {"operator": "and", "operands": [
                            {"expression": {"left": "type", "operation": "equal", "right": "dr"}}
                        ]}},
                        {"operation": {"operator": "and", "operands": [
                            {"expression": {"left": "type", "operation": "equal", "right": "fund"}},
                            {"expression": {"left": "typespecs", "operation": "has_none_of", "right": ["etf"]}}
                        ]}}
                    ]
                }
            },
            {"expression": {"left": "typespecs", "operation": "has_none_of", "right": ["pre-ipo"]}}
        ]
    },
    "ignore_unknown_fields": False,
    "markets": ["turkey"],
    "options": {"lang": "en"},
    "range": [0, 5000], 
    "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
    "symbols": {}
}


# ------------------- Yardımcı Fonksiyonlar (Dosya Yönetimi & Utility) -------------------

def clear():
    """Konsolu temizler."""
    os.system("cls" if os.name == "nt" else "clear")

def log_user(user_id, username, first_name):
    """Kullanıcı bilgilerini users.txt dosyasına kaydeder (benzersiz kayıt)."""
    user_data = f"{user_id},{username if username else 'N/A'},{first_name if first_name else 'N/A'}\n"
    try:
        with open(USER_LOG_FILE, 'r') as f:
            existing_users = f.readlines()
    except FileNotFoundError:
        existing_users = []
        
    if not any(line.startswith(str(user_id) + ',') for line in existing_users):
        with open(USER_LOG_FILE, 'a') as f:
            f.write(user_data)
        print(f"Yeni kullanıcı kaydedildi: {user_id}")

def get_all_user_ids():
    """Kayıtlı tüm kullanıcı ID'lerini döndürür."""
    user_ids = []
    try:
        with open(USER_LOG_FILE, 'r') as f:
            for line in f:
                try:
                    user_id = int(line.split(',')[0])
                    user_ids.append(user_id)
                except ValueError:
                    continue
    except FileNotFoundError:
        pass
    return user_ids

def get_required_channels():
    """Zorunlu kanal ID'lerini channels.txt dosyasından okur."""
    channels = []
    try:
        with open(CHANNEL_LOG_FILE, 'r') as f:
            channels = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        pass
    return list(set(channels))

def add_channel_to_file(channel_id: str):
    """Yeni kanalı listeye ekler."""
    channels = get_required_channels()
    if channel_id not in channels:
        with open(CHANNEL_LOG_FILE, 'a') as f:
            f.write(f"\n{channel_id.strip()}")
        return True
    return False

def remove_channel_from_file(channel_id: str):
    """Kanalları listeden siler."""
    channels = get_required_channels()
    if channel_id in channels:
        channels.remove(channel_id)
        with open(CHANNEL_LOG_FILE, 'w') as f:
            f.write('\n'.join(channels))
        return True
    return False

# ------------------- Finansal Veri Çekme Fonksiyonları (Yahooquery) -------------------

def fetch_chart_data(symbol: str):
    params = {"range": "6mo", "interval": "1d"}
    try:
        resp = requests.get(YAHOO_CHART_URL.format(symbol), params=params, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return None
        data = resp.json()
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
        times = [datetime.fromtimestamp(t) for t in timestamps]
        return times, closes
    except Exception:
        return None

def plot_advanced_chart(symbol, times, closes):
    filtered = [(t, c) for t, c in zip(times, closes) if c is not None]
    if not filtered:
        return None
    times, closes = zip(*filtered)
    closes_np = np.array(closes)

    peaks, _ = find_peaks(closes_np, distance=5)
    troughs, _ = find_peaks(-closes_np, distance=5)

    support_level = np.mean(closes_np[troughs]) if len(troughs) > 0 else np.min(closes_np)
    resistance_level = np.mean(closes_np[peaks]) if len(peaks) > 0 else np.max(closes_np)

    x = np.arange(len(closes_np))
    z = np.polyfit(x, closes_np, 1)
    trend = np.poly1d(z)

    plt.figure(figsize=(10,5))
    plt.plot(times, closes_np, label=f"{symbol} (6 Ay)", linewidth=2)
    if len(peaks) > 0:
        plt.scatter(np.array(times)[peaks], closes_np[peaks], color='red', marker='^', label='Tepeler')
    if len(troughs) > 0:
        plt.scatter(np.array(times)[troughs], closes_np[troughs], color='green', marker='v', label='Dipler')
    plt.axhline(support_level, color='green', linestyle='--', label='Destek (ortalama)')
    plt.axhline(resistance_level, color='red', linestyle='--', label='Direnç (ortalama)')
    plt.plot(times, trend(x), color='blue', linestyle='-.', label='Trend çizgisi')
    plt.title(f"{symbol} - Son 6 Ay Gelişmiş Grafiği")
    plt.xlabel("Tarih")
    plt.ylabel("Fiyat (TRY)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    filename = f"chart_{symbol}_6m_advanced.png"
    plt.savefig(filename)
    plt.close()
    return filename

def format_value(value, is_percentage=False):
    if value is None:
        return '—'

    if isinstance(value, (int, float)):
        if is_percentage:
            return f"{value:,.2f} %"
        if abs(value) >= 1_000_000_000_000:
            return f"{value / 1_000_000_000_000:,.2f} T"
        if abs(value) >= 1_000_000_000:
            return f"{value / 1_000_000_000:,.2f} B"
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:,.2f} M"
        return f"{value:,.2f}"
    return str(value)

# YENİDEN EKLEMEK İSTEDİĞİNİZ TEMEL VERİ PNG TABLOSU FONKSİYONU
def generate_fundamentals_image(symbol, fundamentals):
    if not fundamentals:
        return None

    # Veri hazırlığı (metin tablosu için)
    data = []
    
    sections = {
        "📊 Piyasa ve Değerleme Oranları": [
            "Fiyat (TRY)", "Piyasa Değeri", "Ort. Hacim (10 gün)",
            "Geriye Dönük F/K", "İleriye Dönük F/K", "Fiyat/Satış (P/S)", 
        ],
        "📈 Karlılık ve Marjlar": [
            "Özkaynak Karlılığı (ROE) (%)", "Varlık Karlılığı (ROA) (%)",
            "Brüt Kar Marjı (%)", "Faaliyet Kar Marjı (%)", "Net Kar Marjı (%)"
        ],
        "⚖️ Likidite ve Borçluluk": [
            "Cari Oran", "Borç/Özkaynak"
        ]
    }
    
    # Tüm veriyi tek bir listeye toplayalım (başlıkları ayırmak için)
    current_section = None
    for section_title, keys in sections.items():
        data.append((section_title, "---"))
        for k in keys:
            value = fundamentals.get(k)
            is_percentage = "%" in k
            formatted_value = format_value(value, is_percentage)
            data.append((k, formatted_value))

    # Matplotlib ile tablo oluşturma
    fig, ax = plt.subplots(figsize=(6, 10))
    ax.axis('off')
    ax.set_title(f"{symbol} ({BILINEN_HISSELER.get(symbol, 'Bilinmeyen Hisse')}) Kapsamlı Veriler", 
                 fontsize=16, fontweight='bold', pad=20)
    
    # Tablo verisi ve renk ayarları
    cell_text = []
    cell_colors = []
    
    for key, val in data:
        if val == "---":
            cell_text.append([key.split(" ")[1], ""]) # Sadece başlık emojisiz
            cell_colors.append(['#D3D3D3', '#D3D3D3']) # Gri tonu başlık
        else:
            cell_text.append([key, val])
            cell_colors.append(['#f8f8f8', '#ffffff']) # Beyaz tonları veri

    # Eğer veri yoksa boş tabloyu önle
    if not data:
         return None

    table = ax.table(cellText=cell_text, 
                     colLabels=["Gösterge", "Değer"], 
                     cellLoc='left', 
                     loc='center', 
                     cellColours=cell_colors)

    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 1.5)
    
    # Başlık hücrelerini kalınlaştırma
    for i in range(len(cell_text)):
        if cell_text[i][1] == "":
            table[i, 0].set_text_props(weight='bold', color='black')
            table[i, 1].set_text_props(weight='bold', color='black')
    filename = f"fundamentals_{symbol}_comprehensive.png"
    plt.savefig(filename, bbox_inches='tight', dpi=150)
    plt.close()
    return filename


def get_val(data, key):
    val = data.get(key)
    if isinstance(val, dict):
        return val.get("raw")
    return val

def fetch_fundamentals(symbol: str):
    try:
        ticker_symbol = f"{symbol}.IS"
        t = Ticker(ticker_symbol)
        
        summary = t.summary_detail.get(ticker_symbol, {})
        price_data = t.price.get(ticker_symbol, {})
        key_stats = t.key_stats.get(ticker_symbol, {})
        financial_data = t.financial_data.get(ticker_symbol, {})

        if not summary:
            return None
            
        info = {}

        # Piyasa ve Değerleme
        info["Fiyat (TRY)"] = get_val(price_data, "regularMarketPrice")
        info["Ort. Hacim (10 gün)"] = get_val(summary, "averageDailyVolume10Day")
        info["Piyasa Değeri"] = get_val(summary, "marketCap")
        info["Geriye Dönük F/K"] = get_val(summary, "trailingPE")
        info["İleriye Dönük F/K"] = get_val(summary, "forwardPE")
        info["Fiyat/Satış (P/S)"] = get_val(summary, "priceToSalesTrailing12Months")
        
        # Karlılık ve Marjlar
        info["Brüt Kar Marjı (%)"] = get_val(financial_data, "grossMargins") * 100 if get_val(financial_data, "grossMargins") is not None else None
        info["Faaliyet Kar Marjı (%)"] = get_val(financial_data, "operatingMargins") * 100 if get_val(financial_data, "operatingMargins") is not None else None
        info["Net Kar Marjı (%)"] = get_val(financial_data, "profitMargins") * 100 if get_val(financial_data, "profitMargins") is not None else None

        info["Özkaynak Karlılığı (ROE) (%)"] = get_val(financial_data, "returnOnEquity") * 100 if get_val(financial_data, "returnOnEquity") is not None else None
        info["Varlık Karlılığı (ROA) (%)"] = get_val(financial_data, "returnOnAssets") * 100 if get_val(financial_data, "returnOnAssets") is not None else None
        
        # Likidite ve Borçluluk
        info["Cari Oran"] = get_val(financial_data, "currentRatio")
        info["Borç/Özkaynak"] = get_val(financial_data, "debtToEquity")

        return info
    except Exception as e:
        print(f"Finansal veri çekme hatası ({symbol}): {e}")
        return None

# ------------------- TradingView Tarama Fonksiyonları -------------------

def get_screener_data_from_payload(payload, url):
    """TradingView scanner API'sinden veri çeker."""
    data_json = json.dumps(payload)
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/100.0 Safari/537.36'
    }

    try:
        response = requests.post(url, headers=headers, data=data_json, timeout=15)
        response.raise_for_status()
        result = response.json()

        df_data = []
        column_names = payload["columns"]

        for item in result.get("data", []):
            symbol_pro_name = item.get("s", "")
            symbol = symbol_pro_name.split(":")[-1]
            values_list = item.get("d", [])

            row_dict = {"Symbol": symbol}
            for i, col_name in enumerate(column_names):
                row_dict[col_name] = values_list[i] if i < len(values_list) else None
            df_data.append(row_dict)

        df = pd.DataFrame(df_data)
        return df, result.get("totalCount", 0)

    except Exception as e:
        print(f"❌ TradingView Veri Çekme Hatası: {e}")
        return pd.DataFrame(), 0

# --- PNG Tablo Oluşturma Fonksiyonları (Tarama için) ---

def create_table_png_base(df, filename_prefix, title, currency_symbol):
    """Ortak PNG oluşturma mantığı."""
    tablo_df = df[["Symbol", "close"]].copy()
    col_fiyat = f"Fiyat ({currency_symbol})"
    tablo_df.rename(columns={"Symbol": "Hisse", "close": col_fiyat}, inplace=True)

    total_rows = len(tablo_df)
    PAGE_SIZE = 20
    total_pages = math.ceil(total_rows / PAGE_SIZE)

    for page in range(total_pages):
        start = page * PAGE_SIZE
        end = min(start + PAGE_SIZE, total_rows)
        chunk = tablo_df.iloc[start:end]

        mid = len(chunk) // 2 + len(chunk) % 2
        left = chunk.iloc[:mid].reset_index(drop=True)
        right = chunk.iloc[mid:].reset_index(drop=True)

        while len(right) < mid:
            right = pd.concat([right, pd.DataFrame([["", ""]] * (mid - len(right)), columns=right.columns)], ignore_index=True)
        
        combined = pd.DataFrame({
            "Hisse": left["Hisse"],
            col_fiyat: left[col_fiyat],
            "Hisse_2": right["Hisse"],
            f"{col_fiyat}_2": right[col_fiyat]
        })

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.axis("off")
        fig.patch.set_facecolor("#1e1e1e")

        ax.text(
            0.5, 1.05,
            f"{title} (Sayfa {page+1}/{total_pages})",
            color="white", fontsize=13, fontweight="bold", ha="center", transform=ax.transAxes
        )

        table = ax.table(
            cellText=combined.values,
            colLabels=["Hisse", col_fiyat, "Hisse", col_fiyat],
            cellLoc="center",
            loc="center"
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.4)

        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_facecolor("#333333")
                cell.set_text_props(color="white", fontweight="bold")
            else:
                cell.set_facecolor("#1e1e1e")
                cell.set_text_props(color="white")
            cell.set_edgecolor("#444444")

        plt.tight_layout()
        file_name = f"{filename_prefix}_{page + 1}.png"
        plt.savefig(file_name, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        print(f"🖼️ {file_name} kaydedildi.")
        
def create_table_png_bist_dip(df, filename_prefix="TR_tablo_dip"):
    return create_table_png_base(df, filename_prefix, "Dip Taraması BIST", "₺")

def create_table_png_nasdaq_dip(df, filename_prefix="US_tablo_dip"):
    return create_table_png_base(df, filename_prefix, "Dip Taraması NASDAQ", "$")

def create_table_png_bist_trend(df, filename_prefix="TR_trend_kirilimi"):
    return create_table_png_base(df, filename_prefix, "Düşen Trend Kırılımı BIST", "₺")

def create_table_png_bist_potansiyel(df, filename_prefix="TR_potansiyelli"):
    return create_table_png_base(df, filename_prefix, "Potansiyelli Kağıtlar BIST", "₺")


# ------------------- TRADINGVIEW ASENKRON TARAMA HANDLER'LARI -------------------

async def send_dip_tarama_bist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """BIST RSI<30 & StochRSI.K<20 sonuçlarını çeker ve PNG olarak gönderir."""
    
    query = update.callback_query
    await query.answer("Tarama başlatılıyor...")
    
    bist_payload = TRADINGVIEW_PAYLOAD_BIST_DIP.copy() 
    scanner_url_bist = "https://scanner.tradingview.com/turkey/scan" 

    await query.edit_message_text("⏳ **Dip Taraması BIST** sonuçları alınıyor ve tablo oluşturuluyor...")
    
    df_sonuc, toplam_adet = get_screener_data_from_payload(bist_payload, scanner_url_bist)
    
    keyboard = [[InlineKeyboardButton("⬅️ Ana Menü", callback_data="BACK_MAIN")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if not df_sonuc.empty:
        filename_prefix = "TR_tablo_dip"
        create_table_png_bist_dip(df_sonuc, filename_prefix=filename_prefix)
        
        all_files = os.listdir('.')
        png_files = sorted([f for f in all_files if f.startswith(filename_prefix) and f.endswith('.png')])
        
        sent_files = 0
        
        if png_files:
            for file_name in png_files:
                try:
                    with open(file_name, "rb") as img:
                        caption = f"📈 **Dip Taraması BIST** Sonuçları ({file_name.split('_')[-1].replace('.png', '')}) - Toplam Hisse: {toplam_adet}"
                        await context.bot.send_photo(chat_id=query.message.chat_id, photo=img, caption=caption)
                    sent_files += 1
                except Exception as e:
                    print(f"PNG gönderme hatası ({file_name}): {e}")
                finally:
                    if os.path.exists(file_name):
                        os.remove(file_name)
                    
            if sent_files > 0:
                await query.message.reply_text(f"✅ Tarama tamamlandı. Toplam **{toplam_adet}** hisse bulundu ve **{sent_files}** görsel gönderildi.", reply_markup=reply_markup)
            else:
                await query.message.reply_text("❌ Tarama sonuçları alındı ancak görsel gönderme hatası oluştu.", reply_markup=reply_markup)
                
        else:
            await query.message.reply_text("❌ Kurala uyan hisse bulunamadı, tablo oluşturulamadı.", reply_markup=reply_markup)

    else:
        await query.message.reply_text("❌ Veri çekme başarısız oldu veya kurala uyan sembol bulunamadı.", reply_markup=reply_markup)


async def send_dip_tarama_nasdaq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nasdaq gelişmiş dip filtresi sonuçlarını çeker ve PNG olarak gönderir."""
    
    query = update.callback_query
    await query.answer("Tarama başlatılıyor...")
    
    nasdaq_payload = TRADINGVIEW_PAYLOAD_NASDAQ_DIP.copy()
    scanner_url_nasdaq = "https://scanner.tradingview.com/america/scan" 

    await query.edit_message_text("⏳ **Dip Taraması NASDAQ** sonuçları alınıyor ve tablo oluşturuluyor...")
    
    df_sonuc, toplam_adet = get_screener_data_from_payload(nasdaq_payload, scanner_url_nasdaq)
    
    keyboard = [[InlineKeyboardButton("⬅️ Ana Menü", callback_data="BACK_MAIN")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if not df_sonuc.empty:
        filename_prefix = "US_tablo_dip"
        create_table_png_nasdaq_dip(df_sonuc, filename_prefix=filename_prefix)
        
        all_files = os.listdir('.')
        png_files = sorted([f for f in all_files if f.startswith(filename_prefix) and f.endswith('.png')])
        
        sent_files = 0
        
        if png_files:
            for file_name in png_files:
                try:
                    with open(file_name, "rb") as img:
                        caption_parts = file_name.split('_')
                        page_info = f"Sayfa {caption_parts[-1].replace('.png', '')}"
                        caption = f"📈 **Dip Taraması NASDAQ** Sonuçları ({page_info}) - Toplam Hisse: {toplam_adet}"
                        await context.bot.send_photo(chat_id=query.message.chat_id, photo=img, caption=caption)
                    sent_files += 1
                except Exception as e:
                    print(f"PNG gönderme hatası ({file_name}): {e}")
                finally:
                    if os.path.exists(file_name):
                        os.remove(file_name)
                    
            if sent_files > 0:
                await query.message.reply_text(f"✅ Tarama tamamlandı. Toplam **{toplam_adet}** hisse bulundu ve **{sent_files}** görsel gönderildi.", reply_markup=reply_markup)
            else:
                await query.message.reply_text("❌ Tarama sonuçları alındı ancak görsel gönderme hatası oluştu.", reply_markup=reply_markup)
                
        else:
            await query.message.reply_text("❌ Kurala uyan hisse bulunamadı, tablo oluşturulamadı.", reply_markup=reply_markup)

    else:
        await query.message.reply_text("❌ Veri çekme başarısız oldu veya kurala uyan sembol bulunamadı.", reply_markup=reply_markup)


async def send_dusen_trend_bist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Düşen Trend Kırılımı BIST (EMA, MACD, RSI bazlı) sonuçlarını çeker ve PNG olarak gönderir."""
    
    query = update.callback_query
    await query.answer("Tarama başlatılıyor...")
    
    trend_payload = TRADINGVIEW_PAYLOAD_BIST_TREND.copy()
    scanner_url_bist = "https://scanner.tradingview.com/turkey/scan" 

    await query.edit_message_text("⏳ **Düşen Trend Kırılımı BIST** sonuçları alınıyor ve tablo oluşturuluyor...")
    
    df_sonuc, toplam_adet = get_screener_data_from_payload(trend_payload, scanner_url_bist)
    
    keyboard = [[InlineKeyboardButton("⬅️ Ana Menü", callback_data="BACK_MAIN")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if not df_sonuc.empty:
        filename_prefix = "TR_trend_kirilimi"
        create_table_png_bist_trend(df_sonuc, filename_prefix=filename_prefix)
        
        all_files = os.listdir('.')
        png_files = sorted([f for f in all_files if f.startswith(filename_prefix) and f.endswith('.png')])
        
        sent_files = 0
        
        if png_files:
            for file_name in png_files:
                try:
                    with open(file_name, "rb") as img:
                        caption_parts = file_name.split('_')
                        page_info = f"Sayfa {caption_parts[-1].replace('.png', '')}"
                        caption = f"🚀 **Düşen Trend Kırılımı BIST** Sonuçları ({page_info}) - Toplam Hisse: {toplam_adet}"
                        await context.bot.send_photo(chat_id=query.message.chat_id, photo=img, caption=caption)
                    sent_files += 1
                except Exception as e:
                    print(f"PNG gönderme hatası ({file_name}): {e}")
                finally:
                    if os.path.exists(file_name):
                        os.remove(file_name)
                    
            if sent_files > 0:
                await query.message.reply_text(f"✅ Tarama tamamlandı. Toplam **{toplam_adet}** hisse bulundu ve **{sent_files}** görsel gönderildi.", reply_markup=reply_markup)
            else:
                await query.message.reply_text("❌ Tarama sonuçları alındı ancak görsel gönderme hatası oluştu.", reply_markup=reply_markup)
                
        else:
            await query.message.reply_text("❌ Kurala uyan hisse bulunamadı, tablo oluşturulamadı.", reply_markup=reply_markup)

    else:
        await query.message.reply_text("❌ Veri çekme başarısız oldu veya kurala uyan sembol bulunamadı.", reply_markup=reply_markup)


async def send_potansiyelli_kagitlar_bist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Potansiyelli Kağıtlar BIST taraması sonuçlarını çeker ve PNG olarak gönderir."""
    
    query = update.callback_query
    await query.answer("Tarama başlatılıyor...")
    
    potansiyel_payload = TRADINGVIEW_PAYLOAD_BIST_POTANSIYEL.copy()
    scanner_url_bist = "https://scanner.tradingview.com/turkey/scan" 

    await query.edit_message_text("⏳ **Potansiyelli Kağıtlar BIST** sonuçları alınıyor ve tablo oluşturuluyor...")
    
    df_sonuc, toplam_adet = get_screener_data_from_payload(potansiyel_payload, scanner_url_bist)
    
    keyboard = [[InlineKeyboardButton("⬅️ Ana Menü", callback_data="BACK_MAIN")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if not df_sonuc.empty:
        filename_prefix = "TR_potansiyelli"
        create_table_png_bist_potansiyel(df_sonuc, filename_prefix=filename_prefix)
        
        all_files = os.listdir('.')
        png_files = sorted([f for f in all_files if f.startswith(filename_prefix) and f.endswith('.png')])
        
        sent_files = 0
        
        if png_files:
            for file_name in png_files:
                try:
                    with open(file_name, "rb") as img:
                        caption_parts = file_name.split('_')
                        page_info = f"Sayfa {caption_parts[-1].replace('.png', '')}"
                        caption = f"💰 **Potansiyelli Kağıtlar BIST** Sonuçları ({page_info}) - Toplam Hisse: {toplam_adet}"
                        await context.bot.send_photo(chat_id=query.message.chat_id, photo=img, caption=caption)
                    sent_files += 1
                except Exception as e:
                    print(f"PNG gönderme hatası ({file_name}): {e}")
                finally:
                    if os.path.exists(file_name):
                        os.remove(file_name)
                    
            if sent_files > 0:
                await query.message.reply_text(f"✅ Tarama tamamlandı. Toplam **{toplam_adet}** hisse bulundu ve **{sent_files}** görsel gönderildi.", reply_markup=reply_markup)
            else:
                await query.message.reply_text("❌ Tarama sonuçları alındı ancak görsel gönderme hatası oluştu.", reply_markup=reply_markup)
                
        else:
            await query.message.reply_text("❌ Kurala uyan hisse bulunamadı, tablo oluşturulamadı.", reply_markup=reply_markup)

    else:
        await query.message.reply_text("❌ Veri çekme başarısız oldu veya kurala uyan sembol bulunamadı.", reply_markup=reply_markup)


# ------------------- KANAL ABONELİĞİ KONTROLÜ -------------------

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcının zorunlu kanallara abone olup olmadığını kontrol eder (Mesaj/Start için)."""
    user_id = update.effective_user.id
    # get_required_channels fonksiyonunun kanal ID'lerini veya @kullanıcıadlarını döndürdüğünü varsayıyoruz.
    required_channels = get_required_channels() 

    if not required_channels:
        return True 

    missing_channels = []
    
    for channel_id in required_channels:
        try:
            # Kanala katılım kontrolü
            member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                missing_channels.append(channel_id)
        except Exception as e:
            # Hata oluştuysa (örn: username not found, bot kanalda değil, user_id yanlış, vs.), eksik kabul et.
            print(f"Kanal kontrol hatası ({channel_id}): {e}")
            missing_channels.append(channel_id) 

    if not missing_channels:
        return True 
    else:
        keyboard = []
        for channel in missing_channels: # Sadece eksik olan kanalları listelemek daha iyi
            # Kanal formatını belirleme ve link oluşturma
            
            # Eğer kanal kimliği @ ile başlıyorsa, genel kullanıcı adıdır.
            if channel.startswith('@'):
                link_url = f"https://t.me/{channel.replace('@', '')}"
                link_name = channel
            # Eğer sayısal ID veya davet bağlantısı (hash) ise.
            # Bot genellikle kanal ID'si (örneğin -10012345678) ile çalışır, 
            # ancak davet için genellikle t.me/joinchat/ hash kullanılır.
            # Güvenlik için, bu tür ID'lerin bir map'te tutulup linkin oradan çekilmesi en sağlıklısıdır.
            # Ancak genel varsayım, kanal ID'sini kullanmaktır.
            else:
                # Botun kanal ID'sine erişim izni varsa, info çekip link oluşturabiliriz
                # Ancak bu karmaşıklığı artırır. En basit yöntem, dışarıdan doğru linki sağlamaktır.
                # Varsayım: Girdiğiniz string zaten davet linkinin son kısmıdır (hash).
                # Eğer kanal ID'si ise, t.me/@ID çalışmaz, bu yüzden sadece @ ile başlayanlara odaklanalım
                # veya manuel olarak t.me/kanal_kullanici_adi şeklinde map yapısı kuralım.
                
                # Şimdilik en güvenli yol: Genel kanallar için kullanıcı adı (@) kullanmak.
                # Eğer bu kısım çalışmıyorsa, bu kanalın davet linkini get_required_channels() içinde tutmanız gerekir.
                link_url = f"https://t.me/joinchat/{channel}"
                link_name = f"ID: {channel}"


            keyboard.append([InlineKeyboardButton(f"➡️ Kanal: {link_name}", url=link_url)])
        
        keyboard.append([InlineKeyboardButton("✅ Kontrol Et (Abone Oldum)", callback_data="CHECK_SUBSCRIPTION")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 'if update.message' kontrolü yerine, update.effective_message kullanmak daha güvenlidir.
        if update.effective_message:
            await update.effective_message.reply_text(
                "🛑 **Devam etmek için aşağıdaki kanallara abone olmanız gerekmektedir.**\n"
                "Abone olduktan sonra 'Kontrol Et' butonuna tıklayınız.", 
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        return False

async def check_subscription_for_callback(user_id, context, message):
    """Callback sorgularından gelen kullanıcılar için abonelik kontrolü ve mesaj güncellemesi yapar."""
    required_channels = get_required_channels()
    missing_channels = []
    
    if not required_channels:
        return True 

    for channel_id in required_channels:
        try:
            member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                missing_channels.append(channel_id)
        except Exception as e:
            print(f"Kanal kontrol hatası ({channel_id}): {e}")
            missing_channels.append(channel_id)

    if not missing_channels:
        return True
    else:
        keyboard = []
        for channel in required_channels:
            link_url = f"https://t.me/{channel}" if channel.startswith('@') else f"https://t.me/joinchat/{channel}"
            link_name = channel.replace('@', '')
            keyboard.append([InlineKeyboardButton(f"➡️ Kanal: {link_name}", url=link_url)])
        
        keyboard.append([InlineKeyboardButton("✅ Kontrol Et (Abone Oldum)", callback_data="CHECK_SUBSCRIPTION")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.edit_text(
            "🛑 **Devam etmek için aşağıdaki kanallara abone olmanız gerekmektedir.**\n"
            "Abone olduktan sonra 'Kontrol Et' butonuna tıklayınız.", 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return False

# ------------------- KLAVYE & MENÜ FONKSİYONLARI -------------------

def main_menu_keyboard():
    """Ana menü için InlineKeyboardMarkup döndürür."""
    keyboard = [
        [
            InlineKeyboardButton("📈 Hisse Analizi (Teknik+Temel)", callback_data="HISSE"),
        ],
        [
            InlineKeyboardButton("📊 Tarama Listeleri", callback_data="TARAMA"),
        ],
        [
            InlineKeyboardButton("📣 Reklam/İletişim", callback_data="REKLAM"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# ------------------- Komutlar -------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user(user.id, user.username, user.first_name)
    
    if not await check_subscription(update, context):
        return
        
    await update.message.reply_text("Hoşgeldiniz! Menüden bir seçenek seçin:", reply_markup=main_menu_keyboard())

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Abonelikler kontrol ediliyor...")
    
    await query.edit_message_text("⏳ Abonelikler tekrar kontrol ediliyor...")
    
    is_subscribed = await check_subscription_for_callback(query.from_user.id, context, query.message)

    if is_subscribed:
        await query.edit_message_text("✅ Abonelik kontrolü başarılı. Menüden bir seçenek seçin:", 
                                     reply_markup=main_menu_keyboard())

# --- YETKİLİ KANAL YÖNETİM KOMUTLARI ---
async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ Bu komutu kullanmaya yetkiniz yok.")
        return

    if not context.args:
        await update.message.reply_text("➕ Lütfen eklenecek kanalın ID'sini veya @kullanıcıadını girin. Örn: `/addchannel @kanal_ismi`")
        return

    channel_id = context.args[0].strip()
    
    if not channel_id.startswith('@') and not channel_id.startswith('-100'):
        await update.message.reply_text("⚠️ Geçersiz kanal ID formatı. Lütfen '@kanal_adı' veya '-100...' sayısal ID kullanın.")
        return

    if add_channel_to_file(channel_id):
        await update.message.reply_text(f"✅ Kanal **{channel_id}** zorunlu abonelik listesine eklendi. Botun bu kanalda yönetici olduğundan emin olun.")
    else:
        await update.message.reply_text(f"ℹ️ Kanal **{channel_id}** zaten listede bulunuyor.")

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ Bu komutu kullanmaya yetkiniz yok.")
        return

    if not context.args:
        await update.message.reply_text("➖ Lütfen kaldırılacak kanalın ID'sini veya @kullanıcıadını girin. Örn: `/removechannel @eski_kanal`")
        return

    channel_id = context.args[0].strip()

    if remove_channel_from_file(channel_id):
        await update.message.reply_text(f"✅ Kanal **{channel_id}** zorunlu abonelik listesinden kaldırıldı.")
    else:
        await update.message.reply_text(f"ℹ️ Kanal **{channel_id}** listede bulunamadı.")
        
async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ Bu komutu kullanmaya yetkiniz yok.")
        return

    channels = get_required_channels()
    if channels:
        channel_list = "\n".join(channels)
        await update.message.reply_text(f"📢 Zorunlu Abonelik Kanalları:\n\n{channel_list}")
    else:
        await update.message.reply_text("📢 Zorunlu abonelik kanalı bulunmamaktadır.")

async def duyuru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Yetki kontrolü
    if update.effective_user.id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ Bu komutu kullanmaya yetkiniz yok.")
        return
    
    if not context.args:
        await update.message.reply_text("📢 Lütfen duyuru metnini girin. Örn: `/duyuru Botumuz güncellenmiştir.`")
        return

    announcement_text = "📣 **DUYURU** 📣\n\n" + " ".join(context.args)
    
    user_ids = get_all_user_ids()
    sent_count = 0
    failed_count = 0

    await update.message.reply_text(f"⏳ Duyuru {len(user_ids)} kayıtlı kullanıcıya gönderiliyor...")

    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=announcement_text, parse_mode='Markdown')
            sent_count += 1
        except Exception as e:
            print(f"Duyuru gönderilemedi (ID: {user_id}): {e}")
            failed_count += 1
            
    await update.message.reply_text(f"✅ Duyuru tamamlandı.\nBaşarılı: **{sent_count}**\nBaşarısız: **{failed_count}**")

# ------------------- Mesaj ve Callback Handler'ları -------------------

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "CHECK_SUBSCRIPTION":
        await check_subscription_callback(update, context)
        return

    if data == "BACK_MAIN":
        is_subscribed = await check_subscription_for_callback(query.from_user.id, context, query.message)
        
        if not is_subscribed:
             return 
             
        await query.edit_message_text("Ana menüye dönüldü.", reply_markup=main_menu_keyboard())
        return

    # Abonelik kontrolü her zaman başta yapılmalı
    is_subscribed = await check_subscription_for_callback(query.from_user.id, context, query.message)
    if not is_subscribed:
        return 

    if data == "HISSE":
        await query.edit_message_text("📈 Lütfen analiz yapmak istediğiniz hisse kodunu yazınız:")
        context.user_data['waiting_for_stock'] = True
        return

    if data == "TARAMA":
        keyboard = [
            [InlineKeyboardButton("✅ Dip Taraması (RSI<30, Stoch<20) BIST", callback_data="Dip_Taramasi_BIST")],
            [InlineKeyboardButton("✅ Dip Taraması (Yeni Filtreler) NASDAQ", callback_data="Dip_Taramasi_NASDAQ")],
            [InlineKeyboardButton("✅ Düşen Trend Kırılımı BIST", callback_data="Dusen_Trend_Kirilimi_BIST")],
            [InlineKeyboardButton("✅ Potansiyelli Kağıtlar BIST", callback_data="Potansiyelli_Kagitlar_BIST")], 
            [InlineKeyboardButton("⬅️ Ana Menü", callback_data="BACK_MAIN")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📊 Tarama seçeneklerinden birini seçin:", reply_markup=reply_markup)
        return

    if data == "REKLAM":
        keyboard = [[InlineKeyboardButton("⬅️ Geri Dön", callback_data="BACK_MAIN")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📢 Yardım, sorun bildir veya reklam ver seçenekleri için mesaj atın.", reply_markup=reply_markup)
        return

    # --- TARAMA BUTONLARI YÖNLENDİRMELERİ ---
    if data == "Dip_Taramasi_BIST":
        await send_dip_tarama_bist(update, context)
        return

    if data == "Dip_Taramasi_NASDAQ":
        await send_dip_tarama_nasdaq(update, context)
        return

    if data == "Dusen_Trend_Kirilimi_BIST":
        await send_dusen_trend_bist(update, context)
        return

    if data == "Potansiyelli_Kagitlar_BIST": 
        await send_potansiyelli_kagitlar_bist(update, context)
        return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context): # Bu fonksiyonun tanımlı olduğunu varsayıyorum
        return

    if context.user_data.get('waiting_for_stock'):
        text = update.message.text.strip().upper()
        context.user_data['waiting_for_stock'] = False
        
        mevcut_hisseler = list(BILINEN_HISSELER.keys())
        
        # 1. Tam Eşleşme Kontrolü
        if text in BILINEN_HISSELER:
            
            hisse_adi = BILINEN_HISSELER[text]
            # 1.1. Yükleniyor Mesajı
            message = await update.message.reply_text(f"⏳ **{text}** ({hisse_adi}) için kapsamlı veriler alınıyor... Bu işlem biraz zaman alabilir.")
            
            # --- VERİ ÇEKME VE GÖRSELLEŞTİRME BLOKU ---
            
            # Grafik ve Temel Analiz için veri çekme ve görselleri oluşturma
            chart_path = None
            chart_result = fetch_chart_data(text) # Bu yardımcı fonksiyon tanımlı olmalı
            if chart_result:
                times, closes = chart_result
                chart_path = plot_advanced_chart(text, times, closes) # Bu yardımcı fonksiyon tanımlı olmalı

            fundamentals = fetch_fundamentals(text) # Bu yardımcı fonksiyon tanımlı olmalı
            fundamentals_path = None
            if fundamentals:
                fundamentals_path = generate_fundamentals_image(text, fundamentals) # Bu yardımcı fonksiyon tanımlı olmalı

            await message.delete() # Yükleniyor mesajını sil

            # 1.2. Teknik Analiz PNG Gönderimi
            if chart_path:
                with open(chart_path, "rb") as img:
                    await update.message.reply_photo(img, caption=f"📈 **{text}** ({hisse_adi}) - Son 6 Ay Gelişmiş Grafiği")
                os.remove(chart_path)
            else:
                await update.message.reply_text(f"⚠️ **{text}** ({hisse_adi}) için teknik analiz grafiği verisi alınamadı.")

            # 1.3. Temel Analiz PNG Tablosu Gönderimi
            if fundamentals_path:
                with open(fundamentals_path, "rb") as img2:
                    await update.message.reply_photo(img2, caption=f"💹 **{text}** ({hisse_adi}) - Kapsamlı Temel Analiz Verileri")
                os.remove(fundamentals_path)
            else:
                await update.message.reply_text(f"⚠️ **{text}** ({hisse_adi}) için kapsamlı temel analiz verileri alınamadı.")


            keyboard = [[InlineKeyboardButton("⬅️ Ana Menü", callback_data="BACK_MAIN")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("İşlem tamamlandı.", reply_markup=reply_markup)
            
            return # Tam eşleşme işlemi bitti
        
        # 2. Benzerlik Kontrolü (Fuzzy Matching) - Şirket Adı Eklendi
        # process import edilmeli (thefuzz kütüphanesi)
        best_matches = process.extractBests(text, mevcut_hisseler, limit=5, score_cutoff=80) 

        if best_matches:
            # Öneri metnini hazırla
            oneriler = []
            for match, score in best_matches:
                company_name = BILINEN_HISSELER.get(match, "Bilinmeyen Şirket") # Şirket adı burada alınıyor
                
                if score >= 85:
                    oneriler.append(f"**{match}** ({company_name}) - Skor: {score}%")
                else:
                    oneriler.append(f"*{match}* ({company_name}) - Skor: {score}%") 
            
            oneriler_metni = "\n".join(oneriler)
            
            keyboard = [
                [InlineKeyboardButton("⬅️ Ana Menü", callback_data="BACK_MAIN")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"❌ **'{text}'** kodu tam olarak bulunamadı, ancak aşağıdaki gibi benzer hisseler bulundu:\n\n{oneriler_metni}\n\nLütfen listedekilerden birini **tam olarak** girin veya ana menüye dönün.", 
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
            return

        # 3. Hiçbir Eşleşme Yoksa
        keyboard = [[InlineKeyboardButton("⬅️ Ana Menü", callback_data="BACK_MAIN")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"❌ **{text}** geçerli bir BIST kodu değil ve benzer bir kod da bulunamadı. Lütfen listedeki kodlardan birini girin: {', '.join(list(BILINEN_HISSELER.keys())[:10])}...", 
            reply_markup=reply_markup
        )
        return
        
    else:
        await update.message.reply_text("Lütfen menüden bir seçenek seçin veya /start yazın.")
# ------------------- Hata -------------------

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f'Hata oluştu: {context.error}')
    if update and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin veya /start ile menüye dönün."
            )
        except:
            pass

# ------------------- Bot Başlat -------------------

def main():
    clear()
    print("Bot modülleri kontrol ediliyor...")
    


    time.sleep(1)
    print("Bot çalışıyor... ✅\n")

    app = Application.builder().token(BOT_TOKEN).build()
    
    # Komutlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("duyuru", duyuru))
    app.add_handler(CommandHandler("addchannel", add_channel)) 
    app.add_handler(CommandHandler("removechannel", remove_channel)) 
    app.add_handler(CommandHandler("listchannels", list_channels)) 
    
    # Callback Query Handler
    app.add_handler(CallbackQueryHandler(button))
    
    # Mesaj Handler (Komut olmayan tüm metin mesajları)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.add_error_handler(error)
    app.run_polling()

if __name__ == "__main__":
    main()