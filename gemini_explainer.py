import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiExplainer:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key and api_key != 'your_api_key_here':
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.api_available = True
                print("✅ Gemini API configured successfully")
            except Exception as e:
                self.model = None
                self.api_available = False
                print(f"⚠️ Gemini API configuration failed: {e}. Using fallback mode.")
        else:
            self.model = None
            self.api_available = False
            print("⚠️ GEMINI_API_KEY not found or not configured. Using fallback explanations.")
    
    def explain_mule_pattern(self, account_data, cyber_flags, fin_flags, ring_info=None):
        """Generate human-readable explanation of mule behavior"""
        
        if not self.api_available:
            return self._fallback_explanation(account_data, cyber_flags, fin_flags, ring_info)
        
        prompt = f"""You are a financial crime analyst. Explain this suspicious account pattern in simple terms:

Account: {account_data['account_id']}
Risk Score: {account_data.get('risk_score', 'N/A')}/100

Cyber Security Flags:
{', '.join(cyber_flags) if cyber_flags else 'None'}

Financial Flags:
{', '.join(fin_flags) if fin_flags else 'None'}

{f"Part of Ring: {ring_info['size']} accounts sharing beneficiaries {ring_info['beneficiaries']}" if ring_info else ""}

Provide:
1. What this pattern indicates (2-3 sentences)
2. Likely victim scenario (how they were recruited - fake job, romance scam, etc.)
3. Recommended action

Keep it under 150 words, direct and actionable."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._fallback_explanation(account_data, cyber_flags, fin_flags, ring_info)
    
    def explain_ring_structure(self, ring_data):
        """Explain how a mule ring operates"""
        
        if not self.api_available:
            return self._fallback_ring_explanation(ring_data)
        
        prompt = f"""Explain this money mule ring in simple terms:

Ring Size: {ring_data['size']} accounts
Shared Beneficiaries: {len(ring_data.get('beneficiaries', []))}
Risk Score: {ring_data.get('risk_score', 'N/A')}/100

Explain:
1. How this ring likely operates
2. Coordination patterns
3. Why it's suspicious
4. Recommended action for the entire ring

Keep it under 120 words."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return self._fallback_ring_explanation(ring_data)
    
    def generate_victim_scenario(self, account_data):
        """Generate likely victim recruitment scenario"""
        
        if not self.api_available:
            return self._fallback_victim_scenario(account_data)
        
        prompt = f"""Generate a realistic victim recruitment scenario for this account:

Account: {account_data['account_id']}
Risk Score: {account_data.get('risk_score', 50)}/100

Create a brief story (80-100 words) about how this person was likely recruited as a money mule:
- What fake job ad or scam they saw
- What promises were made
- Why they didn't realize it was illegal
- Their likely demographic (student, unemployed, etc.)

Make it realistic and educational."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return self._fallback_victim_scenario(account_data)
    
    def suggest_investigation_steps(self, account_data, flags):
        """Suggest next steps for investigators"""
        
        if not self.api_available:
            return self._fallback_investigation_steps(account_data, flags)
        
        prompt = f"""As a financial crime investigator, suggest investigation steps for:

Account: {account_data['account_id']}
Risk: {account_data.get('risk_score', 50)}/100
Flags: {', '.join(flags[:5])}

Provide 4-5 specific investigation steps in order of priority.
Keep it under 100 words, actionable and specific."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return self._fallback_investigation_steps(account_data, flags)
    
    def generate_sar_narrative(self, account_data, cyber_flags, fin_flags):
        """Generate SAR (Suspicious Activity Report) narrative"""
        
        if not self.api_available:
            return self._fallback_sar_narrative(account_data, cyber_flags, fin_flags)
        
        prompt = f"""Write a professional SAR narrative for:

Account: {account_data['account_id']}
Risk Score: {account_data.get('risk_score', 50)}/100
Cyber Flags: {', '.join(cyber_flags)}
Financial Flags: {', '.join(fin_flags)}

Write in formal regulatory language:
1. Summary of suspicious activity
2. Timeline of events
3. Red flags identified
4. Basis for suspicion

Keep it under 150 words, professional tone."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return self._fallback_sar_narrative(account_data, cyber_flags, fin_flags)
    
    def explain_prevention_tips(self, scenario_type="general"):
        """Generate prevention tips for potential victims"""
        
        if not self.api_available:
            return self._fallback_prevention_tips(scenario_type)
        
        prompt = f"""Generate 5 prevention tips to help people avoid becoming money mules.

Focus on: {scenario_type}

Make them:
- Practical and actionable
- Easy to understand
- Specific warning signs
- What to do if approached

Keep it under 120 words."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return self._fallback_prevention_tips(scenario_type)
    
    def _fallback_explanation(self, account_data, cyber_flags, fin_flags, ring_info):
        """Fallback explanation when Gemini is unavailable"""
        
        explanation = f"**Account {account_data['account_id']} Analysis**\n\n"
        
        # Pattern detection
        if 'malware_detected' in cyber_flags or 'password_reset' in cyber_flags:
            explanation += "🚨 **Compromised Account Pattern**: "
            explanation += "Account shows signs of unauthorized access (malware/password reset). "
        
        if 'new_device' in cyber_flags and 'foreign_ip' in cyber_flags:
            explanation += "Accessed from new device and foreign location. "
        
        if 'rapid_transactions' in fin_flags:
            explanation += "\n\n💰 **Financial Red Flags**: Multiple rapid transactions detected. "
        
        if 'near_threshold_amount' in fin_flags:
            explanation += "Amounts just below reporting thresholds (structuring). "
        
        if ring_info:
            explanation += f"\n\n🔗 **Network Analysis**: Part of a {ring_info['size']}-account ring "
            explanation += f"sharing beneficiaries {', '.join(ring_info['beneficiaries'][:2])}. "
        
        # Victim scenario
        explanation += "\n\n**Likely Scenario**: "
        if len(cyber_flags) > 2:
            explanation += "Account holder likely victim of phishing/malware. "
        else:
            explanation += "Possible recruited mule (fake job offer, 'easy money' promise). "
        
        explanation += "Common tactics: Instagram/WhatsApp job ads, romance scams, or 'work from home' schemes."
        
        # Action
        explanation += "\n\n**Recommended Action**: "
        if account_data.get('risk_score', 0) >= 70:
            explanation += "🛑 FREEZE account immediately. Block pending transactions. File SAR."
        elif account_data.get('risk_score', 0) >= 50:
            explanation += "⚠️ Flag for manual review. Contact account holder. Monitor closely."
        else:
            explanation += "📋 Continue monitoring. Document for compliance."
        
        return explanation
    
    def _fallback_ring_explanation(self, ring_data):
        """Fallback ring explanation"""
        explanation = f"**Ring Analysis ({ring_data['size']} accounts)**\n\n"
        explanation += "🔗 **Coordination Pattern**: Multiple accounts sharing the same beneficiaries, "
        explanation += "indicating coordinated activity typical of mule recruitment networks.\n\n"
        explanation += "**How It Operates**: Recruiter finds victims (often through fake job ads), "
        explanation += "convinces them to receive and forward money, all funds flow to same beneficiaries.\n\n"
        explanation += "**Recommended Action**: Investigate entire ring, freeze all accounts, "
        explanation += "file consolidated SAR, contact account holders (likely victims)."
        return explanation
    
    def _fallback_victim_scenario(self, account_data):
        """Fallback victim scenario"""
        scenarios = [
            "Saw Instagram ad: '💰 Earn ₹15,000/week from home! No experience needed. Just receive and forward payments.' Thought it was legitimate payment processing job. Didn't realize moving money for strangers is illegal.",
            "Responded to WhatsApp job offer: 'Work from home - Financial Assistant. ₹20k/month.' Was told to open account and 'process transactions.' Believed it was real remote work.",
            "Met someone on dating app who asked for 'help with business transactions.' Promised relationship and money. Classic romance scam turned mule recruitment.",
            "Student saw Facebook post: 'Easy money for students! Just let us use your account for payments.' Needed money for tuition. Didn't know it was money laundering.",
            "Unemployed person desperate for income. Recruiter promised ₹500 per transaction. Seemed like easy money. Unaware of criminal consequences."
        ]
        import random
        return f"**Likely Recruitment Scenario:**\n\n{random.choice(scenarios)}\n\n**Reality**: 71% of Gen Z unaware this leads to criminal record. Account now frozen, person faces prosecution."
    
    def _fallback_investigation_steps(self, account_data, flags):
        """Fallback investigation steps"""
        steps = f"**Investigation Steps for {account_data['account_id']}:**\n\n"
        steps += "1. **Freeze Account**: Immediately block all pending transactions\n"
        steps += "2. **Contact Holder**: Call account holder, assess if victim or willing participant\n"
        steps += "3. **Trace Beneficiaries**: Identify and investigate all receiving accounts\n"
        steps += "4. **Review Timeline**: Map all transactions and cyber events chronologically\n"
        steps += "5. **File SAR**: Submit Suspicious Activity Report with all evidence\n"
        steps += "6. **Check Network**: Identify other accounts in same ring\n"
        steps += "7. **Preserve Evidence**: Document all findings for potential prosecution"
        return steps
    
    def _fallback_sar_narrative(self, account_data, cyber_flags, fin_flags):
        """Fallback SAR narrative"""
        narrative = f"**SUSPICIOUS ACTIVITY REPORT - {account_data['account_id']}**\n\n"
        narrative += f"**Summary**: Account exhibits multiple indicators consistent with money mule activity. "
        narrative += f"Risk score: {account_data.get('risk_score', 50)}/100.\n\n"
        narrative += f"**Cyber Security Indicators**: {', '.join(cyber_flags) if cyber_flags else 'None detected'}.\n\n"
        narrative += f"**Financial Indicators**: {', '.join(fin_flags) if fin_flags else 'None detected'}.\n\n"
        narrative += "**Basis for Suspicion**: Pattern consistent with recruited money mule. "
        narrative += "Account shows signs of compromise followed by rapid fund movement. "
        narrative += "Transactions structured to avoid reporting thresholds. "
        narrative += "Likely victim of recruitment scam, but account used for money laundering.\n\n"
        narrative += "**Recommendation**: Freeze account, investigate beneficiaries, contact account holder."
        return narrative
    
    def _fallback_prevention_tips(self, scenario_type):
        """Fallback prevention tips"""
        tips = "**🛡️ How to Avoid Becoming a Money Mule:**\n\n"
        tips += "1. **Red Flag**: Any 'job' asking you to receive and forward money is illegal\n"
        tips += "2. **Warning**: Legitimate employers NEVER ask you to use your personal account for business\n"
        tips += "3. **Check**: If it sounds too easy ('earn ₹15k/week doing nothing'), it's a scam\n"
        tips += "4. **Verify**: Research company, check reviews, never trust Instagram/WhatsApp job ads\n"
        tips += "5. **Consequences**: Money mule = criminal record, frozen accounts, prosecution\n\n"
        tips += "**If Approached**: Report to bank immediately. Don't agree even if desperate for money."
        return tips

if __name__ == "__main__":
    # Test
    explainer = GeminiExplainer()
    
    test_account = {
        'account_id': 'ACC_002747',
        'risk_score': 90
    }
    
    test_cyber = ['malware_detected', 'new_device', 'foreign_ip']
    test_fin = ['rapid_transactions', 'near_threshold_amount']
    test_ring = {'size': 12, 'beneficiaries': ['BEN_SG_001', 'BEN_RO_003']}
    
    explanation = explainer.explain_mule_pattern(test_account, test_cyber, test_fin, test_ring)
    print(explanation)
