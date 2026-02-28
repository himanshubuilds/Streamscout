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
# 2. RAW CSS (Vertical 3D Depth Effect + Layout Tweaks)
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
    
    /* NEW VERTICAL 3D TABS */
    .provider-row { display: flex; flex-direction: column; gap: 1rem; padding-bottom: 0.5rem; align-items: flex-start; }
    .provider-row a { text-decoration: none !important; width: 100%; max-width: 320px; }
    .provider-pill { 
        display: flex; align-items: center; gap: 1rem; padding: 0.75rem 1.5rem 0.75rem 0.75rem; 
        border-radius: 1rem; 
        background: linear-gradient(145deg, rgba(60, 40, 80, 0.8), rgba(20, 10, 30, 0.9));
        border-top: 1px solid rgba(255, 255, 255, 0.2);
        border-bottom: 2px solid rgba(0, 0, 0, 0.8);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.1);
        color: #ffffff; font-size: 1.1rem; font-weight: 700; 
        transition: all 0.2s ease; cursor: pointer; width: 100%;
    }
    .provider-pill:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.2);
        background: linear-gradient(145deg, rgba(80, 50, 110, 0.9), rgba(30, 15, 45, 0.95));
    }
    .provider-pill:active {
        transform: translateY(1px);
        box-shadow: 0 2px 3px rgba(0, 0, 0, 0.5), inset 0 2px 4px rgba(
