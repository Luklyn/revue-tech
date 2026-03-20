import streamlit as st
import feedparser
from datetime import datetime, timedelta
import pandas as pd
import re

# Configuration de la page
st.set_page_config(page_title="Hardware Hub - Presse & Vidéo", page_icon="🖥️", layout="wide")

# --- CONFIGURATION DES SOURCES ---
RSS_FEEDS = {
    "TechPowerUp": "https://www.techpowerup.com/rss/news",
    "Hardware & Co": "https://hardwareand.co/actualites?format=feed&type=rss",
    "Hardware.fr": "https://www.hardware.fr/backend/news.xml",
    "Frandroid": "https://www.frandroid.com/produits/pc-ordinateurs/feed",
    "Les Numériques": "https://www.lesnumeriques.com/informatique/rss.xml",
}

# Liste des chaînes YouTube (ID ou lien RSS de la chaîne)
YOUTUBE_CHANNELS = {
    "Gamers Nexus": "https://www.youtube.com/feeds/videos.xml?channel_id=UCPY35SuS86mOxlIc_pT_UvQ",
    "Vieux Con Gaming (VCG)": "https://www.youtube.com/feeds/videos.xml?channel_id=UC6YF6z_Z98vP9m_W2A0v-Xg",
    "Hardware Canucks": "https://www.youtube.com/feeds/videos.xml?channel_id=UChIs72whgZI9w6d6FhwGGHA",
    "Mr Matt Lee": "https://www.youtube.com/feeds/videos.xml?channel_id=UC_S9S_T0zR6fFshzG9y6p_w",
    "Hardware Unboxed": "https://www.youtube.com/feeds/videos.xml?channel_id=UCI8iQa1hv7oV_Z8B35MpwLA"
}

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1591799264318-7e698ddb7c1d?q=80&w=400&auto=format&fit=crop"

# --- FONCTIONS DE RÉCUPÉRATION ---

@st.cache_data(ttl=3600)
def fetch_articles():
    all_entries = []
    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            try:
                dt = datetime(*entry.published_parsed[:6])
                img_url = DEFAULT_IMAGE
                if 'links' in entry:
                    for link in entry.links:
                        if 'image' in link.type or 'enclosure' in link.rel: img_url = link.href
                elif 'media_content' in entry: img_url = entry.media_content[0]['url']
                
                summary = re.sub('<[^<]+?>', '', entry.get("summary", ""))[:180] + "..."
                all_entries.append({"source": source, "title": entry.title, "link": entry.link, "date": dt, "image": img_url, "summary": summary, "type": "Presse"})
            except: continue
    return pd.DataFrame(all_entries).sort_values(by="date", ascending=False)

@st.cache_data(ttl=3600)
def fetch_videos():
    all_videos = []
    for channel_name, url in YOUTUBE_CHANNELS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            try:
                dt = datetime(*entry.published_parsed[:6])
                # Extraction de l'ID vidéo pour la miniature et le lien
                video_id = entry.link.split("v=")[1]
                img_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                all_videos.append({"source": channel_name, "title": entry.title, "link": entry.link, "date": dt, "image": img_url, "summary": "Nouvelle vidéo disponible !", "type": "Vidéo"})
            except: continue
    return pd.DataFrame(all_videos).sort_values(by="date", ascending=False)

# --- STYLE CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    .news-card { background-color: white; border-radius: 12px; padding: 0px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); overflow: hidden; }
    .card-image { width: 100%; height: 160px; object-fit: cover; }
    .card-content { padding: 12px; }
    .card-title { font-weight: bold; font-size: 1rem; height: 3em; overflow: hidden; margin-bottom: 8px; }
    .card-title a { text-decoration: none; color: #1f1f1f; }
    .card-source { color: #ff4b4b; font-size: 0.75rem; font-weight: bold; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION PRINCIPALE ---
st.sidebar.title("🎮 Menu Principal")
choix = st.sidebar.radio("Aller vers :", ["📰 Articles Presse", "📺 Vidéos YouTube"])

if choix == "📰 Articles Presse":
    st.title("📰 Revue de Presse Hardware")
    df = fetch_articles()
else:
    st.title("📺 Dernières Vidéos Hardware")
    df = fetch_videos()

# --- FILTRES COMMUNS ---
st.sidebar.divider()
search = st.sidebar.text_input("🔍 Rechercher...").lower()

# Filtrage par date (3 jours)
if not df.empty:
    max_date = df['date'].max()
    min_date = df['date'].min()
    periods = []
    curr = max_date
    while curr >= min_date:
        start_p = curr - timedelta(days=3)
        periods.append((f"Du {start_p.strftime('%d/%m')} au {curr.strftime('%d/%m')}", start_p, curr))
        curr = start_p
    
    sel_p_label = st.sidebar.selectbox("📅 Période :", [p[0] for p in periods])
    sel_p = next(p for p in periods if p[0] == sel_p_label)
    
    df = df[(df['date'] >= sel_p[1]) & (df['date'] <= sel_p[2])]
    if search:
        df = df[df['title'].str.lower().str.contains(search)]

# --- AFFICHAGE ---
if df.empty:
    st.info("Aucun contenu trouvé.")
else:
    cols = st.columns(4) # 4 cartes par ligne pour les vidéos/articles
    for idx, row in df.reset_index().iterrows():
        with cols[idx % 4]:
            st.markdown(f"""
            <div class="news-card">
                <img src="{row['image']}" class="card-image">
                <div class="card-content">
                    <div class="card-source">{row['source']}</div>
                    <div class="card-title"><a href="{row['link']}" target="_blank">{row['title']}</a></div>
                    <div style="font-size:0.8rem; color:gray;">📅 {row['date'].strftime('%d/%m')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
