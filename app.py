import streamlit as st
import feedparser
from datetime import datetime, timedelta
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Hardware News Hub", page_icon="🖥️", layout="wide")

# Liste des flux RSS ciblés
RSS_FEEDS = {
    "TechPowerUp (Global)": "https://www.techpowerup.com/rss/news",
    "Hardware & Co (FR)": "https://hardwareand.co/actualites?format=feed&type=rss",
    "Hardware.fr (FR)": "https://www.hardware.fr/backend/news.xml",
    "Frandroid - Computing (FR)": "https://www.frandroid.com/produits/pc-ordinateurs/feed",
    "Les Numériques - Informatique (FR)": "https://www.lesnumeriques.com/informatique/rss.xml",
    "Gamers Nexus (Global)": "https://www.gamersnexus.net/rss.xml"
}

@st.cache_data(ttl=3600)  # Rafraîchissement automatique toutes les heures
def fetch_news():
    all_entries = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # Gestion des différents formats de date RSS
                dt = datetime(*entry.published_parsed[:6])
                all_entries.append({
                    "source": source,
                    "title": entry.title,
                    "link": entry.link,
                    "date": dt,
                    "summary": entry.get("summary", "Pas de description disponible.")[:250] + "..."
                })
        except Exception as e:
            st.warning(f"Impossible de lire le flux {source}")
    
    df = pd.DataFrame(all_entries)
    if not df.empty:
        df = df.sort_values(by="date", ascending=False)
    return df

# --- INTERFACE ---
st.title("🖥️ Revue Hardware & Composants")
st.markdown(f"*Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}*")

df = fetch_news()

if df.empty:
    st.error("Aucune donnée récupérée. Vérifiez votre connexion ou les flux RSS.")
else:
    # --- LOGIQUE DE NAVIGATION ---
    st.sidebar.header("📂 Archives & Filtres")
    
    # Sélecteur par tranches de 3 jours
    max_date = df['date'].max()
    min_date = df['date'].min()
    
    # Création des périodes
    periods = []
    current_end = max_date
    while current_end >= min_date:
        current_start = current_end - timedelta(days=3)
        label = f"Du {current_start.strftime('%d/%m')} au {current_end.strftime('%d/%m/%Y')}"
        periods.append((label, current_start, current_end))
        current_end = current_start

    selected_period_label = st.sidebar.selectbox("Période (3 jours) :", [p[0] for p in periods])
    selected_period = next(p for p in periods if p[0] == selected_period_label)

    # Filtrage par source
    sources_dispos = ["Toutes"] + list(df['source'].unique())
    selected_source = st.sidebar.selectbox("Filtrer par source :", sources_dispos)

    # Application des filtres
    mask = (df['date'] >= selected_period[1]) & (df['date'] <= selected_period[2])
    if selected_source != "Toutes":
        mask = mask & (df['source'] == selected_source)
    
    final_df = df[mask]

    # --- AFFICHAGE ---
    st.info(f"Affichage de **{len(final_df)}** articles pour la période sélectionnée.")

    for _, row in final_df.iterrows():
        with st.expander(f"{row['date'].strftime('%H:%M')} | {row['source']} : {row['title']}", expanded=True):
            st.markdown(f"### [{row['title']}]({row['link']})")
            st.write(row['summary'])
            st.markdown(f"**[🔗 Lire l'article sur {row['source']}]({row['link']})**")

# Style CSS personnalisé pour épurer l'interface
st.markdown("""
    <style>
    .stExpander { border: 1px solid #e6e9ef; border-radius: 10px; margin-bottom: 10px; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)