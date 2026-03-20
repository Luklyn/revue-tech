import streamlit as st
import feedparser
from datetime import datetime, timedelta
import pandas as pd
import re

# Configuration
st.set_page_config(page_title="Hardware Hub", page_icon="🖥️", layout="wide")

# --- SOURCES CORRIGÉES ---
RSS_FEEDS = {
    "TechPowerUp": "https://www.techpowerup.com/rss/news",
    "Hardware & Co": "https://hardwareand.co/actualites?format=feed&type=rss",
    "Hardware.fr": "https://www.hardware.fr/backend/news.xml",
    "Frandroid": "https://www.frandroid.com/produits/pc-ordinateurs/feed",
    "Les Numériques": "https://www.lesnumeriques.com/informatique/rss.xml",
}

YOUTUBE_CHANNELS = {
    "Gamers Nexus": "https://www.youtube.com/feeds/videos.xml?channel_id=UCPY35SuS86mOxlIc_pT_UvQ",
    "VCG (Vieux Con Gaming)": "https://www.youtube.com/@VC-Gaming/videos",
    "Hardware Canucks": "https://www.youtube.com/@HardwareCanucks/videos",
    "Mr Matt Lee": "https://www.youtube.com/@Mr_Matt_Lee/videos",
    "Hardware Unboxed": "https://www.youtube.com/@Hardwareunboxed/videos"
}

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?q=80&w=400&auto=format&fit=crop"

# --- LOGIQUE RÉCUPÉRATION ---
@st.cache_data(ttl=1800) # Rafraîchissement toutes les 30 min
def fetch_content(source_dict, is_youtube=False):
    all_data = []
    for name, url in source_dict.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            try:
                dt = datetime(*entry.published_parsed[:6])
                link = entry.link
                
                if is_youtube:
                    # Extraction ID vidéo pour miniature YouTube
                    v_id = entry.link.split("v=")[1] if "v=" in entry.link else entry.id.split(":")[-1]
                    img = f"https://img.youtube.com/vi/{v_id}/mqdefault.jpg"
                    summary = "Vidéo YouTube"
                else:
                    # Extraction image Presse
                    img = DEFAULT_IMAGE
                    if 'media_content' in entry: img = entry.media_content[0]['url']
                    elif 'links' in entry:
                        for l in entry.links:
                            if 'image' in l.get('type', ''): img = l.href
                    summary = re.sub('<[^<]+?>', '', entry.get("summary", ""))[:150] + "..."

                all_data.append({
                    "source": name, "title": entry.title, "link": link, 
                    "date": dt, "image": img, "summary": summary
                })
            except: continue
    return pd.DataFrame(all_data).sort_values(by="date", ascending=False) if all_data else pd.DataFrame()

# --- INTERFACE ---
st.sidebar.title("🎮 Hardware Hub")
mode = st.sidebar.radio("Navigation", ["📰 Articles Presse", "📺 Vidéos YouTube"])

if mode == "📰 Articles Presse":
    st.title("📰 Revue de Presse")
    df = fetch_content(RSS_FEEDS)
else:
    st.title("📺 Dernières Vidéos")
    df = fetch_content(YOUTUBE_CHANNELS, is_youtube=True)

# Filtres
st.sidebar.divider()
if not df.empty:
    # Filtre 3 jours
    latest = df['date'].max()
    limit = latest - timedelta(days=3)
    
    # Option pour voir tout ou seulement les 3 derniers jours
    show_all = st.sidebar.checkbox("Voir toutes les archives", value=False)
    if not show_all:
        df = df[df['date'] >= limit]
        st.sidebar.caption(f"Affichage des news depuis le {limit.strftime('%d/%m')}")

    search = st.sidebar.text_input("🔍 Rechercher un composant...").lower()
    if search:
        df = df[df['title'].str.lower().str.contains(search)]

# Affichage en Grille
if df.empty:
    st.warning("Aucun contenu trouvé. Essayez de décocher les filtres.")
else:
    # CSS pour corriger l'affichage des images
    st.markdown("""
        <style>
        .card { background: white; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); overflow: hidden; height: 320px; }
        .card-img { width: 100%; height: 150px; object-fit: cover; background: #222; }
        .card-body { padding: 10px; }
        .card-source { color: #ff4b4b; font-size: 0.7rem; font-weight: bold; }
        .card-title { font-size: 0.9rem; font-weight: bold; margin: 5px 0; height: 3.5em; overflow: hidden; line-height: 1.2; }
        .card-title a { text-decoration: none; color: #333; }
        </style>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    for idx, row in df.reset_index().iterrows():
        with cols[idx % 4]:
            st.markdown(f"""
                <div class="card">
                    <img src="{row['image']}" class="card-img">
                    <div class="card-body">
                        <div class="card-source">{row['source']}</div>
                        <div class="card-title"><a href="{row['link']}" target="_blank">{row['title']}</a></div>
                        <div style="font-size: 0.7rem; color: gray;">📅 {row['date'].strftime('%d/%m à %H:%M')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
