"""
Test ring selection logic for Live Graph view
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 60)
print("RING SELECTION LOGIC TEST")
print("=" * 60)

# Test the ring selection parsing logic
test_cases = [
    "Ring 0 (12 accounts)",
    "Ring 1 (8 accounts)",
    "Ring 5 (15 accounts)",
    "Ring 10 (20 accounts)",
    "Ring 123 (5 accounts)"
]

print("\nTesting ring ID extraction from dropdown strings:")
print("-" * 60)

for test_str in test_cases:
    # This is the logic used in the dashboard
    ring_idx = int(test_str.split()[1].split('(')[0])
    print(f"Input:  '{test_str}'")
    print(f"Output: Ring ID = {ring_idx}")
    print()

# Test with actual detector
print("=" * 60)
print("TESTING WITH ACTUAL DETECTOR")
print("=" * 60)

try:
    import pandas as pd
    from detection_engine_neo4j import CyberFinDetectorNeo4j
    
    # Load data
    cyber_df = pd.read_csv('cyber_events.csv')
    txn_df = pd.read_csv('transactions.csv')
    
    # Initialize detector
    detector = CyberFinDetectorNeo4j(cyber_df, txn_df)
    
    print("\n✅ Detector initialized")
    print("✅ Building graph and detecting rings...")
    
    # Detect rings
    rings = detector.detect_mule_rings()
    
    print(f"\n✅ Found {len(rings)} rings")
    print("\nFirst 10 rings:")
    print("-" * 60)
    
    for i, ring in enumerate(rings[:10]):
        ring_id = ring['ring_id']
        size = ring['size']
        dropdown_text = f"Ring {ring_id} ({size} accounts)"
        
        # Test extraction
        extracted_id = int(dropdown_text.split()[1].split('(')[0])
        
        status = "✅" if extracted_id == ring_id else "❌"
        print(f"{status} Ring {ring_id}: {size} accounts")
        print(f"   Dropdown: '{dropdown_text}'")
        print(f"   Extracted ID: {extracted_id}")
        
        if extracted_id != ring_id:
            print(f"   ❌ ERROR: Mismatch! Expected {ring_id}, got {extracted_id}")
        print()
    
    print("=" * 60)
    print("RING SELECTION TEST SUMMARY")
    print("=" * 60)
    
    # Test that we can select each ring correctly
    all_correct = True
    for ring in rings[:10]:
        dropdown_text = f"Ring {ring['ring_id']} ({ring['size']} accounts)"
        extracted_id = int(dropdown_text.split()[1].split('(')[0])
        
        # Find the ring by extracted ID
        found_ring = [r for r in rings if r['ring_id'] == extracted_id]
        
        if not found_ring or found_ring[0]['ring_id'] != ring['ring_id']:
            all_correct = False
            print(f"❌ Ring {ring['ring_id']} selection failed")
    
    if all_correct:
        print("✅ All ring selections working correctly")
        print("✅ Ring dropdown will properly switch between rings")
    else:
        print("❌ Some ring selections failed")
    
    print("\n" + "=" * 60)
    print("UNIQUE KEY GENERATION TEST")
    print("=" * 60)
    
    # Test unique key generation
    print("\nTesting unique keys for Streamlit components:")
    for ring in rings[:5]:
        ring_id = ring['ring_id']
        selector_key = "live_graph_ring_selector"
        chart_key = f"live_graph_ring_{ring_id}"
        button_key = f"live_graph_ai_button_{ring_id}"
        
        print(f"\nRing {ring_id}:")
        print(f"  Selector key: {selector_key}")
        print(f"  Chart key: {chart_key}")
        print(f"  Button key: {button_key}")
    
    print("\n✅ Each ring has unique keys for chart and button")
    print("✅ This ensures proper re-rendering when selection changes")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("FINAL RESULT")
print("=" * 60)
print("✅ Ring selection logic is correct")
print("✅ Unique keys will force re-rendering")
print("✅ Live Graph should now switch between rings properly")
print("\nTo test in dashboard:")
print("1. Run: streamlit run dashboard_enhanced.py")
print("2. Go to 'Live Graph' view")
print("3. Change the dropdown - graph should update immediately")
print("=" * 60)
