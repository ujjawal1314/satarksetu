import google.generativeai as genai
import os
from dotenv import load_dotenv
from functools import lru_cache
import json
import random
import sys

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv()

class GeminiExplainer:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key and api_key != 'your_api_key_here':
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(
                    'gemini-1.5-flash',
                    generation_config={"response_mime_type": "application/json"}
                )
                self.api_available = True
                print("✅ Gemini API configured successfully with JSON mode")
            except Exception as e:
                self.model = None
                self.api_available = False
                print(f"⚠️ Gemini API configuration failed: {e}. Using fallback mode.")
        else:
            self.model = None
            self.api_available = False
            print("⚠️ GEMINI_API_KEY not found. Using fallback mode. See GEMINI_API_SETUP.md")
    
    @lru_cache(maxsize=128)
    def explain_ring(self, ring_id, ring_size, beneficiaries_str, risk_score):
        """Explain how a mule ring operates - LIVE GEMINI GENERATION #1"""
        
        if not self.api_available:
            return self._fallback_ring_explanation(ring_id, ring_size, beneficiaries_str)
        
        prompt = f"""Analyze this money mule ring and return JSON:

Ring ID: {ring_id}
Size: {ring_size} accounts
Shared Beneficiaries: {beneficiaries_str}
Risk Score: {risk_score}/100

Return JSON with these fields:
{{
  "operation_summary": "2-3 sentences on how this ring operates",
  "coordination_pattern": "How accounts are coordinated",
  "suspicion_reason": "Why this is highly suspicious",
  "recommended_action": "Specific action for investigators"
}}

Keep each field under 50 words."""

        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            
            result = f"""**🔗 Ring {ring_id} Analysis ({ring_size} accounts)**

**Operation**: {data.get('operation_summary', 'N/A')}

**Coordination**: {data.get('coordination_pattern', 'N/A')}

**Why Suspicious**: {data.get('suspicion_reason', 'N/A')}

**Action**: {data.get('recommended_action', 'N/A')}"""
            return result
            
        except Exception as e:
            print(f"Gemini API error in explain_ring: {e}")
            return self._fallback_ring_explanation(ring_id, ring_size, beneficiaries_str)
    
    @lru_cache(maxsize=128)
    def generate_victim_ad(self, account_id, risk_score):
        """Generate realistic fake job ad that recruited this victim - LIVE GEMINI GENERATION #2"""
        
        if not self.api_available:
            return self._fallback_victim_ad(account_id)
        
        prompt = f"""Generate a realistic fake job ad that likely recruited this money mule victim.

Account: {account_id}
Risk: {risk_score}/100

Return JSON:
{{
  "ad_text": "The fake job ad text (40-60 words, include emojis, make it look like Instagram/WhatsApp)",
  "platform": "Where victim saw it (Instagram/WhatsApp/Facebook/Telegram)",
  "promise": "What was promised (money amount, easy work, etc)",
  "victim_profile": "Likely victim demographic (student/unemployed/etc)",
  "reality": "What actually happened (1 sentence)"
}}"""

        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            
            result = f"""**🎭 Likely Recruitment Scenario for {account_id}**

**Platform**: {data.get('platform', 'Social Media')}

**The Fake Ad They Saw**:
_{data.get('ad_text', 'N/A')}_

**Promise**: {data.get('promise', 'Easy money')}

**Victim Profile**: {data.get('victim_profile', 'Vulnerable individual')}

**Reality**: {data.get('reality', 'Account used for money laundering, now faces criminal charges.')}

⚠️ **71% of Gen Z unaware this leads to criminal record**"""
            return result
            
        except Exception as e:
            print(f"Gemini API error in generate_victim_ad: {e}")
            return self._fallback_victim_ad(account_id)
    
    @lru_cache(maxsize=128)
    def generate_sar_narrative(self, account_id, risk_score, cyber_flags_str, fin_flags_str):
        """Generate professional SAR narrative - LIVE GEMINI GENERATION #3"""
        
        if not self.api_available:
            return self._fallback_sar_narrative(account_id, risk_score, cyber_flags_str, fin_flags_str)
        
        prompt = f"""Write a professional Suspicious Activity Report (SAR) narrative.

Account: {account_id}
Risk: {risk_score}/100
Cyber Flags: {cyber_flags_str}
Financial Flags: {fin_flags_str}

Return JSON:
{{
  "summary": "Executive summary (2 sentences)",
  "timeline": "Timeline of suspicious events (3-4 bullet points)",
  "red_flags": "Key red flags identified (3-4 items)",
  "basis": "Legal basis for suspicion (1-2 sentences)",
  "recommendation": "Recommended action"
}}

Use formal regulatory language."""

        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            
            result = f"""**📋 SUSPICIOUS ACTIVITY REPORT - {account_id}**

**SUMMARY**
{data.get('summary', 'N/A')}

**TIMELINE**
{data.get('timeline', 'N/A')}

**RED FLAGS IDENTIFIED**
{data.get('red_flags', 'N/A')}

**BASIS FOR SUSPICION**
{data.get('basis', 'N/A')}

**RECOMMENDATION**
{data.get('recommendation', 'Freeze account and investigate.')}

---
*Report generated: {self._get_timestamp()}*"""
            return result
            
        except Exception as e:
            print(f"Gemini API error in generate_sar_narrative: {e}")
            return self._fallback_sar_narrative(account_id, risk_score, cyber_flags_str, fin_flags_str)
    
    @lru_cache(maxsize=128)
    def explain_single_account(self, account_id, risk_score, cyber_flags_str, fin_flags_str):
        """Explain single account suspicious pattern - LIVE GEMINI GENERATION #4"""
        
        if not self.api_available:
            return self._fallback_single_account(account_id, risk_score, cyber_flags_str, fin_flags_str)
        
        prompt = f"""Analyze this suspicious account for financial crime investigators.

Account: {account_id}
Risk Score: {risk_score}/100
Cyber Flags: {cyber_flags_str}
Financial Flags: {fin_flags_str}

Return JSON:
{{
  "pattern_type": "Type of suspicious pattern (compromised/recruited mule/willing participant)",
  "explanation": "What the pattern indicates (2-3 sentences)",
  "victim_scenario": "How they were likely recruited (2 sentences)",
  "action": "Recommended immediate action"
}}"""

        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            
            result = f"""**🔍 Account Analysis: {account_id}**

**Pattern Type**: {data.get('pattern_type', 'Suspicious Activity')}

**What This Indicates**:
{data.get('explanation', 'N/A')}

**Likely Recruitment**:
{data.get('victim_scenario', 'N/A')}

**Recommended Action**: {data.get('action', 'Investigate immediately')}"""
            return result
            
        except Exception as e:
            print(f"Gemini API error in explain_single_account: {e}")
            return self._fallback_single_account(account_id, risk_score, cyber_flags_str, fin_flags_str)
    
    @lru_cache(maxsize=128)
    def generate_timeline_summary(self, total_events, total_txns, high_risk_count, rings_count):
        """Generate timeline summary of detection results - LIVE GEMINI GENERATION #5"""
        
        if not self.api_available:
            return self._fallback_timeline_summary(total_events, total_txns, high_risk_count, rings_count)
        
        prompt = f"""Summarize this 24-hour financial crime detection analysis.

Total Events: {total_events}
Total Transactions: {total_txns}
High-Risk Accounts: {high_risk_count}
Mule Rings: {rings_count}

Return JSON:
{{
  "executive_summary": "2-3 sentence overview of findings",
  "key_insights": "3-4 bullet points of key insights",
  "threat_level": "Overall threat level assessment",
  "next_steps": "Priority actions for next 24 hours"
}}"""

        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            
            result = f"""**📊 24-Hour Detection Summary**

**Executive Summary**:
{data.get('executive_summary', 'N/A')}

**Key Insights**:
{data.get('key_insights', 'N/A')}

**Threat Level**: {data.get('threat_level', 'Elevated')}

**Next 24 Hours Priority**:
{data.get('next_steps', 'Continue monitoring')}"""
            return result
            
        except Exception as e:
            print(f"Gemini API error in generate_timeline_summary: {e}")
            return self._fallback_timeline_summary(total_events, total_txns, high_risk_count, rings_count)
    
    @lru_cache(maxsize=128)
    def freeze_impact_simulation(self, ring_id, ring_size, estimated_amount):
        """Simulate impact of freezing a ring - LIVE GEMINI GENERATION #6"""
        
        if not self.api_available:
            return self._fallback_freeze_impact(ring_id, ring_size, estimated_amount)
        
        prompt = f"""Simulate the impact of freezing this money mule ring.

Ring ID: {ring_id}
Accounts: {ring_size}
Estimated Daily Volume: ₹{estimated_amount:,}

Return JSON:
{{
  "immediate_impact": "What happens immediately when frozen",
  "funds_saved": "Estimated funds that will be saved/recovered",
  "disruption_level": "Impact on criminal network (High/Medium/Low)",
  "victim_impact": "Impact on recruited victims",
  "next_actions": "What investigators should do next"
}}"""

        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            
            result = f"""**🛑 Freeze Impact Simulation - Ring {ring_id}**

**Immediate Impact**:
{data.get('immediate_impact', 'N/A')}

**Estimated Funds Saved**: {data.get('funds_saved', 'Significant amount')}

**Network Disruption**: {data.get('disruption_level', 'High')}

**Victim Impact**:
{data.get('victim_impact', 'Victims will be contacted and educated')}

**Next Actions**:
{data.get('next_actions', 'File SAR and investigate beneficiaries')}"""
            return result
            
        except Exception as e:
            print(f"Gemini API error in freeze_impact_simulation: {e}")
            return self._fallback_freeze_impact(ring_id, ring_size, estimated_amount)
    
    # ===== FALLBACK FUNCTIONS =====
    
    def _fallback_ring_explanation(self, ring_id, ring_size, beneficiaries_str):
        return f"""**🔗 Ring {ring_id} Analysis ({ring_size} accounts)**

**Operation**: Multiple accounts coordinated to receive and forward funds to same beneficiaries ({beneficiaries_str}). Classic mule recruitment network.

**Coordination**: Accounts show synchronized activity patterns - likely recruited by same operator through fake job ads or social media scams.

**Why Suspicious**: {ring_size} unrelated accounts sharing beneficiaries is statistically impossible without coordination. Indicates organized money laundering operation.

**Action**: Freeze all {ring_size} accounts immediately. File consolidated SAR. Investigate beneficiaries. Contact account holders (likely victims)."""
    
    def _fallback_victim_ad(self, account_id):
        ads = [
            "💰 Earn ₹15,000/week from home! No experience needed. Just receive & transfer payments. Apply now! 📱",
            "🏠 Work From Home - Payment Processing Agent. ₹20k/month guaranteed. Easy work, flexible hours! DM for details.",
            "💼 Urgent Hiring: Financial Assistant. Handle transactions from home. ₹18k/week + bonus! Students welcome!",
            "📱 Instagram Opportunity: Be a payment coordinator. ₹25k/month. No investment required!",
            "🎯 Part-Time Job: Process payments for international company. ₹12k/week. Work from anywhere!"
        ]
        
        return f"""**🎭 Likely Recruitment Scenario for {account_id}**

**Platform**: Instagram/WhatsApp

**The Fake Ad They Saw**:
_{random.choice(ads)}_

**Promise**: Easy money for simple work, no experience needed

**Victim Profile**: Likely student or unemployed person desperate for income

**Reality**: Account used for money laundering. Victim now faces criminal charges and frozen account.

⚠️ **71% of Gen Z unaware this leads to criminal record**"""
    
    def _fallback_sar_narrative(self, account_id, risk_score, cyber_flags_str, fin_flags_str):
        return f"""**📋 SUSPICIOUS ACTIVITY REPORT - {account_id}**

**SUMMARY**
Account {account_id} exhibits multiple indicators consistent with money mule activity. Risk score: {risk_score}/100. Pattern suggests recruited victim used for money laundering.

**TIMELINE**
• Cyber security flags detected: {cyber_flags_str or 'None'}
• Financial velocity flags: {fin_flags_str or 'None'}
• Activity consistent with compromised or recruited account
• Rapid fund movement following suspicious cyber events

**RED FLAGS IDENTIFIED**
• Multiple cyber security anomalies indicating compromise
• Transaction patterns consistent with structuring (amounts just below thresholds)
• Rapid transaction velocity inconsistent with normal account behavior
• Connections to known suspicious beneficiaries

**BASIS FOR SUSPICION**
Pattern consistent with money mule recruitment. Account shows signs of compromise followed by rapid fund movement. Transactions structured to avoid reporting thresholds. Likely victim of recruitment scam, but account actively used for money laundering.

**RECOMMENDATION**
Freeze account immediately. Block all pending transactions. Investigate beneficiaries. Contact account holder to assess if victim or willing participant. File with FinCEN.

---
*Report generated: {self._get_timestamp()}*"""
    
    def _fallback_single_account(self, account_id, risk_score, cyber_flags_str, fin_flags_str):
        return f"""**🔍 Account Analysis: {account_id}**

**Pattern Type**: Likely Recruited Money Mule

**What This Indicates**:
Account shows {risk_score}/100 risk score with flags: {cyber_flags_str}, {fin_flags_str}. Pattern consistent with recruited victim - account compromised or willingly provided for "easy money" job offer.

**Likely Recruitment**:
Victim probably responded to fake job ad on social media promising easy income for "payment processing." Didn't realize moving money for strangers is illegal money laundering.

**Recommended Action**: Freeze account, contact holder, file SAR, investigate beneficiaries"""
    
    def _fallback_timeline_summary(self, total_events, total_txns, high_risk_count, rings_count):
        return f"""**📊 24-Hour Detection Summary**

**Executive Summary**:
Analyzed {total_events:,} cyber events and {total_txns:,} transactions. Identified {high_risk_count} high-risk accounts and {rings_count} coordinated mule rings. Threat level: Elevated.

**Key Insights**:
• {rings_count} mule rings detected with coordinated activity
• {high_risk_count} accounts flagged for immediate review
• Multiple accounts showing compromise + rapid fund movement pattern
• Strong evidence of organized recruitment network

**Threat Level**: Elevated - Active mule recruitment operation detected

**Next 24 Hours Priority**:
Freeze critical accounts, file SARs, contact victims, investigate beneficiaries, monitor for new recruitment activity"""
    
    def _fallback_freeze_impact(self, ring_id, ring_size, estimated_amount):
        return f"""**🛑 Freeze Impact Simulation - Ring {ring_id}**

**Immediate Impact**:
All {ring_size} accounts frozen. Pending transactions blocked. Criminal network disrupted.

**Estimated Funds Saved**: ₹{estimated_amount:,} daily volume stopped. Potential recovery of recent transactions.

**Network Disruption**: High - Freezing {ring_size} accounts will significantly disrupt this mule network

**Victim Impact**:
Victims will be contacted, educated about scam, and offered support. Most are unaware they committed crime.

**Next Actions**:
File consolidated SAR for entire ring. Investigate all beneficiaries. Contact account holders. Monitor for new accounts in same network."""
    
    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

if __name__ == "__main__":
    # Test all 6 functions
    explainer = GeminiExplainer()
    
    print("\n=== Testing 6 Gemini Functions ===\n")
    
    # Test 1: Ring explanation
    print("1. RING EXPLANATION:")
    print(explainer.explain_ring(5, 12, "BEN_SG_001, BEN_RO_003", 85))
    
    # Test 2: Victim ad
    print("\n2. VICTIM AD:")
    print(explainer.generate_victim_ad("ACC_002747", 90))
    
    # Test 3: SAR narrative
    print("\n3. SAR NARRATIVE:")
    print(explainer.generate_sar_narrative("ACC_002747", 90, "malware, new_device", "rapid_transactions"))
    
    # Test 4: Single account
    print("\n4. SINGLE ACCOUNT:")
    print(explainer.explain_single_account("ACC_002747", 90, "malware, foreign_ip", "rapid_transactions"))
    
    # Test 5: Timeline summary
    print("\n5. TIMELINE SUMMARY:")
    print(explainer.generate_timeline_summary(20000, 2402, 2136, 286))
    
    # Test 6: Freeze impact
    print("\n6. FREEZE IMPACT:")
    print(explainer.freeze_impact_simulation(5, 12, 500000))
