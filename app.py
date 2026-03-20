import streamlit as st
import feedparser
from datetime import datetime, timedelta
import pandas as pd
import re
import urllib.request

# Configuration
st.set_page_config(page_title="Revue de presse Tech", page_icon="🖥️", layout="wide")

# Style CSS (Fond noir + Glassmorphism + Correction Couleurs)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp {{
        background-color: #000000 !important;
        --primary-color: #c1002c;
    }}
    
    [data-testid="stAppViewContainer"] {{ background-color: #000000 !important; }}
    header {{visibility: hidden;}}
    h1, h2, h3, p, span, label {{ color: #ffffff !important; font-family: 'Inter', sans-serif !important; }}

    /* Cartes Glassmorphism */
    .card {{ 
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        margin-bottom: 10px; 
        overflow: hidden; 
        height: 280px; /* Réduit pour laisser de la place au bouton Streamlit dessous */
        transition: all 0.3s ease;
    }}
    
    .card-img {{ width: 100%; height: 140px; object-fit: cover; opacity: 0.9; }}
    .card-body {{ padding: 12px; }}
    .card-source {{ color: #c1002c !important; font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }}
    .card-title {{ font-size: 14px; font-weight: 700; line-height: 1.3; color: #ffffff !important; height: 38px; overflow: hidden; margin-bottom: 5px; }}
    .card-summary {{ font-size: 12px; color: #bbbbbb !important; line-height: 1.4; height: 34px; overflow: hidden; }}

    /* Boutons personnalisés */
    button[kind="primary"] {{ background-color: #c1002c !important; border: none !important; }}
    button[kind="secondary"] {{ background: rgba(255,255,255,0.1) !important; color: white !important; border: 1px solid rgba(255,255,255,0.2) !important; }}
    </style>
""", unsafe_allow_html=True)

# --- FONCTION POP-UP (MODALE) ---
@st.dialog("Détails de l'actualité", width="large")
def show_details(item):
    st.image(item['image'], use_container_width=True)
    st.subheader(item['title'])
    st.write(f"**Source :** {item['source']} | **Date :** {item['date'].strftime('%d %b %Y')}")
    st.markdown("---")
    # Simulation d'un résumé plus long (le flux RSS est souvent limité)
    st.write(item['summary'] if item['summary'] else "Pas de résumé additionnel disponible pour cette vidéo.")
    st.write("")
    st.link_button("VOIR L'ARTICLE COMPLET", item['link'], type="primary", use_container_width=True)

# --- RÉCUPÉRATION DES DONNÉES ---
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
                        summary = "Résumé vidéo non disponible via flux RSS."
                    else:
                        img = "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800"
                        if 'media_content' in entry: img = entry.media_content[0]['url']
                        summary = re.sub('<[^<]+?>', '', entry.get("summary", ""))[:300] + "..."
                    all_data.append({"source": name, "title": entry.title, "link": entry.link, "date": dt, "image": img, "summary": summary, "is_video": is_youtube})
                except: continue
        except: continue
    return pd.DataFrame(all_data).sort_values(by="date", ascending=False) if all_data else pd.DataFrame()

# --- INTERFACE ---
st.title("Revue de presse Tech")

if 'menu' not in st.session_state: st.session_state.menu = 'Articles'

c1, c2, _ = st.columns([1.2, 1.2, 4])
if c1.button("ARTICLES PRESSE", type="primary" if st.session_state.menu == 'Articles' else "secondary", use_container_width=True):
    st.session_state.menu = 'Articles'; st.rerun()
if c2.button("VIDEOS YOUTUBE", type="primary" if st.session_state.menu == 'Videos' else "secondary", use_container_width=True):
    st.session_state.menu = 'Videos'; st.rerun()

st.divider()

# Sources
RSS_FEEDS = {"TechPowerUp": "...", "Frandroid": "...", "Hardware.fr": "..."} # (Garder tes URLs ici)
# Note : Pour l'exemple j'utilise tes dictionnaires précédents
YOUTUBE_CHANNELS = {"Gamers Nexus": "...", "Hardware Unboxed": "..."} 

df = fetch_content(RSS_FEEDS if st.session_state.menu == 'Articles' else YOUTUBE_CHANNELS, is_youtube=(st.session_state.menu == 'Videos'))

if not df.empty:
    cols = st.columns(4)
    for idx, row in df.reset_index().iterrows():
        with cols[idx % 4]:
            # Carte visuelle
            st.markdown(f"""
                <div class="card">
                    <img src="{row['image']}" class="card-img">
                    <div class="card-body">
                        <div class="card-source">{row['source']}</div>
                        <div class="card-title">{row['title']}</div>
                        <div class="card-summary">{row['summary'][:80]}...</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Bouton de déclenchement de la Pop-up
            if st.button("Lire le résumé", key=f"btn_{idx}", use_container_width=True):
                show_details(row)
else:
    st.info("Chargement...")
