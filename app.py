import streamlit as st
import feedparser
from datetime import datetime
import pandas as pd
import re
import urllib.request

# Configuration
st.set_page_config(page_title="Hardware Briefing", layout="wide")

# --- SOURCES (Inchangées) ---
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
                        img = "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400"
                        summary = re.sub('<[^<]+?>', '', entry.get("summary", ""))[:110] + "..."
                    all_data.append({"source": name, "title": entry.title, "link": entry.link, "date": dt, "image": img, "summary": summary, "is_video": is_youtube})
                except: continue
        except: continue
    return pd.DataFrame(all_data).sort_values(by="date", ascending=False) if not pd.DataFrame(all_data).empty else pd.DataFrame()

# --- STYLE CSS (LISIBILITÉ MAXIMALE) ---
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #111 !important; }
    header {visibility: hidden;}
    .stCheckbox label p { font-size: 1.2rem !important; font-weight: 600 !important; color: #111 !important; }
    .card { background: #fff; border: 1px solid #eee; border-radius: 4px; margin-bottom: 20px; height: 310px; overflow: hidden; }
    .card-img { width: 100%; height: 160px; object-fit: cover; }
    .card-body { padding: 12px; }
    .card-source { color: #111; font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .card-title a { text-decoration: none; color: #111 !important; font-size: 14px; font-weight: 600; }
    .card-summary { font-size: 13px; color: #444; margin-top: 5px; }
    .card-date { font-size: 11px; color: #999; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
st.title("Hardware Briefing")

# Un toggle simple intégré à Streamlit
mode_video = st.toggle("Activer le mode Vidéos YouTube", value=False)

search = st.sidebar.text_input("Rechercher").lower()

if mode_video:
    st.subheader("Vidéos YouTube")
    df = fetch_content(YOUTUBE_CHANNELS, is_youtube=True)
else:
    st.subheader("Articles de Presse")
    df = fetch_content(RSS_FEEDS)

if not df.empty:
    if search: df = df[df['title'].str.lower().str.contains(search)]
    cols = st.columns(4)
    for idx, row in df.reset_index().iterrows():
        with cols[idx % 4]:
            sum_div = f'<div class="card-summary">{row["summary"]}</div>' if not row["is_video"] else ""
            st.markdown(f"""
                <div class="card">
                    <img src="{row['image']}" class="card-img">
                    <div class="card-body">
                        <div class="card-source">{row['source']}</div>
                        <div class="card-title"><a href="{row['link']}" target="_blank">{row['title']}</a></div>
                        {sum_div}
                        <div class="card-date">{row['date'].strftime('%d %b %Y')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
