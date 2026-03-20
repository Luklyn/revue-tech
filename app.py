import streamlit as st
import feedparser
from datetime import datetime
import pandas as pd
import re
import urllib.request

# Configuration Responsive
st.set_page_config(page_title="Revue de presse Tech", page_icon="🖥️", layout="wide")

# --- DESIGN RESPONSIVE & NAVBAR (CSS CUSTOM) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* Fond et suppression des marges inutiles */
    .stApp {{ background-color: #000000 !important; }}
    [data-testid="stAppViewContainer"] {{ background-color: #000000 !important; padding-top: 1rem; }}
    header {{visibility: hidden;}}
    
    /* Style des titres et textes */
    h1 {{ color: #ffffff !important; font-family: 'Inter', sans-serif !important; font-size: 1.8rem !important; margin-bottom: 1.5rem; }}

    /* Cartes Glassmorphism */
    .card {{ 
        background: rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        margin-bottom: 20px; 
        overflow: hidden; 
        height: 320px; 
        transition: transform 0.3s ease, border-color 0.3s ease;
    }}
    .card:hover {{ 
        border-color: #c1002c; 
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.1);
    }}
    .card-img {{ width: 100%; height: 150px; object-fit: cover; border-bottom: 1px solid rgba(255,255,255,0.05); }}
    .card-body {{ padding: 15px; }}
    .card-source {{ color: #c1002c !important; font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }}
    .card-title a {{ text-decoration: none; color: #ffffff !important; font-size: 14px; font-weight: 700; line-height: 1.3; }}
    .card-summary {{ font-size: 12px; color: #aaaaaa !important; margin-top: 8px; line-height: 1.4; height: 34px; overflow: hidden; }}
    .card-date {{ font-size: 10px; color: #555555; margin-top: 10px; }}

    /* Ajustement Responsive des colonnes Streamlit */
    [data-testid="stHorizontalBlock"] {{
        align-items: center;
    }}

    /* Boutons de la Navbar */
    button[kind="primary"] {{ background-color: #c1002c !important; border: none !important; color: white !important; }}
    button[kind="secondary"] {{ background: rgba(255,255,255,0.08) !important; color: white !important; border: 1px solid rgba(255,255,255,0.1) !important; }}
    
    /* Input de recherche */
    .stTextInput>div>div>input {{
        background-color: rgba(255,255,255,0.05) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 20px !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- LOGIQUE DE DONNÉES ---
RSS_FEEDS = {{
    "TechPowerUp": "https://www.techpowerup.com/rss/news",
    "Hardware & Co": "https://hardwareand.co/actualites?format=feed&type=rss",
    "Hardware.fr": "https://www.hardware.fr/backend/news.xml",
    "Frandroid": "https://www.frandroid.com/produits/pc-ordinateurs/feed",
    "Les Numériques": "https://www.lesnumeriques.com/informatique/rss.xml",
}}

@st.cache_data(ttl=600)
def fetch_data(source_dict):
    all_data = []
    headers = {{'User-Agent': 'Mozilla/5.0'}}
    for name, url in source_dict.items():
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                feed = feedparser.parse(response.read())
            for entry in feed.entries:
                try:
                    dt = datetime(*entry.published_parsed[:6])
                    img = "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800"
                    if 'media_content' in entry: img = entry.media_content[0]['url']
                    summary = re.sub('<[^<]+?>', '', entry.get("summary", ""))[:100] + "..."
                    all_data.append({{"source": name, "title": entry.title, "link": entry.link, "date": dt, "image": img, "summary": summary}})
                except: continue
        except: continue
    return pd.DataFrame(all_data).sort_values(by="date", ascending=False) if all_data else pd.DataFrame()

# --- NAVBAR UNIFIÉE ---
# Ligne 1 : Titre + Recherche
top_col1, top_col2 = st.columns([2, 1])
with top_col1:
    st.title("Revue de presse Tech")
with top_col2:
    search_query = st.text_input("", placeholder="Rechercher...", label_visibility="collapsed")

# Ligne 2 : Univers / Catégories (Responsive via colonnes multiples)
if 'cat' not in st.session_state: st.session_state.cat = "TOUT"

# On utilise plus de colonnes pour un effet "barre de menu"
menu_cols = st.columns([1, 1.2, 1, 1.2, 1, 1, 1])
cats = ["TOUT", "HARDWARE", "PC", "MOBILE", "GAMING", "IA"]

for i, c_name in enumerate(cats):
    if menu_cols[i].button(c_name, type="primary" if st.session_state.cat == c_name else "secondary", use_container_width=True):
        st.session_state.cat = c_name
        st.rerun()

st.divider()

# --- FILTRAGE ET AFFICHAGE ---
df = fetch_data(RSS_FEEDS)

if not df.empty:
    # Filtre Recherche
    if search_query:
        df = df[df['title'].str.lower().str.contains(search_query.lower())]
    
    # Filtre Univers
    if st.session_state.cat != "TOUT":
        keywords = {{
            "HARDWARE": "cpu|gpu|nvidia|intel|amd|ryzen|rtx|carte mère|ssd",
            "PC": "ordinateur|laptop|clavier|souris|windows|macbook|dell|asus",
            "MOBILE": "iphone|smartphone|android|samsung|pixel|mobile|ios",
            "GAMING": "jeu|ps5|xbox|nintendo|console|steam|gaming",
            "IA": "ia|ai|chatgpt|openai|gemini|llm|intelligence"
        }}
        df = df[df['title'].str.lower().str.contains(keywords.get(st.session_state.cat, ""))]

    # Grille Responsive (4 colonnes sur PC, Streamlit gère la réduction sur mobile)
    if not df.empty:
        grid_cols = st.columns(4)
        for idx, row in df.reset_index().iterrows():
            with grid_cols[idx % 4]:
                st.markdown(f"""
                    <div class="card">
                        <img src="{{row['image']}}" class="card-img">
                        <div class="card-body">
                            <div class="card-source">{{row['source']}}</div>
                            <div class="card-title"><a href="{{row['link']}}" target="_blank">{{row['title']}}</a></div>
                            <div class="card-summary">{{row['summary']}}</div>
                            <div class="card-date">Publié le {{row['date'].strftime('%d/%m/%Y')}}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Aucun résultat pour cette sélection.")
else:
    st.error("Impossible de charger les flux RSS.")
