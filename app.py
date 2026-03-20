import streamlit as st
import feedparser
import requests
from datetime import datetime, timezone
import pandas as pd
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# ─── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Revue de presse Tech", page_icon="🖥️", layout="wide")

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');

:root {
    --red: #c1002c;
    --red-dim: rgba(193,0,44,0.15);
    --surface: rgba(255,255,255,0.06);
    --border: rgba(255,255,255,0.08);
    --text-muted: #888;
    --text-dim: #555;
}

.stApp, [data-testid="stAppViewContainer"] { background: #080808 !important; }
header { visibility: hidden; }

/* Typography */
h1 {
    font-family: 'Syne', sans-serif !important;
    color: #fff !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.5px;
    margin-bottom: 0 !important;
}

/* Inputs */
.stTextInput > div > div > input {
    background: var(--surface) !important;
    color: #fff !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif;
}
.stTextInput > div > div > input:focus {
    border-color: var(--red) !important;
    box-shadow: 0 0 0 2px var(--red-dim) !important;
}
.stSelectbox > div > div > div {
    background: var(--surface) !important;
    color: #fff !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif;
}

/* Nav buttons */
button[kind="primary"] {
    background: var(--red) !important;
    border: none !important;
    color: #fff !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px;
    border-radius: 8px !important;
}
button[kind="secondary"] {
    background: var(--surface) !important;
    color: #aaa !important;
    border: 1px solid var(--border) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
button[kind="secondary"]:hover { color: #fff !important; border-color: rgba(255,255,255,0.3) !important; }

/* Meta bar */
.meta-bar {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 8px;
}
.result-badge {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 12px;
    color: var(--text-muted);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 3px 12px;
}
.refresh-info {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 12px;
    color: var(--text-dim);
    margin-left: auto;
}

/* Cards */
.card {
    background: var(--surface);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 20px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
    cursor: pointer;
}
.card:hover {
    border-color: var(--red);
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(193,0,44,0.15);
}
.card-img-wrap { position: relative; width: 100%; height: 160px; overflow: hidden; background: #111; }
.card-img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform 0.3s ease; }
.card:hover .card-img { transform: scale(1.04); }
.card-img-placeholder {
    width: 100%; height: 160px;
    background: linear-gradient(135deg, #111 0%, #1a1a1a 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 32px; opacity: 0.4;
}
.card-body { padding: 14px 16px 16px; flex: 1; display: flex; flex-direction: column; gap: 6px; }
.card-source {
    font-family: 'Space Grotesk', sans-serif;
    color: var(--red);
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.card-title a {
    font-family: 'Space Grotesk', sans-serif;
    text-decoration: none;
    color: #ffffff !important;
    font-size: 13.5px;
    font-weight: 600;
    line-height: 1.45;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.card-title a:hover { color: #ddd !important; }
.card-summary {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 12px;
    color: #999;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    flex: 1;
}
.card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid var(--border);
    padding-top: 10px;
    margin-top: 4px;
}
.card-date {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 10px;
    color: #777;    /* WCAG AA-compliant sur fond sombre */
    letter-spacing: 0.2px;
}
.card-link-icon { color: var(--text-dim); font-size: 11px; }

/* Empty/error states */
.state-box {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
    font-family: 'Space Grotesk', sans-serif;
}
.state-box .icon { font-size: 40px; margin-bottom: 12px; }
.state-box p { margin: 0; font-size: 15px; }
.state-box small { color: var(--text-dim); font-size: 12px; }

/* Date filter pills */
.filter-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }

/* Divider */
hr { border-color: var(--border) !important; margin: 12px 0 20px !important; }

/* Error banner */
.err-banner {
    background: rgba(193,0,44,0.1);
    border: 1px solid rgba(193,0,44,0.3);
    border-radius: 8px;
    padding: 10px 16px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 12px;
    color: #ff6b6b;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# ─── SOURCES ──────────────────────────────────────────────────────────────────
RSS_FEEDS = {
    "TechPowerUp":  "https://www.techpowerup.com/rss/news",
    "Hardware & Co": "https://hardwareand.co/actualites?format=feed&type=rss",
    "Hardware.fr":  "https://www.hardware.fr/backend/news.xml",
    "Frandroid":    "https://www.frandroid.com/produits/pc-ordinateurs/feed",
    "Les Numériques": "https://www.lesnumeriques.com/informatique/rss.xml",
}
YOUTUBE_CHANNELS = {
    "Gamers Nexus":    "https://www.youtube.com/feeds/videos.xml?channel_id=UChIs72whgZI9w6d6FhwGGHA",
    "VCG":             "https://www.youtube.com/feeds/videos.xml?channel_id=UCjrj3gdo-KL2S_JN_gdNyPw",
    "Hardware Canucks": "https://www.youtube.com/feeds/videos.xml?channel_id=UCVn2OUZWZ0V7xC7n0z7nK0w",
    "Hardware Unboxed": "https://www.youtube.com/feeds/videos.xml?channel_id=UCI8iQa1hv7oV_Z8B35vVuSg",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ─── FETCH ────────────────────────────────────────────────────────────────────
def fetch_one(name, url, is_youtube):
    """Fetch & parse a single RSS feed. Returns (name, list_of_items, error_str|None)."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        r.raise_for_status()
        feed = feedparser.parse(r.content)
        items = []
        for entry in feed.entries:
            try:
                dt = datetime(*entry.published_parsed[:6])
                if is_youtube:
                    v_id = entry.link.split("v=")[1].split("&")[0] if "v=" in entry.link else entry.id.split(":")[-1]
                    img = f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg"
                    summary = ""
                else:
                    img = ""
                    if hasattr(entry, "media_content") and entry.media_content:
                        img = entry.media_content[0].get("url", "")
                    elif hasattr(entry, "enclosures") and entry.enclosures:
                        img = entry.enclosures[0].get("href", "")
                    raw = re.sub(r"<[^<]+?>", "", entry.get("summary", ""))
                    summary = (raw[:120] + "…") if len(raw) > 120 else raw
                items.append({
                    "source": name,
                    "title": entry.title,
                    "link": entry.link,
                    "date": dt,
                    "image": img,
                    "summary": summary,
                    "is_video": is_youtube,
                })
            except Exception:
                continue
        return name, items, None
    except requests.Timeout:
        return name, [], f"{name} : délai dépassé (6 s)"
    except Exception as e:
        return name, [], f"{name} : {str(e)[:60]}"


@st.cache_data(ttl=600, show_spinner=False)
def fetch_all(source_dict_items, is_youtube):
    """Parallel fetch of all sources. Returns (DataFrame, errors list, fetch_ts)."""
    all_items, errors = [], []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(fetch_one, n, u, is_youtube): n for n, u in source_dict_items}
        for fut in as_completed(futures):
            name, items, err = fut.result()
            all_items.extend(items)
            if err:
                errors.append(err)
    df = pd.DataFrame(all_items).sort_values("date", ascending=False) if all_items else pd.DataFrame()
    return df, errors, time.time()


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def relative_time(ts):
    delta = int(time.time() - ts)
    if delta < 60:
        return "à l'instant"
    elif delta < 3600:
        return f"il y a {delta // 60} min"
    else:
        return f"il y a {delta // 3600} h"

def card_html(row):
    img_block = (
        f'<img src="{row["image"]}" class="card-img" alt="{row["title"]}" loading="lazy">'
        if row["image"]
        else '<div class="card-img-placeholder">📺' if row["is_video"] else '<div class="card-img-placeholder">📰</div>'
    )
    summary_block = f'<div class="card-summary">{row["summary"]}</div>' if row["summary"] else ""
    date_str = row["date"].strftime("%d %b %Y")
    return f"""
    <div class="card" onclick="window.open('{row["link"]}','_blank')">
        <div class="card-img-wrap">{img_block}</div>
        <div class="card-body">
            <div class="card-source">{row["source"]}</div>
            <div class="card-title"><a href="{row["link"]}" target="_blank" onclick="event.stopPropagation()">{row["title"]}</a></div>
            {summary_block}
            <div class="card-footer">
                <span class="card-date">📅 {date_str}</span>
                <span class="card-link-icon">↗</span>
            </div>
        </div>
    </div>
    """

# ─── UI ───────────────────────────────────────────────────────────────────────
# Header
col_title, col_refresh = st.columns([6, 1])
with col_title:
    st.title("Revue de presse Tech")
with col_refresh:
    st.write("")
    refresh = st.button("⟳ Actualiser", use_container_width=True, type="secondary")
    if refresh:
        st.cache_data.clear()
        st.rerun()

# Navigation tabs
if "view" not in st.session_state:
    st.session_state.view = "Articles"

c1, c2, _ = st.columns([1.2, 1.2, 5])
if c1.button("ARTICLES PRESSE", use_container_width=True,
             type="primary" if st.session_state.view == "Articles" else "secondary"):
    st.session_state.view = "Articles"; st.rerun()
if c2.button("VIDÉOS YOUTUBE", use_container_width=True,
             type="primary" if st.session_state.view == "Videos" else "secondary"):
    st.session_state.view = "Videos"; st.rerun()

st.write("")

# Fetch
is_yt = st.session_state.view == "Videos"
source_dict = YOUTUBE_CHANNELS if is_yt else RSS_FEEDS

with st.spinner("Chargement des flux…"):
    df, errors, fetch_ts = fetch_all(tuple(source_dict.items()), is_yt)

# Error banners (network issues)
if errors:
    for err in errors:
        st.markdown(f'<div class="err-banner">⚠️ {err}</div>', unsafe_allow_html=True)

# Filters row
col_search, col_source, col_date = st.columns([2.5, 2, 2])
with col_search:
    search_query = st.text_input("", placeholder="🔍  Rechercher un article…", label_visibility="collapsed")
with col_source:
    source_opts = ["Toutes les sources"] + list(source_dict.keys())
    selected_source = st.selectbox("", options=source_opts, label_visibility="collapsed")
with col_date:
    date_opts = ["Toutes les dates", "Aujourd'hui", "Cette semaine", "Ce mois"]
    selected_date = st.selectbox("", options=date_opts, label_visibility="collapsed")

st.divider()

# Apply filters
filtered = df.copy() if not df.empty else df

if not filtered.empty:
    if search_query:
        filtered = filtered[filtered["title"].str.contains(search_query, case=False, na=False)]

    if selected_source != "Toutes les sources":
        filtered = filtered[filtered["source"] == selected_source]

    now = datetime.utcnow()
    if selected_date == "Aujourd'hui":
        filtered = filtered[filtered["date"].apply(lambda d: d.date() == now.date())]
    elif selected_date == "Cette semaine":
        filtered = filtered[filtered["date"].apply(lambda d: (now - d).days <= 7)]
    elif selected_date == "Ce mois":
        filtered = filtered[filtered["date"].apply(lambda d: d.month == now.month and d.year == now.year)]

# Meta bar (count + refresh time)
count = len(filtered) if not filtered.empty else 0
st.markdown(f"""
<div class="meta-bar">
    <span class="result-badge">{count} résultat{'s' if count != 1 else ''}</span>
    <span class="refresh-info">Mis à jour {relative_time(fetch_ts)}</span>
</div>
""", unsafe_allow_html=True)

# Grid
if df.empty:
    st.markdown("""
    <div class="state-box">
        <div class="icon">📡</div>
        <p>Impossible de charger les flux RSS.</p>
        <small>Vérifiez votre connexion ou cliquez sur Actualiser.</small>
    </div>""", unsafe_allow_html=True)

elif filtered.empty:
    label = f'« {search_query} »' if search_query else selected_source
    st.markdown(f"""
    <div class="state-box">
        <div class="icon">🔍</div>
        <p>Aucun résultat pour {label}.</p>
        <small>Essayez d'autres mots-clés ou élargissez les filtres.</small>
    </div>""", unsafe_allow_html=True)

else:
    cols = st.columns(4)
    for idx, (_, row) in enumerate(filtered.reset_index(drop=True).iterrows()):
        with cols[idx % 4]:
            st.markdown(card_html(row), unsafe_allow_html=True)
