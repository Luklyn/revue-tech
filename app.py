import streamlit as st
import feedparser
from datetime import datetime
import pandas as pd
import re
import urllib.request

# Configuration
st.set_page_config(page_title="Revue de presse Tech", page_icon="🖥️", layout="wide")

# V3 - Style CSS complet avec ajustements pour la Sidebar
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    /* Forcer le thème sombre */
    .stApp {
        --primary-color: #c1002c;
        background-color: #000000 !important;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #000000 !important;
    }
    header {visibility: hidden;}

    /* Boutons de navigation (Articles / Vidéos) */
    div.stButton > button:first-child {
        border-radius: 4px;
        font-weight: 600;
    }
    button[kind="primary"] {
        background-color: #c1002c !important;
        border-color: #c1002c !important;
        color: white !important;
    }

    h1 {
        color: #ffffff !important;
        font-weight: 800;
        letter-spacing: -1px;
    }

    /* Cartes Glassmorphism */
    .card { 
        background: rgba(255, 255, 255, 0.05); 
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        margin-bottom: 20px; 
        overflow: hidden; 
        height: 330px; 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .card:hover { 
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(193, 0, 44, 0.6); 
        transform: translateY(-8px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.5);
    }
    
    .card-img { width: 100%; height: 160px; object-fit: cover; opacity: 0.85; transition: 0.3s; }
    .card:hover .card-img { opacity: 1; transform: scale(1.05); }
    
    .card-body { padding: 15px; }
    .card-source { color: #c1002c; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 8px; }
    .card-title { font-size: 15px; font-weight: 700; line-height: 1.3; margin-bottom: 8px; height: 40px; overflow: hidden; }
    .card-title a { text-decoration: none; color: #ffffff !important; }
    .card-summary { font-size: 13px; color: #999999; line-height: 1.4; height: 38px; overflow: hidden; }
    .card-date { font-size: 10px; color: #555555; margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px; }

    /* Customisation de la Sidebar */
    section[data-testid="stSidebar"] { 
        background-color: #0a0a0a !important; 
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    .stRadio label { font-weight: 600; color: #ffffff !important; }
    
</style>
""", unsafe_allow_html=True)

# Initialisation
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

# --- SIDEBAR : RECHERCHE & FILTRES ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3067/3067260.png", width=50) # Petite icône stylée (optionnelle)
st.sidebar.header("Recherche & Filtres")

# 1. Recherche libre
search_query = st.sidebar.text_input("Recherche libre", placeholder="Ex: RTX 5090...")

st.sidebar.markdown("---")

# 2. Catégories / Univers
st.sidebar.subheader("Univers Tech")
category = st.sidebar.radio(
    "Filtrer par catégorie :",
    ["Toutes les news", "Hardware & Composants", "PC & Laptops", "Smartphones & Mobile", "Gaming", "Intelligence Artificielle"]
)

# --- NAVIGATION PRINCIPALE (HAUT DE PAGE) ---
st.title("Revue de presse Tech")

col_nav1, col_nav2, col_spacer = st.columns([1.2, 1.2, 4])
with col_nav1:
    if st.button("ARTICLES PRESSE", use_container_width=True, type="primary" if st.session_state.menu_selection == 'Articles' else "secondary"):
        st.session_state.menu_selection = 'Articles'
        st.rerun()
with col_nav2:
    if st.button("VIDEOS YOUTUBE", use_container_width=True, type="primary" if st.session_state.menu_selection == 'Videos' else "secondary"):
        st.session_state.menu_selection = 'Videos'
        st.rerun()

st.divider()

# --- RÉCUPÉRATION ET FILTRAGE DES DONNÉES ---
df = fetch_content(RSS_FEEDS if st.session_state.menu_selection == 'Articles' else YOUTUBE_CHANNELS, 
                   is_youtube=(st.session_state.menu_selection == 'Videos'))

if not df.empty:
    
    # Appliquer le filtre de recherche libre
    if search_query:
        # Regex case=False permet de chercher sans se soucier des majuscules/minuscules
        df = df[df['title'].str.contains(search_query, case=False, regex=True, na=False)]
        
    # Appliquer le filtre de catégorie
    if category != "Toutes les news":
        keywords_dict = {
            "Hardware & Composants": "cpu|gpu|nvidia|intel|amd|ryzen|rtx|radeon|carte mère|ssd|ram|processeur",
            "PC & Laptops": "pc|ordinateur|laptop|clavier|souris|windows|macbook|dell|asus|lenovo|écran|moniteur",
            "Smartphones & Mobile": "iphone|smartphone|android|samsung|pixel|mobile|ios|galaxy|xiaomi|honor|apple",
            "Gaming": "jeu|ps5|xbox|nintendo|console|steam|gaming|playstation|switch",
            "Intelligence Artificielle": "ia|ai|chatgpt|openai|gemini|llm|intelligence artificielle|copilot"
        }
        query = keywords_dict.get(category, "")
        df = df[df['title'].str.contains(query, case=False, regex=True, na=False)]

    # --- AFFICHAGE DE LA GRILLE ---
    if not df.empty:
        cols = st.columns(4)
        for idx, row in df.reset_index().iterrows():
            with cols[idx % 4]:
                summary_div = f'<div class="card-summary">{row["summary"]}</div>' if not row["is_video"] else '<div style="height:38px;"></div>'
                st.markdown(f"""
                    <div class="card">
                        <div style="overflow:hidden;"><img src="{row['image']}" class="card-img"></div>
                        <div class="card-body">
                            <div class="card-source">{row['source']}</div>
                            <div class="card-title"><a href="{row['link']}" target="_blank">{row['title']}</a></div>
                            {summary_div}
                            <div class="card-date">Publié le {row['date'].strftime('%d %b %Y')}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.warning(f"Aucune actualité ne correspond à la catégorie '{category}' ou à votre recherche.")
else:
    st.info("Chargement des flux en cours...")
