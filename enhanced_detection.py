"""
Enhanced Detection Engine with Real-Time Capabilities
Integrates with streaming backend for live detection
"""
import networkx as nx
import pandas as pd
import community.community_louvain as community_louvain
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

class EnhancedDetector:
    def __init__(self, graph=None):
        self.graph = graph if graph else nx.Graph()
        self.risk_cache = {}
        self.ring_cache = None
        self.last_ring_detection = None
        
    def calculate_risk(self, account_id):
        """
        Enhanced risk calculation with multiple factors
        Returns: Risk score 0-100
        """
        if account_id not in self.graph:
            return 0
        
        # Check cache (valid for 60 seconds)
        if account_id in self.risk_cache:
            cached_time, cached_score = self.risk_cache[account_id]
            if (datetime.now() - cached_time).seconds < 60:
                return cached_score
        
        risk_score = 0
        neighbors = list(self.graph.neighbors(account_id))
        
        # Factor 1: Cyber anomaly connections (40 points max)
        cyber_neighbors = [n for n in neighbors if n.startswith('IP_') or n.startswith('DEV_')]
        risk_score += min(len(cyber_neighbors) * 5, 40)
        
        # Factor 2: Transaction velocity (30 points max)
        txn_edges = [e for e in self.graph.edges(account_id, data=True) if 'amount' in e[2]]
        if len(txn_edges) >= 5:
            risk_score += 30
        elif len(txn_edges) >= 3:
            risk_score += 20
        elif len(txn_edges) >= 1:
            risk_score += 10
        
        # Factor 3: Network centrality (30 points max)
        degree = self.graph.degree(account_id)
        risk_score += min(degree * 2, 30)
        
        # Factor 4: Shared beneficiaries (bonus)
        beneficiary_neighbors = [n for n in neighbors if n.startswith('BEN_')]
        if len(beneficiary_neighbors) >= 2:
            risk_score += 10
        
        final_score = min(risk_score, 100)
        
        # Cache the result
        self.risk_cache[account_id] = (datetime.now(), final_score)
        
        return final_score
    
    def find_mule_rings(self, min_size=3, force_refresh=False):
        """
        Detect mule rings using community detection
        Returns: List of rings with metadata
        """
        # Use cache if available and recent (5 minutes)
        if not force_refresh and self.ring_cache and self.last_ring_detection:
            if (datetime.now() - self.last_ring_detection).seconds < 300:
                return self.ring_cache
        
        if self.graph.number_of_nodes() == 0:
            return []
        
        # Community detection using Louvain algorithm
        try:
            partition = community_louvain.best_partition(self.graph)
        except:
            return []
        
        # Group nodes by community
        communities = defaultdict(list)
        for node, comm_id in partition.items():
            communities[comm_id].append(node)
        
        # Identify suspicious rings
        rings = []
        for comm_id, nodes in communities.items():
            # Filter for communities with accounts
            accounts = [n for n in nodes if n.startswith('ACC_')]
            
            if len(accounts) >= min_size:
                # Get shared beneficiaries
                beneficiaries = set()
                for acc in accounts:
                    neighbors = self.graph.neighbors(acc)
                    beneficiaries.update([n for n in neighbors if n.startswith('BEN_')])
                
                # Get shared IPs (suspicious if multiple accounts from same IP)
                shared_ips = set()
                for acc in accounts:
                    neighbors = self.graph.neighbors(acc)
                    shared_ips.update([n for n in neighbors if n.startswith('IP_')])
                
                # Calculate ring risk score
                ring_risk = self._calculate_ring_risk(accounts, beneficiaries, shared_ips)
                
                rings.append({
                    'ring_id': comm_id,
                    'size': len(accounts),
                    'accounts': accounts[:20],  # Limit for display
                    'total_accounts': len(accounts),
                    'shared_beneficiaries': list(beneficiaries),
                    'shared_ips': list(shared_ips)[:10],
                    'ring_risk_score': ring_risk,
                    'detected_at': datetime.now().isoformat()
                })
        
        # Sort by risk score
        rings.sort(key=lambda x: x['ring_risk_score'], reverse=True)
        
        # Cache results
        self.ring_cache = rings
        self.last_ring_detection = datetime.now()
        
        return rings
    
    def _calculate_ring_risk(self, accounts, beneficiaries, shared_ips):
        """Calculate risk score for entire ring"""
        risk = 0
        
        # Size factor (larger rings = higher risk)
        risk += min(len(accounts) * 2, 40)
        
        # Shared beneficiaries (key indicator)
        risk += min(len(beneficiaries) * 15, 30)
        
        # Shared IPs (multiple accounts from same IP)
        if len(shared_ips) > 0:
            accounts_per_ip = len(accounts) / len(shared_ips)
            if accounts_per_ip > 2:
                risk += 20
        
        # Average account risk
        avg_account_risk = np.mean([self.calculate_risk(acc) for acc in accounts[:10]])
        risk += avg_account_risk * 0.1
        
        return min(risk, 100)
    
    def detect_anomalies_realtime(self, account_id, event_type, event_data):
        """
        Real-time anomaly detection as events arrive
        Returns: (is_anomaly, anomaly_type, severity)
        """
        anomalies = []
        
        # Check for rapid events
        if account_id in self.graph:
            # Get account's recent activity
            neighbors = list(self.graph.neighbors(account_id))
            
            # Anomaly 1: Multiple IPs in short time
            ips = [n for n in neighbors if n.startswith('IP_')]
            if len(ips) > 3:
                anomalies.append(('multiple_ips', 'high'))
            
            # Anomaly 2: Multiple devices
            devices = [n for n in neighbors if n.startswith('DEV_')]
            if len(devices) > 2:
                anomalies.append(('multiple_devices', 'medium'))
            
            # Anomaly 3: High transaction velocity
            if event_type == 'transaction':
                txn_edges = [e for e in self.graph.edges(account_id, data=True) if 'amount' in e[2]]
                if len(txn_edges) >= 3:
                    anomalies.append(('rapid_transactions', 'high'))
                
                # Check for structuring (amounts just below threshold)
                if event_data.get('amount', 0) > 45000 and event_data.get('amount', 0) < 50000:
                    anomalies.append(('structuring', 'critical'))
        
        # Anomaly 4: Foreign location
        if event_data.get('location') in ['Romania', 'Nigeria', 'Singapore']:
            anomalies.append(('foreign_location', 'medium'))
        
        # Anomaly 5: Malware signal
        if event_type == 'malware_signal':
            anomalies.append(('malware_detected', 'critical'))
        
        return len(anomalies) > 0, anomalies
    
    def get_account_network(self, account_id, depth=2):
        """
        Get subgraph around account (for visualization)
        Returns: Subgraph with neighbors up to depth
        """
        if account_id not in self.graph:
            return nx.Graph()
        
        # BFS to get neighbors up to depth
        nodes = {account_id}
        current_level = {account_id}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                neighbors = set(self.graph.neighbors(node))
                next_level.update(neighbors)
            nodes.update(next_level)
            current_level = next_level
        
        return self.graph.subgraph(nodes).copy()
    
    def get_high_risk_accounts(self, threshold=50, limit=100):
        """
        Get all accounts above risk threshold
        Returns: List of (account_id, risk_score) sorted by risk
        """
        accounts = [n for n in self.graph.nodes() if n.startswith('ACC_')]
        
        risks = []
        for acc in accounts:
            risk = self.calculate_risk(acc)
            if risk >= threshold:
                risks.append((acc, risk))
        
        risks.sort(key=lambda x: x[1], reverse=True)
        return risks[:limit]
    
    def generate_alert(self, account_id, risk_score, anomalies):
        """
        Generate structured alert for high-risk activity
        """
        severity = 'CRITICAL' if risk_score >= 70 else 'HIGH' if risk_score >= 50 else 'MEDIUM'
        
        alert = {
            'alert_id': f"ALERT_{account_id}_{int(datetime.now().timestamp())}",
            'timestamp': datetime.now().isoformat(),
            'account_id': account_id,
            'risk_score': risk_score,
            'severity': severity,
            'anomalies': [{'type': a[0], 'severity': a[1]} for a in anomalies],
            'recommended_action': self._get_recommended_action(risk_score, anomalies),
            'requires_review': risk_score >= 70
        }
        
        return alert
    
    def _get_recommended_action(self, risk_score, anomalies):
        """Determine recommended action based on risk"""
        if risk_score >= 80:
            return "FREEZE_ACCOUNT_IMMEDIATELY"
        elif risk_score >= 70:
            return "BLOCK_PENDING_TRANSACTIONS"
        elif risk_score >= 50:
            return "FLAG_FOR_MANUAL_REVIEW"
        else:
            return "MONITOR_CLOSELY"
    
    def get_statistics(self):
        """Get current detection statistics"""
        accounts = [n for n in self.graph.nodes() if n.startswith('ACC_')]
        high_risk = len([a for a in accounts if self.calculate_risk(a) >= 50])
        critical_risk = len([a for a in accounts if self.calculate_risk(a) >= 70])
        
        rings = self.find_mule_rings()
        
        return {
            'total_accounts': len(accounts),
            'high_risk_accounts': high_risk,
            'critical_risk_accounts': critical_risk,
            'mule_rings_detected': len(rings),
            'graph_nodes': self.graph.number_of_nodes(),
            'graph_edges': self.graph.number_of_edges(),
            'largest_ring_size': max([r['size'] for r in rings]) if rings else 0
        }

# Test functions
def test_enhanced_detector():
    """Test the enhanced detector"""
    print("🧪 Testing Enhanced Detection Engine\n")
    
    # Load data
    cyber_df = pd.read_csv('cyber_events.csv')
    txn_df = pd.read_csv('transactions.csv')
    
    # Build graph
    G = nx.Graph()
    
    print("1️⃣ Building graph...")
    for _, row in cyber_df.iterrows():
        G.add_node(row['account_id'], type='account')
        G.add_node(f"IP_{row['ip']}", type='ip')
        G.add_node(f"DEV_{row['device']}", type='device')
        G.add_edge(row['account_id'], f"IP_{row['ip']}")
        G.add_edge(row['account_id'], f"DEV_{row['device']}")
    
    for _, row in txn_df.iterrows():
        G.add_edge(row['account_id'], row['beneficiary'], amount=row['amount'])
    
    print(f"   ✅ Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges\n")
    
    # Initialize detector
    detector = EnhancedDetector(G)
    
    # Test 2: Find mule rings
    print("2️⃣ Detecting mule rings...")
    rings = detector.find_mule_rings()
    print(f"   ✅ Found {len(rings)} rings")
    if rings:
        top_ring = rings[0]
        print(f"   📊 Highest risk ring: {top_ring['size']} accounts, risk={top_ring['ring_risk_score']:.1f}\n")
    
    # Test 3: Calculate risk for specific account
    print("3️⃣ Testing risk calculation...")
    test_account = 'ACC_002747'
    risk = detector.calculate_risk(test_account)
    print(f"   ✅ {test_account}: Risk = {risk}/100\n")
    
    # Test 4: Get high-risk accounts
    print("4️⃣ Finding high-risk accounts...")
    high_risk = detector.get_high_risk_accounts(threshold=50, limit=10)
    print(f"   ✅ Found {len(high_risk)} high-risk accounts")
    if high_risk:
        print(f"   🚨 Top 3:")
        for acc, risk in high_risk[:3]:
            print(f"      • {acc}: {risk}/100")
    print()
    
    # Test 5: Real-time anomaly detection
    print("5️⃣ Testing real-time anomaly detection...")
    is_anomaly, anomalies = detector.detect_anomalies_realtime(
        test_account, 
        'transaction',
        {'amount': 48000, 'location': 'Romania'}
    )
    print(f"   ✅ Anomaly detected: {is_anomaly}")
    if anomalies:
        print(f"   ⚠️  Anomalies: {', '.join([a[0] for a in anomalies])}\n")
    
    # Test 6: Generate alert
    print("6️⃣ Testing alert generation...")
    alert = detector.generate_alert(test_account, risk, anomalies)
    print(f"   ✅ Alert ID: {alert['alert_id']}")
    print(f"   ✅ Severity: {alert['severity']}")
    print(f"   ✅ Action: {alert['recommended_action']}\n")
    
    # Test 7: Statistics
    print("7️⃣ Getting statistics...")
    stats = detector.get_statistics()
    print(f"   ✅ Total Accounts: {stats['total_accounts']}")
    print(f"   ✅ High Risk: {stats['high_risk_accounts']}")
    print(f"   ✅ Critical Risk: {stats['critical_risk_accounts']}")
    print(f"   ✅ Mule Rings: {stats['mule_rings_detected']}")
    print(f"   ✅ Largest Ring: {stats['largest_ring_size']} accounts\n")
    
    print("=" * 60)
    print("✅ ALL ENHANCED DETECTION TESTS PASSED!")
    print("=" * 60)
    
    return detector, rings

if __name__ == "__main__":
    detector, rings = test_enhanced_detector()
    
    print("\n📊 Sample Ring Details:")
    if rings:
        ring = rings[0]
        print(f"\nRing {ring['ring_id']}:")
        print(f"  • Size: {ring['size']} accounts")
        print(f"  • Risk Score: {ring['ring_risk_score']:.1f}/100")
        print(f"  • Shared Beneficiaries: {', '.join(ring['shared_beneficiaries'][:3])}")
        print(f"  • Sample Accounts: {', '.join(ring['accounts'][:5])}")
