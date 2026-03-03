"""
Enhanced Detection Engine with Neo4j Support
Hybrid implementation supporting both Neo4j and NetworkX
"""

import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from graph_database import GraphDatabaseFactory, GraphDatabaseInterface, NetworkXGraphDatabase
from mule_ai_detector import detect_mule_rings_with_ai


class CyberFinDetectorNeo4j:
    """Detection engine with graph database support"""
    
    def __init__(self, cyber_df, txn_df, use_neo4j=True):
        self.cyber_df = cyber_df
        self.txn_df = txn_df
        self.cyber_df['timestamp'] = pd.to_datetime(self.cyber_df['timestamp'])
        self.txn_df['timestamp'] = pd.to_datetime(self.txn_df['timestamp'])
        
        # Initialize graph database (Neo4j or NetworkX)
        self.db = GraphDatabaseFactory.create(use_neo4j=use_neo4j)
        self.risk_scores = {}
        
        print(f"Detector initialized with {self.db.get_stats()['database']}")
    
    def build_graph(self):
        """Build network graph in database"""
        print("Building graph in database...")
        
        # Clear existing data
        self.db.clear()
        
        # Add account-device edges
        for _, row in self.cyber_df.iterrows():
            # Add nodes
            self.db.add_node(row['account_id'], "Account")
            self.db.add_node(f"DEV_{row['device']}", "Device", device_type=row['device'])
            self.db.add_node(f"IP_{row['ip']}", "IP", ip_address=row['ip'], location=row['location'])
            
            # Add edges
            self.db.add_edge(row['account_id'], f"DEV_{row['device']}", "USES_DEVICE")
            self.db.add_edge(row['account_id'], f"IP_{row['ip']}", "ACCESSED_FROM")
        
        # Add account-beneficiary edges
        for _, row in self.txn_df.iterrows():
            # Add nodes
            self.db.add_node(row['account_id'], "Account")
            self.db.add_node(row['beneficiary'], "Beneficiary")
            
            # Add edge with transaction details
            self.db.add_edge(
                row['account_id'], 
                row['beneficiary'], 
                "SENT_TO",
                amount=float(row['amount']),
                timestamp=str(row['timestamp']),
                txn_type=row['type']
            )
        
        # Get statistics
        stats = self.db.get_stats()
        print(f"[DEBUG] Graph built: {stats['nodes']} nodes, {stats['edges']} edges")
        print(f"Graph built: {stats['nodes']} nodes, {stats['edges']} edges using {stats['database']}")
        
        return stats
    
    def detect_cyber_anomalies(self, account_id, time_window_minutes=60):
        """Detect suspicious cyber activity patterns"""
        recent_time = datetime.now() - timedelta(minutes=time_window_minutes)
        account_events = self.cyber_df[
            (self.cyber_df['account_id'] == account_id) & 
            (self.cyber_df['timestamp'] >= recent_time)
        ]
        
        flags = []
        if len(account_events[account_events['event_type'] == 'malware_signal']) > 0:
            flags.append('malware_detected')
        if len(account_events[account_events['event_type'] == 'new_device']) > 0:
            flags.append('new_device')
        if len(account_events[account_events['event_type'] == 'foreign_ip']) > 0:
            flags.append('foreign_ip')
        if len(account_events[account_events['event_type'] == 'password_reset']) > 0:
            flags.append('password_reset')
        if len(account_events[account_events['event_type'] == 'login_fail']) >= 3:
            flags.append('multiple_login_failures')
            
        return flags
    
    def detect_financial_velocity(self, account_id, time_window_minutes=120):
        """Detect rapid/high-value transactions"""
        recent_time = datetime.now() - timedelta(minutes=time_window_minutes)
        account_txns = self.txn_df[
            (self.txn_df['account_id'] == account_id) & 
            (self.txn_df['timestamp'] >= recent_time)
        ]
        
        flags = []
        if len(account_txns) >= 3:
            flags.append('rapid_transactions')
        if (account_txns['amount'] > 45000).any():
            flags.append('near_threshold_amount')
        if account_txns['amount'].sum() > 100000:
            flags.append('high_total_volume')
            
        return flags
    
    def detect_mule_rings(self):
        """Detect mule rings using AI model checkpoint (best_gnn_a_transactions.pth)."""
        ai_result = detect_mule_rings_with_ai(self.cyber_df, self.txn_df)
        if ai_result.used_ai:
            print(f"✅ Mule detection mode: AI model ({len(ai_result.rings)} rings)")
            return ai_result.rings

        # Fallback only if model runtime is unavailable.
        print(f"⚠️ Mule detection fallback: graph-community rules ({ai_result.reason})")
        print("Detecting mule rings using graph database...")

        communities = self.db.detect_communities()
        community_accounts = defaultdict(list)
        for node, comm_id in communities.items():
            if node.startswith('ACC_'):
                community_accounts[comm_id].append(node)

        suspicious_rings = []
        for comm_id, accounts in community_accounts.items():
            if len(accounts) >= 3:
                shared_beneficiaries = set()
                for acc in accounts:
                    neighbors = self.db.get_neighbors(acc)
                    beneficiaries = [n for n in neighbors if n.startswith('BEN_')]
                    shared_beneficiaries.update(beneficiaries)

                if len(shared_beneficiaries) > 0:
                    suspicious_rings.append({
                        'ring_id': comm_id,
                        'accounts': accounts,
                        'shared_beneficiaries': list(shared_beneficiaries),
                        'size': len(accounts)
                    })

        print(f"Found {len(suspicious_rings)} suspicious rings")
        return suspicious_rings
    
    def calculate_risk_score(self, account_id):
        """Calculate composite risk score (0-100)"""
        score = 0
        
        # Cyber anomaly score (40 points max)
        cyber_flags = self.detect_cyber_anomalies(account_id)
        score += len(cyber_flags) * 10
        
        # Financial velocity score (30 points max)
        fin_flags = self.detect_financial_velocity(account_id)
        score += len(fin_flags) * 10
        
        # Network centrality score (30 points max)
        degree = self.db.get_node_degree(account_id)
        score += min(degree * 2, 30)
        
        self.risk_scores[account_id] = min(score, 100)
        return self.risk_scores[account_id]
    
    def get_flagged_accounts(self, threshold=50):
        """Get all accounts above risk threshold"""
        flagged = []
        for account in self.cyber_df['account_id'].unique():
            score = self.calculate_risk_score(account)
            if score >= threshold:
                flagged.append({
                    'account_id': account,
                    'risk_score': score,
                    'cyber_flags': self.detect_cyber_anomalies(account),
                    'financial_flags': self.detect_financial_velocity(account)
                })
        
        return sorted(flagged, key=lambda x: x['risk_score'], reverse=True)
    
    def get_networkx_graph(self):
        """Get NetworkX graph for visualization (compatibility method)"""
        if isinstance(self.db, NetworkXGraphDatabase):
            return self.db.get_networkx_graph()
        else:
            # If using Neo4j, export to NetworkX for visualization
            import networkx as nx
            G = nx.Graph()
            
            # This is a simplified export - in production you'd query Neo4j
            # For now, rebuild from dataframes
            for _, row in self.cyber_df.iterrows():
                G.add_edge(row['account_id'], f"DEV_{row['device']}", type='device')
                G.add_edge(row['account_id'], f"IP_{row['ip']}", type='ip')
            
            for _, row in self.txn_df.iterrows():
                G.add_edge(row['account_id'], row['beneficiary'], 
                          type='transaction', amount=row['amount'])
            
            return G
    
    def close(self):
        """Close database connection"""
        if hasattr(self.db, 'close'):
            self.db.close()


if __name__ == "__main__":
    # Set UTF-8 encoding for console output (Windows compatibility)
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    # Test the detector with graph database
    print("\n=== Testing CyberFin Detector with Graph Database ===\n")
    
    cyber = pd.read_csv('cyber_events.csv')
    txns = pd.read_csv('transactions.csv')
    
    # Try Neo4j first, fallback to NetworkX
    detector = CyberFinDetectorNeo4j(cyber, txns, use_neo4j=True)
    stats = detector.build_graph()
    
    print(f"\n📊 Graph Statistics:")
    print(f"   Database: {stats['database']}")
    print(f"   Nodes: {stats['nodes']:,}")
    print(f"   Edges: {stats['edges']:,}")
    print(f"   Node Types: {stats['node_types']}")
    
    print("\n🔍 Detecting mule rings...")
    rings = detector.detect_mule_rings()
    print(f"Found {len(rings)} suspicious rings")
    for ring in rings[:3]:
        print(f"  Ring {ring['ring_id']}: {ring['size']} accounts → {ring['shared_beneficiaries']}")
    
    print("\n⚠️  Top 10 high-risk accounts:")
    flagged = detector.get_flagged_accounts(threshold=40)
    for acc in flagged[:10]:
        print(f"  {acc['account_id']}: Risk={acc['risk_score']} | {acc['cyber_flags']} | {acc['financial_flags']}")
    
    # Close connection
    detector.close()
    print("\n✅ Test complete!")
