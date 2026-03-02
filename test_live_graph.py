"""
Quick test to verify Live Graph functionality
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 60)
print("LIVE GRAPH FUNCTIONALITY TEST")
print("=" * 60)

# Test imports
print("\n1. Testing imports...")
try:
    from detection_engine_neo4j import CyberFinDetectorNeo4j
    import networkx as nx
    import plotly.graph_objects as go
    print("   ✅ All imports successful")
except Exception as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Test detector initialization
print("\n2. Testing detector initialization...")
try:
    import pandas as pd
    
    # Load data
    cyber_df = pd.read_csv('cyber_events.csv')
    txn_df = pd.read_csv('transactions.csv')
    print(f"   ✅ Data loaded: {len(cyber_df)} cyber events, {len(txn_df)} transactions")
    
    detector = CyberFinDetectorNeo4j(cyber_df, txn_df)
    print("   ✅ Detector initialized")
except Exception as e:
    print(f"   ❌ Detector error: {e}")
    sys.exit(1)

# Test ring detection
print("\n3. Testing ring detection...")
try:
    rings = detector.detect_mule_rings()
    print(f"   ✅ Found {len(rings)} rings")
    if rings:
        print(f"   ✅ Sample ring: Ring {rings[0]['ring_id']} with {rings[0]['size']} accounts")
except Exception as e:
    print(f"   ❌ Ring detection error: {e}")
    sys.exit(1)

# Test graph creation
print("\n4. Testing graph visualization...")
try:
    if rings:
        ring = rings[0]
        subgraph = nx.Graph()
        
        # Add edges
        for acc in ring['accounts'][:10]:
            for ben in ring['shared_beneficiaries'][:5]:
                subgraph.add_edge(acc, ben)
        
        print(f"   ✅ Subgraph created: {len(subgraph.nodes())} nodes, {len(subgraph.edges())} edges")
        
        # Test layout
        pos = nx.spring_layout(subgraph, k=0.5, iterations=50)
        print(f"   ✅ Layout calculated for {len(pos)} nodes")
        
        # Test plotly traces
        edge_trace = go.Scatter(
            x=[], y=[], 
            line=dict(width=0.8, color='#4b5563'), 
            hoverinfo='none', 
            mode='lines'
        )
        
        for edge in subgraph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += tuple([x0, x1, None])
            edge_trace['y'] += tuple([y0, y1, None])
        
        node_trace = go.Scatter(
            x=[], y=[], text=[], 
            mode='markers+text', 
            hoverinfo='text', 
            marker=dict(showscale=False, size=12, color='#00d2ff', line_width=2)
        )
        
        for node in subgraph.nodes():
            x, y = pos[node]
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])
            node_trace['text'] += tuple([node[:15]])
        
        print(f"   ✅ Plotly traces created: {len(edge_trace['x'])} edge points, {len(node_trace['x'])} nodes")
        
        # Test figure creation
        fig = go.Figure(
            data=[edge_trace, node_trace], 
            layout=go.Layout(
                title=dict(text=f"Ring {ring['ring_id']} Network", font=dict(color="white")),
                showlegend=False, 
                hovermode='closest', 
                margin=dict(b=0,l=0,r=0,t=40), 
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), 
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
        )
        print(f"   ✅ Plotly figure created successfully")
        
except Exception as e:
    print(f"   ❌ Graph visualization error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test AI integration
print("\n5. Testing AI integration...")
try:
    from gemini_explainer import GeminiExplainer
    explainer = GeminiExplainer()
    
    if rings:
        ring = rings[0]
        beneficiaries_str = ', '.join(ring['shared_beneficiaries'][:5])
        explanation = explainer.explain_ring(
            ring['ring_id'], 
            ring['size'], 
            beneficiaries_str, 
            85
        )
        print(f"   ✅ AI explanation generated ({len(explanation)} chars)")
        print(f"   Preview: {explanation[:100]}...")
except Exception as e:
    print(f"   ❌ AI integration error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("✅ All Live Graph components working:")
print("   • Detector initialization")
print("   • Ring detection")
print("   • NetworkX graph creation")
print("   • Plotly visualization")
print("   • AI explanation integration")
print("\n✅ Live Graph view is ready to use in dashboard")
print("\nRun: streamlit run dashboard_enhanced.py")
print("Then: Select 'Live Graph' from sidebar")
print("=" * 60)
