import streamlit as st
import feedparser
from datetime import datetime
import pandas as pd
import re
import urllib.request

# Configuration
st.set_page_config(page_title="Revue de presse Tech", page_icon="🖥️", layout="wide")

# --- STYLE CSS (NAVBAR & GLASSMORPHISM) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp {{ background-color: #000000 !important; }}
    [data-testid="stAppViewContainer"] {{ background-color: #000000 !important; }}
    header {{visibility: hidden;}}
    
    /* Navbar Container */
    .nav-bar {{
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        padding: 10px 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 30px;
        position: sticky;
        top: 0;
        z-index: 999;
    }}

    /* Cartes */
    .card {{ 
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        margin-bottom: 25px; 
        overflow: hidden; 
        height: 310px; 
        transition: all 0.3s ease;
    }}
    .card:hover {{ 
        border-color: #c1002c; 
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.12);
    }}
    
    .card-img {{ width: 100%; height: 160px; object-fit: cover; opacity: 0.9; }}
    .card-body {{ padding: 15px; }}
    .card-source {{ color: #c1002c !important; font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }}
    .card-title a {{ text-decoration: none; color: #ffffff !important; font-size: 14px; font-weight: 700; }}
    .card-summary {{ font-size: 13px; color: #bbbbbb !important; line-height: 1.4; height: 38px; overflow: hidden; }}
    .card-date {{ font-size: 11px; color: #666666; margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px; }}

    /* Boutons de la Navbar */
    button[kind="primary"] {{ background-color: #c1002c !important; border: none !important; }}
    button[kind="secondary"] {{ background: rgba(255,255,255,0.05) !important; color: white !important; border: 1px solid rgba(255,255,255,0.1) !important; }}
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURATION DES SOURCES ---
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
                        img = "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800"
                        if 'media_content' in entry: img = entry.media_content[0]['url']
                        summary = re.sub('<[^<]+?>', '', entry.get("summary", ""))[:110] + "..."
                    all_data.append({"source": name, "title": entry.title, "link": entry.link, "date": dt, "image": img, "summary": summary, "is_video": is_youtube})
                except: continue
        except: continue
    return pd.DataFrame(all_data).sort_values(by="date", ascending=False) if all_data else pd.DataFrame()

# --- INITIALISATION ÉTATS ---
if 'view' not in st.session_state: st.session_state.view = 'Articles'
if 'category' not in st.session_state: st.session_state.category = 'TOUT'

# --- NAVBAR HAUTE ---
st.title("Revue de presse Tech")

# Colonnes pour la Navbar
col_mode1, col_mode2, col_spacer, col_search = st.columns([1, 1, 2, 2])

with col_mode1:
    if st.button("ARTICLES", type="primary" if st.session_state.view == 'Articles' else "secondary", use_container_width=True):
        st.session_state.view = 'Articles'; st.rerun()
with col_mode2:
    if st.button("VIDEOS", type="primary" if st.session_state.view == 'Videos' else "secondary", use_container_width=True):
        st.session_state.view = 'Videos'; st.rerun()
with col_search:
    search_query = st.text_input("", placeholder="Rechercher une news...", label_visibility="collapsed")

# --- BARRE DE CATÉGORIES ---
st.write("") # Espacement
cat_cols = st.columns(6)
categories = ["TOUT", "HARDWARE", "PC", "SMARTPHONE", "GAMING", "IA"]

for i, cat in enumerate(categories):
    with cat_cols[i]:
        if st.button(cat, type="primary" if st.session_state.category == cat else "secondary", use_container_width=True):
            st.session_state.category = cat
            st.rerun()

st.divider()

# --- LOGIQUE DE FILTRE ---
df = fetch_content(RSS_FEEDS if st.session_state.view == 'Articles' else YOUTUBE_CHANNELS, is_youtube=(st.session_state.view == 'Videos'))

if not df.empty:
    # Filtre recherche libre
    if search_query:
        df = df[df['title'].str.lower().str.contains(search_query.lower())]
    
    # Filtre par catégorie (mots-clés dans le titre)
    if st.session_state.category != "TOUT":
        keywords = {
            "HARDWARE": "cpu|gpu|nvidia|intel|amd|ryzen|rtx|carte mère|ram|ssd",
            "PC": "ordinateur|laptop|clavier|souris|windows|macbook|dell|asus",
            "SMARTPHONE": "iphone|android|samsung|pixel|mobile|ios|xiaomi",
            "GAMING": "jeu|ps5|xbox|nintendo|console|steam|playstation",
            "IA": "ia|ai|chatgpt|openai|gemini|llm|copilot"
        }
        query = keywords.get(st.session_state.category, "")
        df = df[df['title'].str.lower().str.contains(query)]

    # Affichage
    if not df.empty:
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
    else:
        st.info("Aucun article ne correspond à cette catégorie ou recherche.")
else:
    st.info("Chargement des flux...")
