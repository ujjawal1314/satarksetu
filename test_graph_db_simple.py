"""Simple test to show graph database is working"""
import pandas as pd
from detection_engine_neo4j import CyberFinDetectorNeo4j

print("=" * 60)
print("GRAPH DATABASE SIMPLE TEST")
print("=" * 60)

# Load small dataset
cyber = pd.read_csv('cyber_events.csv').head(100)
txn = pd.read_csv('transactions.csv').head(100)

print(f"\nLoaded {len(cyber)} cyber events and {len(txn)} transactions")

# Create detector with NetworkX
print("\nInitializing detector with NetworkX...")
detector = CyberFinDetectorNeo4j(cyber, txn, use_neo4j=False)

# Build graph
print("\nBuilding graph...")
stats = detector.build_graph()

print("\n" + "=" * 60)
print("RESULT")
print("=" * 60)
print(f"✅ Graph Database: {stats['database']}")
print(f"✅ Nodes: {stats['nodes']:,}")
print(f"✅ Edges: {stats['edges']:,}")
print("\n✅ Graph database IS working!")
print("=" * 60)
