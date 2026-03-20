import streamlit as st
import feedparser
from datetime import datetime
import pandas as pd
import re
import urllib.request

# Configuration
st.set_page_config(page_title="Revue de presse Tech", page_icon="🖥️", layout="wide")

# Style CSS (Fond noir + Glassmorphism + Boutons Rouges)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp {{ background-color: #000000 !important; }}
    [data-testid="stAppViewContainer"] {{ background-color: #000000 !important; }}
    header {{visibility: hidden;}}
    h1, h2, h3, p, span, label {{ color: #ffffff !important; font-family: 'Inter', sans-serif !important; }}

    /* Cartes Glassmorphism */
    .card {{ 
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        margin-bottom: 5px; 
        overflow: hidden; 
        height: 280px; 
        transition: all 0.3s ease;
    }}
    .card:hover {{ border-color: #c1002c; transform: translateY(-5px); }}
    .card-img {{ width: 100%; height: 140px; object-fit: cover; opacity: 0.8; }}
    .card-body {{ padding: 15px; }}
    .card-source {{ color: #c1002c !important; font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }}
    .card-title {{ font-size: 14px; font-weight: 700; line-height: 1.3; color: #ffffff !important; height: 38px; overflow: hidden; }}
    
    /* Boutons Streamlit */
    button[kind="primary"] {{ background-color: #c1002c !important; border: none !important; }}
    button[kind="secondary"] {{ background: rgba(255,255,255,0.05) !important; color: white !important; border: 1px solid rgba(255,255,255,0.1) !important; }}
    
    /* Style de la Pop-up */
    div[data-testid="stDialog"] {{ background-color: #0a0a0a !important; border: 1px solid #c1002c !important; border-radius: 15px; }}
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
    "VCG (Vieux Con Gaming)": "https://www.youtube.com/feeds/videos.xml?channel_id=UCjrj3gdo-KL2S_JN_gdNyPw",
    "Hardware Canucks": "https://www.youtube.com/feeds/videos.xml?channel_id=UCVn2OUZWZ0V7xC7n0z7nK0w",
    "Mr Matt Lee": "https://www.youtube.com/feeds/videos.xml?channel_id=UCbLTf6hZpZkY7kC3Y7x5L9A",
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
                    img = "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800"
                    if is_youtube:
                        v_id = entry.link.split("v=")[1].split("&")[0] if "v=" in entry.link else entry.id.split(":")[-1]
                        img = f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg"
                        summary = "Cette vidéo traite des dernières actualités hardware. Cliquez sur le bouton pour la visionner."
                    else:
                        if 'media_content' in entry: img = entry.media_content[0]['url']
                        summary = re.sub('<[^<]+?>', '', entry.get("summary", ""))
                    all_data.append({"source": name, "title": entry.title, "link": entry.link, "date": dt, "image": img, "summary": summary, "is_video": is_youtube})
                except: continue
        except: continue
    return pd.DataFrame(all_data).sort_values(by="date", ascending=False) if all_data else pd.DataFrame()

# --- FONCTION POP-UP ---
@st.dialog("Synthèse de l'article")
def show_details(item):
    st.image(item['image'], use_container_width=True)
    st.subheader(item['title'])
    st.markdown(f"**Source :** {item['source']} | **Publié le :** {item['date'].strftime('%d/%m/%Y')}")
    st.divider()
    
    # Simulation de résumé intelligent
    st.markdown("### 📝 Résumé Rapide")
    content = item['summary']
    if len(content) > 100:
        # On affiche le texte de manière plus aérée
        st.info(f"Analyse de l'article : {content[:500]}...")
    else:
        st.write(content)
        
    st.write("")
    st.link_button("VOIR L'ARTICLE COMPLET", item['link'], type="primary", use_container_width=True)

# --- UI ---
st.title("Revue de presse Tech")

if 'selection' not in st.session_state: st.session_state.selection = 'Articles'

c1, c2, _ = st.columns([1.2, 1.2, 4])
if c1.button("ARTICLES PRESSE", type="primary" if st.session_state.selection == 'Articles' else "secondary", use_container_width=True):
    st.session_state.selection = 'Articles'; st.rerun()
if c2.button("VIDEOS YOUTUBE", type="primary" if st.session_state.selection == 'Videos' else "secondary", use_container_width=True):
    st.session_state.selection = 'Videos'; st.rerun()

st.divider()

df = fetch_content(RSS_FEEDS if st.session_state.selection == 'Articles' else YOUTUBE_CHANNELS, is_youtube=(st.session_state.selection == 'Videos'))

if not df.empty:
    cols = st.columns(4)
    for idx, row in df.reset_index().iterrows():
        with cols[idx % 4]:
            st.markdown(f"""
                <div class="card">
                    <img src="{row['image']}" class="card-img">
                    <div class="card-body">
                        <div class="card-source">{row['source']}</div>
                        <div class="card-title">{row['title']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Lire la synthèse", key=f"btn_{idx}", use_container_width=True):
                show_details(row)
else:
    st.info("Chargement des actus...")
