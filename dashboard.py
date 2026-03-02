import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import html
import base64
import os
from detection_engine import CyberFinDetector
from gemini_explainer import GeminiExplainer
import networkx as nx
from datetime import datetime

# Page config
st.set_page_config(page_title="CyberFin Fusion", layout="wide", page_icon="🛡️")

# Reference-style light dashboard CSS
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
    .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 16px;
        box-shadow: var(--shadow);
        padding: 16px 18px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .chip {
        display: inline-block;
        padding: 8px 14px;
        border-radius: 999px;
        background: #eef2ff;
        border: 1px solid var(--border);
        color: #334155;
        font-size: 13px;
        font-weight: 600;
        margin-right: 8px;
    }
    .chip.active { color: var(--primary-dark); background: #e8edff; }
    .cta {
        display: inline-block;
        border-radius: 10px;
        padding: 8px 14px;
        color: #fff;
        font-weight: 600;
        font-size: 13px;
        margin-left: 8px;
    }
    .cta.deposit { background: var(--primary); }
    .cta.transfer { background: #111827; }

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
    .landing-nav-anchor {
        height: 62px;
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
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    cyber = pd.read_csv('cyber_events.csv')
    txns = pd.read_csv('transactions.csv')
    return cyber, txns

@st.cache_resource
def initialize_detector(cyber, txns):
    detector = CyberFinDetector(cyber, txns)
    detector.build_graph()
    return detector

@st.cache_resource
def initialize_explainer():
    return GeminiExplainer()

def compute_graph_layout(graph):
    try:
        return nx.spring_layout(graph, k=0.5, iterations=50), False
    except ModuleNotFoundError as exc:
        if "scipy" in str(exc).lower():
            return nx.circular_layout(graph), True
        raise

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

# Main app
st.title("🏦 CyberFin Fusion - Enterprise Financial Intelligence")
st.markdown("<p style='color: #64748B; font-size: 1.05rem;'>Unified Anti-Money Laundering & Threat Detection Portal</p>", unsafe_allow_html=True)

cyber_df, txn_df = load_data()
detector = initialize_detector(cyber_df, txn_df)
explainer = initialize_explainer()

VIEW_OPTIONS = ["Dashboard", "Live Graph", "Account Lookup"]
if "view_mode" not in st.session_state or st.session_state.view_mode not in VIEW_OPTIONS:
    st.session_state.view_mode = VIEW_OPTIONS[0]

top_title, top_overview, top_revenue, top_retention, top_spacer, top_deposit, top_transfer = st.columns([2.4, 1, 1.25, 1, 2.25, 0.9, 0.9])
with top_title:
    st.markdown("**CyberFin Fusion Console**")
with top_overview:
    if st.button("Overview", key="d_top_overview", type="primary" if st.session_state.view_mode == "Dashboard" else "secondary", use_container_width=True):
        st.session_state.view_mode = "Dashboard"
        st.rerun()
with top_revenue:
    if st.button("Revenue Signals", key="d_top_revenue", type="primary" if st.session_state.view_mode == "Live Graph" else "secondary", use_container_width=True):
        st.session_state.view_mode = "Live Graph"
        st.rerun()
with top_retention:
    if st.button("Retention", key="d_top_retention", type="primary" if st.session_state.view_mode == "Account Lookup" else "secondary", use_container_width=True):
        st.session_state.view_mode = "Account Lookup"
        st.rerun()
with top_deposit:
    st.button("Deposit", key="d_top_deposit", use_container_width=True)
with top_transfer:
    st.button("Transfer", key="d_top_transfer", use_container_width=True)

# Sidebar
st.sidebar.header("⚙️ Controls")
risk_threshold = st.sidebar.slider("Risk Score Threshold", 0, 100, 50)
selected_mode = st.sidebar.selectbox("View Mode", VIEW_OPTIONS, index=VIEW_OPTIONS.index(st.session_state.view_mode))
if selected_mode != st.session_state.view_mode:
    st.session_state.view_mode = selected_mode
view_mode = st.session_state.view_mode

if view_mode == "Dashboard":
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    flagged_accounts = detector.get_flagged_accounts(threshold=risk_threshold)
    rings = detector.detect_mule_rings()
    
    with col1:
        st.metric("🚨 Flagged Accounts", len(flagged_accounts))
    with col2:
        st.metric("🔗 Mule Rings Detected", len(rings))
    with col3:
        st.metric("📊 Total Events", len(cyber_df))
    with col4:
        st.metric("💰 Total Transactions", len(txn_df))
    
    # Top risks
    st.subheader("⚠️ High-Risk Accounts")
    if flagged_accounts:
        risk_data = []
        for acc in flagged_accounts[:20]:
            risk_data.append({
                'Account': acc['account_id'],
                'Risk Score': acc['risk_score'],
                'Cyber Flags': ', '.join(acc['cyber_flags']) if acc['cyber_flags'] else 'None',
                'Financial Flags': ', '.join(acc['financial_flags']) if acc['financial_flags'] else 'None'
            })
        
        df_risks = pd.DataFrame(risk_data)
        st.dataframe(df_risks, use_container_width=True)
        
        # Risk distribution
        fig_risk = px.histogram(df_risks, x='Risk Score', nbins=20, 
                               title="Risk Score Distribution",
                               color_discrete_sequence=['#5B6CFF'])
        fig_risk.update_layout(
            template="plotly_white",
            plot_bgcolor='rgba(255,255,255,0)',
            paper_bgcolor='rgba(255,255,255,0)',
            font=dict(color="#0F172A"),
            legend=dict(font=dict(color="#0F172A"))
        )
        st.plotly_chart(fig_risk, use_container_width=True)
    
    # Mule rings
    st.subheader("🔗 Detected Mule Rings")
    if rings:
        ring_data = []
        for ring in rings[:10]:
            ring_data.append({
                'Ring ID': ring['ring_id'],
                'Accounts': ring['size'],
                'Shared Beneficiaries': ', '.join(ring['shared_beneficiaries'])
            })
        
        df_rings = pd.DataFrame(ring_data)
        st.dataframe(df_rings, use_container_width=True)
    
    # Event timeline
    st.subheader("📈 Event Timeline")
    cyber_df['timestamp'] = pd.to_datetime(cyber_df['timestamp'])
    event_counts = cyber_df.groupby([pd.Grouper(key='timestamp', freq='1h'), 'event_type']).size().reset_index(name='count')
    
    fig_timeline = px.line(event_counts, x='timestamp', y='count', color='event_type',
                          title="Cyber Events Over Time")
    fig_timeline.update_layout(
        template="plotly_white",
        plot_bgcolor='rgba(255,255,255,0)',
        paper_bgcolor='rgba(255,255,255,0)',
        font=dict(color="#0F172A"),
        legend=dict(font=dict(color="#0F172A")),
        height=620,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

elif view_mode == "Live Graph":
    st.subheader("🕸️ Network Graph Visualization")
    st.info("Showing connections between accounts, devices, IPs, and beneficiaries")
    
    # Select a ring to visualize
    rings = detector.detect_mule_rings()
    if rings:
        ring_lookup = {int(r["ring_id"]): r for r in rings}
        ring_ids = sorted(ring_lookup.keys())[:10]
        selected_ring_id = st.selectbox(
            "Select Ring to Visualize",
            ring_ids,
            key="live_graph_ring_id",
            format_func=lambda rid: f"Ring {rid} ({ring_lookup[rid]['size']} accounts)"
        )
        ring_idx = int(selected_ring_id)
        ring = ring_lookup[ring_idx]
        
        # Create a focused subgraph for this ring:
        # only ring accounts + shared beneficiaries to avoid graph explosion.
        subgraph = nx.Graph()
        ring_accounts = list(ring.get('accounts', []))
        shared_beneficiaries = set(ring.get('shared_beneficiaries', []))
        allowed_nodes = set(ring_accounts) | shared_beneficiaries

        # Keep accounts visible even if no eligible edge exists.
        for acc in ring_accounts:
            subgraph.add_node(acc)
        for ben in shared_beneficiaries:
            subgraph.add_node(ben)

        # Add only relevant edges among allowed nodes.
        for acc in ring_accounts:
            for neighbor in detector.graph.neighbors(acc):
                if neighbor in allowed_nodes:
                    subgraph.add_edge(acc, neighbor)
        
        # Create plotly network graph
        pos, used_fallback_layout = compute_graph_layout(subgraph)
        if used_fallback_layout:
            st.info("SciPy not installed in this environment. Using fallback graph layout.")
        
        edge_trace = go.Scatter(
            x=[], y=[], line=dict(width=0.5, color='#94A3B8'), hoverinfo='none', mode='lines')
        
        for edge in subgraph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += tuple([x0, x1, None])
            edge_trace['y'] += tuple([y0, y1, None])
        
        node_trace = go.Scatter(
            x=[], y=[], text=[], mode='markers+text', hoverinfo='text',
            marker=dict(showscale=False, size=10, line_width=2, color=[]),
            textfont=dict(color="#1F2937", size=13))
        
        for node in subgraph.nodes():
            x, y = pos[node]
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])
            node_trace['text'] += tuple([node[:15]])
            
            # Color by node type
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
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title=f"Ring {ring_idx} Network",
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=0,l=0,r=0,t=40),
                           plot_bgcolor='rgba(255,255,255,0)',
                           paper_bgcolor='rgba(255,255,255,0)',
                           hoverlabel=dict(bgcolor="#0B1220", font=dict(color="#FFFFFF", size=13)),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                       )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.write(f"**Accounts in Ring:** {', '.join(ring['accounts'][:10])}")
        st.write(f"**Shared Beneficiaries:** {', '.join(ring['shared_beneficiaries'])}")

        if st.button("🤖 Explain using AI", key=f"live_graph_explain_ai_{ring_idx}", type="primary"):
            st.info(
                "AI explanation placeholder. Integrate your Gemini API call here using the selected ring context "
                f"(Ring {ring_idx}, {ring['size']} accounts)."
            )

elif view_mode == "Account Lookup":
    st.subheader("🔍 Account Risk Analysis")
    
    input_col, button_col = st.columns([4, 1])
    with input_col:
        account_id = st.text_input("Enter Account ID (e.g., ACC_000860)")
    with button_col:
        st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
        analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)
    
    if account_id and analyze_clicked:
        if account_id in cyber_df['account_id'].values:
            risk_score = detector.calculate_risk_score(account_id)
            cyber_flags = detector.detect_cyber_anomalies(account_id)
            fin_flags = detector.detect_financial_velocity(account_id)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Risk Score", f"{risk_score}/100")
                
                if risk_score >= 70:
                    st.error("🚨 CRITICAL RISK")
                elif risk_score >= 50:
                    st.warning("⚠️ HIGH RISK")
                else:
                    st.success("✅ LOW RISK")
            
            with col2:
                st.write("**Cyber Flags:**")
                if cyber_flags:
                    for flag in cyber_flags:
                        st.write(f"- {flag}")
                else:
                    st.write("None")
                
                st.write("**Financial Flags:**")
                if fin_flags:
                    for flag in fin_flags:
                        st.write(f"- {flag}")
                else:
                    st.write("None")
            
            # Recent activity
            st.subheader("Recent Cyber Events")
            recent_cyber = cyber_df[cyber_df['account_id'] == account_id].tail(10)
            st.dataframe(recent_cyber, use_container_width=True)
            
            st.subheader("Recent Transactions")
            recent_txns = txn_df[txn_df['account_id'] == account_id].tail(10)
            if not recent_txns.empty:
                st.dataframe(recent_txns, use_container_width=True)
            else:
                st.info("No transactions found")
            
            # AI Explanation
            st.subheader("🤖 AI-Powered Explanation")
            with st.spinner("Generating explanation..."):
                account_data = {'account_id': account_id, 'risk_score': risk_score}
                explanation = explainer.explain_mule_pattern(account_data, cyber_flags, fin_flags)
                st.markdown(explanation)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🛑 Freeze Account"):
                    st.success("Account frozen! Transaction blocked.")
            with col2:
                if st.button("📋 Generate SAR"):
                    st.success("SAR report generated!")
            with col3:
                if st.button("📞 Contact Customer"):
                    st.info("Alert sent to account holder")
        else:
            st.error("Account not found")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**CyberFin Fusion v1.0**")
st.sidebar.markdown("Built for 24hr Hackathon")
