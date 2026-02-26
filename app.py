import streamlit as st
import requests
import google.generativeai as genai
import json
import urllib.parse

# --------------------------------------------------------------------------------
# 1. SETUP & CONFIGURATION
# --------------------------------------------------------------------------------
st.set_page_config(page_title="StreamScout India", page_icon="🦉", layout="centered")

# Hide Streamlit's default header/footer and make background transparent
# so our injected Tailwind HTML background works perfectly.
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        background: transparent !important;
    }
    /* Style the native Streamlit text input to match the theme */
    div[data-baseweb="input"] {
        background-color: rgba(42, 28, 61, 0.4) !important;
        border-radius: 1rem !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
    }
    div[data-baseweb="input"] input {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# Secure API Keys
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# --------------------------------------------------------------------------------
# 2. HTML & TAILWIND TEMPLATES (From your design)
# --------------------------------------------------------------------------------
# We extract the head, background, and header to inject globally
GLOBAL_HTML = """
<!DOCTYPE html><html class="dark" lang="en"><head>
    <link href="https://fonts.googleapis.com" rel="preconnect">
    <link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect">
    <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;700;900&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <script>
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    colors: {
                        primary: "#7f13ec",
                        "primary-content": "#ffffff",
                        "background-light": "#f7f6f8",
                        "background-dark": "#191022",
                        "surface-glass": "rgba(42, 28, 61, 0.4)",
                        "surface-glass-border": "rgba(255, 255, 255, 0.1)",
                        teal: { 400: '#2dd4bf', 500: '#14b8a6' }
                    },
                    fontFamily: { display: ["Be Vietnam Pro", "sans-serif"] },
                },
            },
        }
    </script>
    <style>
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        body { background-color: #191022 !important; color: white !important; }
    </style>
</head>
<body class="bg-background-dark font-display text-slate-100 antialiased overflow-x-hidden relative selection:bg-teal-400 selection:text-background-dark">
    <!-- Ambient Background -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none z-[-1]">
        <div class="absolute -top-[10%] -left-[10%] w-[50%] h-[50%] rounded-full bg-primary/20 blur-[120px] mix-blend-screen opacity-60"></div>
        <div class="absolute top-[20%] right-[10%] w-[40%] h-[60%] rounded-full bg-teal-500/10 blur-[100px] mix-blend-screen opacity-50"></div>
        <div class="absolute -bottom-[20%] left-[20%] w-[60%] h-[50%] rounded-full bg-primary/10 blur-[130px] mix-blend-screen opacity-40"></div>
    </div>
    
    <!-- Header -->
    <header class="flex items-center justify-between whitespace-nowrap px-8 py-6 w-full max-w-7xl mx-auto">
        <div class="flex items-center gap-3 group cursor-pointer">
            <div class="size-10 bg-gradient-to-br from-primary to-teal-400 rounded-lg flex items-center justify-center shadow-lg shadow-primary/20">
                <span class="material-symbols-outlined text-white text-[28px]">movie_filter</span>
            </div>
            <h2 class="text-white text-2xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">StreamScout</h2>
        </div>
    </header>
</body></html>
"""

# The Dynamic Glass Card Template
GLASS_CARD_TEMPLATE = """
<div class="w-full backdrop-blur-2xl bg-surface-glass border border-surface-glass-border rounded-[2.5rem] shadow-2xl p-6 md:p-8 flex flex-col gap-8 mt-4 overflow-hidden relative">
    <div class="absolute top-0 right-0 w-96 h-96 bg-primary/10 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>
    <div class="flex flex-col lg:flex-row gap-8 items-start relative z-10">
        
        <!-- Poster -->
        <div class="w-full lg:w-1/3 shrink-0">
            <div class="aspect-[2/3] w-full rounded-2xl overflow-hidden shadow-2xl shadow-black/50 relative group">
                <div class="w-full h-full bg-cover bg-center transition-transform duration-700 group-hover:scale-105" style="background-image: url('{poster_url}');"></div>
                <div class="absolute top-4 left-4 z-20">
                    <span class="px-3 py-1 bg-black/40 backdrop-blur-md border border-white/10 rounded-lg text-xs font-bold text-white uppercase tracking-wider">{status_badge}</span>
                </div>
            </div>
        </div>
        
        <!-- Details -->
        <div class="flex flex-col flex-1 py-2 gap-6">
            <div class="space-y-1">
                <h2 class="text-4xl md:text-5xl font-black text-white leading-[1.1] tracking-tight">{title}</h2>
                <div class="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm md:text-base text-slate-300 font-medium pt-2">
                    <span class="flex items-center gap-1 text-teal-400">
                        <span class="material-symbols-outlined text-[20px] fill-current">star</span>
                        {rating} TMDb
                    </span>
                    <span class="size-1 rounded-full bg-slate-500"></span>
                    <span>{year}</span>
                    <span class="size-1 rounded-full bg-slate-500"></span>
                    <span>{duration}</span>
                    <span class="size-1 rounded-full bg-slate-500"></span>
                    <span>{genres}</span>
                </div>
            </div>
            
            <p class="text-slate-300 text-lg leading-relaxed max-w-2xl font-light">{overview}</p>
            
            <div class="w-full h-px bg-gradient-to-r from-transparent via-surface-glass-border to-transparent my-2"></div>
            
            <!-- Streaming Providers -->
            <div class="flex flex-col gap-3">
                <p class="text-sm text-slate-400 font-medium uppercase tracking-widest">Available in India (IN)</p>
                <div class="flex gap-3 overflow-x-auto no-scrollbar py-2 mask-linear-fade">
                    {providers_html}
                </div>
            </div>
        </div>
    </div>
</div>
"""

PROVIDER_PILL_TEMPLATE = """
<button class="flex items-center gap-3 pl-2 pr-5 py-2 rounded-full bg-black/40 border border-white/5 hover:bg-black/60 hover:border-white/20 transition-all cursor-pointer whitespace-nowrap group/service">
    <div class="size-8 rounded-full bg-black flex items-center justify-center text-white overflow-hidden">
        <img src="{logo_url}" class="w-full h-full object-cover" alt="{name}">
    </div>
    <span class="text-slate-200 font-medium text-sm group-hover/service:text-white">{name}</span>
</button>
"""

NOT_AVAILABLE_TEMPLATE = """
<span class="text-red-400 font-medium text-base bg-red-400/10 px-4 py-2 rounded-lg border border-red-400/20">
    Not currently available to stream legally in India.
</span>
"""

# Inject global styles and head
st.markdown(GLOBAL_HTML, unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 3. STATE MANAGEMENT
# --------------------------------------------------------------------------------
if "selected_media" not in st.session_state:
    st.session_state.selected_media = None

def reset_selection():
    st.session_state.selected_media = None

# --------------------------------------------------------------------------------
# 4. CORE LOGIC (GEMINI + TMDB)
# --------------------------------------------------------------------------------
def analyze_intent(query):
    """Uses Gemini to route the intent of the search query."""
    prompt = f"""
    Analyze the following search query for an OTT search engine. 
    Return a strictly formatted JSON object with no markdown wrappers.
    Schema:
    {{
      "title": "Cleaned title",
      "type": "movie" | "tv" | "multi",
      "season": <integer or null if no season mentioned>,
      "is_exact": <true if user is asking for a precise title (e.g., 'Breaking Bad', 'Panchayat season 2'), false if ambiguous (e.g., 'Batman', 'action movies')>
    }}
    Query: "{query}"
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    return json.loads(response.text)

def search_tmdb(title, media_type):
    """Searches TMDB for fuzzy matches."""
    endpoint = "multi" if media_type not in ["movie", "tv"] else media_type
    url = f"https://api.themoviedb.org/3/search/{endpoint}?api_key={TMDB_API_KEY}&query={urllib.parse.quote(title)}&language=en-US&page=1"
    res = requests.get(url).json()
    return res.get("results", [])[:5]

def get_tmdb_details(media_id, media_type):
    """Fetches exact movie/tv details."""
    url = f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={TMDB_API_KEY}&language=en-US"
    return requests.get(url).json()

def get_tmdb_providers(media_id, media_type, season=None):
    """Fetches watch providers for India (IN)."""
    if season:
        url = f"https://api.themoviedb.org/3/tv/{media_id}/season/{season}/watch/providers?api_key={TMDB_API_KEY}"
    else:
        url = f"https://api.themoviedb.org/3/{media_type}/{media_id}/watch/providers?api_key={TMDB_API_KEY}"
    
    res = requests.get(url).json()
    results = res.get("results", {})
    return results.get("IN", {})

# --------------------------------------------------------------------------------
# 5. UI RENDER FUNCTIONS
# --------------------------------------------------------------------------------
def format_time(minutes):
    if not minutes: return "N/A"
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if h > 0 else f"{m}m"

def render_glass_card(media_id, media_type, season=None):
    """Builds and renders the dynamic Glass Card for Output 1, 3, 4 & 6."""
    details = get_tmdb_details(media_id, media_type)
    providers = get_tmdb_providers(media_id, media_type, season)
    
    # Extract Details
    title = details.get("title") or details.get("name")
    if season:
        title += f" (Season {season})"
        
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
    overview = details.get("overview", "No overview available.")
    
    # Extract Providers (Prioritize Flatrate/Streaming, fallback to Rent/Buy)
    provider_list = providers.get("flatrate", [])
    if not provider_list:
        provider_list = providers.get("rent", []) + providers.get("buy", [])
        
    # Deduplicate providers
    seen = set()
    unique_providers = []
    for p in provider_list:
        if p["provider_id"] not in seen:
            seen.add(p["provider_id"])
            unique_providers.append(p)
            
    # Build Provider HTML (Output 6 if empty)
    if not unique_providers:
        providers_html = NOT_AVAILABLE_TEMPLATE
    else:
        providers_html = ""
        for p in unique_providers:
            logo_url = f"https://image.tmdb.org/t/p/original{p['logo_path']}"
            providers_html += PROVIDER_PILL_TEMPLATE.format(
                logo_url=logo_url, 
                name=p["provider_name"]
            )
            
    # Render Output Card
    final_html = GLASS_CARD_TEMPLATE.format(
        poster_url=poster_url,
        status_badge=status_badge,
        title=title,
        rating=rating,
        year=year,
        duration=duration,
        genres=genres,
        overview=overview,
        providers_html=providers_html
    )
    
    st.markdown(final_html, unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 6. MAIN APP FLOW
# --------------------------------------------------------------------------------
# Title Layout
st.markdown("""
<div class="w-full max-w-3xl mx-auto flex flex-col gap-4 items-center z-20 mt-10 mb-6 text-center">
    <h1 class="text-4xl md:text-5xl font-bold text-white tracking-tight">
        Find your next <span class="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-primary">obsession</span>
    </h1>
    <p class="text-slate-400 text-lg">Search millions of movies and TV shows in India.</p>
</div>
""", unsafe_allow_html=True)

# Input
query = st.text_input("Enter a movie or show...", placeholder="e.g. Dune, Panchayat season 2, Batman...", on_change=reset_selection)

if query:
    if st.session_state.selected_media:
        # User selected a specific movie from the fuzzy list
        render_glass_card(
            st.session_state.selected_media["id"],
            st.session_state.selected_media["type"],
            st.session_state.selected_media["season"]
        )
    else:
        with st.spinner("Analyzing intent..."):
            try:
                intent = analyze_intent(query)
                title = intent.get("title", query)
                media_type = intent.get("type", "multi")
                season = intent.get("season")
                is_exact = intent.get("is_exact", False)
                
                # Search TMDB
                results = search_tmdb(title, media_type)
                
            except Exception as e:
                st.error("Error processing request. Please try again.")
                st.stop()
                
        if not results:
            st.warning(f"No results found for '{query}'.")
        else:
            if is_exact:
                # Output 1, 3 & 4 (Exact Match / Specific Season)
                first_result = results[0]
                detected_type = first_result.get("media_type", media_type if media_type in ["movie", "tv"] else "movie")
                render_glass_card(first_result["id"], detected_type, season)
                
            else:
                # Output 2 & 5 (Fuzzy Match -> Show Top 5)
                st.markdown("<h3 class="text-xl text-white font-bold mb-4">Top Matches:</h3>", unsafe_allow_html=True)
                
                # Streamlit columns to layout 5 small posters
                cols = st.columns(5)
                for idx, res in enumerate(results):
                    res_type = res.get("media_type", media_type if media_type in ["movie", "tv"] else "movie")
                    # Skip people
                    if res_type not in ["movie", "tv"]:
                        continue
                        
                    res_title = res.get("title") or res.get("name")
                    res_poster = res.get("poster_path")
                    poster_url = f"https://image.tmdb.org/t/p/w342{res_poster}" if res_poster else "https://via.placeholder.com/342x513?text=No+Image"
                    
                    with cols[idx]:
                        st.image(poster_url, use_container_width=True)
                        if st.button(f"View Details", key=f"btn_{res['id']}"):
                            st.session_state.selected_media = {
                                "id": res["id"],
                                "type": res_type,
                                "season": None
                            }
                            st.rerun()

# Note: Streamlit execution ends here. The UI updates dynamically based on session_state.
