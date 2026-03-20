import streamlit as st
import feedparser
from datetime import datetime
import pandas as pd
import re
import urllib.request

# Configuration V9
st.set_page_config(page_title="Revue de presse Tech", page_icon="🖥️", layout="wide")

# --- STYLE CSS V9 ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    .stApp {{ background-color: #000000 !important; }}
    [data-testid="stAppViewContainer"] {{ background-color: #000000 !important; }}
    header {{visibility: hidden;}}
    
    h1 {{ color: #ffffff !important; font-family: 'Inter', sans-serif !important; text-align: left; font-weight: 800; margin-bottom: 20px; }}

    /* Barre de recherche */
    .stTextInput>div>div>input {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
    }}
    .stTextInput>div>div>input:focus {{ border-color: #c1002c !important; box-shadow: 0 0 0 1px #c1002c !important; }}

    /* Cartes */
    .card {{ 
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        margin-bottom: 25px; 
        overflow: hidden; 
        height: 320px; 
        transition: all 0.3s ease;
    }}
    .card:hover {{ border-color: rgba(193, 0, 44, 0.8); transform: translateY(-5px); }}
    
    .card-img {{ width: 100%; height: 160px; object-fit: cover; background-color: #111; }}
    .card-body {{ padding: 15px; }}
    .card-source {{ color: #c1002c !important; font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }}
    .card-title a {{ text-decoration: none; color: #ffffff !important; font-size: 14px; font-weight: 700; line-height: 1.4; }}
    .card-summary {{ font-size: 13px; color: #bbbbbb !important; line-height: 1.4; height: 38px; overflow: hidden; margin-top: 5px; }}
    .card-date {{ font-size: 11px; color: #666666; margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px; }}

    button[kind="primary"] {{ background-color: #c1002c !important; border: none !important; color: white !important; font-weight: 600 !important; }}
    button[kind="secondary"] {{ background: rgba(255,255,255,0.05) !important; color: white !important; border: 1px solid rgba(255,255,255,0.2) !important; }}
    </style>
""", unsafe_allow_html=True)

# --- LOGIQUE DE DONNÉES AMÉLIORÉE ---
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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
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
                        # 1. Tentative media_content
                        if 'media_content' in entry:
                            img = entry.media_content[0]['url']
                        # 2. Tentative liens enclosures
                        elif 'enclosures' in entry and len(entry.enclosures) > 0:
                            img = entry.enclosures[0]['href']
                        # 3. Tentative Extraction HTML dans le résumé
                        else:
                            content = entry.get("summary", "") + entry.get("description", "")
                            img_match = re.search(r'<img [^>]*src="([^"]+)"', content)
                            if img_match:
                                img = img_match.group(1)
                        
                        # Image de secours si rien n'est trouvé
                        if not img or "http" not in img:
                            img = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&q=80" # Image hardware retro
                            
                        summary = re.sub('<[^<]+?>', '', entry.get("summary", ""))[:110] + "..."
                    
                    all_data.append({"source": name, "title": entry.title, "link": entry.link, "date": dt, "image": img, "summary": summary, "is_video": is_youtube})
                except: continue
        except: continue
    return pd.DataFrame(all_data).sort_values(by="date", ascending=False) if all_data else pd.DataFrame()

# --- INTERFACE ---
st.title("Revue de presse Tech")

if 'view' not in st.session_state: st.session_state.view = 'Articles'

c1, c2, _ = st.columns([1.2, 1.2, 4])
if c1.button("ARTICLES PRESSE", use_container_width=True, type="primary" if st.session_state.view == 'Articles' else "secondary"):
    st.session_state.view = 'Articles'; st.rerun()
if c2.button("VIDEOS YOUTUBE", use_container_width=True, type="primary" if st.session_state.view == 'Videos' else "secondary"):
    st.session_state.view = 'Videos'; st.rerun()

col_search, _ = st.columns([2.5, 5]) 
with col_search:
    search_query = st.text_input("", placeholder="Rechercher...", label_visibility="collapsed")

st.divider()

df = fetch_content(RSS_FEEDS if st.session_state.view == 'Articles' else YOUTUBE_CHANNELS, is_youtube=(st.session_state.view == 'Videos'))

if not df.empty:
    if search_query:
        df = df[df['title'].str.contains(search_query, case=False, na=False)]
    
    cols = st.columns(4)
    for idx, row in df.reset_index().iterrows():
        with cols[idx % 4]:
            st.markdown(f"""
                <div class="card">
                    <img src="{row['image']}" class="card-img">
                    <div class="card-body">
                        <div class="card-source">{row['source']}</div>
                        <div class="card-title"><a href="{row['link']}" target="_blank">{row['title']}</a></div>
                        <div class="card-summary">{row['summary'] if not row['is_video'] else ''}</div>
                        <div class="card-date">{row['date'].strftime('%d %b %Y')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("Chargement des flux...")
