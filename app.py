import streamlit as st
import feedparser
from datetime import datetime
import pandas as pd
import re
import urllib.request

# Configuration V11
st.set_page_config(page_title="Revue de presse Tech", page_icon="🖥️", layout="wide")

# --- STYLE CSS V11 (Date réactivée et stylisée) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    .stApp {{ background-color: #000000 !important; }}
    [data-testid="stAppViewContainer"] {{ background-color: #000000 !important; }}
    header {{visibility: hidden;}}
    
    h1 {{ color: #ffffff !important; font-family: 'Inter', sans-serif !important; text-align: left; font-weight: 800; margin-bottom: 20px; }}

    /* Inputs (Recherche et Selectbox) */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
    }}
    
    /* Cartes */
    .card {{ 
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        margin-bottom: 25px; 
        overflow: hidden; 
        height: 330px; /* Légèrement augmenté pour la date */
        transition: all 0.3s ease;
    }}
    .card:hover {{ border-color: rgba(193, 0, 44, 0.8); transform: translateY(-5px); }}
    
    .card-img {{ width: 100%; height: 160px; object-fit: cover; background-color: #111; }}
    .card-body {{ padding: 15px; position: relative; height: 170px; }} /* Structure pour fixer la date en bas */
    .card-source {{ color: #c1002c !important; font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }}
    .card-title a {{ text-decoration: none; color: #ffffff !important; font-size: 14px; font-weight: 700; line-height: 1.4; }}
    .card-summary {{ font-size: 13px; color: #bbbbbb !important; line-height: 1.4; height: 38px; overflow: hidden; margin-top: 5px; }}
    
    /* Style de la Date (Réactivée) */
    .card-date {{ 
        font-size: 10px; 
        color: #666666; 
        position: absolute; 
        bottom: 12px; 
        left: 15px; 
        right: 15px; 
        border-top: 1px solid rgba(255,255,255,0.05); 
        padding-top: 8px; 
    }}

    button[kind="primary"] {{ background-color: #c1002c !important; border: none !important; color: white !important; font-weight: 600 !important; }}
    button[kind="secondary"] {{ background: rgba(255,255,255,0.05) !important; color: white !important; border: 1px solid rgba(255,255,255,0.2) !important; }}
    </style>
""", unsafe_allow_html=True)

# --- SOURCES ---
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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for name, url in source_dict.items():
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                feed = feedparser.parse(response.read())
            for entry in feed.entries:
                try:
                    dt = datetime(*entry.published_parsed[:6])
                    img = ""
                    if is_youtube:
                        v_id = entry.link.split("v=")[1].split("&")[0] if "v=" in entry.link else entry.id.split(":")[-1]
                        img = f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg"
                        summary = ""
                    else:
                        img = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800"
                        if 'media_content' in entry: img = entry.media_content[0]['url']
                        elif 'enclosures' in entry and len(entry.enclosures) > 0: img = entry.enclosures[0]['href']
                        summary = re.sub('<[^<]+?>', '', entry.get("summary", ""))[:110] + "..."
                    all_data.append({"source": name, "title": entry.title, "link": entry.link, "date": dt, "image": img, "summary": summary, "is_video": is_youtube})
                except: continue
        except: continue
    return pd.DataFrame(all_data).sort_values(by="date", ascending=False) if all_data else pd.DataFrame()

# --- INTERFACE ---
st.title("Revue de presse Tech")

if 'view' not in st.session_state: st.session_state.view = 'Articles'

# Navigation
c1, c2, _ = st.columns([1.2, 1.2, 4])
if c1.button("ARTICLES PRESSE", use_container_width=True, type="primary" if st.session_state.view == 'Articles' else "secondary"):
    st.session_state.view = 'Articles'; st.rerun()
if c2.button("VIDEOS YOUTUBE", use_container_width=True, type="primary" if st.session_state.view == 'Videos' else "secondary"):
    st.session_state.view = 'Videos'; st.rerun()

st.write("")

# Barre de recherche et Filtre Source
col_search, col_filter, col_spacer = st.columns([2.5, 2, 3]) 

with col_search:
    search_query = st.text_input("", placeholder="Rechercher...", label_visibility="collapsed")

with col_filter:
    source_list = ["Toutes les sources"] + list(RSS_FEEDS.keys() if st.session_state.view == 'Articles' else YOUTUBE_CHANNELS.keys())
    selected_source = st.selectbox("", options=source_list, label_visibility="collapsed")

st.divider()

# Récupération et Filtrage
df = fetch_content(RSS_FEEDS if st.session_state.view == 'Articles' else YOUTUBE_CHANNELS, is_youtube=(st.session_state.view == 'Videos'))

if not df.empty:
    if search_query:
        df = df[df['title'].str.contains(search_query, case=False, na=False)]
    if selected_source != "Toutes les sources":
        df = df[df['source'] == selected_source]

    # Affichage Grille
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
                        <div class="card-date">Publié le {row['date'].strftime('%d %b %Y')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("Aucun contenu disponible pour le moment.")
