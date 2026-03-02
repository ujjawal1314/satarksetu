from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import networkx as nx
from datetime import datetime
import time
import json
import asyncio
from typing import List
from detection_engine import CyberFinDetector

app = FastAPI(title="CyberFin Fusion - Streaming Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
G = nx.Graph()  # Live graph
active_connections: List[WebSocket] = []

# Load data
cyber_df = pd.read_csv('cyber_events.csv', parse_dates=['timestamp'])
txn_df = pd.read_csv('transactions.csv', parse_dates=['timestamp'])

# Initialize detector
detector = CyberFinDetector(cyber_df, txn_df)
detector.build_graph()

print(f"✅ Backend initialized: {len(cyber_df)} events, {len(txn_df)} transactions")

# Streaming simulation
def stream_events():
    """Generator that simulates real-time event streaming"""
    event_count = 0
    
    # Stream cyber events
    for idx, row in cyber_df.iterrows():
        # Add to live graph
        G.add_node(row['account_id'], type='account')
        G.add_node(row['ip'], type='ip')
        G.add_node(row['device'], type='device')
        G.add_edge(row['account_id'], row['ip'], relation='login')
        G.add_edge(row['account_id'], row['device'], relation='device')
        
        event = {
            'type': 'cyber_event',
            'timestamp': row['timestamp'].isoformat(),
            'account_id': row['account_id'],
            'event_type': row['event_type'],
            'ip': row['ip'],
            'device': row['device'],
            'location': row['location'],
            'graph_nodes': G.number_of_nodes(),
            'graph_edges': G.number_of_edges()
        }
        
        event_count += 1
        if event_count % 100 == 0:
            time.sleep(0.05)  # Slight delay every 100 events for demo effect
        
        yield f"data: {json.dumps(event)}\n\n"
    
    # Stream transactions
    for idx, row in txn_df.iterrows():
        # Add to live graph
        G.add_edge(row['account_id'], row['beneficiary'], 
                  amount=float(row['amount']), relation='transaction')
        
        # Check if this triggers a risk alert
        risk_score = detector.calculate_risk_score(row['account_id'])
        alert = risk_score >= 70
        
        event = {
            'type': 'transaction',
            'timestamp': row['timestamp'].isoformat(),
            'account_id': row['account_id'],
            'amount': float(row['amount']),
            'beneficiary': row['beneficiary'],
            'txn_type': row['type'],
            'risk_score': risk_score,
            'alert': alert,
            'graph_nodes': G.number_of_nodes(),
            'graph_edges': G.number_of_edges()
        }
        
        event_count += 1
        if event_count % 50 == 0:
            time.sleep(0.05)
        
        yield f"data: {json.dumps(event)}\n\n"

@app.get("/")
def root():
    return {
        "service": "CyberFin Fusion Streaming Backend",
        "status": "active",
        "version": "1.0",
        "endpoints": {
            "stream": "/stream (SSE)",
            "websocket": "/ws",
            "stats": "/stats",
            "graph": "/graph/stats"
        }
    }

@app.get("/stream")
def stream():
    """Server-Sent Events (SSE) endpoint for real-time streaming"""
    return StreamingResponse(
        stream_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/stats")
def get_stats():
    """Get current system statistics"""
    rings = detector.detect_mule_rings()
    flagged = detector.get_flagged_accounts(threshold=50)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_events": len(cyber_df),
        "total_transactions": len(txn_df),
        "total_accounts": cyber_df['account_id'].nunique(),
        "mule_rings_detected": len(rings),
        "high_risk_accounts": len(flagged),
        "graph": {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges()
        },
        "detection_graph": {
            "nodes": detector.graph.number_of_nodes(),
            "edges": detector.graph.number_of_edges()
        }
    }

@app.get("/graph/stats")
def get_graph_stats():
    """Get detailed graph statistics"""
    return {
        "live_graph": {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "density": nx.density(G) if G.number_of_nodes() > 0 else 0
        },
        "detection_graph": {
            "nodes": detector.graph.number_of_nodes(),
            "edges": detector.graph.number_of_edges(),
            "density": nx.density(detector.graph)
        }
    }

@app.get("/rings")
def get_rings():
    """Get all detected mule rings"""
    rings = detector.detect_mule_rings()
    return {
        "count": len(rings),
        "rings": rings[:20]  # Top 20
    }

@app.get("/flagged/{threshold}")
def get_flagged(threshold: int = 50):
    """Get flagged accounts above threshold"""
    flagged = detector.get_flagged_accounts(threshold=threshold)
    return {
        "threshold": threshold,
        "count": len(flagged),
        "accounts": flagged[:50]  # Top 50
    }

@app.get("/account/{account_id}")
def analyze_account(account_id: str):
    """Analyze specific account"""
    if account_id not in cyber_df['account_id'].values:
        return {"error": "Account not found"}
    
    risk_score = detector.calculate_risk_score(account_id)
    cyber_flags = detector.detect_cyber_anomalies(account_id)
    fin_flags = detector.detect_financial_velocity(account_id)
    
    # Get recent activity
    recent_cyber = cyber_df[cyber_df['account_id'] == account_id].tail(10)
    recent_txns = txn_df[txn_df['account_id'] == account_id].tail(10)
    
    return {
        "account_id": account_id,
        "risk_score": risk_score,
        "status": "critical" if risk_score >= 70 else "high" if risk_score >= 50 else "low",
        "cyber_flags": cyber_flags,
        "financial_flags": fin_flags,
        "recent_events": len(recent_cyber),
        "recent_transactions": len(recent_txns),
        "graph_degree": detector.graph.degree(account_id) if account_id in detector.graph else 0
    }

# WebSocket support for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for bidirectional real-time communication"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial stats
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to CyberFin Fusion",
            "stats": {
                "events": len(cyber_df),
                "transactions": len(txn_df),
                "rings": len(detector.detect_mule_rings())
            }
        })
        
        # Keep connection alive and send periodic updates
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            # Echo back with stats
            await websocket.send_json({
                "type": "update",
                "received": data,
                "timestamp": datetime.now().isoformat(),
                "graph_nodes": G.number_of_nodes(),
                "graph_edges": G.number_of_edges()
            })
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("Client disconnected")

@app.get("/stream/test")
def stream_test():
    """Test endpoint - returns first 100 events"""
    events = []
    count = 0
    
    for idx, row in cyber_df.head(100).iterrows():
        events.append({
            'type': 'cyber_event',
            'account_id': row['account_id'],
            'event_type': row['event_type'],
            'timestamp': row['timestamp'].isoformat()
        })
        count += 1
    
    return {
        "message": "Test stream",
        "count": count,
        "events": events
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting CyberFin Fusion Streaming Backend...")
    print("📊 Endpoints:")
    print("   • Main: http://localhost:8000")
    print("   • Stream: http://localhost:8000/stream")
    print("   • Stats: http://localhost:8000/stats")
    print("   • WebSocket: ws://localhost:8000/ws")
    print("   • Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
