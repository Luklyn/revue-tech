import streamlit as st
import feedparser
from datetime import datetime, timedelta
import pandas as pd
import re
import urllib.request

# Configuration de la page
st.set_page_config(page_title="Tech Briefing", page_icon="🖥️", layout="wide")

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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
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
                    
                    all_data.append({
                        "source": name, 
                        "title": entry.title, 
                        "link": entry.link, 
                        "date": dt, 
                        "image": img, 
                        "summary": summary, 
                        "is_video": is_youtube
                    })
                except: continue
        except: continue
    
    return pd.DataFrame(all_data).sort_values(by="date", ascending=False) if all_data else pd.DataFrame()

# --- DESIGN CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #ffffff;
    }

    header {visibility: hidden;}
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #eee;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-weight: 600;
        font-size: 16px;
        color: #888;
    }
    .stTabs [aria-selected="true"] {
        color: #111 !important;
        border-bottom-color: #111 !important;
    }

    .card {
        background: #fff;
        border: 1px solid #efefef;
        border-radius: 4px;
        margin-bottom: 20px;
        overflow: hidden;
        height: 310px;
        transition: all 0.2s ease;
    }
    .card:hover {
        border-color: #bbb;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .card-img {
        width: 100%;
        height: 160px;
        object-fit: cover;
    }
    .card-body { padding: 12px; }
    .card-source {
        color: #111;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .card-title {
        font-size: 14px;
        font-weight: 600;
        line-height: 1.4;
        margin-bottom: 8px;
        height: 40px;
        overflow: hidden;
    }
    .card-title a { text-decoration: none; color: #111; }
    
    .card-summary {
        font-size: 13px;
        color: #666;
        line-height: 1.4;
        height: 38px;
        overflow: hidden;
    }
    .card-date {
        font-size: 11px;
        color: #999;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- APPLICATION ---
st.title("Tech Briefing")
tab_presse, tab_video = st.tabs(["Articles", "Vidéos YouTube"])

search = st.sidebar.text_input("Rechercher un sujet").lower()

with tab_presse:
    df_p = fetch_content(RSS_FEEDS)
    if not df_p.empty:
        if search: df_p = df_p[df_p['title'].str.lower().str.contains(search)]
        
        cols = st.columns(4)
        for idx, row in df_p.reset_index().iterrows():
            with cols[idx % 4]:
                st.markdown(f"""
                    <div class="card">
                        <img src="{row['image']}" class="card-img">
                        <div class="card-body">
                            <div class="card-source">{row['source']}</div>
                            <div class="card-title"><a href="{row['link']}" target="_blank">{row['title']}</a></div>
                            <div class="card-summary">{row['summary']}</div>
                            <div class="card-date">{row['date'].strftime('%d %b %Y')}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

with tab_video:
    df_v = fetch_content(YOUTUBE_CHANNELS, is_youtube=True)
    if not df_v.empty:
        if search: df_v = df_v[df_v['title'].str.lower().str.contains(search)]
        
        cols = st.columns(4)
        for idx, row in df_v.reset_index().iterrows():
            with cols[idx % 4]:
                st.markdown(f"""
                    <div class="card">
                        <img src="{row['image']}" class="card-img">
                        <div class="card-body">
                            <div class="card-source">{row['source']}</div>
                            <div class="card-title"><a href="{row['link']}" target="_blank">{row['title']}</a></div>
                            <div class="card-date">{row['date'].strftime('%d %b %Y')}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
