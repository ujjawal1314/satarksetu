import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import random

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="CyberFin Fusion 🛡️",
    page_icon="🛡️",
    layout="wide"
)

# ==========================================
# SESSION STATE INIT
# ==========================================
if "frozen_accounts" not in st.session_state:
    st.session_state.frozen_accounts = set()

if "show_graph_ai" not in st.session_state:
    st.session_state.show_graph_ai = False

if "show_ring_ai" not in st.session_state:
    st.session_state.show_ring_ai = False

if "show_victim" not in st.session_state:
    st.session_state.show_victim = False

# ==========================================
# MOCK DATA
# ==========================================
@st.cache_data
def generate_accounts():
    return pd.DataFrame([
        {"Account_ID": "ACC_002747", "Risk_Score": 90},
        {"Account_ID": "ACC_004611", "Risk_Score": 90},
        {"Account_ID": "ACC_000815", "Risk_Score": 88},
        {"Account_ID": "ACC_009122", "Risk_Score": 85},
        {"Account_ID": "ACC_003341", "Risk_Score": 75}
    ])

@st.cache_data
def generate_graph():
    G = nx.Graph()
    beneficiaries = ["BENEF_A", "BENEF_B", "BENEF_C"]

    for b in beneficiaries:
        G.add_node(b, type="Beneficiary", color="#FF1744", size=30)

    for i in range(1, 24):
        acc = f"ACC_{i:06d}"
        G.add_node(acc, type="Account", color="#FFB300", size=18)
        G.add_edge(acc, random.choice(beneficiaries))

    pos = nx.spring_layout(G, seed=42)
    return G, pos

df_accounts = generate_accounts()
G, pos = generate_graph()

# Filter based on threshold
risk_threshold = st.sidebar.slider("Risk Threshold", 0, 100, 70)
filtered_accounts = df_accounts[df_accounts["Risk_Score"] >= risk_threshold]

total_frozen_amount = len(st.session_state.frozen_accounts) * 49000

# ==========================================
# HEADER
# ==========================================
st.title("🛡️ CyberFin Fusion")
st.subheader("Unified Cyber-Financial Intelligence Platform")

c1, c2, c3, c4 = st.columns(4)
c1.metric("High-Risk Accounts", len(filtered_accounts))
c2.metric("Frozen Accounts", len(st.session_state.frozen_accounts))
c3.metric("Funds Frozen (₹)", f"{total_frozen_amount:,.0f}")
c4.metric("Mule Rings Detected", "1")

st.markdown("---")

# ==========================================
# NAVIGATION
# ==========================================
view = st.sidebar.radio("Navigation", [
    "Dashboard",
    "Live Graph",
    "Account Lookup",
    "Ring Analysis"
])

# ==========================================
# DASHBOARD
# ==========================================
if view == "Dashboard":

    df_display = filtered_accounts.copy()
    df_display["Status"] = df_display["Account_ID"].apply(
        lambda x: "FROZEN ❄️" if x in st.session_state.frozen_accounts else "Active ⚠️"
    )

    st.dataframe(df_display, use_container_width=True)

# ==========================================
# LIVE GRAPH
# ==========================================
elif view == "Live Graph":

    edge_x, edge_y = [], []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color="#888"),
        hoverinfo="none",
        mode="lines"
    )

    node_x, node_y = [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers",
        marker=dict(size=12, color="#FFB300")
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    st.plotly_chart(fig, use_container_width=True)

    if st.button("🤖 Explain Ring"):
        st.session_state.show_graph_ai = not st.session_state.show_graph_ai

    if st.session_state.show_graph_ai:
        st.info(
            "This ring demonstrates coordinated mule behavior. "
            "Multiple accounts funnel money to shared beneficiaries."
        )

# ==========================================
# ACCOUNT LOOKUP
# ==========================================
elif view == "Account Lookup":

    account_id = st.text_input("Enter Account ID")

    if account_id in df_accounts["Account_ID"].values:
        risk = df_accounts[df_accounts["Account_ID"] == account_id]["Risk_Score"].values[0]
        st.metric("Risk Score", risk)

        if account_id in st.session_state.frozen_accounts:
            if st.button("Unfreeze Account"):
                st.session_state.frozen_accounts.remove(account_id)
                st.rerun()
        else:
            if st.button("Freeze Account"):
                st.session_state.frozen_accounts.add(account_id)
                st.rerun()

# ==========================================
# RING ANALYSIS
# ==========================================
elif view == "Ring Analysis":

    st.write("Ring 13 - 23 Accounts Connected to 3 Beneficiaries")

    if st.button("🤖 Generate AI Explanation"):
        st.session_state.show_ring_ai = not st.session_state.show_ring_ai

    if st.session_state.show_ring_ai:
        st.success(
            "This network shows classic smurfing behavior. "
            "Funds are split across accounts and routed to central nodes."
        )

    if st.button("🎭 Show Victim Scenario"):
        st.session_state.show_victim = not st.session_state.show_victim

    if st.session_state.show_victim:
        st.warning(
            "Victim likely recruited through fake job ad promising easy income. "
            "Account unknowingly used for laundering."
        )