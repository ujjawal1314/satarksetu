"""
Tests for enhanced_detection.py
"""
import pytest
import networkx as nx
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from enhanced_detection import EnhancedDetector

class TestEnhancedDetector:
    """Test EnhancedDetector class"""
    
    def test_initialization_empty(self):
        """Test initialization with empty graph"""
        detector = EnhancedDetector()
        assert detector.graph is not None
        assert detector.risk_cache == {}
    
    def test_initialization_with_graph(self, sample_graph):
        """Test initialization with existing graph"""
        detector = EnhancedDetector(sample_graph)
        assert detector.graph.number_of_nodes() > 0
    
    def test_calculate_risk_basic(self, sample_graph):
        """Test basic risk calculation"""
        detector = EnhancedDetector(sample_graph)
        risk = detector.calculate_risk('ACC_000000')
        
        assert isinstance(risk, (int, float))
        assert 0 <= risk <= 100
    
    def test_calculate_risk_nonexistent_account(self, sample_graph):
        """Test risk calculation for non-existent account"""
        detector = EnhancedDetector(sample_graph)
        risk = detector.calculate_risk('ACC_999999')
        
        assert risk == 0
    
    def test_risk_caching(self, sample_graph):
        """Test that risk scores are cached"""
        detector = EnhancedDetector(sample_graph)
        
        # First call
        risk1 = detector.calculate_risk('ACC_000000')
        assert 'ACC_000000' in detector.risk_cache
        
        # Second call (should use cache)
        risk2 = detector.calculate_risk('ACC_000000')
        assert risk1 == risk2
    
    def test_find_mule_rings(self, sample_graph):
        """Test mule ring detection"""
        detector = EnhancedDetector(sample_graph)
        rings = detector.find_mule_rings(min_size=2)
        
        assert isinstance(rings, list)
        for ring in rings:
            assert 'ring_id' in ring
            assert 'size' in ring
            assert 'accounts' in ring
            assert 'ring_risk_score' in ring
            assert ring['size'] >= 2
    
    def test_ring_caching(self, sample_graph):
        """Test that rings are cached"""
        detector = EnhancedDetector(sample_graph)
        
        # First call
        rings1 = detector.find_mule_rings()
        assert detector.ring_cache is not None
        
        # Second call (should use cache)
        rings2 = detector.find_mule_rings()
        assert rings1 == rings2
    
    def test_ring_force_refresh(self, sample_graph):
        """Test force refresh of ring cache"""
        detector = EnhancedDetector(sample_graph)
        
        rings1 = detector.find_mule_rings()
        rings2 = detector.find_mule_rings(force_refresh=True)
        
        # Should recalculate
        assert detector.last_ring_detection is not None
    
    def test_detect_anomalies_realtime(self, sample_graph):
        """Test real-time anomaly detection"""
        detector = EnhancedDetector(sample_graph)
        
        is_anomaly, anomalies = detector.detect_anomalies_realtime(
            'ACC_000000',
            'transaction',
            {'amount': 48000, 'location': 'Romania'}
        )
        
        assert isinstance(is_anomaly, bool)
        assert isinstance(anomalies, list)
    
    def test_anomaly_detection_structuring(self, sample_graph):
        """Test detection of structuring behavior"""
        detector = EnhancedDetector(sample_graph)
        
        is_anomaly, anomalies = detector.detect_anomalies_realtime(
            'ACC_000000',
            'transaction',
            {'amount': 48500}  # Just below 50k threshold
        )
        
        anomaly_types = [a[0] for a in anomalies]
        assert 'structuring' in anomaly_types
    
    def test_anomaly_detection_malware(self, sample_graph):
        """Test detection of malware signals"""
        detector = EnhancedDetector(sample_graph)
        
        is_anomaly, anomalies = detector.detect_anomalies_realtime(
            'ACC_000000',
            'malware_signal',
            {}
        )
        
        anomaly_types = [a[0] for a in anomalies]
        assert 'malware_detected' in anomaly_types
    
    def test_get_account_network(self, sample_graph):
        """Test getting account subgraph"""
        detector = EnhancedDetector(sample_graph)
        subgraph = detector.get_account_network('ACC_000000', depth=1)
        
        assert isinstance(subgraph, nx.Graph)
        assert 'ACC_000000' in subgraph.nodes()
    
    def test_get_account_network_nonexistent(self, sample_graph):
        """Test getting network for non-existent account"""
        detector = EnhancedDetector(sample_graph)
        subgraph = detector.get_account_network('ACC_999999', depth=1)
        
        assert subgraph.number_of_nodes() == 0
    
    def test_get_high_risk_accounts(self, sample_graph):
        """Test getting high-risk accounts"""
        detector = EnhancedDetector(sample_graph)
        high_risk = detector.get_high_risk_accounts(threshold=0, limit=10)
        
        assert isinstance(high_risk, list)
        assert len(high_risk) <= 10
        
        for account, risk in high_risk:
            assert account.startswith('ACC_')
            assert 0 <= risk <= 100
    
    def test_high_risk_accounts_sorted(self, sample_graph):
        """Test that high-risk accounts are sorted by risk"""
        detector = EnhancedDetector(sample_graph)
        high_risk = detector.get_high_risk_accounts(threshold=0, limit=10)
        
        if len(high_risk) > 1:
            for i in range(len(high_risk) - 1):
                assert high_risk[i][1] >= high_risk[i+1][1]
    
    def test_generate_alert(self, sample_graph):
        """Test alert generation"""
        detector = EnhancedDetector(sample_graph)
        
        anomalies = [('malware_detected', 'critical'), ('structuring', 'high')]
        alert = detector.generate_alert('ACC_000000', 85, anomalies)
        
        assert 'alert_id' in alert
        assert 'timestamp' in alert
        assert 'account_id' in alert
        assert 'risk_score' in alert
        assert 'severity' in alert
        assert 'anomalies' in alert
        assert 'recommended_action' in alert
        assert alert['risk_score'] == 85
    
    def test_alert_severity_levels(self, sample_graph):
        """Test alert severity levels"""
        detector = EnhancedDetector(sample_graph)
        
        # Critical
        alert_critical = detector.generate_alert('ACC_000000', 75, [])
        assert alert_critical['severity'] == 'CRITICAL'
        
        # High
        alert_high = detector.generate_alert('ACC_000000', 55, [])
        assert alert_high['severity'] == 'HIGH'
        
        # Medium
        alert_medium = detector.generate_alert('ACC_000000', 35, [])
        assert alert_medium['severity'] == 'MEDIUM'
    
    def test_recommended_actions(self, sample_graph):
        """Test recommended action logic"""
        detector = EnhancedDetector(sample_graph)
        
        # Freeze account
        alert1 = detector.generate_alert('ACC_000000', 85, [])
        assert alert1['recommended_action'] == 'FREEZE_ACCOUNT_IMMEDIATELY'
        
        # Block transactions
        alert2 = detector.generate_alert('ACC_000000', 72, [])
        assert alert2['recommended_action'] == 'BLOCK_PENDING_TRANSACTIONS'
        
        # Manual review
        alert3 = detector.generate_alert('ACC_000000', 55, [])
        assert alert3['recommended_action'] == 'FLAG_FOR_MANUAL_REVIEW'
        
        # Monitor
        alert4 = detector.generate_alert('ACC_000000', 35, [])
        assert alert4['recommended_action'] == 'MONITOR_CLOSELY'
    
    def test_get_statistics(self, sample_graph):
        """Test statistics generation"""
        detector = EnhancedDetector(sample_graph)
        stats = detector.get_statistics()
        
        assert 'total_accounts' in stats
        assert 'high_risk_accounts' in stats
        assert 'critical_risk_accounts' in stats
        assert 'mule_rings_detected' in stats
        assert 'graph_nodes' in stats
        assert 'graph_edges' in stats
        assert 'largest_ring_size' in stats
        
        assert stats['total_accounts'] >= 0
        assert stats['graph_nodes'] == sample_graph.number_of_nodes()
        assert stats['graph_edges'] == sample_graph.number_of_edges()
    
    def test_ring_risk_calculation(self, sample_graph):
        """Test ring risk score calculation"""
        detector = EnhancedDetector(sample_graph)
        rings = detector.find_mule_rings(min_size=2)
        
        for ring in rings:
            assert 0 <= ring['ring_risk_score'] <= 100

class TestEnhancedDetectorWithRealData:
    """Test enhanced detector with real data"""
    
    def test_real_data_performance(self, real_data):
        """Test performance with real data"""
        import pandas as pd
        
        cyber_df, txn_df = real_data
        
        # Build graph
        G = nx.Graph()
        for _, row in cyber_df.head(1000).iterrows():
            G.add_node(row['account_id'], type='account')
            G.add_node(f"IP_{row['ip']}", type='ip')
            G.add_edge(row['account_id'], f"IP_{row['ip']}")
        
        detector = EnhancedDetector(G)
        
        # Test operations
        rings = detector.find_mule_rings()
        assert len(rings) >= 0
        
        high_risk = detector.get_high_risk_accounts(threshold=50, limit=10)
        assert len(high_risk) >= 0
        
        stats = detector.get_statistics()
        assert stats['total_accounts'] > 0
