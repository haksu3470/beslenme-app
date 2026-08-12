import streamlit as st
import pandas as pd
import requests
import re
import json
import os
from PIL import Image
import numpy as np
import easyocr

st.set_page_config(page_title="Beslenme & Öğün Takibi", layout="wide")

DB_FILE = "database.json"

# --- ZENGİNLEŞTİRİLMİŞ VARSAYILAN BESİN LİSTESİ ---
DEFAULT_FOOD_DATABASE = [
    # --- MEYVELER ---
    {"id": 1, "kategori": "Meyveler", "isim": "Karpuz", "kalori": 30.0, "protein": 0.6, "karbonhidrat": 7.5, "yag": 0.2},
    {"id": 2, "kategori": "Meyveler", "isim": "Kavun", "kalori": 34.0, "protein": 0.8, "karbonhidrat": 8.1, "yag": 0.2},
    {"id": 3, "kategori": "Meyveler", "isim": "Şeftali / Nektarin", "kalori": 39.0, "protein": 0.9, "karbonhidrat": 9.5, "yag": 0.3},
    {"id": 4, "kategori": "Meyveler", "isim": "Üzüm (Yeşil/Siyah)", "kalori": 69.0, "protein": 0.7, "karbonhidrat": 18.1, "yag": 0.2},
    {"id": 5, "kategori": "Meyveler", "isim": "Kiraz / Vişne", "kalori": 50.0, "protein": 1.0, "karbonhidrat": 12.0, "yag": 0.3},
    {"id": 6, "kategori": "Meyveler", "isim": "Erik (Yeşil/Mürdüm)", "kalori": 46.0, "protein": 0.7, "karbonhidrat": 11.4, "yag": 0.3},
    {"id": 7, "kategori": "Meyveler", "isim": "Taze İncir", "kalori": 74.0, "protein": 0.8, "karbonhidrat": 19.0, "yag": 0.3},
    {"id": 8, "kategori": "Meyveler", "isim": "Kayısı", "kalori": 48.0, "protein": 1.4, "karbonhidrat": 11.0, "yag": 0.4},
    {"id": 9, "kategori": "Meyveler", "isim": "Elma", "kalori": 52.0, "protein": 0.3, "karbonhidrat": 13.8, "yag": 0.2},
    {"id": 10, "kategori": "Meyveler", "isim": "Muz (1 Orta Boy ~110g)", "kalori": 98.0, "protein": 1.2, "karbonhidrat": 25.0, "yag": 0.3},
    {"id": 11, "kategori": "Meyveler", "isim": "Portakal / Mandalina", "kalori": 47.0, "protein": 0.9, "karbonhidrat": 11.8, "yag": 0.1},
    {"id": 12, "kategori": "Meyveler", "isim": "Çilek", "kalori": 32.0, "protein": 0.7, "karbonhidrat": 7.7, "yag": 0.3},
    {"id": 13, "kategori": "Meyveler", "isim": "Avokado", "kalori": 160.0, "protein": 2.0, "karbonhidrat": 8.5, "yag": 14.7},
    
    # --- ET, BALIK, TAVUK & YUMURTA ---
    {"id": 14, "kategori": "Et, Balık & Yumurta", "isim": "Dana Kıyma (Az Yağlı)", "kalori": 175.0, "protein": 21.0, "karbonhidrat": 0.0, "yag": 10.0},
    {"id": 15, "kategori": "Et, Balık & Yumurta", "isim": "Dana Bonfile / Kontrfile", "kalori": 150.0, "protein": 23.0, "karbonhidrat": 0.0, "yag": 6.0},
    {"id": 16, "kategori": "Et, Balık & Yumurta", "isim": "Kuzu Pirzola / Külbastı", "kalori": 230.0, "protein": 19.0, "karbonhidrat": 0.0, "yag": 17.0},
    {"id": 17, "kategori": "Et, Balık & Yumurta", "isim": "Tavuk Göğsü (Derisiz/Çiğ)", "kalori": 120.0, "protein": 22.5, "karbonhidrat": 0.0, "yag": 2.5},
    {"id": 18, "kategori": "Et, Balık & Yumurta", "isim": "Tavuk Pirzola / Sarma", "kalori": 170.0, "protein": 18.0, "karbonhidrat": 0.0, "yag": 11.0},
    {"id": 19, "kategori": "Et, Balık & Yumurta", "isim": "Somon Balığı", "kalori": 206.0, "protein": 20.0, "karbonhidrat": 0.0, "yag": 13.0},
    {"id": 20, "kategori": "Et, Balık & Yumurta", "isim": "Ton Balığı (Konserve)", "kalori": 116.0, "protein": 26.0, "karbonhidrat": 0.0, "yag": 1.0},
    {"id": 21, "kategori": "Et, Balık & Yumurta", "isim": "Yumurta (Adet ~50g)", "kalori": 70.0, "protein": 6.0, "karbonhidrat": 0.5, "yag": 5.0},

    # --- TAHILLAR & BAKLİYAT ---
    {"id": 22, "kategori": "Tahıllar & Bakliyat", "isim": "Kinoa (Çiğ)", "kalori": 368.0, "protein": 14.1, "karbonhidrat": 64.0, "yag": 6.0},
    {"id": 23, "kategori": "Tahıllar & Bakliyat", "isim": "Karabuğday / Greçka (Çiğ)", "kalori": 343.0, "protein": 13.2, "karbonhidrat": 71.5, "yag": 3.4},
    {"id": 24, "kategori": "Tahıllar & Bakliyat", "isim": "Pirinç (Çiğ)", "kalori": 360.0, "protein": 7.0, "karbonhidrat": 78.0, "yag": 1.0},
    {"id": 25, "kategori": "Tahıllar & Bakliyat", "isim": "Bulgur (Çiğ)", "kalori": 342.0, "protein": 12.3, "karbonhidrat": 76.0, "yag": 1.3},
    {"id": 26, "kategori": "Tahıllar & Bakliyat", "isim": "Yulaf Ezmesi", "kalori": 370.0, "protein": 13.5, "karbonhidrat": 60.0, "yag": 7.0},
    {"id": 27, "kategori": "Tahıllar & Bakliyat", "isim": "Kırmızı / Yeşil Mercimek (Çiğ)", "kalori": 330.0, "protein": 24.0, "karbonhidrat": 48.0, "yag": 1.5},
    {"id": 28, "kategori": "Tahıllar & Bakliyat", "isim": "Nohut (Çiğ)", "kalori": 364.0, "protein": 19.0, "karbonhidrat": 61.0, "yag": 6.0},
    {"id": 29, "kategori": "Tahıllar & Bakliyat", "isim": "Kuru Fasulye (Çiğ)", "kalori": 337.0, "protein": 21.5, "karbonhidrat": 61.0, "yag": 1.2},
    {"id": 30, "kategori": "Tahıllar & Bakliyat", "isim": "Tam Buğday Ekmeği (1 Dilim ~30g)", "kalori": 72.0, "protein": 2.7, "karbonhidrat": 12.6, "yag": 0.9},

    # --- SEBZELER ---
    {"id": 31, "kategori": "Sebzeler", "isim": "Domates", "kalori": 18.0, "protein": 0.9, "karbonhidrat": 3.9, "yag": 0.2},
    {"id": 32, "kategori": "Sebzeler", "isim": "Salatalık", "kalori": 15.0, "protein": 0.7, "karbonhidrat": 3.6, "yag": 0.1},
    {"id": 33, "kategori": "Sebzeler", "isim": "Biber (Yeşil/Kapya)", "kalori": 20.0, "protein": 0.9, "karbonhidrat": 4.6, "yag": 0.2},
    {"id": 34, "kategori": "Sebzeler", "isim": "Ispanak", "kalori": 23.0, "protein": 2.9, "karbonhidrat": 3.6, "yag": 0.4},
    {"id": 35, "kategori": "Sebzeler", "isim": "Brokoli", "kalori": 34.0, "protein": 2.8, "karbonhidrat": 6.6, "yag": 0.4},
    {"id": 36, "kategori": "Sebzeler", "isim": "Patates (Haşlanmış)", "kalori": 87.0, "protein": 1.9, "karbonhidrat": 20.1, "yag": 0.1},
    {"id": 37, "kategori": "Sebzeler", "isim": "Mantar", "kalori": 22.0, "protein": 3.1, "karbonhidrat": 3.3, "yag": 0.3},

    # --- KURUYEMİŞLER & YAĞLAR ---
    {"id": 38, "kategori": "Kuruyemişler & Yağlar", "isim": "Çiğ Badem", "kalori": 579.0, "protein": 21.2, "karbonhidrat": 21.6, "yag": 49.9},
    {"id": 39, "kategori": "Kuruyemişler & Yağlar", "isim": "Ceviz içi", "kalori": 654.0, "protein": 15.2, "karbonhidrat": 13.7, "yag": 65.2},
    {"id": 40, "kategori": "Kuruyemişler & Yağlar", "isim": "Çiğ Fındık", "kalori": 628.0, "protein": 15.0, "karbonhidrat": 16.7, "yag": 60.8},
    {"id": 41, "kategori": "Kuruyemişler & Yağlar", "isim": "Zeytinyağı (1 Y.Kaşığı ~10g)", "kalori": 88.0, "protein": 0.0, "karbonhidrat": 0.0, "yag": 10.0},

    # --- SÜT ÜRÜNLERİ ---
    {"id": 42, "kategori": "Süt Ürünleri", "isim": "Süzme Yoğurt (%2 Yağlı)", "kalori": 60.0, "protein": 8.0, "karbonhidrat": 4.0, "yag": 1.5},
    {"id": 43, "kategori": "Süt Ürünleri", "isim": "Lor Peyniri (Yağsız)", "kalori": 85.0, "protein": 11.0, "karbonhidrat": 3.0, "yag": 3.0},
    {"id": 44, "kategori": "Süt Ürünleri", "isim": "Beyaz Peynir (Tam Yağlı)", "kalori": 260.0, "protein": 15.0, "karbonhidrat": 2.5, "yag": 21.0},
    {"id": 45, "kategori": "Süt Ürünleri", "isim": "Tam Yağlı Süt", "kalori": 61.0, "protein": 3.2, "karbonhidrat": 4.8, "yag": 3.3},

    # --- EV YEMEKLERİ ---
    {"id": 46, "kategori": "Ev Yemekleri", "isim": "Mercimek Çorbası (1 Kepçe ~150g)", "kalori": 120.0, "protein": 5.0, "karbonhidrat": 18.0, "yag": 3.0},
    {"id": 47, "kategori": "Ev Yemekleri", "isim": "Pirinç Pilavı", "kalori": 160.0, "protein": 2.5, "karbonhidrat": 28.0, "yag": 4.5},
    {"id": 48, "kategori": "Ev Yemekleri", "isim": "Izgara Köfte", "kalori": 200.0, "protein": 18.0, "karbonhidrat": 3.0, "yag": 12.0},
]

# --- VERİTABANI YÜKLEME VE BİRLEŞTİRME ---
def load_data():
    db = {
        "users": {
            "Hüseyin": {
                "cinsiyet": "Erkek", "yas": 30, "kilo": 75.0, "boy": 175,
                "aktivite": "Orta Hareketli (Haftada 3-5 gün egzersiz)",
                "hedef": "Kilo Verme (Yağ Yakımı)",
                "target_kalori": 2000.0, "target_protein": 150.0,
                "target_karb": 225.0, "target_yag": 55.0,
                "daily_meals": []
            }
        },
        "food_db": DEFAULT_FOOD_DATABASE,
        "active_user": "Hüseyin"
    }

    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                saved_db = json.load(f)
                db["users"] = saved_db.get("users", db["users"])
                db["active_user"] = saved_db.get("active_user", "Hüseyin")
                
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

# --- OCR MODELİ ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['tr', 'en'])

# --- SIDEBAR: KULLANICI SEÇİMİ VE PROFiL ---
st.sidebar.header("👥 Kullanıcı Yönetimi")

user_list = list(db["users"].keys())
selected_user_option = st.sidebar.selectbox(
    "Aktif Kişi Seçin", 
    user_list + ["+ Yeni Kişi Ekle"]
)

if selected_user_option == "+ Yeni Kişi Ekle":
    new_name = st.sidebar.text_input("Yeni Kişi Adı")
    if st.sidebar.button("Kişiyi Oluştur"):
        if new_name and new_name not in db["users"]:
            db["users"][new_name] = {
                "cinsiyet": "Erkek", "yas": 30, "kilo": 70.0, "boy": 170,
                "aktivite": "Hareketsiz (Masa başı iş)",
                "hedef": "Kilo Koruma",
                "target_kalori": 2000.0, "target_protein": 150.0,
                "target_karb": 225.0, "target_yag": 55.0,
                "daily_meals": []
            }
            db["active_user"] = new_name
            save_data(db)
            st.rerun()
    active_user = db.get("active_user", user_list[0])
else:
    active_user = selected_user_option
    db["active_user"] = active_user

user_data = db["users"][active_user]

st.sidebar.markdown("---")
st.sidebar.subheader(f"⚙️ {active_user} - Profil Ayarları")

cinsiyet = st.sidebar.selectbox("Cinsiyet Bilgisi", ["Erkek", "Kadın"], index=0 if user_data["cinsiyet"] == "Erkek" else 1)
yas = st.sidebar.number_input("Yaş Bilgisi", min_value=15, max_value=90, value=int(user_data["yas"]))
kilo = st.sidebar.number_input("Vücut Ağırlığı (kg)", min_value=30.0, max_value=200.0, value=float(user_data["kilo"]), step=0.5)
boy = st.sidebar.number_input("Boy Uzunluğu (cm)", min_value=120, max_value=220, value=int(user_data["boy"]))

akt_options = [
    "Hareketsiz (Masa başı iş)",
    "Hafif Hareketli (Haftada 1-3 gün egzersiz)",
    "Orta Hareketli (Haftada 3-5 gün egzersiz)",
    "Çok Hareketli (Haftada 6-7 gün egzersiz)"
]
akt_index = akt_options.index(user_data["aktivite"]) if user_data["aktivite"] in akt_options else 0
aktivite = st.sidebar.selectbox("Aktivite Seviyesi", akt_options, index=akt_index)

hedef_options = ["Kilo Verme (Yağ Yakımı)", "Kilo Koruma", "Kilo Alma / Kas Yapma"]
hedef_index = hedef_options.index(user_data["hedef"]) if user_data["hedef"] in hedef_options else 0
hedef = st.sidebar.selectbox("Hedefiniz", hedef_options, index=hedef_index)

# HEDEF HESAPLAMA VE KAYDET
if st.sidebar.button("💾 Bilgileri ve Hesaplamayı Kaydet"):
    if cinsiyet == "Erkek":
        bmr = (10 * kilo) + (6.25 * boy) - (5 * yas) + 5
    else:
        bmr = (10 * kilo) + (6.25 * boy) - (5 * yas) - 161

    akt_carpanlar = {
        "Hareketsiz (Masa başı iş)": 1.2,
        "Hafif Hareketli (Haftada 1-3 gün egzersiz)": 1.375,
        "Orta Hareketli (Haftada 3-5 gün egzersiz)": 1.55,
        "Çok Hareketli (Haftada 6-7 gün egzersiz)": 1.725
    }
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
    st.sidebar.success("Profil ve Hedefler Kaydedildi!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Aktif Günlük Hedefler")
st.sidebar.write(f"• **Hedef Kalori:** {int(user_data['target_kalori'])} kcal")
st.sidebar.write(f"• **Hedef Protein:** {int(user_data['target_protein'])} Gram")
st.sidebar.write(f"• **Hedef Karbonhidrat:** {int(user_data['target_karb'])} Gram")
st.sidebar.write(f"• **Hedef Yağ:** {int(user_data['target_yag'])} Gram")

# --- ANA EKRAN ---
st.title(f"🥗 {active_user} - Beslenme ve Öğün Takibi")

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

# --- SEKMELER ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Öğün Oluştur", "🔍 Barkod Arama", "📷 Etiket Okuma (OCR)", "📊 Günlük Özet & Hedefler", "➕ Ürün Yönetimi"])

food_df = pd.DataFrame(db["food_db"])
if "kategori" not in food_df.columns:
    food_df["kategori"] = "Diğer / Eklenenler"

# TAB 1: Öğün Oluştur
with tab1:
    st.subheader(f"{active_user} İçin Besin Ekle")
    
    categories = ["Tüm Kategoriler"] + sorted(list(food_df["kategori"].dropna().unique()))
    selected_cat = st.selectbox("Kategori Filtresi", categories)
    
    if selected_cat != "Tüm Kategoriler":
        filtered_df = food_df[food_df["kategori"] == selected_cat]
    else:
        filtered_df = food_df

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        food_list_sorted = filtered_df["isim"].tolist()[::-1]
        selected_food_name = st.selectbox("Besin Seçin", food_list_sorted)
    with col2:
        gramaj = st.number_input("Gramaj (g)", min_value=1, value=100, step=10)
    with col3:
        meal_type = st.selectbox("Öğün Seçin", ["Kahvaltı", "Öğle Yemeği", "Akşam Yemeği", "Aperatif"])

    if st.button("Öğüne Ekle"):
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
        user_data["daily_meals"].append(meal_item)
        save_data(db)
        st.success(f"{gramaj}g {selected_food_name} ({meal_type}) eklendi ve kaydedildi!")
        st.rerun()

    # --- ÖĞÜN TİPİNE GÖRE DİNAMİK LİSTELEME ---
    st.markdown("---")
    
    # Öğün Filtresi (Seçilen Öğüne Göre veya Tümünü Göster)
    filter_meal_type = st.radio(
        "Listelenecek Öğünü Seçin:", 
        ["Seçili Öğün (" + meal_type + ")", "Tüm Günün Öğünleri"], 
        horizontal=True
    )
    
    if "Seçili Öğün" in filter_meal_type:
        displayed_meals = [item for item in user_data["daily_meals"] if item["Öğün"] == meal_type]
        st.subheader(f"📋 {meal_type} İçin Eklenenler ({len(displayed_meals)} Adet)")
    else:
        displayed_meals = user_data["daily_meals"]
        st.subheader(f"📋 Tüm Gün Eklenen Öğünler ({len(displayed_meals)} Adet)")

    if displayed_meals:
        for idx, item in enumerate(user_data["daily_meals"]):
            # Filtreye göre gösterme kontrolü
            if "Seçili Öğün" in filter_meal_type and item["Öğün"] != meal_type:
                continue

            c_meal, c_name, c_cal, c_macro, c_del = st.columns([1.5, 2.5, 1.5, 2.5, 1])
            c_meal.write(f"**{item['Öğün']}**")
            c_name.write(f"{item['Besin']} ({item['Gramaj (g)']}g)")
            c_cal.write(f"🔥 {item['Kalori (kcal)']} kcal")
            c_macro.write(f"P: {item['Protein (g)']}g | K: {item['Karbonhidrat (g)']}g | Y: {item['Yağ (g)']}g")
            
            if c_del.button("🗑️ Sil", key=f"del_tab1_{idx}"):
                user_data["daily_meals"].pop(idx)
                save_data(db)
                st.rerun()
    else:
        st.info("Bu öğün için henüz yiyecek eklenmedi.")

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
            st.subheader("Okunan Değerler (100g İçin - İsterseniz Düzenleyin)")
            c_kal = st.number_input("Kalori (kcal)", value=p_data['kalori'])
            c_pro = st.number_input("Protein (g)", value=p_data['protein'])
            c_karb = st.number_input("Karbonhidrat (g)", value=p_data['karbonhidrat'])
            c_yag = st.number_input("Yağ (g)", value=p_data['yag'])
            
            new_food_name = st.text_input("Ürün Adı Girin", value="Taranan Ürün")
            c_kat = st.selectbox("Kategori Seçin", ["Meyveler", "Sebzeler", "Tahıllar & Bakliyat", "Kuruyemişler & Yağlar", "Et, Balık & Yumurta", "Süt Ürünleri", "Ev Yemekleri", "Diğer / Eklenenler"], index=7)
            
            if st.button("Veritabanına Kaydet"):
                new_id = len(db["food_db"]) + 1
                new_entry = {
                    "id": new_id, 
                    "kategori": c_kat,
                    "isim": new_food_name, 
                    "kalori": float(c_kal), 
                    "protein": float(c_pro), 
                    "karbonhidrat": float(c_karb), 
                    "yag": float(c_yag)
                }
                db["food_db"].append(new_entry)
                save_data(db)
                del st.session_state['parsed_ocr']
                st.success(f"'{new_food_name}' veritabanına eklendi!")
                st.rerun()

# TAB 4: Günlük Özet & Hedefler
with tab4:
    st.subheader(f"📊 {active_user} - Günlük Tüketim Özeti")
    
    t_kal = user_data["target_kalori"]
    t_pro = user_data["target_protein"]
    t_karb = user_data["target_karb"]
    t_yag = user_data["target_yag"]

    meals = user_data["daily_meals"]

    if meals:
        df_meals = pd.DataFrame(meals)
        tot_kalori = df_meals['Kalori (kcal)'].sum()
        tot_protein = df_meals['Protein (g)'].sum()
        tot_karb = df_meals['Karbonhidrat (g)'].sum()
        tot_yag = df_meals['Yağ (g)'].sum()

        m1, m2, m3, m4 = st.columns(4)
        kalan_kalori = int(t_kal - tot_kalori)
        
        m1.metric("Alınan Kalori", f"{tot_kalori:.1f} kcal", f"Kalan: {kalan_kalori} kcal")
        m2.metric("Alınan Protein", f"{tot_protein:.1f} g", f"Hedef: {int(t_pro)} g")
        m3.metric("Alınan Karbonhidrat", f"{tot_karb:.1f} g", f"Hedef: {int(t_karb)} g")
        m4.metric("Alınan Yağ", f"{tot_yag:.1f} g", f"Hedef: {int(t_yag)} g")

        st.markdown("---")
        kal_ratio = min(tot_kalori / t_kal, 1.0) if t_kal > 0 else 0.0
        pro_ratio = min(tot_protein / t_pro, 1.0) if t_pro > 0 else 0.0
        karb_ratio = min(tot_karb / t_karb, 1.0) if t_karb > 0 else 0.0
        yag_ratio = min(tot_yag / t_yag, 1.0) if t_yag > 0 else 0.0

        st.write("### 🎯 Hedef İlerleme Barları")
        st.write("**Kalori Doluluk Oranı**")
        st.progress(kal_ratio)

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.write("**Protein**")
            st.progress(pro_ratio)
        with col_m2:
            st.write("**Karbonhidrat**")
            st.progress(karb_ratio)
        with col_m3:
            st.write("**Yağ**")
            st.progress(yag_ratio)

        st.markdown("---")
        col_t1, col_t2 = st.columns([4, 1])
        with col_t1:
            st.subheader("📋 Öğün Öğün Yenen Yemekler")
        with col_t2:
            if st.button("🗑️ Tüm Günü Sıfırla"):
                user_data["daily_meals"] = []
                save_data(db)
                st.rerun()

        # Öğünleri Kendi Başlıklarında Gruplama
        for meal_group in ["Kahvaltı", "Öğle Yemeği", "Akşam Yemeği", "Aperatif"]:
            group_items = [m for m in meals if m["Öğün"] == meal_group]
            if group_items:
                st.write(f"#### 🍽️ {meal_group}")
                for idx, item in enumerate(meals):
                    if item["Öğün"] == meal_group:
                        c_meal, c_name, c_cal, c_macro, c_del = st.columns([1.5, 2.5, 1.5, 2.5, 1])
                        c_meal.write(f"**{item['Öğün']}**")
                        c_name.write(f"{item['Besin']} ({item['Gramaj (g)']}g)")
                        c_cal.write(f"🔥 {item['Kalori (kcal)']} kcal")
                        c_macro.write(f"P: {item['Protein (g)']}g | K: {item['Karbonhidrat (g)']}g | Y: {item['Yağ (g)']}g")
                        
                        if c_del.button("🗑️ Sil", key=f"del_tab4_{idx}"):
                            user_data["daily_meals"].pop(idx)
                            save_data(db)
                            st.rerun()
    else:
        st.info("Henüz bir öğün eklenmedi. 'Öğün Oluştur' sekmesinden yemek ekleyerek başlayabilirsiniz.")

# TAB 5: DİNAMİK ÜRÜN YÖNETİMİ
with tab5:
    st.subheader("➕ Veritabanına Yeni Besin / Yemek Ekle")
    col_a, col_b = st.columns(2)
    with col_a:
        custom_name = st.text_input("Yiyecek / Ürün Adı")
        custom_cat = st.selectbox("Kategorisi", ["Meyveler", "Sebzeler", "Tahıllar & Bakliyat", "Kuruyemişler & Yağlar", "Et, Balık & Yumurta", "Süt Ürünleri", "Ev Yemekleri", "Diğer / Eklenenler"])
    with col_b:
        col_b1, col_b2 = st.columns(2)
        custom_kal = col_b1.number_input("100g Kalori (kcal)", min_value=0.0, value=50.0, step=1.0)
        custom_pro = col_b2.number_input("100g Protein (g)", min_value=0.0, value=1.0, step=0.1)
        custom_karb = col_b1.number_input("100g Karbonhidrat (g)", min_value=0.0, value=10.0, step=0.1)
        custom_yag = col_b2.number_input("100g Yağ (g)", min_value=0.0, value=0.0, step=0.1)

    if st.button("✨ Veritabanına Kalıcı Olarak Ekle"):
        if custom_name:
            existing_names = [f["isim"].lower() for f in db["food_db"]]
            if custom_name.lower() in existing_names:
                st.warning(f"'{custom_name}' zaten veritabanında mevcut!")
            else:
                new_id = len(db["food_db"]) + 1
                new_entry = {
                    "id": new_id,
                    "kategori": custom_cat,
                    "isim": custom_name,
                    "kalori": float(custom_kal),
                    "protein": float(custom_pro),
                    "karbonhidrat": float(custom_karb),
                    "yag": float(custom_yag)
                }
                db["food_db"].append(new_entry)
                save_data(db)
                st.success(f"'{custom_name}' başarıyla veritabanına eklendi!")
                st.rerun()
        else:
            st.error("Lütfen bir yiyecek adı girin.")

    st.markdown("---")
    st.subheader("🗑️ Veritabanındaki Besinleri Yönet / Sil")
    
    del_cat = st.selectbox("Filtrelenecek Kategori", ["Tüm Kategoriler"] + sorted(list(food_df["kategori"].dropna().unique())), key="del_cat_select")
    if del_cat != "Tüm Kategoriler":
        f_df = food_df[food_df["kategori"] == del_cat]
    else:
        f_df = food_df

    food_to_delete = st.selectbox("Silinecek Besini Seçin", f_df["isim"].tolist())
    if st.button("❌ Bu Besini Veritabanından Sil"):
        db["food_db"] = [f for f in db["food_db"] if f["isim"] != food_to_delete]
        save_data(db)
        st.success(f"'{food_to_delete}' veritabanından silindi.")
        st.rerun()