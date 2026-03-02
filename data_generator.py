import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
n = 20000
start_time = datetime.now() - timedelta(hours=24)

# Cyber events
cyber = pd.DataFrame({
    'timestamp': [start_time + timedelta(minutes=i*0.7) for i in range(n)],
    'account_id': np.random.choice([f'ACC_{i:06d}' for i in range(5000)], n),
    'event_type': np.random.choice(['login_success', 'login_fail', 'password_reset', 'new_device', 'foreign_ip', 'malware_signal'], n, p=[0.6, 0.1, 0.08, 0.08, 0.08, 0.06]),
    'ip': ['192.168.' + str(random.randint(1,255)) + '.' + str(random.randint(1,255)) if random.random()>0.2 else '45.67.' + str(random.randint(1,255)) + '.' + str(random.randint(1,255)) for _ in range(n)],
    'device': np.random.choice(['iPhone15', 'SamsungS24', 'WindowsPC', 'Unknown'], n),
    'location': np.random.choice(['India', 'Romania', 'Nigeria', 'Singapore', 'UK'], n, p=[0.7, 0.08, 0.08, 0.07, 0.07])
})

# Transactions (only for accounts that had cyber events)
txns = []
for acc in cyber['account_id'].unique()[:800]:
    base_time = random.choice(cyber[cyber['account_id']==acc]['timestamp'].tolist())
    for _ in range(random.randint(1,5)):
        txns.append({
            'timestamp': base_time + timedelta(minutes=random.randint(5,120)),
            'account_id': acc,
            'amount': round(random.uniform(8000, 49000), 2),  # just under common limits
            'beneficiary': random.choice(['BEN_SG_001', 'BEN_NG_002', 'BEN_RO_003', 'BEN_IN_004']),
            'type': 'UPI/NEFT'
        })

txns_df = pd.DataFrame(txns)

# ===== OPTIONAL: Blend with realistic PaySim/SAML-D data =====
# Uncomment to add small realistic dataset blend (requires Kaggle datasets)
try:
    # Try to load PaySim or SAML-D dataset if available
    # realistic_data = pd.read_csv('paysim_sample.csv')  # User must download separately
    # txns_df = pd.concat([txns_df, realistic_data.head(100)], ignore_index=True)
    # print("✅ Blended with realistic PaySim data")
    pass
except Exception as e:
    # Silently continue with mock data only
    pass
# ===== END OPTIONAL BLEND =====

cyber.to_csv('cyber_events.csv', index=False)
txns_df.to_csv('transactions.csv', index=False)
print("✅ Mock data generated! 20k events ready.")
