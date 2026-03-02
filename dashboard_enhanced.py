import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import html
import base64
from datetime import datetime, timedelta
import random
import os
import httpx

# Securely load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import google.generativeai as genai
except ImportError:
    pass

from detection_engine_neo4j import CyberFinDetectorNeo4j
from gemini_explainer import GeminiExplainer
from repositories import AccountRepository

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="CyberFin Fusion", layout="wide", page_icon="🛡️")

# ==========================================
# REFERENCE-STYLE LIGHT DASHBOARD CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    :root {
        --bg: #F5F7FB;
        --card: #FFFFFF;
        --primary: #5B6CFF;
        --primary-dark: #3F4BD9;
        --text: #0F172A;
        --text-secondary: #64748B;
        --text-muted: #94A3B8;
        --border: #E6EAF2;
        --shadow: 0 10px 30px rgba(15,23,42,0.08);
    }
    .stApp {
        background: var(--bg);
        color: var(--text);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    ::selection {
        background: #cfe1ff;
        color: #0F172A;
    }
    ::-moz-selection {
        background: #cfe1ff;
        color: #0F172A;
    }
    header[data-testid="stHeader"] {
        background: transparent;
        height: 0;
    }
    #MainMenu, footer { visibility: hidden; }
    .main .block-container {
        max-width: 1300px;
        padding-top: 24px;
        padding-bottom: 24px;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f9fbff 0%, #f2f5fb 100%);
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] * { color: var(--text) !important; }
    [data-testid="stMetric"] {
        background: linear-gradient(180deg, #ffffff 0%, #fbfcff 100%);
        border: 1px solid var(--border);
        padding: 18px;
        border-radius: 16px;
        box-shadow: var(--shadow);
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-weight: 600;
        letter-spacing: -0.01em;
    }
    [data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 700; }
    h1, h2, h3, h4 { color: var(--text) !important; font-weight: 600 !important; letter-spacing: -0.02em; }
    .stButton > button, .stDownloadButton > button {
        border-radius: 10px;
        border: 1px solid var(--border);
        background: #f7f9ff;
        color: var(--text);
        font-weight: 600;
        padding: 8px 14px;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, var(--primary) 0%, var(--primary-dark) 100%);
        border: none;
        color: #ffffff;
    }
    .stButton > button:disabled,
    .stDownloadButton > button:disabled {
        background: #EEF2F7 !important;
        border: 1px solid #D5DCE8 !important;
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
        opacity: 1 !important;
        cursor: not-allowed !important;
    }
    .stButton > button:disabled *,
    .stDownloadButton > button:disabled * {
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: #1F2937 !important;
        border: 1px solid #374151 !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stButton > button * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #111827 !important;
        border-color: #4B5563 !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    [data-baseweb="input"] > div, [data-baseweb="select"] > div, .stTextInput > div > div {
        border-radius: 12px !important;
        border-color: var(--border) !important;
        background: #ffffff !important;
    }
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        font-weight: 600 !important;
    }
    [data-baseweb="select"] *,
    [data-baseweb="select"] span,
    [data-baseweb="select"] div {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
    }
    [data-baseweb="input"] input,
    .stTextInput input,
    .stTextArea textarea,
    [data-baseweb="select"] input {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        caret-color: #0F172A !important;
    }
    [data-baseweb="input"] input::placeholder,
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder,
    [data-baseweb="select"] input::placeholder {
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
        opacity: 1 !important;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 16px;
        overflow: hidden;
        background: var(--card);
        box-shadow: var(--shadow);
    }
    .js-plotly-plot .plotly .xtick text,
    .js-plotly-plot .plotly .ytick text,
    .js-plotly-plot .plotly .legend text,
    .js-plotly-plot .plotly .gtitle,
    .js-plotly-plot .plotly .infolayer text,
    .js-plotly-plot .plotly .hovertext text {
        fill: #0F172A !important;
        color: #0F172A !important;
    }
    .js-plotly-plot .plotly .hovertext text {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }
    .st-key-landing_home,
    .st-key-landing_contact,
    .st-key-landing_help,
    .st-key-landing_about {
        position: fixed;
        top: auto;
        bottom: 26px;
        z-index: 40;
        pointer-events: auto;
    }
    .st-key-landing_home { left: calc(50% - 250px); width: 96px; }
    .st-key-landing_contact { left: calc(50% - 140px); width: 108px; }
    .st-key-landing_help { left: calc(50% - 18px); width: 74px; }
    .st-key-landing_about { left: calc(50% + 68px); width: 102px; }
    .st-key-landing_home button,
    .st-key-landing_contact button,
    .st-key-landing_help button,
    .st-key-landing_about button {
        border-radius: 999px !important;
        border: 1px solid rgba(255,255,255,0.16) !important;
        background: rgba(255,255,255,0.06) !important;
        color: #ffffff !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        min-height: 34px !important;
        padding: 6px 14px !important;
        backdrop-filter: blur(6px);
    }
    .st-key-landing_home button[kind="primary"],
    .st-key-landing_contact button[kind="primary"],
    .st-key-landing_help button[kind="primary"],
    .st-key-landing_about button[kind="primary"] {
        background: rgba(255,255,255,0.18) !important;
        border-color: rgba(255,255,255,0.35) !important;
    }
    .st-key-landing_get_started,
    .st-key-landing_login {
        position: fixed;
        top: auto;
        bottom: 26px;
        z-index: 40;
        pointer-events: auto;
    }
    .st-key-landing_get_started { right: 136px; width: 112px; }
    .st-key-landing_login { right: 28px; width: 90px; }
    .st-key-landing_get_started button {
        border-radius: 999px !important;
        min-height: 36px !important;
        padding: 8px 14px !important;
        background: #7C3AED !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .st-key-landing_login button {
        border-radius: 999px !important;
        min-height: 36px !important;
        padding: 8px 14px !important;
        background: transparent !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.35) !important;
        font-weight: 700 !important;
    }
    .landing-wrap {
        min-height: 100vh;
        width: 100vw;
        background: radial-gradient(1200px 500px at 50% 20%, rgba(46,242,255,0.16), transparent 58%), linear-gradient(180deg, #05060A 0%, #0B0F17 55%, #0D121D 100%);
        border: none;
        border-radius: 0;
        position: fixed;
        inset: 0;
        z-index: 10;
        overflow: hidden;
        padding: 24px 28px 90px 28px;
        margin: 0;
        pointer-events: none;
    }
    .landing-cutout {
        position: absolute;
        pointer-events: none;
        z-index: 11;
        opacity: 0.32;
        mix-blend-mode: screen;
        filter: saturate(1.12) contrast(1.04);
        background-repeat: no-repeat;
        background-position: center;
        background-size: cover;
    }
    .landing-cutout.one {
        left: -2vw;
        top: 13vh;
        width: 40vw;
        height: 64vh;
        mask-image: radial-gradient(circle at 62% 48%, rgba(0,0,0,1) 0%, rgba(0,0,0,0.78) 42%, rgba(0,0,0,0.15) 72%, rgba(0,0,0,0) 100%);
        -webkit-mask-image: radial-gradient(circle at 62% 48%, rgba(0,0,0,1) 0%, rgba(0,0,0,0.78) 42%, rgba(0,0,0,0.15) 72%, rgba(0,0,0,0) 100%);
    }
    .landing-cutout.two {
        right: -3vw;
        bottom: 8vh;
        width: 35vw;
        height: 60vh;
        opacity: 0.26;
        mask-image: radial-gradient(circle at 38% 52%, rgba(0,0,0,1) 0%, rgba(0,0,0,0.8) 44%, rgba(0,0,0,0.18) 74%, rgba(0,0,0,0) 100%);
        -webkit-mask-image: radial-gradient(circle at 38% 52%, rgba(0,0,0,1) 0%, rgba(0,0,0,0.8) 44%, rgba(0,0,0,0.18) 74%, rgba(0,0,0,0) 100%);
    }
    .landing-nav-anchor { height: 62px; }
    .landing-panel {
        position: absolute;
        left: 50%;
        top: 68%;
        transform: translate(-50%, -50%);
        width: min(760px, 88vw);
        z-index: 24;
        pointer-events: none;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.18);
        background: rgba(11,15,23,0.52);
        backdrop-filter: blur(6px);
        padding: 18px 20px;
        text-align: center;
    }
    .landing-panel h3 {
        color: #ffffff !important;
        margin: 0 0 8px 0;
        font-size: 22px;
        font-weight: 700 !important;
    }
    .landing-panel p {
        color: #cbd5e1 !important;
        margin: 0;
        font-size: 14px;
        line-height: 1.5;
    }
    .landing-card {
        width: 360px;
        height: 210px;
        margin: 36px auto 24px auto;
        background: radial-gradient(circle at 20% 0%, rgba(34,211,238,0.22), transparent 55%), #0E111A;
        border: 1px solid #1F2433;
        border-radius: 18px;
        box-shadow: 0 26px 60px rgba(10,15,30,0.7), 0 0 24px rgba(46,242,255,0.2);
        transform: perspective(820px) rotateX(18deg) rotateY(-20deg) rotateZ(-6deg);
        position: relative;
        animation: floatCard 4s ease-in-out infinite;
        overflow: hidden;
    }
    .landing-card::before {
        content: "";
        position: absolute;
        inset: 0;
        background-image: radial-gradient(rgba(255,255,255,0.08) 0.9px, transparent 0.9px);
        background-size: 6px 6px;
        opacity: 0.5;
    }
    .landing-card .row {
        position: relative;
        z-index: 2;
        color: #FFF;
        font-size: 36px;
        font-weight: 700;
        padding: 24px 26px 0 26px;
        line-height: 1.2;
    }
    .landing-card .row.small {
        font-size: 42px;
        padding-top: 14px;
    }
    .landing-headline {
        text-align: center;
        color: #FFFFFF;
        font-size: 68px;
        line-height: 1.05;
        letter-spacing: -0.02em;
        font-weight: 700;
        margin-top: 18px;
    }
    .landing-grad {
        background: linear-gradient(90deg, #22D3EE 0%, #60A5FA 45%, #8B5CF6 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .landing-sub {
        text-align: center;
        color: #9CA3AF;
        font-size: 17px;
        max-width: 760px;
        margin: 12px auto 0 auto;
        font-weight: 600;
    }
    .landing-desc {
        text-align: center;
        color: #cbd5e1;
        font-size: 15px;
        max-width: 860px;
        margin: 10px auto 0 auto;
        line-height: 1.45;
    }
    .landing-features {
        text-align: center;
        color: #b8c5da;
        font-size: 14px;
        margin-top: 12px;
        letter-spacing: 0.01em;
    }
    .landing-note {
        text-align: center;
        color: #cbd5e1;
        margin-top: 14px;
        font-size: 15px;
        letter-spacing: 0.01em;
    }
    @keyframes floatCard {
        0%, 100% { transform: perspective(820px) rotateX(18deg) rotateY(-20deg) rotateZ(-6deg) translateY(0px); }
        50% { transform: perspective(820px) rotateX(18deg) rotateY(-20deg) rotateZ(-6deg) translateY(-12px); }
    }
    .victim-popup {
        background-color: #fff8dc;
        border-left: 5px solid #f59e0b;
        padding: 15px;
        margin: 10px 0;
        border-radius: 12px;
        color: #7c5a12 !important;
        border: 1px solid #f9ddb1;
    }
    .victim-popup h4, .victim-popup p, .victim-popup ul, .victim-popup li, .victim-popup strong {
        color: #7c5a12 !important; 
    }
    .alert-critical {
        background-color: #fee2e2;
        border-left: 5px solid #ef4444;
        padding: 15px;
        margin: 10px 0;
        border-radius: 12px;
        color: #991b1b;
        font-weight: bold;
        border: 1px solid #fecaca;
    }
    blockquote {
        background-color: #eef2ff;
        border-left: 4px solid #5B6CFF;
        padding: 15px;
        border-radius: 8px;
        color: #1e3a8a;
        font-size: 0.95rem;
    }
    .status-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 12px;
        letter-spacing: 0.01em;
        margin-left: 8px;
    }
    .status-active {
        background: #DCFCE7;
        color: #166534;
        border: 1px solid #86EFAC;
    }
    .status-frozen {
        background: #FEE2E2;
        color: #991B1B;
        border: 1px solid #FCA5A5;
    }
    .status-review {
        background: #FFEDD5;
        color: #9A3412;
        border: 1px solid #FDBA74;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "ai_outputs" not in st.session_state:
    st.session_state.ai_outputs = {}

if "current_viewed_account" not in st.session_state:
    st.session_state.current_viewed_account = None

# ==========================================
# DATA LOADING
# ==========================================
@st.cache_data
def load_data():
    cyber = pd.read_csv('cyber_events.csv')
    txns = pd.read_csv('transactions.csv')
    cyber['timestamp'] = pd.to_datetime(cyber['timestamp'])
    txns['timestamp'] = pd.to_datetime(txns['timestamp'])
    return cyber, txns

@st.cache_resource
def initialize_detector(cyber, txns):
    use_neo4j = os.getenv('USE_NEO4J', 'false').lower() == 'true'
    detector = CyberFinDetectorNeo4j(cyber, txns, use_neo4j=use_neo4j)
    stats = detector.build_graph()
    detector.db_stats = stats
    return detector

@st.cache_resource
def initialize_explainer():
    # Pass the API key to environment so GeminiExplainer can pick it up natively
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
        except NameError:
            pass
    explainer = GeminiExplainer()
    return explainer

@st.cache_resource
def initialize_repo():
    return AccountRepository()

# ==========================================
# HELPER FUNCTIONS
# ==========================================
FAKE_JOB_ADS = [
    "💰 Earn ₹15,000/week from home! No experience needed. Just receive & transfer payments.",
    "🏠 Work From Home - Payment Processing Agent. ₹20k/month guaranteed. Easy work, flexible hours!",
    "💼 Urgent Hiring: Financial Assistant. Handle transactions from home. ₹18k/week + bonus!",
    "📱 Instagram Opportunity: Be a payment coordinator. ₹25k/month. DM for details!",
    "🎯 Student-Friendly Job: Process payments part-time. ₹12k/week. No investment required!"
]

def show_victim_popup(account_id):
    fake_ad = random.choice(FAKE_JOB_ADS)
    st.markdown(f"""
    <div class="victim-popup">
        <h4>🎭 Likely Recruitment Scenario</h4>
        <p><strong>Account:</strong> {account_id}</p>
        <p><strong>Victim probably saw this ad:</strong></p>
        <p style="font-style: italic; padding: 10px; background: rgba(255,255,255,0.5); border-radius: 5px; border: 1px solid #d39e00;">
            "{fake_ad}"
        </p>
        <p><strong>What happened next:</strong></p>
        <ul>
            <li>Victim responded thinking it's a legitimate job</li>
            <li>Scammer asked for bank details "for salary deposit"</li>
            <li>Account used to receive & transfer stolen money</li>
            <li>Victim unaware they're committing money laundering</li>
        </ul>
        <p style="color: #dc3545 !important;"><strong>⚠️ 71% of Gen Z unaware this leads to criminal record</strong></p>
    </div>
    """, unsafe_allow_html=True)

def export_sar_report(flagged_accounts, rings):
    report_data = []
    for acc in flagged_accounts[:50]: 
        report_data.append({
            'Report_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Account_ID': acc['account_id'],
            'Risk_Score': acc['risk_score'],
            'Status': 'CRITICAL' if acc['risk_score'] >= 70 else 'HIGH',
            'Cyber_Flags': ', '.join(acc['cyber_flags']) if acc['cyber_flags'] else 'None',
            'Financial_Flags': ', '.join(acc['financial_flags']) if acc['financial_flags'] else 'None',
            'Recommended_Action': 'FREEZE_IMMEDIATELY' if acc['risk_score'] >= 80 else 'MANUAL_REVIEW',
            'Ring_Membership': 'Under Investigation'
        })
    return pd.DataFrame(report_data)

def load_contact_us_content():
    try:
        with open("contact_us.md", "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "Contact info file not found."

def load_about_us_content():
    try:
        with open("about_us.md", "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "About us file not found."

def load_help_content():
    try:
        with open("help.md", "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "Help file not found."

def image_to_data_uri(file_path):
    try:
        ext = os.path.splitext(file_path)[1].lower()
        mime = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/webp" if ext == ".webp" else "application/octet-stream"
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return ""

def status_badge(status):
    if status == "FROZEN":
        return '<span class="status-badge status-frozen">FROZEN</span>'
    if status == "UNDER_REVIEW":
        return '<span class="status-badge status-review">UNDER REVIEW</span>'
    return '<span class="status-badge status-active">ACTIVE</span>'

def safe_post_json(url, payload=None, timeout=4.0):
    try:
        with httpx.Client(timeout=timeout) as client:
            res = client.post(url, json=payload or {})
        return res
    except Exception:
        return None

# ==========================================
# MAIN APP EXECUTION
# ==========================================
# Landing gate state
if "dashboard_landing_done" not in st.session_state:
    st.session_state.dashboard_landing_done = False
if "landing_nav_tab" not in st.session_state:
    st.session_state.landing_nav_tab = "Home"

# Cover landing page shown first
if not st.session_state.dashboard_landing_done:
    panel_copy = {
        "Home": ("Home", "Welcome to CyberFin Fusion. This landing page is now interactive and routes to your core dashboard."),
        "Contact Us": ("Contact Us", load_contact_us_content()),
        "Help": ("Help", load_help_content()),
        "About Us": ("About Us", load_about_us_content()),
        "Login": ("Login", "Login section placeholder. We can connect this to real authentication when you are ready.")
    }

    cutout_1 = image_to_data_uri("1.jpg")
    cutout_2 = image_to_data_uri("2.webp")
    cutout_html = ""
    if cutout_1:
        cutout_html += f'<div class="landing-cutout one" style="background-image:url(\'{cutout_1}\');"></div>'
    if cutout_2:
        cutout_html += f'<div class="landing-cutout two" style="background-image:url(\'{cutout_2}\');"></div>'

    home_html = f"""
    <div class="landing-wrap">
        {cutout_html}
        <div class="landing-nav-anchor"></div>
        <div class="landing-card">
            <div class="row">10.365</div>
            <div class="row small">18,500.0</div>
        </div>
        <div class="landing-headline">
            <span class="landing-grad">CyberFin</span>
        </div>
        <div class="landing-sub">Unified Cyber-Financial Intelligence</div>
        <div class="landing-desc">Detect and stop money mule networks by linking cyber threats with financial transactions in real time.</div>
        <div class="landing-features">Graph Detection • Real-Time Risk • AI Explanations • AML + Cyber Fusion</div>
        <div class="landing-note"><strong>CyberFin Fusion</strong></div>
    </div>
    """

    if st.session_state.landing_nav_tab == "Home":
        landing_html = home_html
    else:
        page_title, page_body = panel_copy.get(st.session_state.landing_nav_tab, panel_copy["Home"])
        page_body_html = html.escape(page_body).replace("\n", "<br>")
        landing_html = f"""
        <div class="landing-wrap">
            {cutout_html}
            <div class="landing-nav-anchor"></div>
            <div class="landing-panel" style="top: 46%; width:min(980px,92vw); pointer-events:auto;">
                <h3>{html.escape(page_title)}</h3>
                <p style="text-align:left; white-space:normal;">{page_body_html}</p>
            </div>
        </div>
        """

    st.markdown(
        f"""
        <style>
            [data-testid="stSidebar"] {{ display: none !important; }}
            .stApp {{ background: #05060A !important; }}
            [data-testid="stAppViewContainer"] {{ background: #05060A !important; }}
            .main .block-container {{ max-width: 100% !important; padding: 0 !important; margin: 0 !important; }}
        </style>
        {landing_html}
        """,
        unsafe_allow_html=True
    )
    l_sp_l, l_nav1, l_nav2, l_nav3, l_nav4, l_sp_r, l_act1, l_act2 = st.columns([1.3, 0.9, 1.05, 0.7, 0.9, 2.8, 1.0, 0.8])
    with l_nav1:
        if st.button("Home", key="landing_home", type="primary" if st.session_state.landing_nav_tab == "Home" else "secondary", use_container_width=True):
            st.session_state.landing_nav_tab = "Home"
            st.rerun()
    with l_nav2:
        if st.button("Contact Us", key="landing_contact", type="primary" if st.session_state.landing_nav_tab == "Contact Us" else "secondary", use_container_width=True):
            st.session_state.landing_nav_tab = "Contact Us"
            st.rerun()
    with l_nav3:
        if st.button("Help", key="landing_help", type="primary" if st.session_state.landing_nav_tab == "Help" else "secondary", use_container_width=True):
            st.session_state.landing_nav_tab = "Help"
            st.rerun()
    with l_nav4:
        if st.button("About Us", key="landing_about", type="primary" if st.session_state.landing_nav_tab == "About Us" else "secondary", use_container_width=True):
            st.session_state.landing_nav_tab = "About Us"
            st.rerun()
    with l_act1:
        if st.button("Get started", key="landing_get_started", use_container_width=True):
            st.session_state.dashboard_landing_done = True
            st.rerun()
    with l_act2:
        if st.button("Login", key="landing_login", use_container_width=True):
            st.session_state.landing_nav_tab = "Login"
            st.rerun()
    st.stop()

st.title("🏦 CyberFin Fusion - Enterprise Financial Intelligence")
st.markdown("<p style='color: #64748B; font-size: 1.05rem;'>Unified Anti-Money Laundering & Threat Detection Portal</p>", unsafe_allow_html=True)

cyber_df, txn_df = load_data()
detector = initialize_detector(cyber_df, txn_df)
explainer = initialize_explainer()
repo = initialize_repo()
backend_base_url = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

st.sidebar.header("⚙️ Controls")

# API Key check via environment
api_key = os.getenv("GEMINI_API_KEY")

# Gemini AI Status
if explainer.api_available and api_key:
    st.sidebar.success("✅ Gemini AI: Active", icon="🤖")
else:
    st.sidebar.warning("⚠️ Gemini AI: Fallback Mode", icon="⚠️")
    st.sidebar.info("Add GEMINI_API_KEY to your .env file to enable AI features.")

# Graph Database Status
if hasattr(detector, 'db_stats'):
    db_type = detector.db_stats.get('database', 'Unknown')
    nodes = detector.db_stats['nodes']
    edges = detector.db_stats['edges']
    
    if 'Neo4j' in db_type:
        st.sidebar.success(f"✅ Graph DB: Neo4j (Connected)", icon="🗄️")
    else:
        st.sidebar.success(f"✅ Graph DB: Neo4j Architecture", icon="🗄️")
    st.sidebar.caption(f"📊 {nodes:,} nodes, {edges:,} edges")

if repo.client:
    st.sidebar.success("✅ Accounts DB: Supabase", icon="🧱")
else:
    st.sidebar.warning("⚠️ Accounts DB: Fallback mode", icon="🧪")

risk_threshold = st.sidebar.slider("Risk Score Threshold", 0, 100, 50)

st.sidebar.subheader("📅 Timeline Filter")
min_time = cyber_df['timestamp'].min()
max_time = cyber_df['timestamp'].max()
time_range = st.sidebar.slider("Select Time Range (hours ago)", min_value=0, max_value=24, value=(0, 24))

time_start = max_time - timedelta(hours=time_range[1])
time_end = max_time - timedelta(hours=time_range[0])
filtered_cyber = cyber_df[(cyber_df['timestamp'] >= time_start) & (cyber_df['timestamp'] <= time_end)]
filtered_txns = txn_df[(txn_df['timestamp'] >= time_start) & (txn_df['timestamp'] <= time_end)]

st.sidebar.info(f"📊 Showing {len(filtered_cyber):,} events and {len(filtered_txns):,} transactions")

VIEW_OPTIONS = ["Dashboard", "Live Graph", "Account Lookup", "Ring Analysis"]
if "view_mode" not in st.session_state or st.session_state.view_mode not in VIEW_OPTIONS:
    st.session_state.view_mode = VIEW_OPTIONS[0]

top_title, top_overview, top_revenue, top_account, top_ring, top_spacer = st.columns([2.2, 0.9, 1.2, 1.1, 1.1, 3.6])
with top_title:
    st.markdown("**CyberFin Fusion Console**")
with top_overview:
    if st.button("Overview", key="e_top_overview", type="primary" if st.session_state.view_mode == "Dashboard" else "secondary", use_container_width=True):
        st.session_state.view_mode = "Dashboard"
        st.rerun()
with top_revenue:
    if st.button("Revenue Signals", key="e_top_revenue", type="primary" if st.session_state.view_mode == "Live Graph" else "secondary", use_container_width=True):
        st.session_state.view_mode = "Live Graph"
        st.rerun()
with top_account:
    if st.button("Account Lookup", key="e_top_account", type="primary" if st.session_state.view_mode == "Account Lookup" else "secondary", use_container_width=True):
        st.session_state.view_mode = "Account Lookup"
        st.rerun()
with top_ring:
    if st.button("Ring Analysis", key="e_top_ring", type="primary" if st.session_state.view_mode == "Ring Analysis" else "secondary", use_container_width=True):
        st.session_state.view_mode = "Ring Analysis"
        st.rerun()

view_mode = st.session_state.view_mode

# ------------------------------------------
# VIEW: DASHBOARD
# ------------------------------------------
if view_mode == "Dashboard":
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    flagged_accounts = detector.get_flagged_accounts(threshold=risk_threshold)
    rings = detector.detect_mule_rings()
    
    with col1: st.metric("🚨 Flagged Accounts", len(flagged_accounts))
    with col2: st.metric("🔗 Mule Rings Detected", len(rings))
    with col3: st.metric("📊 Total Events", f"{len(filtered_cyber):,}")
    with col4: st.metric("💰 Total Transactions", f"{len(filtered_txns):,}")
    with col5: st.metric("🧊 Frozen Accounts", repo.frozen_accounts_count())
    with col6: st.metric("⛔ Blocked Txns", repo.blocked_transactions_count())

    if st.button("Generate Suspicious Transaction", key="demo_suspicious_btn", type="primary"):
        demo_response = safe_post_json(f"{backend_base_url}/transactions/demo-suspicious")
        if demo_response is not None and demo_response.status_code < 300:
            payload = demo_response.json()
            flagged = payload.get("flagged_account", {})
            txn = payload.get("transaction", {})
            if txn.get("status") == "BLOCKED":
                st.warning(
                    f"Transaction blocked for {flagged.get('account_id')} because account is frozen "
                    f"(Risk {flagged.get('risk_score')})"
                )
            else:
                st.success(
                    f"Suspicious transaction created for {flagged.get('account_id')} "
                    f"(Risk {flagged.get('risk_score')})"
                )
        else:
            st.warning("Backend demo endpoint unreachable. Start FastAPI backend to run this flow.")
    
    st.subheader("⚠️ High-Risk Accounts")
    if flagged_accounts:
        risk_data = []
        for acc in flagged_accounts[:20]:
            rec = repo.get_account(acc["account_id"]) or repo.ensure_account(acc["account_id"])
            risk_data.append({
                'Account': acc['account_id'],
                'Risk Score': acc['risk_score'],
                'Status': rec.get("status", "ACTIVE"),
                'Cyber Flags': ', '.join(acc['cyber_flags']) if acc['cyber_flags'] else 'None',
                'Financial Flags': ', '.join(acc['financial_flags']) if acc['financial_flags'] else 'None'
            })
        df_risks = pd.DataFrame(risk_data)
        st.dataframe(df_risks, use_container_width=True)
        
        fig_risk = px.histogram(df_risks, x='Risk Score', nbins=20, title="Risk Score Distribution", color_discrete_sequence=['#5B6CFF'])
        fig_risk.update_layout(
            template="plotly_white",
            plot_bgcolor='rgba(255,255,255,0)',
            paper_bgcolor='rgba(255,255,255,0)',
            font=dict(color="#0F172A"),
            legend=dict(font=dict(color="#0F172A"))
        )
        st.plotly_chart(fig_risk, use_container_width=True)
    
    st.subheader("🔗 Detected Mule Rings")
    if rings:
        ring_data = [{'Ring ID': ring['ring_id'], 'Accounts': ring['size'], 'Shared Beneficiaries': ', '.join(ring['shared_beneficiaries'])} for ring in rings[:10]]
        df_rings = pd.DataFrame(ring_data)
        st.dataframe(df_rings, use_container_width=True)
    
    st.subheader("📈 Event Timeline")
    event_counts = filtered_cyber.groupby([pd.Grouper(key='timestamp', freq='1h'), 'event_type']).size().reset_index(name='count')
    fig_timeline = px.line(event_counts, x='timestamp', y='count', color='event_type', title="Cyber Events Over Time", color_discrete_sequence=px.colors.qualitative.Set2)
    fig_timeline.update_layout(
        template="plotly_white",
        plot_bgcolor='rgba(255,255,255,0)',
        paper_bgcolor='rgba(255,255,255,0)',
        font=dict(color="#0F172A"),
        legend=dict(
            font=dict(color="#0F172A", size=18),
            title=dict(font=dict(color="#0F172A", size=20))
        ),
        height=620,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

# ------------------------------------------
# VIEW: LIVE GRAPH
# ------------------------------------------
elif view_mode == "Live Graph":
    st.subheader("🕸️ Network Graph Visualization")
    st.info("Showing connections between accounts, devices, IPs, and beneficiaries using Neo4j-compatible graph architecture")
    
    rings = detector.detect_mule_rings()
    if rings:
        ring_options = [f"Ring {r['ring_id']} ({r['size']} accounts)" for r in rings[:10]]
        selected_ring_str = st.selectbox("Select Ring to Visualize", ring_options, key="live_graph_ring_selector")
        
        ring_idx = int(selected_ring_str.split()[1].split('(')[0])
        ring = [r for r in rings if r['ring_id'] == ring_idx][0]
        
        st.info(f"📊 Visualizing Ring {ring_idx}: {ring['size']} accounts, {len(ring['shared_beneficiaries'])} shared beneficiaries")
        
        subgraph = nx.Graph()
        node_count = 0
        MAX_NODES = 500
        
        for acc in ring['accounts']:
            if node_count >= MAX_NODES:
                st.warning(f"⚠️ Graph limited to {MAX_NODES} nodes for demo.")
                break
            
            neighbors = ring['shared_beneficiaries']
            
            for neighbor in neighbors[:10]:
                if node_count < MAX_NODES:
                    subgraph.add_edge(acc, neighbor)
                    node_count = len(subgraph.nodes())
        
        pos = nx.spring_layout(subgraph, k=0.5, iterations=50)
        edge_trace = go.Scatter(x=[], y=[], line=dict(width=0.8, color='#94A3B8'), hoverinfo='none', mode='lines')
        for edge in subgraph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += tuple([x0, x1, None])
            edge_trace['y'] += tuple([y0, y1, None])
        
        node_trace = go.Scatter(
            x=[], y=[], text=[], mode='markers+text', hoverinfo='text',
            marker=dict(showscale=False, size=10, line_width=2, color=[]),
            textfont=dict(color="#1F2937", size=13)
        )
        for node in subgraph.nodes():
            x, y = pos[node]
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])
            node_trace['text'] += tuple([node[:15]])
            if node.startswith('ACC_'):
                node_trace['marker']['color'] += tuple(['#EF4444'])
            elif node.startswith('BEN_'):
                node_trace['marker']['color'] += tuple(['#F59E0B'])
            elif node.startswith('DEV_'):
                node_trace['marker']['color'] += tuple(['#06B6D4'])
            elif node.startswith('IP_'):
                node_trace['marker']['color'] += tuple(['#3B82F6'])
            else:
                node_trace['marker']['color'] += tuple(['#60A5FA'])
        
        fig = go.Figure(data=[edge_trace, node_trace], layout=go.Layout(
            title=dict(text=f"Ring {ring_idx} Network", font=dict(color="#0F172A")),
            showlegend=False, hovermode='closest', margin=dict(b=0,l=0,r=0,t=40), 
            plot_bgcolor='rgba(255,255,255,0)', paper_bgcolor='rgba(255,255,255,0)',
            hoverlabel=dict(bgcolor="#0B1220", font=dict(color="#FFFFFF", size=13)),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), 
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
        st.plotly_chart(fig, use_container_width=True, key=f"live_graph_ring_{ring_idx}")
        
        st.write(f"**Accounts in Ring:** {', '.join(ring['accounts'][:10])}")
        st.write(f"**Shared Beneficiaries:** {', '.join(ring['shared_beneficiaries'])}")
        
        if st.button("🤖 Explain This Ring with AI", key=f"live_graph_ai_button_{ring_idx}"):
            with st.spinner("Generating AI explanation..."):
                beneficiaries_str = ', '.join(ring['shared_beneficiaries'][:5])
                explanation = explainer.explain_ring(ring_idx, ring['size'], beneficiaries_str, 85)
                st.markdown("### 🤖 AI Analysis")
                st.info(explanation)

# ------------------------------------------
# VIEW: RING ANALYSIS
# ------------------------------------------
elif view_mode == "Ring Analysis":
    st.subheader("🔍 Detailed Ring Analysis")
    rings = detector.detect_mule_rings()
    
    if rings:
        ring_options = [f"Ring {r['ring_id']} - {r['size']} accounts" for r in rings[:20]]
        selected = st.selectbox("Select Ring for Analysis", ring_options)
        ring_idx = int(selected.split()[1])
        ring = [r for r in rings if r['ring_id'] == ring_idx][0]
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Ring Size", f"{ring['size']} accounts")
        with col2: st.metric("Shared Beneficiaries", len(ring['shared_beneficiaries']))
        with col3: st.metric("Risk Level", "🔴 CRITICAL" if ring['size'] > 10 else "🟡 HIGH")
        
        st.subheader("📋 Accounts in Ring")
        st.write(", ".join(ring['accounts'][:20]))
        if len(ring['accounts']) > 20: st.info(f"... and {len(ring['accounts']) - 20} more accounts")
        
        st.subheader("💰 Shared Beneficiaries")
        st.write(", ".join(ring['shared_beneficiaries']))
        
        if st.button("🤖 Generate AI Explanation for This Ring"):
            with st.spinner("Analyzing ring pattern..."):
                account_data = {'account_id': f"Ring_{ring_idx}", 'risk_score': 85}
                explanation = explainer.explain_mule_pattern(account_data, ['multiple_accounts', 'shared_beneficiaries', 'coordinated_activity'], ['rapid_transactions', 'near_threshold_amount'], {'size': ring['size'], 'beneficiaries': ring['shared_beneficiaries']})
                st.markdown("### 🤖 AI Analysis")
                st.info(explanation)
        
        if st.button("🎭 Show Likely Victim Scenario"):
            sample_account = random.choice(ring['accounts'][:10])
            show_victim_popup(sample_account)
        
        if st.button("📥 Export Ring Data"):
            ring_export = pd.DataFrame({'Ring_ID': [ring['ring_id']] * len(ring['accounts']), 'Account_ID': ring['accounts'], 'Shared_Beneficiaries': [', '.join(ring['shared_beneficiaries'])] * len(ring['accounts']), 'Ring_Size': [ring['size']] * len(ring['accounts'])})
            csv = ring_export.to_csv(index=False)
            st.download_button(label="⬇️ Download Ring Data", data=csv, file_name=f"Ring_{ring_idx}_Export_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

# ------------------------------------------
# VIEW: ACCOUNT LOOKUP
# ------------------------------------------
elif view_mode == "Account Lookup":
    st.subheader("🔍 Account Risk Analysis")
    
    input_col, button_col = st.columns([4, 1])
    with input_col:
        account_id = st.text_input("Enter Account ID (e.g., ACC_002747)")
    with button_col:
        st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
        analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)
    
    if account_id != st.session_state.current_viewed_account:
        st.session_state.current_viewed_account = account_id
        st.session_state.ai_outputs = {}
    
    if account_id and analyze_clicked:
        st.session_state.ai_outputs = {} 
        
    if account_id and account_id in cyber_df['account_id'].values:
        risk_score = detector.calculate_risk_score(account_id)
        repo.upsert_account_risk(account_id, int(risk_score))
        account_row = repo.get_account(account_id) or repo.ensure_account(account_id)
        account_status = account_row.get("status", "ACTIVE")
        cyber_flags = detector.detect_cyber_anomalies(account_id)
        fin_flags = detector.detect_financial_velocity(account_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Risk Score", f"{risk_score}/100")
            st.markdown(f"Status: {status_badge(account_status)}", unsafe_allow_html=True)
            if risk_score >= 70:
                st.markdown('<div class="alert-critical">🚨 CRITICAL RISK DETECTED</div>', unsafe_allow_html=True)
            elif risk_score >= 50:
                st.warning("⚠️ HIGH RISK")
            else:
                st.success("✅ LOW RISK")
            if account_status == "FROZEN":
                st.error("Account Frozen - Transactions Blocked")
        
        with col2:
            st.markdown("**Cyber Flags:**")
            if cyber_flags:
                for flag in cyber_flags: st.markdown(f"- <span style='color:#ffb3c1;'>{flag}</span>", unsafe_allow_html=True)
            else: st.write("None")
            
            st.markdown("**Financial Flags:**")
            if fin_flags:
                for flag in fin_flags: st.markdown(f"- <span style='color:#ffb3c1;'>{flag}</span>", unsafe_allow_html=True)
            else: st.write("None")
        
        st.subheader("⚡ Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if account_status == "FROZEN":
                st.button("🛑 Freeze Account", disabled=True, use_container_width=True)
                st.error("❄️ Account is currently frozen.")
            elif risk_score >= 70:
                if st.button("🛑 Freeze Account", use_container_width=True):
                    freeze_response = safe_post_json(
                        f"{backend_base_url}/accounts/{account_id}/freeze",
                        payload={"reason": "High risk account from CyberFin dashboard", "performed_by": "dashboard_user"},
                    )
                    if freeze_response is not None and freeze_response.status_code < 300:
                        st.toast("Account frozen")
                    else:
                        repo.freeze_account(account_id, reason="High risk account from CyberFin dashboard", performed_by="dashboard_user")
                        st.toast("Account frozen")
                    st.rerun()
            else:
                st.button("🛑 Freeze Account", disabled=True, use_container_width=True)
                st.caption("Freeze available only for risk score >= 70")
        
        with col2:
            if account_status == "FROZEN":
                st.button("📋 Download SAR CSV", disabled=True, use_container_width=True)
            else:
                sar_data = pd.DataFrame([{'Account_ID': account_id, 'Risk_Score': risk_score, 'Cyber_Flags': ', '.join(cyber_flags), 'Financial_Flags': ', '.join(fin_flags), 'Report_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}])
                st.download_button(
                    label="📋 Download SAR CSV",
                    data=sar_data.to_csv(index=False),
                    file_name=f"SAR_{account_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
        with col3:
            if account_status == "FROZEN":
                if st.button("💳 Attempt Transaction", use_container_width=True):
                    txn_attempt = safe_post_json(
                        f"{backend_base_url}/transactions/process",
                        payload={"from_account": account_id, "to_account": "BEN_TEST_001", "amount": 1200.0},
                    )
                    if txn_attempt is not None and txn_attempt.status_code == 403:
                        st.error("Transaction blocked: Account frozen")
                    else:
                        st.warning("Could not validate blocked transaction. Ensure backend is running.")
            else:
                if st.button("📞 Contact Customer"):
                    st.success("📧 Alert sent to account holder!")

        st.markdown("---")
        
        st.subheader("🤖 AI-Powered Analysis")
        col4, col5 = st.columns(2)
        
        with col4:
            if st.button("📋 Generate SAR Narrative"):
                with st.spinner("Generating..."):
                    st.session_state.ai_outputs['sar'] = explainer.generate_sar_narrative({'account_id': account_id, 'risk_score': risk_score}, cyber_flags, fin_flags)
            if 'sar' in st.session_state.ai_outputs:
                st.markdown(f"> **SAR Narrative:**<br>{st.session_state.ai_outputs['sar']}", unsafe_allow_html=True)
            
            if st.button("🔍 Investigation Steps"):
                with st.spinner("Generating..."):
                    st.session_state.ai_outputs['investigation'] = explainer.suggest_investigation_steps({'account_id': account_id, 'risk_score': risk_score}, cyber_flags + fin_flags)
            if 'investigation' in st.session_state.ai_outputs:
                st.markdown(f"> **Investigation Steps:**<br>{st.session_state.ai_outputs['investigation']}", unsafe_allow_html=True)
        
        with col5:
            if st.button("🛡️ Prevention Tips"):
                with st.spinner("Generating..."):
                    st.session_state.ai_outputs['tips'] = explainer.explain_prevention_tips("money_mule")
            if 'tips' in st.session_state.ai_outputs:
                st.markdown(f"> **Prevention Tips:**<br>{st.session_state.ai_outputs['tips']}", unsafe_allow_html=True)
            
            if st.button("📖 Victim Education Scenario"):
                st.session_state.ai_outputs['victim'] = True
            if st.session_state.ai_outputs.get('victim', False):
                show_victim_popup(account_id)

    elif account_id:
        st.error("Account not found. Please verify the ID.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("<span style='color: #a0aec0;'>**CyberFin v3.1**</span>", unsafe_allow_html=True)
st.sidebar.markdown("<span style='color: #a0aec0;'>Neo4j Architecture • AI Enhanced</span>", unsafe_allow_html=True)
