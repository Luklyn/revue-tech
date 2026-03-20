import streamlit as st
import feedparser
from datetime import datetime, timedelta
import pandas as pd
import re
import urllib.request

# Configuration
st.set_page_config(page_title="Hardware Hub", page_icon="🖥️", layout="wide")

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
    "VCG (Vieux Con Gaming)": "https://www.youtube.com/feeds/videos.xml?channel_id=UCs6m0wUQfQSdCrGYbtxB1Kw",
    "Hardware Canucks": "https://www.youtube.com/feeds/videos.xml?channel_id=UCVn2OUZWZ0V7xC7n0z7nK0w",
    "Mr Matt Lee": "https://www.youtube.com/feeds/videos.xml?channel_id=UCbLTf6hZpZkY7kC3Y7x5L9A",
    "Hardware Unboxed": "https://www.youtube.com/feeds/videos.xml?channel_id=UCI8iQa1hv7oV_Z8D35vVuSg"
}

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?q=80&w=400&auto=format&fit=crop"

# --- LOGIQUE RÉCUPÉRATION (Blindée) ---
@st.cache_data(ttl=600) # Rafraîchissement toutes les 10 min
def fetch_content(source_dict, is_youtube=False):
    all_data = []
    # User-Agent pour YouTube
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    for name, url in source_dict.items():
        try:
            # Récupération manuelle pour contourner le blocage robot
            if is_youtube:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    content = response.read()
                feed = feedparser.parse(content)
            else:
                feed = feedparser.parse(url)
            
            if not feed.entries: continue
                
            for entry in feed.entries:
                try:
                    dt = datetime(*entry.published_parsed[:6])
                    
                    if is_youtube:
                        # Extraction ID vidéo
                        v_id = entry.link.split("v=")[1].split("&")[0] if "v=" in entry.link else entry.id.split(":")[-1]
                        img = f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg"
                        # Pas de résumé pour les vidéos
                        summary = ""
                    else:
                        # Extraction image Presse
                        img = DEFAULT_IMAGE
                        if 'media_content' in entry: img = entry.media_content[0]['url']
                        elif 'links' in entry:
                            for l in entry.links:
                                if 'image' in l.get('type', ''): img = l.href
                        # Résumé court (2 lignes max)
                        summary = re.sub('<[^<]+?>', '', entry.get("summary", ""))[:120] + "..."

                    all_data.append({
                        "source": name, "title": entry.title, "link": entry.link, 
                        "date": dt, "image": img, "summary": summary, "is_video": is_youtube
                    })
                except: continue
        except:
            st.sidebar.warning(f"Impossible de joindre {name}")
            
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
    latest = df['date'].max()
    limit = latest - timedelta(days=3)
    
    show_all = st.sidebar.checkbox("Voir toutes les archives", value=False)
    if not show_all:
        df = df[df['date'] >= limit]
        st.sidebar.caption(f"News depuis le {limit.strftime('%d/%m')}")

    search = st.sidebar.text_input("🔍 Rechercher...").lower()
    if search:
        df = df[df['title'].str.lower().str.contains(search)]

# --- NOUVEAU STYLE CSS COMPACT ---
st.markdown("""
    <style>
    /* Carte plus compacte */
    .card { 
        background: white; 
        border-radius: 8px; /* Bords moins arrondis */
        margin-bottom: 15px; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); /* Ombre plus légère */
        overflow: hidden; 
        height: 290px; /* Hauteur totale réduite (au lieu de 320px) */
        transition: transform 0.2s;
    }
    .card:hover { transform: translateY(-2px); } /* Animation plus discrète */
    
    /* Image */
    .card-img { width: 100%; height: 140px; object-fit: cover; background: #222; }
    
    /* Corps du texte - MOINS DE PADDING */
    .card-body { 
        padding: 8px; /* Padding réduit de moitié (au lieu de 15px) */
    }
    
    /* Source (Gamers Nexus...) */
    .card-source { 
        color: #ff4b4b; 
        font-size: 0.65rem; /* Plus petit */
        font-weight: bold; 
        text-transform: uppercase;
        margin-bottom: 2px;
    }
    
    /* Titre - PLUS COMPACT */
    .card-title { 
        font-size: 0.85rem; /* Plus petit */
        font-weight: 600; 
        margin: 3px 0; 
        height: 2.5em; /* Bloqué à 2 lignes au lieu de 3.5 */
        overflow: hidden; 
        line-height: 1.2; /* Interligne serré */
    }
    .card-title a { text-decoration: none; color: #333; }
    
    /* Résumé (Seulement Presse) */
    .card-summary {
        font-size: 0.75rem;
        color: #666;
        height: 2.6em; /* Bloqué à 2 lignes de résumé */
        overflow: hidden;
        line-height: 1.3;
        margin-bottom: 5px;
    }
    
    /* Date */
    .card-date {
        font-size: 0.65rem;
        color: #888;
    }
    </style>
""", unsafe_allow_html=True)

# --- AFFICHAGE EN GRILLE (4 COLONNES) ---
if df.empty:
    st.warning("Aucun contenu trouvé.")
else:
    cols = st.columns(4)
    for idx, row in df.reset_index().iterrows():
        with cols[idx % 4]:
            # Construction dynamique du contenu de la carte
            summary_html = f'<div class="card-summary">{row["summary"]}</div>' if not row["is_video"] else ""
            
            st.markdown(f"""
                <div class="card">
                    <img src="{row['image']}" class="card-img">
                    <div class="card-body">
                        <div class="card-source">{row['source']}</div>
                        <div class="card-title"><a href="{row['link']}" target="_blank">{row['title']}</a></div>
                        {summary_html}
                        <div class="card-date">📅 {row['date'].strftime('%d/%m à %H:%M')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
