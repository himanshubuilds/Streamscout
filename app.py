import streamlit as st
import requests
import google.generativeai as genai
import json
import urllib.parse

# --------------------------------------------------------------------------------
# 1. SETUP & CONFIGURATION
# --------------------------------------------------------------------------------
st.set_page_config(page_title="StreamScout India", page_icon="🎬", layout="wide")

TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

# --------------------------------------------------------------------------------
# 2. RAW CSS
# --------------------------------------------------------------------------------
st.markdown("""
<style>
    [data-testid="stHeader"] { visibility: hidden; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    [data-testid="stAppViewContainer"] {
        background-color: #191022 !important;
        background-image: 
            radial-gradient(circle at 10% 10%, rgba(127, 19, 236, 0.25) 0%, transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(20, 184, 166, 0.15) 0%, transparent 40%) !important;
        color: white !important;
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stAppViewBlockContainer"] {
        max-width: 1200px !important; 
        padding-top: 1rem;
        margin: 0 auto;
    }

    .stTextInput div[data-baseweb="base-input"] {
        background-color: #2a1c3d !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 1rem !important;
    }
    .stTextInput input {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 1.1rem !important;
        background-color: transparent !important;
        padding: 0.75rem 1rem !important;
    }
    
    div[data-testid="stButton"] > button {
        background-color: rgba(127, 19, 236, 0.8) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 0.5rem !important;
        width: 100%;
        margin-top: 0.1rem;
    }
    div[data-testid="stButton"] > button p { color: #ffffff !important; font-weight: bold !important; font-size: 1.1rem !important; }
    div[data-testid="stButton"] > button:hover {
        background-color: rgba(20, 184, 166, 0.9) !important;
        border-color: rgba(255, 255, 255, 0.9) !important;
    }

    .glass-card {
        backdrop-filter: blur(20px); background-color: rgba(42, 28, 61, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 2rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        padding: 2.5rem; display: flex; gap: 3rem; margin-top: 1rem; position: relative; overflow: hidden;
    }
    @media (max-width: 768px) { .glass-card { flex-direction: column; gap: 1.5rem; padding: 1.5rem;} }
    
    .glass-poster-container { flex-shrink: 0; width: 300px; border-radius: 1rem; overflow: hidden; position: relative; }
    @media (max-width: 768px) { .glass-poster-container { width: 100%; max-width: 300px; margin: 0 auto;} }
    .glass-poster { width: 100%; height: auto; display: block; border-radius: 1rem; }
    .status-badge { position: absolute; top: 1rem; left: 1rem; padding: 0.25rem 0.75rem; background: rgba(0,0,0,0.8); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2); border-radius: 0.5rem; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; color: white; }
    
    .card-details { flex: 1; display: flex; flex-direction: column; gap: 1rem; justify-content: center;}
    .card-title { font-size: 3rem; font-weight: 900; line-height: 1.1; margin: 0; color: white; }
    .meta-row { display: flex; flex-wrap: wrap; gap: 1rem; font-size: 1rem; color: #cbd5e1; align-items: center; font-weight: 500;}
    .dot { width: 5px; height: 5px; border-radius: 50%; background-color: #64748b; }
    .card-overview { font-size: 1.15rem; line-height: 1.6; color: #cbd5e1; font-weight: 300; margin: 0; }
    .divider { width: 100%; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); margin: 1rem 0; }
    
    .provider-row { display: flex; gap: 1rem; overflow-x: auto; padding-bottom: 0.5rem; align-items: center; }
    .provider-row::-webkit-scrollbar { display: none; }
    .provider-row a { text-decoration: none !important; }
    .provider-pill { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 1.25rem 0.5rem 0.5rem; border-radius: 9999px; background: rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.15); color: #e2e8f0; font-size: 0.95rem; font-weight: 600; white-space: nowrap; transition: all 0.2s; cursor: pointer; }
    .provider-pill:hover { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.4); transform: translateY(-2px); }
    .provider-img { width: 2.5rem; height: 2.5rem; border-radius: 50%; object-fit: cover; }
    
    .logo-text { font-size: 2rem; font-weight: 900; color: #2dd4bf; margin: 0; padding-top: 0.5rem;}
    .main-title { font-size: 3.5rem; font-weight: 800; text-align: center; margin-top: 1rem; margin-bottom: 0.5rem; color: white;}
    .sub-title { font-size: 1.25rem; color: #94a3b8; text-align: center; margin-bottom: 2.5rem; }
    .highlight { color: #2dd4bf; }
    .not-available { color: #f87171; font-weight: 500; background: rgba(248, 113, 113, 0.1); padding: 0.75rem 1.25rem; border-radius: 0.5rem; border: 1px solid rgba(248, 113, 113, 0.2); display: inline-block;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 3. STATE MANAGEMENT
# --------------------------------------------------------------------------------
if "selected_media" not in st.session_state: st.session_state.selected_media = None
if "show_all" not in st.session_state: st.session_state.show_all = False
if "search_query" not in st.session_state: st.session_state.search_query = ""

def handle_search():
    st.session_state.selected_media = None
    st.session_state.show_all = False

def go_home():
    st.session_state.selected_media = None
    st.session_state.show_all = False
    st.session_state.search_query = ""

def go_back():
    st.session_state.selected_media = None

# --------------------------------------------------------------------------------
# 4. CORE LOGIC
# --------------------------------------------------------------------------------
def analyze_intent(query):
    try:
        prompt = f"""
        Analyze the search query for an OTT search engine. Return strictly JSON.
        Schema: {{"title": "Cleaned title", "type": "movie" | "tv" | "multi", "season": <int or null>, "is_exact": <bool>}}
        Query: "{query}"
        """
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        if raw_text.startswith("```json"): raw_text = raw_text[7:-3].strip()
        elif raw_text.startswith("```"): raw_text = raw_text[3:-3].strip()
        return json.loads(raw_text)
    except Exception:
        return {"title": query, "type": "multi", "season": None, "is_exact": False}

def search_tmdb(title, media_type):
    endpoint = "multi" if media_type not in ["movie", "tv"] else media_type
    url = f"https://api.themoviedb.org/3/search/{endpoint}?api_key={TMDB_API_KEY}&query={urllib.parse.quote(title)}&language=en-US&page=1"
    res = requests.get(url)
    if res.status_code != 200: return []
    return res.json().get("results", [])[:10]

def get_tmdb_details(media_id, media_type):
    url = f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={TMDB_API_KEY}&language=en-US"
    return requests.get(url).json()

def get_tmdb_providers(media_id, media_type, season=None):
    if season: url = f"https://api.themoviedb.org/3/tv/{media_id}/season/{season}/watch/providers?api_key={TMDB_API_KEY}"
    else: url = f"https://api.themoviedb.org/3/{media_type}/{media_id}/watch/providers?api_key={TMDB_API_KEY}"
    res = requests.get(url).json()
    results = res.get("results", {})
    return results.get("IN", {}) if isinstance(results, dict) else {}

# --------------------------------------------------------------------------------
# 5. UI RENDER FUNCTIONS
# --------------------------------------------------------------------------------
def format_time(minutes):
    if not minutes: return "N/A"
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if h > 0 else f"{m}m"

def render_glass_card(media_id, media_type, season=None):
    details = get_tmdb_details(media_id, media_type)
    providers = get_tmdb_providers(media_id, media_type, season)
    
    title = details.get("title") or details.get("name")
    if season: title += f" (Season {season})"
        
    poster_path = details.get("poster_path")
    poster_url = f"https://image.tmdb.org/t/p/w780{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Poster"
    rating = round(details.get("vote_average", 0), 1)
    release_date = details.get("release_date") or details.get("first_air_date")
    year = release_date[:4] if release_date else "N/A"
    
    if media_type == "movie":
        duration = format_time(details.get("runtime"))
        status_badge = "Movie"
    else:
        seasons_count = details.get("number_of_seasons", 1)
        duration = f"{seasons_count} Season{'s' if seasons_count > 1 else ''}"
        status_badge = "TV Show"
        
    genres = ", ".join([g["name"] for g in details.get("genres", [])[:2]])
    overview = details.get("overview", "No overview available.").replace("{", "(").replace("}", ")")
    
    provider_list = providers.get("flatrate") or []
    if not provider_list:
        provider_list = (providers.get("rent") or []) + (providers.get("buy") or [])
        
    seen = set()
    unique_providers = []
    for p in provider_list:
        if p["provider_id"] not in seen:
            seen.add(p["provider_id"])
            unique_providers.append(p)
            
    if not unique_providers:
        providers_html = '<div class="not-available">Not currently available to stream legally in India.</div>'
    else:
        providers_html = ""
        justwatch_link = providers.get("link", "#")
        for p in unique_providers:
            logo_url = f"https://image.tmdb.org/t/p/original{p['logo_path']}"
            # Wrap the provider pill in a clickable anchor tag
            providers_html += f"""
            <a href="{justwatch_link}" target="_blank">
                <div class="provider-pill">
                    <img src="{logo_url}" class="provider-img" alt="{p["provider_name"]}">
                    <span>{p["provider_name"]}</span>
                </div>
            </a>
            """
            
    final_html = f"""
<div class="glass-card">
    <div class="glass-poster-container">
        <img src="{poster_url}" class="glass-poster">
        <span class="status-badge">{status_badge}</span>
    </div>
    <div class="card-details">
        <h2 class="card-title">{title}</h2>
        <div class="meta-row">
            <span class="highlight">⭐ {rating} TMDb</span>
            <div class="dot"></div><span>{year}</span>
            <div class="dot"></div><span>{duration}</span>
            <div class="dot"></div><span>{genres}</span>
        </div>
        <p class="card-overview">{overview}</p>
        <div class="divider"></div>
        <p style="color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0;">Available in India (IN)</p>
        <div class="provider-row">
            {providers_html}
        </div>
    </div>
</div>
"""
    st.markdown(final_html, unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 6. MAIN APP FLOW
# --------------------------------------------------------------------------------
col_logo, col_home = st.columns([5, 1])
with col_logo:
    st.markdown('<p class="logo-text">🎬 StreamScout</p>', unsafe_allow_html=True)
with col_home:
    if st.button("🏠 Home", use_container_width=True):
        go_home()
        st.rerun()

st.markdown("""
    <div class="main-title">Where is it <span class="highlight">streaming?</span></div>
    <div class="sub-title">Discover instantly where to watch any movie or series.</div>
""", unsafe_allow_html=True)

# Added the side-by-side layout for Input + Search Button
col_search, col_btn = st.columns([5, 1])
with col_search:
    st.text_input("Search Input", placeholder="e.g. Dune, Panchayat season 2, Batman...", key="search_query", label_visibility="collapsed", on_change=handle_search)
with col_btn:
    st.button("Search", use_container_width=True, on_click=handle_search)

if st.session_state.search_query:
    if st.session_state.selected_media:
        col_back, _ = st.columns([1, 5])
        with col_back:
            if st.button("← Back to Results", use_container_width=True):
                go_back()
                st.rerun()
        render_glass_card(st.session_state.selected_media["id"], st.session_state.selected_media["type"], st.session_state.selected_media["season"])
    else:
        with st.spinner("Searching records..."):
            intent = analyze_intent(st.session_state.search_query)
            results = search_tmdb(intent.get("title", st.session_state.search_query), intent.get("type", "multi"))
            
            if not results:
                st.warning(f"No results found for '{st.session_state.search_query}'.")
            else:
                if intent.get("is_exact", False) and len(results) > 0:
                    first = results[0]
                    render_glass_card(first["id"], first.get("media_type", "movie"), intent.get("season"))
                else:
                    st.markdown('<h3 style="color: white; margin-top: 1rem;">Top Matches:</h3>', unsafe_allow_html=True)
                    
                    display_count = 10 if st.session_state.show_all else 5
                    visible_results = results[:display_count]
                    
                    for i in range(0, len(visible_results), 5):
                        cols = st.columns(5)
                        for j in range(5):
                            if i + j < len(visible_results):
                                res = visible_results[i+j]
                                if res.get("media_type", "movie") not in ["movie", "tv"]: continue
                                
                                res_poster = res.get("poster_path")
                                poster_url = f"https://image.tmdb.org/t/p/w342{res_poster}" if res_poster else "https://via.placeholder.com/342x513?text=No+Image"
                                
                                with cols[j]:
                                    st.image(poster_url, use_container_width=True)
                                    if st.button(f"Select", key=f"btn_{res['id']}", use_container_width=True):
                                        st.session_state.selected_media = {"id": res["id"], "type": res.get("media_type", "movie"), "season": None}
                                        st.rerun()

                    if len(results) > 5 and not st.session_state.show_all:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("Show More ▼", use_container_width=True):
                            st.session_state.show_all = True
                            st.rerun()
