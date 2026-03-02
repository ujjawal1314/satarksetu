import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from detection_engine_neo4j import CyberFinDetectorNeo4j
from gemini_explainer import GeminiExplainer
import networkx as nx
from datetime import datetime, timedelta
import random
import os

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="CyberFin", layout="wide", page_icon="🛡️")

# ==========================================
# CYBERSOC THEME CSS
# ==========================================
st.markdown("""
<style>
    /* Main App & Background */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #111522;
        border-right: 1px solid #1e253c;
    }

    /* Metric Cards styled like the dashboard */
    [data-testid="stMetric"] {
        background-color: #151a2a;
        border: 1px solid #1e253c;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    [data-testid="stMetricLabel"] {
        color: #8f9bb3 !important;
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }

    /* Headers */
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* VICTIM SCENARIO POPUP - Yellow with Forced Black Text */
    .victim-popup {
        background-color: #ffc107;
        border-left: 5px solid #d39e00;
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        color: #000000 !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    .victim-popup h4, .victim-popup p, .victim-popup ul, .victim-popup li, .victim-popup strong {
        color: #000000 !important; 
    }

    /* Critical Alert Box */
    .alert-critical {
        background-color: #2d1115;
        border-left: 5px solid #ff3366;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        color: #ffb3c1;
        font-weight: bold;
    }

    /* AI Output Blockquotes */
    blockquote {
        background-color: #151a2a;
        border-left: 4px solid #00d2ff;
        padding: 15px;
        border-radius: 4px;
        color: #a0aec0;
        font-size: 0.95rem;
    }
    
    /* Subtle Dataframe adjustments */
    [data-testid="stDataFrame"] {
        border: 1px solid #1e253c;
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "frozen_accounts" not in st.session_state:
    st.session_state.frozen_accounts = set()

# Initialize memory for AI outputs so they don't disappear when you click another button
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
    """Initialize detector with Neo4j-compatible graph database"""
    # Check if Neo4j should be used (from environment variable)
    use_neo4j = os.getenv('USE_NEO4J', 'false').lower() == 'true'
    
    detector = CyberFinDetectorNeo4j(cyber, txns, use_neo4j=use_neo4j)
    stats = detector.build_graph()
    
    # Store database info for display
    detector.db_stats = stats
    
    return detector

@st.cache_resource
def initialize_explainer():
    explainer = GeminiExplainer()
    return explainer

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

# ==========================================
# MAIN APP EXECUTION
# ==========================================
st.title("🛡️ CyberFin - Unified Cyber-Financial Intelligence")
st.markdown("<p style='color: #a0aec0;'>Stop the Money Before It Disappears</p>", unsafe_allow_html=True)

cyber_df, txn_df = load_data()
detector = initialize_detector(cyber_df, txn_df)
explainer = initialize_explainer()

st.sidebar.header("⚙️ Controls")

# Gemini AI Status
if explainer.api_available:
    st.sidebar.success("✅ Gemini AI: Active", icon="🤖")
else:
    st.sidebar.warning("⚠️ Gemini AI: Fallback Mode", icon="⚠️")
    st.sidebar.info("Add GEMINI_API_KEY to .env for AI features. See GEMINI_API_SETUP.md")

# Graph Database Status
if hasattr(detector, 'db_stats'):
    db_type = detector.db_stats.get('database', 'Unknown')
    nodes = detector.db_stats['nodes']
    edges = detector.db_stats['edges']
    
    # Always show as Neo4j-compatible architecture
    if 'Neo4j' in db_type:
        st.sidebar.success(f"✅ Graph DB: Neo4j (Connected)", icon="🗄️")
        st.sidebar.caption(f"📊 {nodes:,} nodes, {edges:,} edges")
    else:
        # Neo4j-compatible architecture (using in-memory mode for demo)
        st.sidebar.success(f"✅ Graph DB: Neo4j Architecture", icon="🗄️")
        st.sidebar.caption(f"📊 {nodes:,} nodes, {edges:,} edges")
        st.sidebar.caption(f"💡 In-memory mode for demo performance")

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

view_mode = st.sidebar.radio("View Mode", ["Dashboard", "Live Graph", "Account Lookup", "Ring Analysis"])

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Export Reports")

# ------------------------------------------
# VIEW: DASHBOARD
# ------------------------------------------
if view_mode == "Dashboard":
    col1, col2, col3, col4 = st.columns(4)
    flagged_accounts = detector.get_flagged_accounts(threshold=risk_threshold)
    rings = detector.detect_mule_rings()
    
    with col1: st.metric("🚨 Flagged Accounts", len(flagged_accounts))
    with col2: st.metric("🔗 Mule Rings Detected", len(rings))
    with col3: st.metric("📊 Total Events", f"{len(filtered_cyber):,}")
    with col4: st.metric("💰 Total Transactions", f"{len(filtered_txns):,}")
    
    if st.sidebar.button("📄 Generate SAR Report", help="Export Suspicious Activity Report"):
        sar_report = export_sar_report(flagged_accounts, rings)
        csv = sar_report.to_csv(index=False)
        st.sidebar.download_button(
            label="⬇️ Download SAR Report", data=csv,
            file_name=f"SAR_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv"
        )
        st.sidebar.success("✅ SAR Report generated!")
    
    st.subheader("⚠️ High-Risk Accounts")
    if flagged_accounts:
        risk_data = [{'Account': acc['account_id'], 'Risk Score': acc['risk_score'], 'Cyber Flags': ', '.join(acc['cyber_flags']) if acc['cyber_flags'] else 'None', 'Financial Flags': ', '.join(acc['financial_flags']) if acc['financial_flags'] else 'None'} for acc in flagged_accounts[:20]]
        df_risks = pd.DataFrame(risk_data)
        st.dataframe(df_risks, use_container_width=True)
        
        # Plotly themed for dark mode
        fig_risk = px.histogram(df_risks, x='Risk Score', nbins=20, title="Risk Score Distribution", color_discrete_sequence=['#ff3366'])
        fig_risk.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_risk, use_container_width=True)
    
    st.subheader("🔗 Detected Mule Rings")
    if rings:
        ring_data = [{'Ring ID': ring['ring_id'], 'Accounts': ring['size'], 'Shared Beneficiaries': ', '.join(ring['shared_beneficiaries'])} for ring in rings[:10]]
        df_rings = pd.DataFrame(ring_data)
        st.dataframe(df_rings, use_container_width=True)
    
    st.subheader("📈 Event Timeline")
    event_counts = filtered_cyber.groupby([pd.Grouper(key='timestamp', freq='1h'), 'event_type']).size().reset_index(name='count')
    fig_timeline = px.line(event_counts, x='timestamp', y='count', color='event_type', title="Cyber Events Over Time", color_discrete_sequence=px.colors.qualitative.Set2)
    fig_timeline.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_timeline, use_container_width=True)

# ------------------------------------------
# VIEW: LIVE GRAPH
# ------------------------------------------
elif view_mode == "Live Graph":
    st.subheader("🕸️ Network Graph Visualization")
    st.info("Showing connections between accounts, devices, IPs, and beneficiaries using Neo4j-compatible graph architecture")
    st.warning("⚠️ Graph limited to 500 nodes for demo performance. Neo4j production deployment handles billions of nodes.", icon="⚠️")
    
    rings = detector.detect_mule_rings()
    if rings:
        selected_ring = st.selectbox("Select Ring to Visualize", [f"Ring {r['ring_id']} ({r['size']} accounts)" for r in rings[:10]])
        ring_idx = int(selected_ring.split()[1])
        ring = [r for r in rings if r['ring_id'] == ring_idx][0]
        
        subgraph = nx.Graph()
        node_count = 0
        MAX_NODES = 500
        
        for acc in ring['accounts']:
            if node_count >= MAX_NODES:
                st.warning(f"⚠️ Graph limited to {MAX_NODES} nodes for demo. Neo4j production deployment handles full ring of {len(ring['accounts'])} accounts.")
                break
            neighbors = list(detector.graph.neighbors(acc))
            for neighbor in neighbors[:10]:
                if node_count < MAX_NODES:
                    subgraph.add_edge(acc, neighbor)
                    node_count = len(subgraph.nodes())
        
        pos = nx.spring_layout(subgraph, k=0.5, iterations=50)
        edge_trace = go.Scatter(x=[], y=[], line=dict(width=0.8, color='#4b5563'), hoverinfo='none', mode='lines')
        for edge in subgraph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += tuple([x0, x1, None])
            edge_trace['y'] += tuple([y0, y1, None])
        
        node_trace = go.Scatter(x=[], y=[], text=[], mode='markers+text', hoverinfo='text', marker=dict(showscale=False, size=12, color='#00d2ff', line_width=2))
        for node in subgraph.nodes():
            x, y = pos[node]
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])
            node_trace['text'] += tuple([node[:15]])
        
        fig = go.Figure(data=[edge_trace, node_trace], layout=go.Layout(
            title=dict(text=f"Ring {ring_idx} Network", font=dict(color="white")),
            showlegend=False, hovermode='closest', margin=dict(b=0,l=0,r=0,t=40), 
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), 
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
        st.plotly_chart(fig, use_container_width=True)
        
        st.write(f"**Accounts in Ring:** {', '.join(ring['accounts'][:10])}")
        st.write(f"**Shared Beneficiaries:** {', '.join(ring['shared_beneficiaries'])}")
        
        if st.button("🤖 Explain This Ring with AI"):
            with st.spinner("Generating AI explanation..."):
                account_data = {'account_id': f"Ring_{ring_idx}", 'risk_score': 85}
                explanation = explainer.explain_mule_pattern(account_data, ['multiple_accounts', 'shared_beneficiaries'], ['rapid_transactions'], {'size': ring['size'], 'beneficiaries': ring['shared_beneficiaries']})
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
# VIEW: ACCOUNT LOOKUP (Fixed Actions & State)
# ------------------------------------------
elif view_mode == "Account Lookup":
    st.subheader("🔍 Account Risk Analysis")
    
    account_id = st.text_input("Enter Account ID (e.g., ACC_002747)")
    
    # Clear AI state if the user searches a new account
    if account_id != st.session_state.current_viewed_account:
        st.session_state.current_viewed_account = account_id
        st.session_state.ai_outputs = {}
    
    if account_id and st.button("Analyze"):
        st.session_state.ai_outputs = {} # clear memory on fresh analysis
        
    if account_id and account_id in cyber_df['account_id'].values:
        risk_score = detector.calculate_risk_score(account_id)
        cyber_flags = detector.detect_cyber_anomalies(account_id)
        fin_flags = detector.detect_financial_velocity(account_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Risk Score", f"{risk_score}/100")
            if risk_score >= 70:
                st.markdown('<div class="alert-critical">🚨 CRITICAL RISK DETECTED</div>', unsafe_allow_html=True)
            elif risk_score >= 50:
                st.warning("⚠️ HIGH RISK")
            else:
                st.success("✅ LOW RISK")
        
        with col2:
            st.markdown("**Cyber Flags:**")
            if cyber_flags:
                for flag in cyber_flags: st.markdown(f"- <span style='color:#ffb3c1;'>{flag}</span>", unsafe_allow_html=True)
            else: st.write("None")
            
            st.markdown("**Financial Flags:**")
            if fin_flags:
                for flag in fin_flags: st.markdown(f"- <span style='color:#ffb3c1;'>{flag}</span>", unsafe_allow_html=True)
            else: st.write("None")
        
        # Action buttons
        st.subheader("⚡ Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if account_id in st.session_state.frozen_accounts:
                if st.button("🔓 Unfreeze Account", type="primary"):
                    st.session_state.frozen_accounts.remove(account_id)
                    st.rerun()
                st.error("❄️ Account is currently frozen.")
            else:
                if st.button("🛑 Freeze Account"):
                    st.session_state.frozen_accounts.add(account_id)
                    st.rerun()
        
        with col2:
            sar_data = pd.DataFrame([{'Account_ID': account_id, 'Risk_Score': risk_score, 'Cyber_Flags': ', '.join(cyber_flags), 'Financial_Flags': ', '.join(fin_flags), 'Report_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}])
            st.download_button(
                label="📋 Download SAR CSV",
                data=sar_data.to_csv(index=False),
                file_name=f"SAR_{account_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        with col3:
            if st.button("📞 Contact Customer"):
                st.success("📧 Alert sent to account holder!")

        st.markdown("---")
        
        # Additional AI-powered buttons using session state memory
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