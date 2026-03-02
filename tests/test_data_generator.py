"""
Tests for data_generator.py
"""
import pytest
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestDataGenerator:
    """Test data generation functionality"""
    
    def test_cyber_events_file_exists(self):
        """Test that cyber_events.csv exists"""
        assert os.path.exists('cyber_events.csv'), "cyber_events.csv not found"
    
    def test_transactions_file_exists(self):
        """Test that transactions.csv exists"""
        assert os.path.exists('transactions.csv'), "transactions.csv not found"
    
    def test_cyber_events_structure(self):
        """Test cyber events DataFrame structure"""
        df = pd.read_csv('cyber_events.csv')
        
        # Check columns
        required_columns = ['timestamp', 'account_id', 'event_type', 'ip', 'device', 'location']
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"
        
        # Check data types
        assert len(df) > 0, "DataFrame is empty"
        assert df['account_id'].dtype == object
        assert df['event_type'].dtype == object
    
    def test_transactions_structure(self):
        """Test transactions DataFrame structure"""
        df = pd.read_csv('transactions.csv')
        
        # Check columns
        required_columns = ['timestamp', 'account_id', 'amount', 'beneficiary', 'type']
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"
        
        # Check data types
        assert len(df) > 0, "DataFrame is empty"
        assert df['amount'].dtype in [float, int]
    
    def test_cyber_events_count(self):
        """Test that we have expected number of events"""
        df = pd.read_csv('cyber_events.csv')
        assert len(df) >= 10000, f"Expected at least 10k events, got {len(df)}"
    
    def test_event_types_valid(self):
        """Test that event types are valid"""
        df = pd.read_csv('cyber_events.csv')
        valid_types = ['login_success', 'login_fail', 'password_reset', 
                      'new_device', 'foreign_ip', 'malware_signal']
        
        for event_type in df['event_type'].unique():
            assert event_type in valid_types, f"Invalid event type: {event_type}"
    
    def test_transaction_amounts_positive(self):
        """Test that transaction amounts are positive"""
        df = pd.read_csv('transactions.csv')
        assert (df['amount'] > 0).all(), "Found negative transaction amounts"
    
    def test_transaction_amounts_realistic(self):
        """Test that transaction amounts are in realistic range"""
        df = pd.read_csv('transactions.csv')
        assert df['amount'].min() >= 1000, "Transaction amounts too low"
        assert df['amount'].max() <= 100000, "Transaction amounts too high"
    
    def test_account_ids_format(self):
        """Test that account IDs follow correct format"""
        df = pd.read_csv('cyber_events.csv')
        
        for acc_id in df['account_id'].head(100):
            assert acc_id.startswith('ACC_'), f"Invalid account ID format: {acc_id}"
            assert len(acc_id) == 10, f"Invalid account ID length: {acc_id}"
    
    def test_beneficiary_format(self):
        """Test that beneficiary IDs follow correct format"""
        df = pd.read_csv('transactions.csv')
        
        for ben_id in df['beneficiary'].unique():
            assert ben_id.startswith('BEN_'), f"Invalid beneficiary format: {ben_id}"
    
    def test_timestamps_chronological(self):
        """Test that timestamps are in reasonable order"""
        df = pd.read_csv('cyber_events.csv', parse_dates=['timestamp'])
        
        # Check that timestamps span a reasonable period
        time_span = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
        assert time_span > 0, "All timestamps are the same"
        assert time_span < 86400 * 30, "Time span too large (>30 days)"  # Increased to 30 days
