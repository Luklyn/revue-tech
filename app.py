import streamlit as st
import feedparser
from datetime import datetime, timedelta
import pandas as pd
import re

# Configuration de la page
st.set_page_config(page_title="Hardware News Hub", page_icon="🖥️", layout="wide")

# Liste des flux RSS ciblés
RSS_FEEDS = {
    "TechPowerUp": "https://www.techpowerup.com/rss/news",
    "Hardware & Co": "https://hardwareand.co/actualites?format=feed&type=rss",
    "Hardware.fr": "https://www.hardware.fr/backend/news.xml",
    "Frandroid": "https://www.frandroid.com/produits/pc-ordinateurs/feed",
    "Les Numériques": "https://www.lesnumeriques.com/informatique/rss.xml",
    "Gamers Nexus": "https://www.gamersnexus.net/rss.xml"
}

# Image par défaut si aucune image n'est trouvée dans l'article
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1591799264318-7e698ddb7c1d?q=80&w=400&auto=format&fit=crop" # Image de CPU standard

def extract_image(entry):
    """Tente d'extraire une image du flux RSS"""
    # Méthode 1: Dans les "links"
    if 'links' in entry:
        for link in entry.links:
            if 'image' in link.type or 'enclosure' in link.rel:
                return link.href
    
    # Méthode 2: Dans la description (balise <img>)
    if 'summary' in entry:
        html_content = entry.summary
        image_match = re.search(r'<img [^>]*src=["\']([^"\']+)["\']', html_content)
        if image_match:
            return image_match.group(1)
            
    # Méthode 3: Spécifique à certains flux (comme media:content)
    if 'media_content' in entry:
        return entry.media_content[0]['url']

    return DEFAULT_IMAGE

@st.cache_data(ttl=3600)  # Rafraîchissement toutes les heures
def fetch_news():
    all_entries = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                try:
                    dt = datetime(*entry.published_parsed[:6])
                    img_url = extract_image(entry)
                    
                    # Nettoyage du sommaire (enlève le HTML)
                    summary = entry.get("summary", "Pas de description.")
                    summary_clean = re.sub('<[^<]+?>', '', summary)[:180] + "..."

                    all_entries.append({
                        "source": source,
                        "title": entry.title,
                        "link": entry.link,
                        "date": dt,
                        "image": img_url,
                        "summary": summary_clean
                    })
                except: continue
        except:
            st.warning(f"Impossible de lire le flux {source}")
    
    df = pd.DataFrame(all_entries)
    if not df.empty:
        df = df.sort_values(by="date", ascending=False)
    return df

# --- STYLE CSS (Pour les Cartes) ---
st.markdown("""
<style>
    /* Style global */
    .stApp { background-color: #f4f7f6; }
    
    /* Style de la carte */
    .news-card {
        background-color: white;
        border-radius: 15px;
        padding: 0px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s;
        overflow: hidden; /* Pour que l'image respecte les bords arrondis */
    }
    .news-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.15);
    }
    
    /* Conteneur de l'image */
    .card-image-container {
        width: 100%;
        height: 180px; /* Hauteur fixe pour l'image */
        overflow: hidden;
    }
    .card-image {
        width: 100%;
        height: 100%;
        object-fit: cover; /* L'image remplit la zone sans se déformer */
    }
    
    /* Contenu texte de la carte */
    .card-content {
        padding: 15px;
    }
    .card-source {
        color: #ff4b4b;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.8rem;
        margin-bottom: 5px;
    }
    .card-date {
        color: #666;
        font-size: 0.8rem;
        margin-bottom: 10px;
    }
    .card-title {
        font-size: 1.1rem !important;
        font-weight: 600;
        line-height: 1.3;
        margin-bottom: 10px;
        height: 2.6em; /* Limite à 2 lignes de titre */
        overflow: hidden;
    }
    .card-title a {
        text-decoration: none;
        color: #1f1f1f;
    }
    .card-title a:hover { color: #ff4b4b; }
    
    .card-summary {
        color: #4f4f4f;
        font-size: 0.9rem;
        line-height: 1.4;
        height: 4.2em; /* Limite à 3 lignes de résumé */
        overflow: hidden;
        margin-bottom: 15px;
    }
    
    /* Masquer le footer Streamlit */
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- INTERFACE ---
st.title("🛰️ Le Hub Hardware")
st.markdown("L'actualité informatique simplifiée, mise à jour toutes les heures.")

df = fetch_news()

if df.empty:
    st.error("Aucune donnée récupérée.")
else:
    # --- LOGIQUE DE NAVIGATION (Sidebar) ---
    st.sidebar.header("📂 Archives & Filtres")
    
    # Sélecteur de période (tranches de 3 jours)
    max_date = df['date'].max()
    min_date = df['date'].min()
    periods = []
    current_end = max_date
    while current_end >= min_date:
        current_start = current_end - timedelta(days=3)
        label = f"Du {current_start.strftime('%d/%m')} au {current_end.strftime('%d/%m/%Y')}"
        periods.append((label, current_start, current_end))
        current_end = current_start

    selected_period_label = st.sidebar.selectbox("📅 Période :", [p[0] for p in periods])
    selected_period = next(p for p in periods if p[0] == selected_period_label)

    # Filtrage par source
    sources_dispos = ["Toutes"] + list(df['source'].unique())
    selected_source = st.sidebar.selectbox("🔍 Source :", sources_dispos)

    # Recherche par mot-clé (Ajout pour le côté néophyte)
    search_term = st.sidebar.text_input("🔤 Rechercher (ex: RTX 5080) :").lower()

    # Application des filtres
    mask = (df['date'] >= selected_period[1]) & (df['date'] <= selected_period[2])
    if selected_source != "Toutes":
        mask = mask & (df['source'] == selected_source)
    
    final_df = df[mask]
    
    if search_term:
        final_df = final_df[final_df['title'].str.lower().str.contains(search_term) | 
                           final_df['summary'].str.lower().str.contains(search_term)]

    # --- AFFICHAGE EN GRILLE ---
    st.markdown(f"**{len(final_df)} articles** trouvés pour cette période.")

    # Création de colonnes (3 cartes par ligne sur PC)
    cols = st.columns(3)
    col_idx = 0

    for _, row in final_df.iterrows():
        # Construction de la carte en HTML
        card_html = f"""
        <div class="news-card">
            <div class="card-image-container">
                <img src="{row['image']}" class="card-image" alt="Image de l'article">
            </div>
            <div class="card-content">
                <div class="card-source">{row['source']}</div>
                <div class="card-date">📅 {row['date'].strftime('%d/%m/%Y à %H:%M')}</div>
                <div class="card-title">
                    <a href="{row['link']}" target="_blank">{row['title']}</a>
                </div>
                <div class="card-summary">{row['summary']}</div>
                <a href="{row['link']}" target="_blank" style="color: #ff4b4b; font-weight: bold; text-decoration: none;">
                    Lire l'article complet ➔
                </a>
            </div>
        </div>
        """
        # Affichage de la carte dans la colonne correspondante
        cols[col_idx % 3].markdown(card_html, unsafe_allow_html=True)
        col_idx += 1
