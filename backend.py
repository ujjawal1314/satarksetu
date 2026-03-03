from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import networkx as nx
from datetime import datetime
import time
import json
from typing import List
from uuid import uuid4

from detection_engine import CyberFinDetector
from detection_engine_neo4j import CyberFinDetectorNeo4j
from repositories import AccountRepository
from api_models import FreezeAccountRequest, TransactionRequest
from neo4j_service import get_neo4j_service

# Load environment variables from .env when running locally.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
repo = AccountRepository()
neo4j_service = get_neo4j_service()

# Load data
cyber_df = pd.read_csv("cyber_events.csv", parse_dates=["timestamp"])
txn_df = pd.read_csv("transactions.csv", parse_dates=["timestamp"])

# Initialize detector with fallback (Neo4j auth failure should not crash backend)
try:
    detector = CyberFinDetector(cyber_df, txn_df)
    detector.build_graph()
    print("✅ Detector mode: Neo4j direct")
except Exception as exc:
    print(f"⚠️ Neo4j direct detector failed ({exc}). Falling back to local graph mode.")
    detector = CyberFinDetectorNeo4j(cyber_df, txn_df, use_neo4j=False)
    detector.build_graph()
    print("✅ Detector mode: Local NetworkX fallback")

print(f"✅ Backend initialized: {len(cyber_df)} events, {len(txn_df)} transactions")


def get_detection_graph() -> nx.Graph:
    if hasattr(detector, "graph"):
        return detector.graph
    if hasattr(detector, "get_networkx_graph"):
        return detector.get_networkx_graph()
    return nx.Graph()


def bootstrap_accounts() -> None:
    """Ensure accounts table has baseline records for demo and persistence."""
    accounts = set(cyber_df["account_id"].unique()).union(set(txn_df["account_id"].unique()))
    for acc in accounts:
        repo.ensure_account(str(acc))
        risk = detector.calculate_risk_score(str(acc))
        repo.upsert_account_risk(str(acc), int(risk))


# Keep startup fast/reliable for demos. Accounts are created/updated on-demand.
# bootstrap_accounts()


def get_account_status(account_id: str):
    account = repo.get_account(account_id)
    if not account:
        return None
    return account.get("status", "ACTIVE")


def sync_risk(account_id: str, default_status: str = "ACTIVE") -> int:
    risk = int(detector.calculate_risk_score(account_id))
    repo.upsert_account_risk(account_id, risk, default_status=default_status)
    return risk


def require_neo4j():
    if not neo4j_service.ensure_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "Neo4j unavailable. Verify NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD and Neo4j service status. "
                "If backend runs in Docker, localhost points to the container; use host.docker.internal:7687 "
                "or a Neo4j service name on the same Docker network."
            ),
        )


# Streaming simulation
def stream_events():
    """Generator that simulates real-time event streaming"""
    event_count = 0

    # Stream cyber events
    for _, row in cyber_df.iterrows():
        # Add to live graph
        G.add_node(row["account_id"], type="account")
        G.add_node(row["ip"], type="ip")
        G.add_node(row["device"], type="device")
        G.add_edge(row["account_id"], row["ip"], relation="login")
        G.add_edge(row["account_id"], row["device"], relation="device")

        event = {
            "type": "cyber_event",
            "timestamp": row["timestamp"].isoformat(),
            "account_id": row["account_id"],
            "event_type": row["event_type"],
            "ip": row["ip"],
            "device": row["device"],
            "location": row["location"],
            "graph_nodes": G.number_of_nodes(),
            "graph_edges": G.number_of_edges(),
        }

        event_count += 1
        if event_count % 100 == 0:
            time.sleep(0.05)

        yield f"data: {json.dumps(event)}\\n\\n"

    # Stream transactions
    for _, row in txn_df.iterrows():
        G.add_edge(row["account_id"], row["beneficiary"], amount=float(row["amount"]), relation="transaction")

        risk_score = detector.calculate_risk_score(row["account_id"])
        alert = risk_score >= 70

        event = {
            "type": "transaction",
            "timestamp": row["timestamp"].isoformat(),
            "account_id": row["account_id"],
            "amount": float(row["amount"]),
            "beneficiary": row["beneficiary"],
            "txn_type": row["type"],
            "risk_score": risk_score,
            "alert": alert,
            "graph_nodes": G.number_of_nodes(),
            "graph_edges": G.number_of_edges(),
        }

        event_count += 1
        if event_count % 50 == 0:
            time.sleep(0.05)

        yield f"data: {json.dumps(event)}\\n\\n"


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
            "graph": "/graph",
            "freeze_account": "POST /accounts/{account_id}/freeze",
            "process_transaction": "POST /transactions",
            "process_transaction_legacy": "POST /transactions/process",
            "demo_suspicious": "POST /transactions/demo-suspicious",
        },
    }


@app.get("/stream")
def stream():
    """Server-Sent Events (SSE) endpoint for real-time streaming"""
    return StreamingResponse(
        stream_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/stats")
def get_stats():
    rings = detector.detect_mule_rings()
    flagged = detector.get_flagged_accounts(threshold=50)
    detection_graph = get_detection_graph()

    return {
        "timestamp": datetime.now().isoformat(),
        "total_events": len(cyber_df),
        "total_transactions": len(txn_df),
        "total_accounts": cyber_df["account_id"].nunique(),
        "mule_rings_detected": len(rings),
        "high_risk_accounts": len(flagged),
        "graph": {"nodes": G.number_of_nodes(), "edges": G.number_of_edges()},
        "detection_graph": {
            "nodes": detection_graph.number_of_nodes(),
            "edges": detection_graph.number_of_edges(),
        },
        "frozen_accounts": repo.frozen_accounts_count(),
        "blocked_transactions": repo.blocked_transactions_count(),
    }


@app.get("/graph/stats")
def get_graph_stats():
    detection_graph = get_detection_graph()
    return {
        "live_graph": {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "density": nx.density(G) if G.number_of_nodes() > 0 else 0,
        },
        "detection_graph": {
            "nodes": detection_graph.number_of_nodes(),
            "edges": detection_graph.number_of_edges(),
            "density": nx.density(detection_graph) if detection_graph.number_of_nodes() > 0 else 0,
        },
    }


@app.get("/rings")
def get_rings():
    rings = detector.detect_mule_rings()
    return {"count": len(rings), "rings": rings[:20]}


@app.get("/flagged/{threshold}")
def get_flagged(threshold: int = 50):
    flagged = detector.get_flagged_accounts(threshold=threshold)
    return {"threshold": threshold, "count": len(flagged), "accounts": flagged[:50]}


@app.get("/account/{account_id}")
def analyze_account(account_id: str):
    if account_id not in cyber_df["account_id"].values:
        return {"error": "Account not found"}

    risk_score = sync_risk(account_id)
    cyber_flags = detector.detect_cyber_anomalies(account_id)
    fin_flags = detector.detect_financial_velocity(account_id)
    if neo4j_service.available:
        account = neo4j_service.get_account(account_id)
        if not account:
            repo_account = repo.get_account(account_id) or repo.ensure_account(account_id)
            account = {"status": repo_account.get("status", "ACTIVE")}
    else:
        account = repo.get_account(account_id) or repo.ensure_account(account_id)
    detection_graph = get_detection_graph()

    recent_cyber = cyber_df[cyber_df["account_id"] == account_id].tail(10)
    recent_txns = txn_df[txn_df["account_id"] == account_id].tail(10)

    return {
        "account_id": account_id,
        "risk_score": risk_score,
        "status": account.get("status", "ACTIVE"),
        "risk_bucket": "critical" if risk_score >= 70 else "high" if risk_score >= 50 else "low",
        "cyber_flags": cyber_flags,
        "financial_flags": fin_flags,
        "recent_events": len(recent_cyber),
        "recent_transactions": len(recent_txns),
        "graph_degree": detection_graph.degree(account_id) if account_id in detection_graph else 0,
    }


@app.get("/accounts")
def list_accounts():
    return {"accounts": repo.list_accounts()}


@app.get("/accounts/{account_id}/status")
def account_status(account_id: str):
    if neo4j_service.available:
        account = neo4j_service.get_account(account_id)
    else:
        account = repo.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {
        "account_id": account_id,
        "status": account.get("status", "ACTIVE"),
        "risk_score": int(account.get("risk_score", 0)),
    }


@app.post("/accounts/{account_id}/freeze")
def freeze_account(account_id: str, req: FreezeAccountRequest | None = None):
    require_neo4j()
    freeze_req = req or FreezeAccountRequest()
    risk_score = int(detector.calculate_risk_score(account_id)) if account_id in cyber_df["account_id"].values else 0

    account = neo4j_service.freeze_account(account_id, risk_score=risk_score)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found in Neo4j graph")

    # Keep relational state in sync for existing non-graph dashboards/metrics.
    repo.freeze_account(
        account_id,
        reason=freeze_req.reason,
        performed_by=freeze_req.performed_by,
    )
    return {"account": account, "message": "Account frozen"}


@app.post("/accounts/{account_id}/unfreeze")
def unfreeze_account(account_id: str, req: FreezeAccountRequest):
    if account_id not in cyber_df["account_id"].values:
        raise HTTPException(status_code=404, detail="Account not found")
    account = repo.unfreeze_account(account_id, reason=req.reason, performed_by=req.performed_by)
    return {"account": account, "message": "Account unfrozen"}


@app.post("/transactions")
@app.post("/transactions/process")
def process_transaction(req: TransactionRequest):
    require_neo4j()

    risk_score = int(detector.calculate_risk_score(req.from_account)) if req.from_account in cyber_df["account_id"].values else 0
    result = neo4j_service.create_transaction(
        from_id=req.from_account,
        to_id=req.to_account,
        amount=float(req.amount),
        txn_id=f"TXN_{uuid4().hex[:12].upper()}",
        risk_score=risk_score,
    )

    txn_payload = result["transaction"]
    repo.log_transaction(txn_payload)
    repo.upsert_account_risk(req.from_account, risk_score)

    if result["blocked"]:
        raise HTTPException(
            status_code=403,
            detail={
                "message": result.get("reason") or "Source account is frozen",
                "transaction": txn_payload,
            },
        )

    return {"transaction": txn_payload}


@app.get("/graph")
def get_graph():
    require_neo4j()
    return neo4j_service.fetch_graph()


@app.post("/transactions/demo-suspicious")
def demo_suspicious_transaction():
    suspicious_account = "ACC_002747" if "ACC_002747" in cyber_df["account_id"].values else str(cyber_df["account_id"].iloc[0])
    risk_score = sync_risk(suspicious_account)

    if risk_score < 70:
        risk_score = 82
        repo.upsert_account_risk(suspicious_account, risk_score)

    if neo4j_service.available:
        account_status = neo4j_service.get_account_status(suspicious_account) or "ACTIVE"
    else:
        account_status = get_account_status(suspicious_account)
    txn_status = "APPROVED" if account_status != "FROZEN" else "BLOCKED"

    txn_payload = {
        "txn_id": f"TXN_DEMO_{uuid4().hex[:10].upper()}",
        "from_account": suspicious_account,
        "to_account": "BEN_DEMO_HIGH_RISK",
        "amount": 49999.00,
        "timestamp": datetime.utcnow().isoformat(),
        "status": txn_status,
        "risk_score": risk_score,
    }
    repo.log_transaction(txn_payload)

    return {
        "transaction": txn_payload,
        "result": "blocked" if txn_status == "BLOCKED" else "created",
        "message": "Transaction blocked: account is frozen" if txn_status == "BLOCKED" else "Suspicious transaction created",
        "flagged_account": {
            "account_id": suspicious_account,
            "risk_score": risk_score,
            "eligible_for_freeze": risk_score >= 70,
            "status": account_status,
        },
    }


@app.get("/ops/metrics")
def ops_metrics():
    return {
        "total_frozen_accounts": repo.frozen_accounts_count(),
        "total_blocked_transactions": repo.blocked_transactions_count(),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        await websocket.send_json(
            {
                "type": "connection",
                "message": "Connected to CyberFin Fusion",
                "stats": {
                    "events": len(cyber_df),
                    "transactions": len(txn_df),
                    "rings": len(detector.detect_mule_rings()),
                },
            }
        )

        while True:
            data = await websocket.receive_text()
            await websocket.send_json(
                {
                    "type": "update",
                    "received": data,
                    "timestamp": datetime.now().isoformat(),
                    "graph_nodes": G.number_of_nodes(),
                    "graph_edges": G.number_of_edges(),
                }
            )

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("Client disconnected")


@app.get("/stream/test")
def stream_test():
    events = []
    count = 0

    for _, row in cyber_df.head(100).iterrows():
        events.append(
            {
                "type": "cyber_event",
                "account_id": row["account_id"],
                "event_type": row["event_type"],
                "timestamp": row["timestamp"].isoformat(),
            }
        )
        count += 1

    return {"message": "Test stream", "count": count, "events": events}


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
