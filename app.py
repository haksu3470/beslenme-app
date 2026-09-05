import streamlit as st
import pandas as pd
import requests
import re
import json
import hashlib
import base64
from datetime import datetime, date
from PIL import Image
import numpy as np
import easyocr
import extra_streamlit_components as stx
from supabase import create_client, Client

st.set_page_config(page_title="Beslenme & Öğün Takibi", layout="wide")

# --- SUPABASE BAĞLANTISI ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("Supabase bağlantısı kurulamadı. Lütfen Streamlit Secrets ayarlarınızı kontrol edin.")

# --- ÇEREZ YÖNETİCİSİ ---
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# --- VERİTABANI İŞLEMLERİ (SUPABASE) ---
def load_data_from_supabase():
    try:
        res = supabase.table("app_state").select("data").eq("id", 1).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]["data"]
    except Exception:
        pass
    
    # Varsayılan Yapı
    return {
        "users": {
            "admin": {
                "password": make_hashes("admin123"),
                "is_admin": True, "cinsiyet": "Erkek", "yas": 35, "kilo": 80.0, "boy": 175,
                "aktivite": "Orta Hareketli (Haftada 3-5 gün egzersiz)", "hedef": "Kilo Koruma",
                "target_kalori": 2200.0, "target_protein": 165.0, "target_karb": 240.0, "target_yag": 60.0,
                "target_su": 2500, "history_meals": {}, "history_water": {}
            }
        },
        "food_db": []
    }

def save_data_to_supabase(data):
    try:
        supabase.table("app_state").upsert({"id": 1, "data": data}).execute()
    except Exception as e:
        st.error(f"Veri kaydedilemedi: {e}")

if 'db' not in st.session_state:
    st.session_state.db = load_data_from_supabase()

db = st.session_state.db

# Oturum Kontrolü
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

# --- GİRİŞ & UYGULAMA MANTIĞI ---
if not st.session_state.logged_in:
    st.title("🔐 Beslenme & Öğün Takip - Giriş Portalı")
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type='password')
    
    if st.button("Giriş Yap"):
        if username in db["users"] and check_hashes(password, db["users"][username]["password"]):
            st.session_state.logged_in = True
            st.session_state.current_user = username
            st.success("Giriş başarılı!")
            st.rerun()
        else:
            st.error("Hatalı kullanıcı adı veya şifre!")
    st.stop()

# Uygulama İçeriği
current_username = st.session_state.current_user
user_data = db["users"][current_username]

st.title(f"🥗 {current_username} - Beslenme ve Öğün Takibi")
st.success("☁️ Verileriniz Supabase bulut veritabanında kalıcı olarak saklanmaktadır.")

# Veri kaydetme çağrılarında save_data_to_supabase(db) kullanabilirsiniz.
