import streamlit as st
import feedparser
from datetime import datetime
import pandas as pd
import re
import urllib.request

# Configuration V5
st.set_page_config(
    page_title="Revue de presse Tech", 
    page_icon="🖥️", 
    layout="wide",
    initial_sidebar_state="expanded" # Force l'ouverture au chargement
)

# --- STYLE CSS V5 (Correction Sidebar et Design) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    /* Fond principal */
    .stApp {
        background-color: #000000 !important;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #000000 !important;
    }

    /* FORCER L'AFFICHAGE DE LA SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
        min-width: 260px !important;
        max-width: 300px !important;
    }
    
    /* Supprimer le bouton de fermeture pour qu'elle reste fixe */
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    /* Titres et Textes */
    h1 { color: #ffffff !important; font-weight: 800; }
    .stMarkdown p { color: #ffffff !important; }
    
    /* Boutons de navigation */
    div.stButton > button:first-child {
        border-radius: 4px;
        font-weight: 600;
    }
    button[kind="primary"] {
        background-color: #c1002c !important;
        border-color: #c1002c !important;
        color: white !important;
    }

    /* Cartes Glassmorphism */
    .card { 
        background: rgba(255, 255, 255, 0.05); 
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        margin-bottom: 20px; 
        height: 330px; 
        transition: all 0.3s ease;
    }
    .card:hover { 
        background: rgba(255, 255, 255, 0.1);
        border-color: #c1002c; 
        transform: translateY(-5px);
    }
    .card-img { width: 100%; height: 160px; object-fit: cover; opacity: 0.85; }
    .card-body { padding: 15px; }
    .card-source { color: #c1002c; font-size: 11px; font-weight: 800; text-transform: uppercase; }
    .card-title a { text-decoration: none; color: #ffffff !important; font-size: 15px; font-weight: 700; }
    .card-summary { font-size: 13px; color: #999999; height: 38px; overflow: hidden; margin-top: 5px; }
    .card-date { font-size: 10px; color: #555555; margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px; }

</style>
""", unsafe_allow_html=True)

# --- LOGIQUE DE RÉCUPÉRATION ---
RSS_FEEDS = {
    "TechPowerUp": "https://www.techpowerup.com/rss/news",
    "Hardware & Co": "https://hardwareand.co/actualites?format=feed&type=rss",
    "Hardware.fr": "https://www.hardware.fr/backend/news.xml",
    "Frandroid": "https://www.frandroid.com/produits/pc-ordinateurs/feed",
    "Les Numériques": "https://www.lesnumeriques.com/informatique/rss.xml",
}

YOUTUBE_CHANNELS = {
    "Gamers Nexus": "https://www.youtube.com/feeds/videos.xml?channel_id=UChIs72whgZI9w6d6FhwGGHA",
    "VCG": "https://www.youtube.com/feeds/videos.xml?channel_id=UCjrj3gdo-KL2S_JN_gdNyPw",
    "Hardware Canucks": "https://www.youtube.com/feeds/videos.xml?channel_id=UCVn2OUZWZ0V7xC7n0z7nK0w",
    "Hardware Unboxed": "https://www.youtube.com/feeds/videos.xml?channel_id=UCI8iQa1hv7oV_Z8B35vVuSg"
}

@st.cache_data(ttl=600)
def fetch_content(source_dict, is_youtube=False):
    all_data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for name, url in source_dict.items():
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                feed = feedparser.parse(response.read())
            for entry in feed.entries:
                try:
                    dt = datetime(*entry.published_parsed[:6])
                    if is_youtube:
                        v_id = entry.link.split("v=")[1].split("&")[0] if "v=" in entry.link else entry.id.split(":")[-1]
                        img = f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg"
                        summary = ""
                    else:
                        img = "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=800"
                        if 'media_content' in entry: img = entry.media_content[0]['url']
                        summary = re.sub('<[^<]+?>', '', entry.get("summary", ""))[:110] + "..."
                    all_data.append({"source": name, "title": entry.title, "link": entry.link, "date": dt, "image": img, "summary": summary, "is_video": is_youtube})
                except: continue
        except: continue
    return pd.DataFrame(all_data).sort_values(by="date", ascending=False) if all_data else pd.DataFrame()

# --- SIDEBAR (PANNEAU LATÉRAL) ---
with st.sidebar:
    st.title("Options")
    search_query = st.text_input("🔍 Recherche libre", placeholder="Ex: RTX 5090...")
    st.markdown("---")
    st.subheader("Univers")
    category = st.radio(
        "Filtrer par :",
        ["Toutes les news", "Hardware", "PC & Laptops", "Mobile", "Gaming", "IA"]
    )

# --- CONTENU PRINCIPAL ---
if 'view' not in st.session_state: st.session_state.view = 'Articles'

st.title("Revue de presse Tech")
c1, c2, _ = st.columns([1.2, 1.2, 4])
if c1.button("ARTICLES", use_container_width=True, type="primary" if st.session_state.view == 'Articles' else "secondary"):
    st.session_state.view = 'Articles'; st.rerun()
if c2.button("VIDEOS", use_container_width=True, type="primary" if st.session_state.view == 'Videos' else "secondary"):
    st.session_state.view = 'Videos'; st.rerun()

st.divider()

# Filtrage
df = fetch_content(RSS_FEEDS if st.session_state.view == 'Articles' else YOUTUBE_CHANNELS, is_youtube=(st.session_state.view == 'Videos'))

if not df.empty:
    if search_query:
        df = df[df['title'].str.contains(search_query, case=False, na=False)]
    
    if category != "Toutes les news":
        kw = {"Hardware": "cpu|gpu|nvidia|intel|amd|rtx|ssd", "PC & Laptops": "pc|laptop|windows|mac", "Mobile": "iphone|smartphone|android", "Gaming": "jeu|ps5|xbox|gaming", "IA": "ia|ai|chatgpt"}
        df = df[df['title'].str.contains(kw.get(category, ""), case=False, na=False)]

    # Grille
    cols = st.columns(4)
    for idx, row in df.reset_index().iterrows():
        with cols[idx % 4]:
            st.markdown(f"""
                <div class="card">
                    <img src="{row['image']}" class="card-img">
                    <div class="card-body">
                        <div class="card-source">{row['source']}</div>
                        <div class="card-title"><a href="{row['link']}" target="_blank">{row['title']}</a></div>
                        <div class="card-summary">{row['summary']}</div>
                        <div class="card-date">{row['date'].strftime('%d %b %Y')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
