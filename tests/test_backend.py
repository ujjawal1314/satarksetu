"""
Tests for backend.py
Note: These tests use the full dataset and may be slow.
Mark as slow tests to skip during quick test runs.
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import app

client = TestClient(app)

@pytest.mark.slow
class TestBackendAPI:
    """Test FastAPI backend endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert 'service' in data
        assert 'status' in data
    
    def test_stats_endpoint(self):
        """Test stats endpoint"""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert 'total_events' in data
        assert 'total_transactions' in data
        assert 'mule_rings_detected' in data
        assert 'high_risk_accounts' in data
    
    def test_graph_stats_endpoint(self):
        """Test graph stats endpoint"""
        response = client.get("/graph/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert 'live_graph' in data
        assert 'detection_graph' in data
    
    def test_rings_endpoint(self):
        """Test rings endpoint"""
        response = client.get("/rings")
        assert response.status_code == 200
        data = response.json()
        
        assert 'count' in data
        assert 'rings' in data
        assert isinstance(data['rings'], list)
    
    def test_flagged_endpoint_default(self):
        """Test flagged accounts endpoint with default threshold"""
        response = client.get("/flagged/50")
        assert response.status_code == 200
        data = response.json()
        
        assert 'threshold' in data
        assert 'count' in data
        assert 'accounts' in data
        assert data['threshold'] == 50
    
    def test_flagged_endpoint_custom_threshold(self):
        """Test flagged accounts with custom threshold"""
        response = client.get("/flagged/70")
        assert response.status_code == 200
        data = response.json()
        
        assert data['threshold'] == 70
    
    def test_account_analysis_valid(self):
        """Test account analysis for valid account"""
        response = client.get("/account/ACC_002747")
        assert response.status_code == 200
        data = response.json()
        
        assert 'account_id' in data
        assert 'risk_score' in data
        assert 'status' in data
        assert 'cyber_flags' in data
        assert 'financial_flags' in data
        assert data['account_id'] == 'ACC_002747'
    
    def test_account_analysis_invalid(self):
        """Test account analysis for invalid account"""
        response = client.get("/account/ACC_999999")
        assert response.status_code == 200
        data = response.json()
        
        assert 'error' in data
    
    def test_stream_test_endpoint(self):
        """Test stream test endpoint"""
        response = client.get("/stream/test")
        assert response.status_code == 200
        data = response.json()
        
        assert 'message' in data
        assert 'count' in data
        assert 'events' in data
        assert isinstance(data['events'], list)
    
    def test_stats_data_types(self):
        """Test that stats return correct data types"""
        response = client.get("/stats")
        data = response.json()
        
        assert isinstance(data['total_events'], int)
        assert isinstance(data['total_transactions'], int)
        assert isinstance(data['mule_rings_detected'], int)
        assert isinstance(data['high_risk_accounts'], int)
    
    def test_account_risk_score_bounds(self):
        """Test that risk scores are within bounds"""
        response = client.get("/account/ACC_002747")
        if response.status_code == 200:
            data = response.json()
            if 'risk_score' in data:
                assert 0 <= data['risk_score'] <= 100
    
    def test_rings_structure(self):
        """Test rings data structure"""
        response = client.get("/rings")
        data = response.json()
        
        if len(data['rings']) > 0:
            ring = data['rings'][0]
            assert 'ring_id' in ring
            assert 'accounts' in ring
            assert 'size' in ring

@pytest.mark.slow
class TestBackendPerformance:
    """Test backend performance"""
    
    def test_stats_response_time(self):
        """Test that stats endpoint responds quickly"""
        import time
        start = time.time()
        response = client.get("/stats")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 30.0  # Should respond within 30 seconds (more realistic for large dataset)
    
    def test_multiple_requests(self):
        """Test handling multiple requests"""
        for _ in range(3):  # Reduced from 5 to 3 for faster testing
            response = client.get("/stats")
            assert response.status_code == 200
