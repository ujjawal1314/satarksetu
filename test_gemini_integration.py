"""
Test script to verify Gemini API integration
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from gemini_explainer import GeminiExplainer
from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 60)
print("GEMINI API INTEGRATION TEST")
print("=" * 60)

# Check API key
api_key = os.getenv('GEMINI_API_KEY')
if api_key and api_key != 'your_api_key_here':
    print(f"✅ API Key found: {api_key[:20]}...")
else:
    print("❌ API Key not configured or is placeholder")
    print("   Please update GEMINI_API_KEY in .env file")
    print("   Get your key from: https://makersuite.google.com/app/apikey")

print("\n" + "=" * 60)
print("TESTING GEMINI EXPLAINER")
print("=" * 60)

explainer = GeminiExplainer()

if explainer.api_available:
    print("\n✅ Gemini API is ACTIVE - Testing live generation...")
else:
    print("\n⚠️ Gemini API not available - Using FALLBACK mode")
    print("   All outputs will be pre-written templates")

print("\n" + "-" * 60)
print("TEST 1: Ring Explanation")
print("-" * 60)
result = explainer.explain_ring(5, 12, "BEN_SG_001, BEN_RO_003", 85)
print(result[:200] + "..." if len(result) > 200 else result)

print("\n" + "-" * 60)
print("TEST 2: Victim Ad Generation")
print("-" * 60)
result = explainer.generate_victim_ad("ACC_002747", 90)
print(result[:200] + "..." if len(result) > 200 else result)

print("\n" + "-" * 60)
print("TEST 3: SAR Narrative")
print("-" * 60)
result = explainer.generate_sar_narrative("ACC_002747", 90, "malware, new_device", "rapid_transactions")
print(result[:200] + "..." if len(result) > 200 else result)

print("\n" + "-" * 60)
print("TEST 4: Single Account Analysis")
print("-" * 60)
result = explainer.explain_single_account("ACC_002747", 90, "malware, foreign_ip", "rapid_transactions")
print(result[:200] + "..." if len(result) > 200 else result)

print("\n" + "-" * 60)
print("TEST 5: Timeline Summary")
print("-" * 60)
result = explainer.generate_timeline_summary(20000, 2402, 2136, 286)
print(result[:200] + "..." if len(result) > 200 else result)

print("\n" + "-" * 60)
print("TEST 6: Freeze Impact Simulation")
print("-" * 60)
result = explainer.freeze_impact_simulation(5, 12, 500000)
print(result[:200] + "..." if len(result) > 200 else result)

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
if explainer.api_available:
    print("✅ All 6 Gemini functions are working with LIVE AI generation")
    print("   The dashboard will show real-time AI analysis")
else:
    print("⚠️ Using FALLBACK mode with pre-written templates")
    print("   To enable live AI generation:")
    print("   1. Get API key from: https://makersuite.google.com/app/apikey")
    print("   2. Update GEMINI_API_KEY in .env file")
    print("   3. Restart the dashboard")

print("\n" + "=" * 60)
print("DASHBOARD INTEGRATION")
print("=" * 60)
print("The following buttons in the dashboard will trigger AI analysis:")
print("  • Overview Tab: '📊 Generate AI Timeline Summary'")
print("  • Ring Analysis Tab: '🔗 Explain Ring Pattern', '🎭 Show Victim Scenario', '🛑 Freeze Impact'")
print("  • Account Lookup Tab: '📋 Generate SAR Narrative', '🔍 Explain Account Pattern', '🎭 Show Recruitment Scenario'")
print("\nRun dashboard: streamlit run dashboard_enhanced.py")
print("=" * 60)
