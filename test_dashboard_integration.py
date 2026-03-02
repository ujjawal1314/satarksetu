"""
Test script to verify dashboard graph database integration
"""

print("Testing dashboard graph database integration...\n")

# Test imports
try:
    from dashboard_enhanced import initialize_detector, load_data
    print("✅ Dashboard imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)

# Test data loading
try:
    cyber, txn = load_data()
    print(f"✅ Data loaded: {len(cyber):,} cyber events, {len(txn):,} transactions")
except Exception as e:
    print(f"❌ Data loading error: {e}")
    exit(1)

# Test detector initialization
try:
    detector = initialize_detector(cyber, txn)
    print(f"✅ Detector initialized")
except Exception as e:
    print(f"❌ Detector initialization error: {e}")
    exit(1)

# Check database stats
try:
    if hasattr(detector, 'db_stats'):
        stats = detector.db_stats
        print(f"\n📊 Graph Database Status:")
        print(f"   Database: {stats['database']}")
        print(f"   Nodes: {stats['nodes']:,}")
        print(f"   Edges: {stats['edges']:,}")
        print(f"   Node Types: {stats['node_types']}")
        print(f"\n✅ Database status available in dashboard")
    else:
        print(f"⚠️  Warning: db_stats not found on detector")
except Exception as e:
    print(f"❌ Database stats error: {e}")
    exit(1)

# Test basic functionality
try:
    rings = detector.detect_mule_rings()
    print(f"\n✅ Mule ring detection working: {len(rings)} rings found")
    
    flagged = detector.get_flagged_accounts(threshold=50)
    print(f"✅ Risk scoring working: {len(flagged)} high-risk accounts")
    
except Exception as e:
    print(f"❌ Functionality test error: {e}")
    exit(1)

print(f"\n🎉 All tests passed! Dashboard is ready with graph database integration.")
print(f"\nTo run dashboard:")
print(f"  streamlit run dashboard_enhanced.py --server.maxUploadSize=200")
print(f"\nCheck sidebar for database status indicator!")
