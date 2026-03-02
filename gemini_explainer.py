import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
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
                
                # Pointing to the new 2.5 Flash model
                self.model = genai.GenerativeModel(
                    'gemini-2.5-flash',
                    generation_config={"response_mime_type": "application/json"}
                )
                self.text_model = genai.GenerativeModel('gemini-2.5-flash')
                
                self.api_available = True
                print("✅ Gemini API configured successfully with gemini-2.5-flash")
            except Exception as e:
                self.model = None
                self.text_model = None
                self.api_available = False
                print(f"⚠️ Gemini API configuration failed: {e}")
        else:
            self.model = None
            self.text_model = None
            self.api_available = False
            print("⚠️ GEMINI_API_KEY not found.")
    
    def explain_ring(self, ring_id, ring_size, beneficiaries_str, risk_score):
        if not self.api_available:
            return "❌ Gemini API is not configured. Please check your .env file."
        
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
        }}"""

        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            
            return f"""**🔗 Ring {ring_id} Analysis ({ring_size} accounts)**
            \n**Operation**: {data.get('operation_summary', 'N/A')}
            \n**Coordination**: {data.get('coordination_pattern', 'N/A')}
            \n**Why Suspicious**: {data.get('suspicion_reason', 'N/A')}
            \n**Action**: {data.get('recommended_action', 'N/A')}"""
        except Exception as e:
            return f"❌ AI Generation Failed: {str(e)}"

    def explain_mule_pattern(self, account_data, cyber_flags, fin_flags, ring_data):
        account_id = account_data.get('account_id', 'Unknown')
        size = ring_data.get('size', 0)
        
        if not self.api_available:
            return "❌ Gemini API is not configured."
            
        prompt = f"""Analyze this mule pattern:
        Account ID: {account_id}
        Ring Size: {size}
        Cyber Flags: {', '.join(cyber_flags)}
        Financial Flags: {', '.join(fin_flags)}
        
        Return JSON:
        {{
            "analysis": "1 paragraph explaining the coordinated threat."
        }}"""
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            return data.get('analysis', "Pattern indicates coordinated mule activity.")
        except Exception as e:
            return f"❌ AI Generation Failed: {str(e)}"
    
    def generate_victim_ad(self, account_id, risk_score):
        if not self.api_available:
            return "❌ Gemini API is not configured."
        
        prompt = f"""Generate a realistic fake job ad that likely recruited this money mule victim.
        Account: {account_id}
        Risk: {risk_score}/100

        Return JSON:
        {{
          "ad_text": "The fake job ad text (include emojis)",
          "platform": "Where victim saw it",
          "promise": "What was promised",
          "reality": "What actually happened"
        }}"""

        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            
            return f"""**🎭 Likely Recruitment Scenario for {account_id}**
            \n**Platform**: {data.get('platform', 'Social Media')}
            \n**The Fake Ad They Saw**: _{data.get('ad_text', 'N/A')}_
            \n**Promise**: {data.get('promise', 'Easy money')}
            \n**Reality**: {data.get('reality', 'Account used for money laundering.')}"""
        except Exception as e:
            return f"❌ AI Generation Failed: {str(e)}"
    
    def generate_sar_narrative(self, account_data, cyber_flags, fin_flags):
        account_id = account_data.get('account_id', 'Unknown')
        risk_score = account_data.get('risk_score', 0)
        cyber_str = ", ".join(cyber_flags) if cyber_flags else "None"
        fin_str = ", ".join(fin_flags) if fin_flags else "None"

        if not self.api_available:
            return "❌ Gemini API is not configured."
        
        prompt = f"""Write a professional Suspicious Activity Report (SAR) narrative.
        Account: {account_id}
        Risk: {risk_score}/100
        Cyber Flags: {cyber_str}
        Financial Flags: {fin_str}

        Return JSON:
        {{
          "summary": "Executive summary (2 sentences)",
          "timeline": "Timeline of suspicious events",
          "red_flags": "Key red flags identified",
          "recommendation": "Recommended action"
        }}"""

        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            
            return f"""**📋 SUSPICIOUS ACTIVITY REPORT - {account_id}**
            \n**SUMMARY**: {data.get('summary', 'N/A')}
            \n**TIMELINE**: {data.get('timeline', 'N/A')}
            \n**RED FLAGS**: {data.get('red_flags', 'N/A')}
            \n**RECOMMENDATION**: {data.get('recommendation', 'Freeze account.')}"""
        except Exception as e:
            return f"❌ AI Generation Failed: {str(e)}"

    def suggest_investigation_steps(self, account_data, flags):
        account_id = account_data.get('account_id', 'Unknown')
        flags_str = ", ".join(flags) if flags else "None"
        
        if not self.api_available:
            return "❌ Gemini API is not configured."

        try:
            prompt = f"Suggest 3 bullet-point investigation steps for account {account_id} showing these flags: {flags_str}. Keep it brief."
            response = self.text_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ AI Generation Failed: {str(e)}"

    def explain_prevention_tips(self, topic: str) -> str:
        if not self.api_available:
            return "❌ Gemini API is not configured."
            
        try:
            prompt = f"Provide 3 actionable prevention tips regarding '{topic}'. Use bullet points."
            response = self.text_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ AI Generation Failed: {str(e)}"