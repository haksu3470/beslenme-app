import streamlit as st
import pandas as pd
import requests
import re
import json
import os
import hashlib
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
    # --- EKMEK & UNLU MAMULLER (YENİ VE ZENGİN KATEGORİ) ---
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

# --- VERİTABANI İŞLEMLERİ ---
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
                "history_meals": {}
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

# --- OTURUM & ÇEREZ KONTROLÜ ---
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

# --- OCR MODELİ ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['tr', 'en'])

# --- GİRİŞ & KAYIT EKRANI ---
if not st.session_state.logged_in:
    st.title("🔐 Beslenme & Öğün Takip - Giriş Portalı")
    
    choice = st.radio("Lütfen işlem seçin:", ["Giriş Yap", "Şifremi Unuttum", "Google ile Hızlı Giriş", "Yeni Hesap Oluştur"], horizontal=True)
    
    if choice == "Giriş Yap":
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
                        st.success("Şifreniz başarıyla güncellendi! 'Giriş Yap' sekmesinden yeni şifrenizle giriş yapabilirsiniz.")
                    else:
                        st.error("Lütfen geçerli bir yeni şifre yazın.")
                else:
                    st.error("Girdiğiniz yaş ve boy bilgisi sistemdeki kayıtla eşleşmedi!")
            else:
                st.error("Bu kullanıcı adıyla kayıtlı hesap bulunamadı.")

    elif choice == "Google ile Hızlı Giriş":
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
                        "history_meals": {}
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
                    "history_meals": {}
                }
                save_data(db)
                st.success("Hesabınız oluşturuldu! 'Giriş Yap' sekmesinden giriş yapabilirsiniz.")

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
if selected_date_str not in user_data["history_meals"]:
    user_data["history_meals"][selected_date_str] = []

current_date_meals = user_data["history_meals"][selected_date_str]

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Profil Ayarlarınız")

cinsiyet = st.sidebar.selectbox("Cinsiyet", ["Erkek", "Kadın"], index=0 if user_data["cinsiyet"] == "Erkek" else 1)
yas = st.sidebar.number_input("Yaş", min_value=15, max_value=90, value=int(user_data["yas"]))
kilo = st.sidebar.number_input("Kilo (kg)", min_value=30.0, max_value=200.0, value=float(user_data["kilo"]), step=0.5)
boy = st.sidebar.number_input("Boy (cm)", min_value=120, max_value=220, value=int(user_data["boy"]))

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

    save_data(db)
    st.sidebar.success("Profil Kaydedildi!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Günlük Hedefleriniz")
st.sidebar.write(f"• **Kalori:** {int(user_data['target_kalori'])} kcal")
st.sidebar.write(f"• **Protein:** {int(user_data['target_protein'])} Gram")
st.sidebar.write(f"• **Karbonhidrat:** {int(user_data['target_karb'])} Gram")
st.sidebar.write(f"• **Yağ:** {int(user_data['target_yag'])} Gram")

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

# MADDELERDEN 3: MENÜ ŞERİDİ ERGONOMİSİ VE SEKMELERİN KOLAY ULAŞILABİLİRLİĞİ
tabs_list = [
    "📝 Öğün Oluştur", 
    "🔍 Barkod Arama", 
    "📷 Etiket Okuma", 
    "📊 Günlük Özet", 
    "➕ Ürün Yönetimi"
]
if is_admin:
    tabs_list.append("👑 Admin Paneli")

tabs = st.tabs(tabs_list)
tab1, tab2, tab3, tab4, tab5 = tabs[0], tabs[1], tabs[2], tabs[3], tabs[4]

food_df = pd.DataFrame(db["food_db"])
if "kategori" not in food_df.columns:
    food_df["kategori"] = "Diğer / Eklenenler"

# TAB 1: ÖĞÜN OLUŞTUR & CANLI ARAMA (MADDELERDEN 1: EKLEMEDEN SONRA OTOMATİK TEMİZLEME)
with tab1:
    st.subheader(f"Öğüne Besin Ekle ({selected_date_str})")
    
    col_cat, col_search = st.columns([1, 2])
    categories = ["Tüm Kategoriler"] + sorted(list(food_df["kategori"].dropna().unique()))
    selected_cat = col_cat.selectbox("Kategori Filtresi", categories, key="cat_filter_select")
    
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""

    search_term = col_search.text_input(
        "🔍 Hızlı Besin Ara (Aramak istediğiniz ürünü yazın)", 
        value=st.session_state.search_query, 
        key="search_term_input",
        placeholder="Örn: Ekmek, Bal, Zeytin, Lavaş, Menemen..."
    )

    filtered_df = food_df.copy()
    if selected_cat != "Tüm Kategoriler":
        filtered_df = filtered_df[filtered_df["kategori"] == selected_cat]
        
    if search_term.strip():
        filtered_df = filtered_df[filtered_df["isim"].str.contains(search_term.strip(), case=False, na=False, regex=False)]

    food_list_sorted = filtered_df["isim"].tolist()

    if not food_list_sorted:
        st.warning(f"'{search_term}' aramasına uygun besin bulunamadı. Lütfen kelimeyi kontrol edin veya 'Ürün Yönetimi' sekmesinden ekleyin.")
    else:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            selected_food_name = st.selectbox(f"Besin Seçin ({len(food_list_sorted)} Sonuç)", food_list_sorted, key="selected_food_select")
        with col2:
            gramaj = st.number_input("Gramaj (g)", min_value=1, value=100, step=10, key="gramaj_input")
        with col3:
            meal_type = st.selectbox("Öğün Seçin", ["Kahvaltı", "Öğle Yemeği", "Akşam Yemeği", "Aperatif"], key="meal_type_select")

        if st.button("➕ Öğüne Ekle", key="add_to_meal_btn"):
            food_row = food_df[food_df["isim"] == selected_food_name].iloc[0]
            ratio = gramaj / 100.0
            meal_item = {
                "Öğün": meal_type,
                "Besin": selected_food_name,
                "Gramaj (g)": gramaj,
                "Kalori (kcal)": round(food_row["kalori"] * ratio, 1),
                "Protein (g)": round(food_row["protein"] * ratio, 1),
                "Karbonhidrat (g)": round(food_row["karbonhidrat"] * ratio, 1),
                "Yağ (g)": round(food_row["yag"] * ratio, 1)
            }
            current_date_meals.append(meal_item)
            save_data(db)
            
            # Arama çubuğunu temizle
            st.session_state.search_query = ""
            st.success(f"{gramaj}g {selected_food_name} ({selected_date_str} - {meal_type}) eklendi ve arama kutusu temizlendi!")
            st.rerun()

    st.markdown("---")
    st.subheader(f"📋 Eklenen Öğünler Ve Hızlı Düzenleme ({len(current_date_meals)} Adet)")

    if current_date_meals:
        for idx, item in enumerate(current_date_meals):
            with st.expander(f"📌 {item['Öğün']} - {item['Besin']} ({item['Gramaj (g)']}g) | {item['Kalori (kcal)']} kcal"):
                e_col1, e_col2, e_col3 = st.columns([2, 2, 1])
                new_gramaj = e_col1.number_input("Gramaj Düzelt (g)", min_value=1, value=int(item['Gramaj (g)']), key=f"edit_g_{idx}")
                new_meal_type = e_col2.selectbox("Öğün Türü Değiştir", ["Kahvaltı", "Öğle Yemeği", "Akşam Yemeği", "Aperatif"], index=["Kahvaltı", "Öğle Yemeği", "Akşam Yemeği", "Aperatif"].index(item['Öğün']), key=f"edit_m_{idx}")
                
                if e_col3.button("💾 Güncelle", key=f"btn_update_{idx}"):
                    orig_food = food_df[food_df["isim"] == item["Besin"]]
                    if not orig_food.empty:
                        f_row = orig_food.iloc[0]
                        r = new_gramaj / 100.0
                        item["Gramaj (g)"] = new_gramaj
                        item["Öğün"] = new_meal_type
                        item["Kalori (kcal)"] = round(f_row["kalori"] * r, 1)
                        item["Protein (g)"] = round(f_row["protein"] * r, 1)
                        item["Karbonhidrat (g)"] = round(f_row["karbonhidrat"] * r, 1)
                        item["Yağ (g)"] = round(f_row["yag"] * r, 1)
                        save_data(db)
                        st.success("Öğün güncellendi!")
                        st.rerun()

                if st.button("🗑️ Bu Öğünü Sil", key=f"btn_del_{idx}"):
                    current_date_meals.pop(idx)
                    save_data(db)
                    st.rerun()
    else:
        st.info("Bu tarih için henüz yiyecek eklenmedi.")

# TAB 2: Barkod
with tab2:
    st.subheader("Barkod Numarası İle Ürün Bul")
    barcode_input = st.text_input("Barkod Numarası")
    if st.button("Sorgula"):
        p_info = fetch_product_by_barcode(barcode_input)
        if p_info:
            st.success(f"Bulunan Ürün: {p_info['isim']}")
            st.json(p_info)
            if st.button("Veritabanına Ekle"):
                new_id = len(db["food_db"]) + 1
                new_row = {"id": new_id, "kategori": "Barkodla Eklenenler", **p_info}
                db["food_db"].append(new_row)
                save_data(db)
                st.success("Ürün veritabanına eklendi!")
                st.rerun()
        else:
            st.error("Ürün bulunamadı.")

# TAB 3: OCR
with tab3:
    st.subheader("Besin Etiketi Fotoğrafı Yükle")
    uploaded_file = st.file_uploader("Görsel Seçin (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Görsel", width=300)
        
        if st.button("Görseli Tara ve Ayrıştır"):
            with st.spinner("Yapay zeka görseli okuyor..."):
                reader = load_ocr()
                image_np = np.array(image)
                results = reader.readtext(image_np, detail=0)
                parsed_data = parse_nutrition_text(results)
                st.session_state['parsed_ocr'] = parsed_data

        if 'parsed_ocr' in st.session_state:
            p_data = st.session_state['parsed_ocr']
            st.subheader("Okunan Değerler (100g İçin)")
            c_kal = st.number_input("Kalori (kcal)", value=p_data['kalori'])
            c_pro = st.number_input("Protein (g)", value=p_data['protein'])
            c_karb = st.number_input("Karbonhidrat (g)", value=p_data['karbonhidrat'])
            c_yag = st.number_input("Yağ (g)", value=p_data['yag'])
            
            new_food_name = st.text_input("Ürün Adı Girin", value="Taranan Ürün")
            c_kat = st.selectbox("Kategori Seçin", ["Ekmek & Unlu Mamuller", "Kahvaltılıklar", "Meyveler", "Sebzeler", "Tahıllar & Bakliyat", "Kuruyemişler & Yağlar", "Et, Balık & Yumurta", "Süt Ürünleri", "Ev Yemekleri", "Diğer / Eklenenler"], index=0)
            
            if st.button("Veritabanına Kaydet"):
                new_id = len(db["food_db"]) + 1
                new_entry = {"id": new_id, "kategori": c_kat, "isim": new_food_name, "kalori": float(c_kal), "protein": float(c_pro), "karbonhidrat": float(c_karb), "yag": float(c_yag)}
                db["food_db"].append(new_entry)
                save_data(db)
                del st.session_state['parsed_ocr']
                st.success(f"'{new_food_name}' veritabanına eklendi!")
                st.rerun()

# TAB 4: Günlük Özet & Hedefler
with tab4:
    st.subheader(f"📊 Özet - {selected_date_str} ({current_username})")
    t_kal, t_pro, t_karb, t_yag = user_data["target_kalori"], user_data["target_protein"], user_data["target_karb"], user_data["target_yag"]

    if current_date_meals:
        df_meals = pd.DataFrame(current_date_meals)
        tot_kalori, tot_protein, tot_karb, tot_yag = df_meals['Kalori (kcal)'].sum(), df_meals['Protein (g)'].sum(), df_meals['Karbonhidrat (g)'].sum(), df_meals['Yağ (g)'].sum()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Alınan Kalori", f"{tot_kalori:.1f} kcal", f"Kalan: {int(t_kal - tot_kalori)} kcal")
        m2.metric("Alınan Protein", f"{tot_protein:.1f} g", f"Hedef: {int(t_pro)} g")
        m3.metric("Alınan Karbonhidrat", f"{tot_karb:.1f} g", f"Hedef: {int(t_karb)} g")
        m4.metric("Alınan Yağ", f"{tot_yag:.1f} g", f"Hedef: {int(t_yag)} g")

        st.markdown("---")
        st.write("### 🎯 Hedef İlerleme Barları")
        st.progress(min(tot_kalori / t_kal, 1.0) if t_kal > 0 else 0.0)

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.write("**Protein**"); col_m1.progress(min(tot_protein / t_pro, 1.0) if t_pro > 0 else 0.0)
        col_m2.write("**Karbonhidrat**"); col_m2.progress(min(tot_karb / t_karb, 1.0) if t_karb > 0 else 0.0)
        col_m3.write("**Yağ**"); col_m3.progress(min(tot_yag / t_yag, 1.0) if t_yag > 0 else 0.0)

        st.markdown("---")
        col_t1, col_t2 = st.columns([4, 1])
        col_t1.subheader(f"📋 {selected_date_str} Yenen Yemekler")
        if col_t2.button("🗑️ Seçili Günü Sıfırla"):
            user_data["history_meals"][selected_date_str] = []
            save_data(db)
            st.rerun()

        st.dataframe(df_meals, use_container_width=True)
    else:
        st.info(f"{selected_date_str} tarihi için henüz bir öğün eklenmedi.")

# TAB 5: DİNAMİK ÜRÜN YÖNETİMİ
with tab5:
    st.subheader("➕ Veritabanına Yeni Besin Ekle / Mevcut Ürünleri Düzenle")
    
    sub_action = st.radio("İşlem Seçin:", ["Yeni Ürün Ekle", "Mevcut Kayıtlı Ürünü Düzenle"], horizontal=True)

    if sub_action == "Yeni Ürün Ekle":
        with st.form(key="add_new_product_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            custom_name = col_a.text_input("Yiyecek / Ürün Adı")
            custom_cat = col_a.selectbox("Kategorisi", ["Ekmek & Unlu Mamuller", "Kahvaltılıklar", "Meyveler", "Sebzeler", "Tahıllar & Bakliyat", "Kuruyemişler & Yağlar", "Et, Balık & Yumurta", "Süt Ürünleri", "Ev Yemekleri", "Diğer / Eklenenler"])
            custom_kal = col_b.number_input("100g Kalori (kcal)", min_value=0.0, value=50.0)
            custom_pro = col_b.number_input("100g Protein (g)", min_value=0.0, value=1.0)
            custom_karb = col_b.number_input("100g Karbonhidrat (g)", min_value=0.0, value=10.0)
            custom_yag = col_b.number_input("100g Yağ (g)", min_value=0.0, value=0.0)

            submit_btn = st.form_submit_button("✨ Veritabanına Kalıcı Olarak Ekle")
            if submit_btn:
                if custom_name:
                    new_id = len(db["food_db"]) + 1
                    new_entry = {"id": new_id, "kategori": custom_cat, "isim": custom_name, "kalori": float(custom_kal), "protein": float(custom_pro), "karbonhidrat": float(custom_karb), "yag": float(custom_yag)}
                    db["food_db"].append(new_entry)
                    save_data(db)
                    st.success(f"'{custom_name}' eklendi ve form temizlendi!")
                    st.rerun()

    elif sub_action == "Mevcut Kayıtlı Ürünü Düzenle":
        st.write("Veritabanındaki bir ürünün besin değerlerini güncelleyebilirsiniz:")
        all_food_names = [f["isim"] for f in db["food_db"]]
        selected_edit_food = st.selectbox("Düzenlenecek Ürünü Seçin", sorted(all_food_names))
        
        food_obj = next((item for item in db["food_db"] if item["isim"] == selected_edit_food), None)
        if food_obj:
            ed_col1, ed_col2 = st.columns(2)
            u_name = ed_col1.text_input("Ürün İsmi", value=food_obj["isim"])
            u_cat = ed_col1.selectbox("Kategori", ["Ekmek & Unlu Mamuller", "Kahvaltılıklar", "Meyveler", "Sebzeler", "Tahıllar & Bakliyat", "Kuruyemişler & Yağlar", "Et, Balık & Yumurta", "Süt Ürünleri", "Ev Yemekleri", "Diğer / Eklenenler"], index=0)
            u_kal = ed_col2.number_input("Kalori (100g)", value=float(food_obj["kalori"]))
            u_pro = ed_col2.number_input("Protein (100g)", value=float(food_obj["protein"]))
            u_karb = ed_col2.number_input("Karbonhidrat (100g)", value=float(food_obj["karbonhidrat"]))
            u_yag = ed_col2.number_input("Yağ (100g)", value=float(food_obj["yag"]))

            if st.button("💾 Ürün Değerlerini Güncelle"):
                food_obj["isim"] = u_name
                food_obj["kategori"] = u_cat
                food_obj["kalori"] = u_kal
                food_obj["protein"] = u_pro
                food_obj["karbonhidrat"] = u_karb
                food_obj["yag"] = u_yag
                save_data(db)
                st.success(f"'{u_name}' başarıyla güncellendi!")
                st.rerun()

# TAB 6: ADMIN PANENİ
if is_admin:
    with tabs[5]:
        st.subheader("👑 Admin Paneli - Tüm Kullanıcıların Takip Özeti")
        
        all_users = list(db["users"].keys())
        selected_view_user = st.selectbox("İncelemek İstediğiniz Kullanıcıyı Seçin", all_users)
        
        u_info = db["users"][selected_view_user]
        st.markdown(f"### 👤 Kullanıcı: **{selected_view_user}**")
        st.write(f"• **Hedef Kalori:** {int(u_info['target_kalori'])} kcal | **Hedef Protein:** {int(u_info['target_protein'])}g")
        
        st.markdown("#### 🔑 Kullanıcı Şifresi Sıfırla (Admin)")
        admin_new_pass = st.text_input(f"'{selected_view_user}' İçin Yeni Şifre Belirle", type="password")
        if st.button(f"'{selected_view_user}' Şifresini Değiştir"):
            if admin_new_pass.strip():
                u_info["password"] = make_hashes(admin_new_pass)
                save_data(db)
                st.success(f"'{selected_view_user}' kullanıcısının şifresi başarıyla değiştirildi!")
            else:
                st.error("Lütfen bir şifre girin.")

        st.markdown("---")
        u_hist = u_info.get("history_meals", {})
        if u_hist:
            v_date = st.selectbox("İncelenecek Tarih", sorted(list(u_hist.keys()), reverse=True))
            u_meals = u_hist.get(v_date, [])
            if u_meals:
                u_df = pd.DataFrame(u_meals)
                tot_kal = u_df['Kalori (kcal)'].sum()
                st.metric(f"{v_date} Tükettiği Kalori", f"{tot_kal:.1f} kcal", f"Kalan: {int(u_info['target_kalori'] - tot_kal)} kcal")
                st.dataframe(u_df, use_container_width=True)
            else:
                st.info(f"{selected_view_user} kullanıcısının {v_date} tarihinde kayıtlı öğünü yok.")
        else:
            st.info(f"{selected_view_user} henüz hiçbir tarih için öğün eklememiş.")
