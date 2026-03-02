"""
Pytest configuration and fixtures
"""
import pytest
import pandas as pd
import networkx as nx
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def sample_cyber_data():
    """Generate sample cyber events data"""
    data = {
        'timestamp': [datetime.now() - timedelta(hours=i) for i in range(10)],
        'account_id': [f'ACC_{i:06d}' for i in range(10)],
        'event_type': ['login_success', 'login_fail', 'malware_signal', 'new_device', 
                      'foreign_ip', 'password_reset', 'login_success', 'login_fail',
                      'malware_signal', 'new_device'],
        'ip': [f'192.168.1.{i}' for i in range(10)],
        'device': ['iPhone15', 'SamsungS24', 'WindowsPC'] * 3 + ['Unknown'],
        'location': ['India', 'Romania', 'Nigeria', 'Singapore', 'UK'] * 2
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_transaction_data():
    """Generate sample transaction data"""
    data = {
        'timestamp': [datetime.now() - timedelta(hours=i) for i in range(5)],
        'account_id': [f'ACC_{i:06d}' for i in range(5)],
        'amount': [10000.0, 25000.0, 48000.0, 15000.0, 35000.0],
        'beneficiary': ['BEN_SG_001', 'BEN_NG_002', 'BEN_RO_003', 'BEN_IN_004', 'BEN_SG_001'],
        'type': ['UPI/NEFT'] * 5
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_graph():
    """Create a sample graph for testing"""
    G = nx.Graph()
    
    # Add accounts
    for i in range(5):
        G.add_node(f'ACC_{i:06d}', type='account')
    
    # Add IPs
    for i in range(3):
        G.add_node(f'IP_192.168.1.{i}', type='ip')
    
    # Add devices
    G.add_node('DEV_iPhone15', type='device')
    G.add_node('DEV_SamsungS24', type='device')
    
    # Add beneficiaries
    G.add_node('BEN_SG_001', type='beneficiary')
    G.add_node('BEN_NG_002', type='beneficiary')
    
    # Add edges
    G.add_edge('ACC_000000', 'IP_192.168.1.0')
    G.add_edge('ACC_000000', 'DEV_iPhone15')
    G.add_edge('ACC_000000', 'BEN_SG_001', amount=10000)
    
    G.add_edge('ACC_000001', 'IP_192.168.1.1')
    G.add_edge('ACC_000001', 'DEV_SamsungS24')
    G.add_edge('ACC_000001', 'BEN_SG_001', amount=25000)
    
    G.add_edge('ACC_000002', 'IP_192.168.1.2')
    G.add_edge('ACC_000002', 'DEV_iPhone15')
    G.add_edge('ACC_000002', 'BEN_NG_002', amount=48000)
    
    return G

@pytest.fixture
def real_data():
    """Load real generated data if available"""
    try:
        cyber_df = pd.read_csv('cyber_events.csv')
        txn_df = pd.read_csv('transactions.csv')
        return cyber_df, txn_df
    except FileNotFoundError:
        pytest.skip("Real data files not found")
