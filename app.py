import streamlit as st
import feedparser
from datetime import datetime, timedelta
import pandas as pd
import re
import urllib.request

# Configuration
st.set_page_config(page_title="Tech Briefing", page_icon="🖥️", layout="wide")

# Initialisation du choix de navigation si absent
if 'menu_selection' not in st.session_state:
    st.session_state.menu_selection = 'Articles'

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
    "VCG (Vieux Con Gaming)": "https://www.youtube.com/feeds/videos.xml?channel_id=UCjrj3gdo-KL2S_JN_gdNyPw",
    "Hardware Canucks": "https://www.youtube.com/feeds/videos.xml?channel_id=UCVn2OUZWZ0V7xC7n0z7nK0w",
    "Mr Matt Lee": "https://www.youtube.com/feeds/videos.xml?channel_id=UCbLTf6hZpZkY7kC3Y7x5L9A",
    "Hardware Unboxed": "https://www.youtube.com/feeds/videos.xml?channel_id=UCI8iQa1hv7oV_Z8B35vVuSg"
}

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=800&auto=format&fit=crop"

@st.cache_data(ttl=600)
def fetch_content(source_dict, is_youtube=False):
    all_data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for name, url in source_dict.items():
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                content = response.read()
            feed = feedparser.parse(content)
            for entry in feed.entries:
                try:
                    dt = datetime(*entry.published_parsed[:6])
                    if is_youtube:
                        v_id = entry.link.split("v=")[1].split("&")[0] if "v=" in entry.link else entry.id.split(":")[-1]
                        img = f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg"
                        summary = ""
                    else:
                        img = DEFAULT_IMAGE
                        if 'media_content' in entry: img = entry.media_content[0]['url']
                        elif 'links' in entry:
                            for l in entry.links:
                                if 'image' in l.get('type', ''): img = l.href
                        summary = re.sub('<[^<]+?>', '', entry.get("summary", ""))[:110] + "..."
                    all_data.append({"source": name, "title": entry.title, "link": entry.link, "date": dt, "image": img, "summary": summary, "is_video": is_youtube})
                except: continue
        except: continue
    return pd.DataFrame(all_data).sort_values(by="date", ascending=False) if not pd.DataFrame(all_data).empty else pd.DataFrame()

# --- STYLE CSS (HIÉRARCHIE VISUELLE RESTAURÉE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    header {visibility: hidden;}
    
    /* Cartes */
    .card { background: #fff; border: 1px solid #efefef; border-radius: 4px; margin-bottom: 20px; overflow: hidden; height: 320px; transition: all 0.2s ease; }
    .card:hover { border-color: #bbb; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transform: translateY(-2px); }
    .card-img { width: 100%; height: 160px; object-fit: cover; }
    .card-body { padding: 12px; }
    
    /* Couleurs de texte pour différenciation */
    .card-source { color: #e63946; font-size: 10px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 6px; }
    
    .card-title { font-size: 14px; font-weight: 700; line-height: 1.4; margin-bottom: 8px; height: 40px; overflow: hidden; }
    .card-title a { text-decoration: none; color: #111111 !important; } /* TITRE NOIR PROFOND */
    
    .card-summary { font-size: 13px; color: #666666; line-height: 1.4; height: 38px; overflow: hidden; } /* CONTENU GRIS */
    
    .card-date { font-size: 11px; color: #999; margin-top: 10px; border-top: 1px solid #eee; padding-top: 8px; }
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
st.title("Tech Briefing")

col_nav1, col_nav2, col_spacer = st.columns([1.2, 1.2, 4])

with col_nav1:
    if st.button("📰 ARTICLES PRESSE", use_container_width=True, type="primary" if st.session_state.menu_selection == 'Articles' else "secondary"):
        st.session_state.menu_selection = 'Articles'
        st.rerun()

with col_nav2:
    if st.button("📺 VIDÉOS YOUTUBE", use_container_width=True, type="primary" if st.session_state.menu_selection == 'Videos' else "secondary"):
        st.session_state.menu_selection = 'Videos'
        st.rerun()

st.divider()

# --- LOGIQUE D'AFFICHAGE ---
search = st.sidebar.text_input("Rechercher un sujet").lower()

if st.session_state.menu_selection == 'Articles':
    df = fetch_content(RSS_FEEDS)
else:
    df = fetch_content(YOUTUBE_CHANNELS, is_youtube=True)

if not df.empty:
    if search:
        df = df[df['title'].str.lower().str.contains(search)]
    
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
                        <div class="card-date">Publié le {row['date'].strftime('%d %b %Y')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("Chargement des flux en cours...")
