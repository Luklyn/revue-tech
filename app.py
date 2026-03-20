import streamlit as st
import feedparser
from datetime import datetime
import pandas as pd
import re
import urllib.request

# Configuration V7
st.set_page_config(page_title="Revue de presse Tech", page_icon="🖥️", layout="wide")

# --- STYLE CSS V7 ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    /* Global */
    .stApp {{ background-color: #000000 !important; }}
    [data-testid="stAppViewContainer"] {{ background-color: #000000 !important; }}
    header {{visibility: hidden;}}
    
    h1 {{ 
        color: #ffffff !important; 
        font-family: 'Inter', sans-serif !important; 
        text-align: left; /* CORRECTION : Alignement à gauche */
        font-weight: 800;
        margin-bottom: 20px; 
    }}

    /* Barre de recherche personnalisée */
    .stTextInput>div>div>input {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        padding: 8px 15px !important; /* Légèrement plus compact */
    }}
    .stTextInput>div>div>input:focus {{
        border-color: #c1002c !important;
        box-shadow: 0 0 0 1px #c1002c !important;
    }}

    /* Cartes Glassmorphism */
    .card {{ 
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        margin-bottom: 25px; 
        overflow: hidden; 
        height: 320px; 
        transition: all 0.3s ease;
    }}
    .card:hover {{ 
        border-color: rgba(193, 0, 44, 0.8); 
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.12);
    }}
    
    .card-img {{ width: 100%; height: 160px; object-fit: cover; opacity: 0.9; }}
    .card-body {{ padding: 15px; }}
    .card-source {{ color: #c1002c !important; font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }}
    .card-title {{ font-size: 14px; font-weight: 700; line-height: 1.4; height: 40px; overflow: hidden; }}
    .card-title a {{ text-decoration: none; color: #ffffff !important; }}
    .card-summary {{ font-size: 13px; color: #bbbbbb !important; line-height: 1.4; height: 38px; overflow: hidden; }}
    .card-date {{ font-size: 11px; color: #666666; margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px; }}

    /* Boutons de navigation */
    button[kind="primary"] {{ background-color: #c1002c !important; border: none !important; color: white !important; font-weight: 600 !important; }}
    button[kind="secondary"] {{ background: rgba(255,255,255,0.05) !important; color: white !important; border: 1px solid rgba(255,255,255,0.2) !important; }}
    </style>
""", unsafe_allow_html=True)

# --- LOGIQUE DE DONNÉES ---
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

# --- INTERFACE PRINCIPALE ---
st.title("Revue de presse Tech")

# 1. Navigation
if 'view' not in st.session_state: st.session_state.view = 'Articles'

col_nav1, col_nav2, _ = st.columns([1.2, 1.2, 4])
if col_nav1.button("ARTICLES PRESSE", use_container_width=True, type="primary" if st.session_state.view == 'Articles' else "secondary"):
    st.session_state.view = 'Articles'; st.rerun()
if col_nav2.button("VIDEOS YOUTUBE", use_container_width=True, type="primary" if st.session_state.view == 'Videos' else "secondary"):
    st.session_state.view = 'Videos'; st.rerun()

# 2. Barre de recherche (Réduite et centrée)
st.write("") # Petit espacement
col_search1, col_search2, col_search3 = st.columns([1, 2, 3]) # Structure pour réduire la largeur
with col_search2:
    search_query = st.text_input("", placeholder="Rechercher un sujet (ex: RTX 5090, Intel...)", label_visibility="collapsed")

st.divider()

# --- AFFICHAGE ---
df = fetch_content(RSS_FEEDS if st.session_state.view == 'Articles' else YOUTUBE_CHANNELS, is_youtube=(st.session_state.view == 'Videos'))

if not df.empty:
    if search_query:
        df = df[df['title'].str.contains(search_query, case=False, na=False)]
    
    cols = st.columns(4)
    for idx, row in df.reset_index().iterrows():
        with cols[idx % 4]:
            summary_div = f'<div class="card-summary">{row["summary"]}</div>' if not row["is_video"] else '<div style="height:38px;"></div>'
            st.markdown(f"""
                <div class="card">
                    <img src="{row['image']}" class="card-img">
                    <div class="card-body">
                        <div class="card-source">{row['source']}</div>
                        <div class="card-title"><a href="{row['link']}" target="_blank">{row['title']}</a></div>
                        {summary_div}
                        <div class="card-date">{row['date'].strftime('%d %b %Y')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("Chargement des flux en cours...")
