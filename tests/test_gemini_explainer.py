"""
Tests for gemini_explainer.py
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gemini_explainer import GeminiExplainer

class TestGeminiExplainer:
    """Test GeminiExplainer class"""
    
    def test_initialization(self):
        """Test explainer initialization"""
        explainer = GeminiExplainer()
        assert explainer is not None
    
    def test_explain_mule_pattern_basic(self):
        """Test basic pattern explanation"""
        explainer = GeminiExplainer()
        
        account_data = {
            'account_id': 'ACC_000001',
            'risk_score': 75
        }
        cyber_flags = ['malware_detected', 'new_device']
        fin_flags = ['rapid_transactions']
        
        explanation = explainer.explain_mule_pattern(
            account_data, cyber_flags, fin_flags
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert 'ACC_000001' in explanation
    
    def test_explain_with_ring_info(self):
        """Test explanation with ring information"""
        explainer = GeminiExplainer()
        
        account_data = {'account_id': 'ACC_000001', 'risk_score': 85}
        cyber_flags = ['malware_detected']
        fin_flags = ['rapid_transactions', 'near_threshold_amount']
        ring_info = {
            'size': 12,
            'beneficiaries': ['BEN_SG_001', 'BEN_RO_003']
        }
        
        explanation = explainer.explain_mule_pattern(
            account_data, cyber_flags, fin_flags, ring_info
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
    
    def test_fallback_explanation(self):
        """Test fallback explanation (without API key)"""
        explainer = GeminiExplainer()
        
        account_data = {'account_id': 'ACC_000001', 'risk_score': 90}
        cyber_flags = ['malware_detected', 'new_device', 'foreign_ip']
        fin_flags = ['rapid_transactions', 'near_threshold_amount']
        
        explanation = explainer._fallback_explanation(
            account_data, cyber_flags, fin_flags, None
        )
        
        assert isinstance(explanation, str)
        assert 'ACC_000001' in explanation
        assert len(explanation) > 50
    
    def test_explanation_contains_risk_score(self):
        """Test that explanation mentions risk score"""
        explainer = GeminiExplainer()
        
        account_data = {'account_id': 'ACC_000001', 'risk_score': 95}
        cyber_flags = ['malware_detected']
        fin_flags = []
        
        explanation = explainer.explain_mule_pattern(
            account_data, cyber_flags, fin_flags
        )
        
        # Should mention high risk or critical
        assert any(word in explanation.lower() for word in ['risk', 'critical', 'high', 'freeze'])
    
    def test_explanation_with_no_flags(self):
        """Test explanation with no flags"""
        explainer = GeminiExplainer()
        
        account_data = {'account_id': 'ACC_000001', 'risk_score': 30}
        cyber_flags = []
        fin_flags = []
        
        explanation = explainer.explain_mule_pattern(
            account_data, cyber_flags, fin_flags
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
    
    def test_explanation_with_all_flags(self):
        """Test explanation with multiple flags"""
        explainer = GeminiExplainer()
        
        account_data = {'account_id': 'ACC_000001', 'risk_score': 100}
        cyber_flags = ['malware_detected', 'new_device', 'foreign_ip', 'password_reset']
        fin_flags = ['rapid_transactions', 'near_threshold_amount', 'high_total_volume']
        
        explanation = explainer.explain_mule_pattern(
            account_data, cyber_flags, fin_flags
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 100
    
    def test_recommended_action_critical(self):
        """Test recommended action for critical risk"""
        explainer = GeminiExplainer()
        
        account_data = {'account_id': 'ACC_000001', 'risk_score': 85}
        cyber_flags = ['malware_detected']
        fin_flags = ['rapid_transactions']
        
        explanation = explainer._fallback_explanation(
            account_data, cyber_flags, fin_flags, None
        )
        
        assert 'FREEZE' in explanation or 'freeze' in explanation
    
    def test_recommended_action_medium(self):
        """Test recommended action for medium risk"""
        explainer = GeminiExplainer()
        
        account_data = {'account_id': 'ACC_000001', 'risk_score': 55}
        cyber_flags = []
        fin_flags = ['rapid_transactions']
        
        explanation = explainer._fallback_explanation(
            account_data, cyber_flags, fin_flags, None
        )
        
        assert 'review' in explanation.lower() or 'monitor' in explanation.lower()
    
    def test_explanation_format(self):
        """Test that explanation is well-formatted"""
        explainer = GeminiExplainer()
        
        account_data = {'account_id': 'ACC_000001', 'risk_score': 75}
        cyber_flags = ['malware_detected']
        fin_flags = ['rapid_transactions']
        
        explanation = explainer.explain_mule_pattern(
            account_data, cyber_flags, fin_flags
        )
        
        # Should have some structure (sections, bullets, etc.)
        assert '\n' in explanation or '•' in explanation or '-' in explanation
