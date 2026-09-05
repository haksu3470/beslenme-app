import streamlit as st
import pandas as pd
import requests
import re
import json
import os
import hashlib
import base64
from datetime import datetime, date
from PIL import Image
import numpy as np
import easyocr
import extra_streamlit_components as stx

st.set_page_config(page_title="Beslenme & Öğün Takibi", layout="wide")

DB_FILE = "database.json"

# --- ÇEREZ (COOKIE) YÖNETİCİSİ ---
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

# --- ŞİFRELEME YARDIMCISI ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# --- ZENGİNLEŞTİRİLMİŞ VARSAYILAN BESİN LİSTESİ ---
DEFAULT_FOOD_DATABASE = [
    # --- EKMEK & UNLU MAMULLER ---
    {"id": 1, "kategori": "Ekmek & Unlu Mamuller", "isim": "Beyaz Somun Ekmek (1 Dilim ~30g)", "kalori": 79.0, "protein": 2.6, "karbonhidrat": 15.0, "yag": 0.8},
    {"id": 2, "kategori": "Ekmek & Unlu Mamuller", "isim": "Tam Buğday Ekmeği (1 Dilim ~30g)", "kalori": 72.0, "protein": 2.7, "karbonhidrat": 12.6, "yag": 0.9},
    {"id": 3, "kategori": "Ekmek & Unlu Mamuller", "isim": "Çavdar Ekmeği (1 Dilim ~30g)", "kalori": 68.0, "protein": 2.5, "karbonhidrat": 13.0, "yag": 0.6},
    {"id": 4, "kategori": "Ekmek & Unlu Mamuller", "isim": "Kepek Ekmeği (1 Dilim ~30g)", "kalori": 65.0, "protein": 2.8, "karbonhidrat": 12.0, "yag": 0.5},
    {"id": 5, "kategori": "Ekmek & Unlu Mamuller", "isim": "Yulaf Ekmeği (1 Dilim ~30g)", "kalori": 74.0, "protein": 3.0, "karbonhidrat": 12.5, "yag": 1.1},
    {"id": 6, "kategori": "Ekmek & Unlu Mamuller", "isim": "Mısır Ekmeği (1 Dilim ~50g)", "kalori": 140.0, "protein": 3.2, "karbonhidrat": 26.0, "yag": 2.5},
    {"id": 7, "kategori": "Ekmek & Unlu Mamuller", "isim": "Lavaş / Dürüm Ekmeği (1 Adet ~60g)", "kalori": 170.0, "protein": 5.0, "karbonhidrat": 32.0, "yag": 2.0},
    {"id": 8, "kategori": "Ekmek & Unlu Mamuller", "isim": "Pita / Tırnak Pide Ekmeği (1 Porsiyon ~100g)", "kalori": 260.0, "protein": 8.5, "karbonhidrat": 52.0, "yag": 1.5},
    {"id": 9, "kategori": "Ekmek & Unlu Mamuller", "isim": "Bazlama (1 Adet ~150g)", "kalori": 390.0, "protein": 12.0, "karbonhidrat": 78.0, "yag": 3.0},
    {"id": 10, "kategori": "Ekmek & Unlu Mamuller", "isim": "Köy Ekmeği (Ekşi Mayalı) (1 Dilim ~50g)", "kalori": 120.0, "protein": 4.0, "karbonhidrat": 23.0, "yag": 1.0},
    {"id": 11, "kategori": "Ekmek & Unlu Mamuller", "isim": "Peynirli / Patatesli Gözleme (1 Adet ~150g)", "kalori": 380.0, "protein": 10.0, "karbonhidrat": 54.0, "yag": 14.0},

    # --- KAHVALTILIKLAR & SÜRÜLEBİLİRLER ---
    {"id": 12, "kategori": "Kahvaltılıklar", "isim": "Siyah Zeytin (1 Adet ~5g)", "kalori": 115.0, "protein": 0.8, "karbonhidrat": 6.3, "yag": 10.7},
    {"id": 13, "kategori": "Kahvaltılıklar", "isim": "Yeşil Zeytin (1 Adet ~5g)", "kalori": 145.0, "protein": 1.0, "karbonhidrat": 3.8, "yag": 15.3},
    {"id": 14, "kategori": "Kahvaltılıklar", "isim": "Süzme / Çiçek Balı (1 Y.Kaşığı ~20g)", "kalori": 304.0, "protein": 0.3, "karbonhidrat": 82.4, "yag": 0.0},
    {"id": 15, "kategori": "Kahvaltılıklar", "isim": "Reçel Çeşitleri (1 Y.Kaşığı ~20g)", "kalori": 278.0, "protein": 0.4, "karbonhidrat": 69.0, "yag": 0.1},
    {"id": 16, "kategori": "Kahvaltılıklar", "isim": "Tahin (1 Y.Kaşığı ~15g)", "kalori": 595.0, "protein": 17.0, "karbonhidrat": 21.0, "yag": 53.0},
    {"id": 17, "kategori": "Kahvaltılıklar", "isim": "Pekmez (Üzüm/Dut) (1 Y.Kaşığı ~20g)", "kalori": 290.0, "protein": 0.0, "karbonhidrat": 74.0, "yag": 0.0},
    {"id": 18, "kategori": "Kahvaltılıklar", "isim": "Tahin-Pekmez Karışımı (1 Y.Kaşığı ~20g)", "kalori": 420.0, "protein": 7.0, "karbonhidrat": 50.0, "yag": 22.0},
    {"id": 19, "kategori": "Kahvaltılıklar", "isim": "Kakaolu Fındık Kreması / Nutella (1 Y.Kaşığı ~20g)", "kalori": 539.0, "protein": 6.3, "karbonhidrat": 57.5, "yag": 30.9},
    {"id": 20, "kategori": "Kahvaltılıklar", "isim": "Fıstık Ezmesi (Şekersiz) (1 Y.Kaşığı ~20g)", "kalori": 588.0, "protein": 25.0, "karbonhidrat": 20.0, "yag": 50.0},
    {"id": 21, "kategori": "Kahvaltılıklar", "isim": "Kaymak (1 Y.Kaşığı ~20g)", "kalori": 586.0, "protein": 1.2, "karbonhidrat": 2.1, "yag": 63.0},
    {"id": 22, "kategori": "Kahvaltılıklar", "isim": "Tereyağı (1 Y.Kaşığı ~14g)", "kalori": 717.0, "protein": 0.9, "karbonhidrat": 0.1, "yag": 81.0},
    {"id": 23, "kategori": "Kahvaltılıklar", "isim": "Dana Sucuk (Pişmiş/Izgara)", "kalori": 330.0, "protein": 14.0, "karbonhidrat": 2.0, "yag": 29.0},
    {"id": 24, "kategori": "Kahvaltılıklar", "isim": "Menemen (1 Porsiyon ~200g)", "kalori": 72.0, "protein": 4.5, "karbonhidrat": 3.2, "yag": 4.8},
    {"id": 25, "kategori": "Kahvaltılıklar", "isim": "Simit (1 Adet ~100g)", "kalori": 320.0, "protein": 10.0, "karbonhidrat": 58.0, "yag": 5.5},
    {"id": 26, "kategori": "Kahvaltılıklar", "isim": "Peynirli Poğaça (1 Adet ~80g)", "kalori": 360.0, "protein": 8.0, "karbonhidrat": 40.0, "yag": 19.0},

    # --- SÜT ÜRÜNLERİ & PEYNİRLER ---
    {"id": 27, "kategori": "Süt Ürünleri", "isim": "Beyaz Peynir (Tam Yağlı)", "kalori": 260.0, "protein": 15.0, "karbonhidrat": 2.5, "yag": 21.0},
    {"id": 28, "kategori": "Süt Ürünleri", "isim": "Kaşar Peyniri", "kalori": 350.0, "protein": 25.0, "karbonhidrat": 1.5, "yag": 27.0},
    {"id": 29, "kategori": "Süt Ürünleri", "isim": "Süzme Peynir", "kalori": 190.0, "protein": 12.0, "karbonhidrat": 2.0, "yag": 15.0},
    {"id": 30, "kategori": "Süt Ürünleri", "isim": "Hellim Peyniri", "kalori": 320.0, "protein": 21.0, "karbonhidrat": 1.8, "yag": 25.0},
    {"id": 31, "kategori": "Süt Ürünleri", "isim": "Labne Peyniri", "kalori": 200.0, "protein": 6.0, "karbonhidrat": 4.0, "yag": 18.0},
    {"id": 32, "kategori": "Süt Ürünleri", "isim": "Lor Peyniri (Yağsız)", "kalori": 85.0, "protein": 11.0, "karbonhidrat": 3.0, "yag": 3.0},
    {"id": 33, "kategori": "Süt Ürünleri", "isim": "Süzme Yoğurt (%2 Yağlı)", "kalori": 60.0, "protein": 8.0, "karbonhidrat": 4.0, "yag": 1.5},
    {"id": 34, "kategori": "Süt Ürünleri", "isim": "Tam Yağlı Süt", "kalori": 61.0, "protein": 3.2, "karbonhidrat": 4.8, "yag": 3.3},

    # --- MEYVELER ---
    {"id": 35, "kategori": "Meyveler", "isim": "Karpuz", "kalori": 30.0, "protein": 0.6, "karbonhidrat": 7.5, "yag": 0.2},
    {"id": 36, "kategori": "Meyveler", "isim": "Kavun", "kalori": 34.0, "protein": 0.8, "karbonhidrat": 8.1, "yag": 0.2},
    {"id": 37, "kategori": "Meyveler", "isim": "Elma", "kalori": 52.0, "protein": 0.3, "karbonhidrat": 13.8, "yag": 0.2},
    {"id": 38, "kategori": "Meyveler", "isim": "Muz (1 Orta Boy ~110g)", "kalori": 98.0, "protein": 1.2, "karbonhidrat": 25.0, "yag": 0.3},

    # --- ET, BALIK, TAVUK & YUMURTA ---
    {"id": 39, "kategori": "Et, Balık & Yumurta", "isim": "Dana Kıyma (Az Yağlı)", "kalori": 175.0, "protein": 21.0, "karbonhidrat": 0.0, "yag": 10.0},
    {"id": 40, "kategori": "Et, Balık & Yumurta", "isim": "Tavuk Göğsü (Derisiz/Çiğ)", "kalori": 120.0, "protein": 22.5, "karbonhidrat": 0.0, "yag": 2.5},
    {"id": 41, "kategori": "Et, Balık & Yumurta", "isim": "Yumurta (Adet ~50g)", "kalori": 70.0, "protein": 6.0, "karbonhidrat": 0.5, "yag": 5.0},

    # --- TAHILLAR & BAKLİYAT ---
    {"id": 42, "kategori": "Tahıllar & Bakliyat", "isim": "Yulaf Ezmesi", "kalori": 370.0, "protein": 13.5, "karbonhidrat": 60.0, "yag": 7.0},
    {"id": 43, "kategori": "Tahıllar & Bakliyat", "isim": "Pirinç (Çiğ)", "kalori": 360.0, "protein": 7.0, "karbonhidrat": 78.0, "yag": 1.0},
    {"id": 44, "kategori": "Tahıllar & Bakliyat", "isim": "Bulgur (Çiğ)", "kalori": 342.0, "protein": 12.3, "karbonhidrat": 76.0, "yag": 1.3},

    # --- SEBZELER ---
    {"id": 45, "kategori": "Sebzeler", "isim": "Domates", "kalori": 18.0, "protein": 0.9, "karbonhidrat": 3.9, "yag": 0.2},
    {"id": 46, "kategori": "Sebzeler", "isim": "Salatalık", "kalori": 15.0, "protein": 0.7, "karbonhidrat": 3.6, "yag": 0.1},
    {"id": 47, "kategori": "Sebzeler", "isim": "Biber (Yeşil/Kapya)", "kalori": 20.0, "protein": 0.9, "karbonhidrat": 4.6, "yag": 0.2},

    # --- KURUYEMİŞLER & YAĞLAR ---
    {"id": 48, "kategori": "Kuruyemişler & Yağlar", "isim": "Çiğ Badem", "kalori": 579.0, "protein": 21.2, "karbonhidrat": 21.6, "yag": 49.9},
    {"id": 49, "kategori": "Kuruyemişler & Yağlar", "isim": "Ceviz içi", "kalori": 654.0, "protein": 15.2, "karbonhidrat": 13.7, "yag": 65.2},
    {"id": 50, "kategori": "Kuruyemişler & Yağlar", "isim": "Zeytinyağı (1 Y.Kaşığı ~10g)", "kalori": 88.0, "protein": 0.0, "karbonhidrat": 0.0, "yag": 10.0},

    # --- EV YEMEKLERİ ---
    {"id": 51, "kategori": "Ev Yemekleri", "isim": "Mercimek Çorbası (1 Kepçe ~150g)", "kalori": 120.0, "protein": 5.0, "karbonhidrat": 18.0, "yag": 3.0},
    {"id": 52, "kategori": "Ev Yemekleri", "isim": "Pirinç Pilavı", "kalori": 160.0, "protein": 2.5, "karbonhidrat": 28.0, "yag": 4.5},
    {"id": 53, "kategori": "Ev Yemekleri", "isim": "Izgara Köfte", "kalori": 200.0, "protein": 18.0, "karbonhidrat": 3.0, "yag": 12.0},
]

def parse_unit_gram(food_name):
    if not food_name:
        return 100
    match = re.search(r'~(\d+)\s*g', str(food_name))
    if match:
        val = int(match.group(1))
        return val if val > 0 else 100
    return 100

def load_data():
    db = {
        "users": {
            "admin": {
                "password": make_hashes("admin123"),
                "is_admin": True,
                "cinsiyet": "Erkek", "yas": 35, "kilo": 80.0, "boy": 175,
                "aktivite": "Orta Hareketli (Haftada 3-5 gün egzersiz)",
                "hedef": "Kilo Koruma",
                "target_kalori": 2200.0, "target_protein": 165.0,
                "target_karb": 240.0, "target_yag": 60.0,
                "target_su": 2500,
                "history_meals": {},
                "history_water": {}
            }
        },
        "food_db": DEFAULT_FOOD_DATABASE
    }

    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                saved_db = json.load(f)
                db["users"] = saved_db.get("users", db["users"])
                
                for u, u_data in db["users"].items():
                    if "history_meals" not in u_data:
                        u_data["history_meals"] = {}
                    if "history_water" not in u_data:
                        u_data["history_water"] = {}
                    if "target_su" not in u_data:
                        u_data["target_su"] = 2500
                    if "daily_meals" in u_data and u_data["daily_meals"]:
                        today_str = date.today().strftime("%Y-%m-%d")
                        if today_str not in u_data["history_meals"]:
                            u_data["history_meals"][today_str] = u_data["daily_meals"]
                        del u_data["daily_meals"]

                existing_foods = saved_db.get("food_db", [])
                existing_names = {f["isim"] for f in existing_foods}
                for default_food in DEFAULT_FOOD_DATABASE:
                    if default_food["isim"] not in existing_names:
                        existing_foods.append(default_food)
                db["food_db"] = existing_foods
        except Exception:
            pass
            
    return db

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = load_data()

db = st.session_state.db

try:
    saved_user = cookie_manager.get('logged_user')
except Exception:
    saved_user = None

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    if 'current_user' in st.session_state and st.session_state.current_user in db["users"]:
        st.session_state.logged_in = True
    elif saved_user and saved_user in db["users"]:
        st.session_state.logged_in = True
        st.session_state.current_user = saved_user
    else:
        st.session_state.logged_in = False
        st.session_state.current_user = None

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['tr', 'en'])

# --- GİRİŞ & KAYIT EKRANI ---
if not st.session_state.logged_in:
    st.title("🔐 Beslenme & Öğün Takip - Giriş Portalı")
    
    choice = st.radio(
        "Lütfen işlem seçin:", 
        ["Google ile Hızlı Giriş", "Kullanıcı Girişi", "Şifremi Unuttum", "Yeni Hesap Oluştur"], 
        index=0, 
        horizontal=True
    )
    
    if choice == "Google ile Hızlı Giriş":
        st.subheader("🌐 Google Hesabı İle Giriş Yap")
        st.info("Google hesabınız ile parola girmeden hızlıca oturum açabilirsiniz.")
        google_email = st.text_input("Google E-posta Adresiniz (Örn: adiniz@gmail.com)")
        
        if st.button("🚀 Google ile Bağlan"):
            if "@" in google_email and "." in google_email:
                g_user = google_email.split("@")[0].replace(".", "_")
                if g_user not in db["users"]:
                    db["users"][g_user] = {
                        "password": make_hashes("google_auth_dummy_pwd"),
                        "is_admin": False, "cinsiyet": "Erkek", "yas": 30, "kilo": 70.0, "boy": 170,
                        "aktivite": "Hafif Hareketli (Haftada 1-3 gün egzersiz)", "hedef": "Kilo Koruma",
                        "target_kalori": 2000.0, "target_protein": 150.0, "target_karb": 200.0, "target_yag": 50.0,
                        "target_su": 2500,
                        "history_meals": {},
                        "history_water": {}
                    }
                    save_data(db)
                st.session_state.logged_in = True
                st.session_state.current_user = g_user
                try:
                    cookie_manager.set('logged_user', g_user, key='set_user_cookie_google', expires_at=datetime(2030, 1, 1))
                except Exception:
                    pass
                st.success(f"Google ile oturum açıldı: {google_email}")
                st.rerun()
            else:
                st.error("Geçerli bir e-posta adresi giriniz.")

    elif choice == "Kullanıcı Girişi":
        st.subheader("🔑 Kullanıcı Girişi")
        username = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type='password')
        remember_me = st.checkbox("☑️ Beni Hatırla / Bu Cihazda Oturumu Açık Tut", value=True)
        
        if st.button("Giriş Yap"):
            if username in db["users"]:
                hashed_pw = db["users"][username]["password"]
                if check_hashes(password, hashed_pw):
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    
                    if remember_me:
                        try:
                            cookie_manager.set('logged_user', username, key='set_user_cookie', expires_at=datetime(2030, 1, 1))
                        except Exception:
                            pass
                    
                    st.success(f"Hoş geldiniz, {username}!")
                    st.rerun()
                else:
                    st.error("Hatalı şifre!")
            else:
                st.error("Kullanıcı bulunamadı!")

    elif choice == "Şifremi Unuttum":
        st.subheader("🔑 Şifre Sıfırlama")
        st.info("Kullanıcı adınızı ve profilinizdeki doğrulama bilgilerini girerek yeni şifre belirleyebilirsiniz.")
        
        reset_user = st.text_input("Kullanıcı Adınız")
        col_r1, col_r2 = st.columns(2)
        verify_yas = col_r1.number_input("Kayıtlı Yaşınız", min_value=15, max_value=90, value=30)
        verify_boy = col_r2.number_input("Kayıtlı Boyunuz (cm)", min_value=120, max_value=220, value=170)
        new_pass = st.text_input("Yeni Şifre Belirleyin", type='password')

        if st.button("🔄 Şifremi Güncelle"):
            if reset_user in db["users"]:
                u_data = db["users"][reset_user]
                if int(u_data.get("yas", 0)) == int(verify_yas) and int(u_data.get("boy", 0)) == int(verify_boy):
                    if new_pass.strip():
                        u_data["password"] = make_hashes(new_pass)
                        save_data(db)
                        st.success("Şifreniz başarıyla güncellendi! 'Kullanıcı Girişi' sekmesinden yeni şifrenizle giriş yapabilirsiniz.")
                    else:
                        st.error("Lütfen geçerli bir yeni şifre yazın.")
                else:
                    st.error("Girdiğiniz yaş ve boy bilgisi sistemdeki kayıtla eşleşmedi!")
            else:
                st.error("Bu kullanıcı adıyla kayıtlı hesap bulunamadı.")

    elif choice == "Yeni Hesap Oluştur":
        st.subheader("📝 Yeni Kullanıcı Kaydı")
        new_user = st.text_input("Kullanıcı Adı Belirleyin")
        new_password = st.text_input("Şifre Belirleyin", type='password')
        
        c_col1, c_col2 = st.columns(2)
        new_cinsiyet = c_col1.selectbox("Cinsiyet", ["Erkek", "Kadın"])
        new_yas = c_col2.number_input("Yaş", min_value=15, max_value=90, value=30)
        new_kilo = c_col1.number_input("Kilo (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.5)
        new_boy = c_col2.number_input("Boy (cm)", min_value=120, max_value=220, value=170)
        
        if st.button("Hesabımı Oluştur"):
            if new_user in db["users"]:
                st.warning("Bu kullanıcı adı zaten alınmış!")
            elif not new_user or not new_password:
                st.error("Lütfen kullanıcı adı ve şifre girin.")
            else:
                bmr = (10 * new_kilo) + (6.25 * new_boy) - (5 * new_yas) + (5 if new_cinsiyet == "Erkek" else -161)
                tdee = bmr * 1.375
                
                db["users"][new_user] = {
                    "password": make_hashes(new_password),
                    "is_admin": False, "cinsiyet": new_cinsiyet, "yas": new_yas, "kilo": new_kilo, "boy": new_boy,
                    "aktivite": "Hafif Hareketli (Haftada 1-3 gün egzersiz)", "hedef": "Kilo Koruma",
                    "target_kalori": tdee, "target_protein": (tdee * 0.30) / 4,
                    "target_karb": (tdee * 0.45) / 4, "target_yag": (tdee * 0.25) / 9,
                    "target_su": int(new_kilo * 35),
                    "history_meals": {},
                    "history_water": {}
                }
                save_data(db)
                st.success("Hesabınız oluşturuldu! Giriş yapabilirsiniz.")

    st.stop()

# --- UYGULAMA İÇİ ---
current_username = st.session_state.current_user
user_data = db["users"][current_username]
is_admin = user_data.get("is_admin", False)

# SIDEBAR: KULLANICI BİLGİSİ VE ÇIKIŞ
st.sidebar.markdown(f"### 👤 Kullanıcı: **{current_username}**")
if is_admin:
    st.sidebar.info("👑 YÖNETİCİ HESABI (ADMIN)")

if st.sidebar.button("🚪 Çıkış Yap"):
    st.session_state.logged_in = False
    st.session_state.current_user = None
    try:
        cookie_manager.delete('logged_user', key='delete_user_cookie')
    except Exception:
        pass
    st.rerun()

st.sidebar.markdown("---")

# 📅 TARİH SEÇİCİ
st.sidebar.subheader("📅 Takip Tarihi Seçin")
selected_date = st.sidebar.date_input("İncelenecek Gün", value=date.today())
selected_date_str = selected_date.strftime("%Y-%m-%d")

if "history_meals" not in user_data:
    user_data["history_meals"] = {}
if "history_water" not in user_data:
    user_data["history_water"] = {}

if selected_date_str not in user_data["history_meals"]:
    user_data["history_meals"][selected_date_str] = []
if selected_date_str not in user_data["history_water"]:
    user_data["history_water"][selected_date_str] = 0

current_date_meals = user_data["history_meals"][selected_date_str]
current_date_water = user_data["history_water"][selected_date_str]

# 💧 SU TAKİBİ MODÜLÜ (SIDEBAR)
st.sidebar.markdown("---")
st.sidebar.subheader("💧 Günlük Su Takibi")
target_su = user_data.get("target_su", 2500)
su_litre = current_date_water / 1000.0
target_litre = target_su / 1000.0

st.sidebar.write(f"**İçilen:** {current_date_water} ml ({su_litre:.2f} L)")
st.sidebar.write(f"**Hedef:** {target_su} ml ({target_litre:.2f} L)")
st.sidebar.progress(min(current_date_water / target_su, 1.0) if target_su > 0 else 0.0)

w_col1, w_col2, w_col3 = st.sidebar.columns(3)
if w_col1.button("🥤+250ml"):
    user_data["history_water"][selected_date_str] += 250
    save_data(db)
    st.rerun()

if w_col2.button("🥛+500ml"):
    user_data["history_water"][selected_date_str] += 500
    save_data(db)
    st.rerun()

if w_col3.button("🍼+1L"):
    user_data["history_water"][selected_date_str] += 1000
    save_data(db)
    st.rerun()

w_custom = st.sidebar.number_input("Özel Miktar Ekle/Çıkar (ml)", value=0, step=50, key="custom_water_input")
if st.sidebar.button("💧 Su Miktarını Güncelle"):
    user_data["history_water"][selected_date_str] = max(0, user_data["history_water"][selected_date_str] + w_custom)
    save_data(db)
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Profil Ayarlarınız")

cinsiyet = st.sidebar.selectbox("Cinsiyet", ["Erkek", "Kadın"], index=0 if user_data["cinsiyet"] == "Erkek" else 1)
yas = st.sidebar.number_input("Yaş", min_value=15, max_value=90, value=int(user_data["yas"]))
kilo = st.sidebar.number_input("Kilo (kg)", min_value=30.0, max_value=200.0, value=float(user_data["kilo"]), step=0.5)
boy = st.sidebar.number_input("Boy (cm)", min_value=120, max_value=220, value=int(user_data["boy"]))
new_target_su = st.sidebar.number_input("Hedef Su Miktarı (ml)", min_value=500, max_value=10000, value=int(target_su), step=250)

akt_options = ["Hareketsiz (Masa başı iş)", "Hafif Hareketli (Haftada 1-3 gün egzersiz)", "Orta Hareketli (Haftada 3-5 gün egzersiz)", "Çok Hareketli (Haftada 6-7 gün egzersiz)"]
akt_index = akt_options.index(user_data["aktivite"]) if user_data["aktivite"] in akt_options else 0
aktivite = st.sidebar.selectbox("Aktivite Seviyesi", akt_options, index=akt_index)

hedef_options = ["Kilo Verme (Yağ Yakımı)", "Kilo Koruma", "Kilo Alma / Kas Yapma"]
hedef_index = hedef_options.index(user_data["hedef"]) if user_data["hedef"] in hedef_options else 0
hedef = st.sidebar.selectbox("Hedefiniz", hedef_options, index=hedef_index)

if st.sidebar.button("💾 Profil ve Hedefleri Kaydet"):
    bmr = (10 * kilo) + (6.25 * boy) - (5 * yas) + (5 if cinsiyet == "Erkek" else -161)
    akt_carpanlar = {"Hareketsiz (Masa başı iş)": 1.2, "Hafif Hareketli (Haftada 1-3 gün egzersiz)": 1.375, "Orta Hareketli (Haftada 3-5 gün egzersiz)": 1.55, "Çok Hareketli (Haftada 6-7 gün egzersiz)": 1.725}
    tdee = bmr * akt_carpanlar[aktivite]

    if hedef == "Kilo Verme (Yağ Yakımı)":
        calc_kalori = tdee * 0.80
    elif hedef == "Kilo Alma / Kas Yapma":
        calc_kalori = tdee * 1.15
    else:
        calc_kalori = tdee

    user_data["cinsiyet"] = cinsiyet
    user_data["yas"] = yas
    user_data["kilo"] = kilo
    user_data["boy"] = boy
    user_data["aktivite"] = aktivite
    user_data["hedef"] = hedef
    user_data["target_kalori"] = calc_kalori
    user_data["target_protein"] = (calc_kalori * 0.30) / 4
    user_data["target_karb"] = (calc_kalori * 0.45) / 4
    user_data["target_yag"] = (calc_kalori * 0.25) / 9
    user_data["target_su"] = new_target_su

    save_data(db)
    st.sidebar.success("Profil Kaydedildi!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Günlük Hedefleriniz")
st.sidebar.write(f"• **Kalori:** {int(user_data['target_kalori'])} kcal")
st.sidebar.write(f"• **Protein:** {int(user_data['target_protein'])} Gram")
st.sidebar.write(f"• **Karbonhidrat:** {int(user_data['target_karb'])} Gram")
st.sidebar.write(f"• **Yağ:** {int(user_data['target_yag'])} Gram")
st.sidebar.write(f"• **Su:** {user_data.get('target_su', 2500)} ml")

# --- ANA EKRAN ---
st.title(f"🥗 {current_username} - Beslenme ve Öğün Takibi")
st.caption(f"📌 Seçili Tarih: **{selected_date_str}**")

def fetch_product_by_barcode(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                product = data.get("product", {})
                nutriments = product.get("nutriments", {})
                return {
                    "isim": product.get("product_name", "Bilinmeyen Ürün"),
                    "kalori": float(nutriments.get("energy-kcal_100g", 0)),
                    "protein": float(nutriments.get("proteins_100g", 0)),
                    "karbonhidrat": float(nutriments.get("carbohydrates_100g", 0)),
                    "yag": float(nutriments.get("fat_100g", 0))
                }
    except Exception:
        pass
    return None

def parse_nutrition_text(text_list):
    full_text = " ".join(text_list).lower().replace(',', '.')
    extracted = {"kalori": 0.0, "protein": 0.0, "karbonhidrat": 0.0, "yag": 0.0}
    
    slash_match = re.search(r'(\d{3,4})\s*[\/\s|]+\s*\d{3,4}', full_text)
    if slash_match:
        extracted["kalori"] = float(slash_match.group(1))
    else:
        kalori_match = re.search(r'(?:kcal|enerji|kalori)[^\d]*?(?:100g?|100)?[^\d]*?(\d{2,4})', full_text)
        if kalori_match:
            extracted["kalori"] = float(kalori_match.group(1))

    yag_match = re.search(r'(?:yağ|yag|fat)[^\d]*?(\d+(?:\.\d+)?)', full_text)
    if yag_match:
        extracted["yag"] = float(yag_match.group(1))

    karb_match = re.search(r'(?:karbonhidrat|carbs)[^\d]*?(\d+(?:\.\d+)?)', full_text)
    if karb_match:
        extracted["karbonhidrat"] = float(karb_match.group(1))

    protein_match = re.search(r'protein[^\d]*?(\d+(?:\.\d+)?)', full_text)
    if protein_match:
        extracted["protein"] = float(protein_match.group(1))

    return extracted

# AI PORSIYON ANALIZI
def analyze_plate_image(image, api_key):
    import io
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    prompt = (
        "Bu porsiyon/tabak fotoğrafındaki yiyecekleri analiz et. "
        "Her yiyecek için tahmini gramajını, kalorisini, proteinini, karbonhidratını ve yağını tespit et. "
        "Yanıtı SADECE geçerli bir JSON listesi formatında ver. Başka hiçbir metin veya markdown formatı yazma. "
        "Örnek Format: "
        '[{"isim": "Pirinç Pilavı", "gramaj": 150, "kalori": 240.0, "protein": 4.0, "karbonhidrat": 42.0, "yag": 6.0}]'
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": img_str}}
            ]
        }]
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, json=payload, timeout=20)
    
    if response.status_code == 200:
        res_json = response.json()
        try:
            raw_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            clean_json = raw_text.replace("```json", "").replace("
