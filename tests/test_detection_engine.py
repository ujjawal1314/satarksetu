"""
Tests for detection_engine.py
"""
import pytest
import pandas as pd
import networkx as nx
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from detection_engine import CyberFinDetector

class TestCyberFinDetector:
    """Test CyberFinDetector class"""
    
    def test_detector_initialization(self, sample_cyber_data, sample_transaction_data):
        """Test detector can be initialized"""
        detector = CyberFinDetector(sample_cyber_data, sample_transaction_data)
        assert detector is not None
        assert detector.cyber_df is not None
        assert detector.txn_df is not None
    
    def test_build_graph(self, sample_cyber_data, sample_transaction_data):
        """Test graph building"""
        detector = CyberFinDetector(sample_cyber_data, sample_transaction_data)
        detector.build_graph()
        
        assert detector.graph.number_of_nodes() > 0
        assert detector.graph.number_of_edges() > 0
    
    def test_detect_cyber_anomalies(self, sample_cyber_data, sample_transaction_data):
        """Test cyber anomaly detection"""
        detector = CyberFinDetector(sample_cyber_data, sample_transaction_data)
        detector.build_graph()
        
        account_id = sample_cyber_data['account_id'].iloc[0]
        flags = detector.detect_cyber_anomalies(account_id)
        
        assert isinstance(flags, list)
    
    def test_detect_financial_velocity(self, sample_cyber_data, sample_transaction_data):
        """Test financial velocity detection"""
        detector = CyberFinDetector(sample_cyber_data, sample_transaction_data)
        detector.build_graph()
        
        account_id = sample_transaction_data['account_id'].iloc[0]
        flags = detector.detect_financial_velocity(account_id)
        
        assert isinstance(flags, list)
    
    def test_calculate_risk_score(self, sample_cyber_data, sample_transaction_data):
        """Test risk score calculation"""
        detector = CyberFinDetector(sample_cyber_data, sample_transaction_data)
        detector.build_graph()
        
        account_id = sample_cyber_data['account_id'].iloc[0]
        score = detector.calculate_risk_score(account_id)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
    
    def test_detect_mule_rings(self, sample_cyber_data, sample_transaction_data):
        """Test mule ring detection"""
        detector = CyberFinDetector(sample_cyber_data, sample_transaction_data)
        detector.build_graph()
        
        rings = detector.detect_mule_rings()
        
        assert isinstance(rings, list)
        for ring in rings:
            assert 'ring_id' in ring
            assert 'accounts' in ring
            assert 'size' in ring
    
    def test_get_flagged_accounts(self, sample_cyber_data, sample_transaction_data):
        """Test getting flagged accounts"""
        detector = CyberFinDetector(sample_cyber_data, sample_transaction_data)
        detector.build_graph()
        
        flagged = detector.get_flagged_accounts(threshold=0)
        
        assert isinstance(flagged, list)
        for account in flagged:
            assert 'account_id' in account
            assert 'risk_score' in account
            assert 'cyber_flags' in account
            assert 'financial_flags' in account
    
    def test_risk_score_bounds(self, sample_cyber_data, sample_transaction_data):
        """Test that risk scores are within bounds"""
        detector = CyberFinDetector(sample_cyber_data, sample_transaction_data)
        detector.build_graph()
        
        for account_id in sample_cyber_data['account_id'].head(5):
            score = detector.calculate_risk_score(account_id)
            assert 0 <= score <= 100, f"Risk score {score} out of bounds"
    
    def test_empty_graph_handling(self):
        """Test handling of empty data"""
        empty_cyber = pd.DataFrame(columns=['timestamp', 'account_id', 'event_type', 'ip', 'device', 'location'])
        empty_txn = pd.DataFrame(columns=['timestamp', 'account_id', 'amount', 'beneficiary', 'type'])
        
        detector = CyberFinDetector(empty_cyber, empty_txn)
        detector.build_graph()
        
        assert detector.graph.number_of_nodes() == 0
        assert detector.graph.number_of_edges() == 0

class TestDetectorWithRealData:
    """Test detector with real generated data"""
    
    def test_real_data_detection(self, real_data):
        """Test detection with real data"""
        cyber_df, txn_df = real_data
        
        detector = CyberFinDetector(cyber_df, txn_df)
        detector.build_graph()
        
        # Test basic functionality
        assert detector.graph.number_of_nodes() > 1000
        assert detector.graph.number_of_edges() > 1000
        
        # Test ring detection
        rings = detector.detect_mule_rings()
        assert len(rings) > 0
        
        # Test flagged accounts
        flagged = detector.get_flagged_accounts(threshold=50)
        assert len(flagged) > 0
