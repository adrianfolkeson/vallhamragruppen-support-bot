"""
SUPPORT STARTER AI - LOCAL FALLBACK MODEL
==========================================
Rule-based responses for VERY SIMPLE queries only - no LLM needed

IMPORTANT: This should only handle EXPLICIT, SIMPLE queries.
Complex questions about availability, rentals, applications, etc.
should fall through to the RAG/LLM system for intelligent handling.
"""

from typing import Optional, Dict, List, Tuple
import re


class LocalModel:
    """
    Rule-based model for handling ONLY very simple, explicit queries.
    All complex questions should fall through to RAG/LLM.
    """
    def __init__(self, company_name: str = "Vallhamragruppen"):
        self.company_name = company_name

        # ONLY very explicit, simple patterns that have clear answers
        self.patterns = {
            # ============================================
            # GREETINGS & SOCIAL - Simple responses
            # ============================================
            r"^(hej|tjena|hallå|god dag|hello|hi|hey|godmorgon|godkväll)[\s!?]*$": {
                "response": f"Hej! 👋 {company_name} här. Jag hjälper med frågor om fastigheter, felanmälan och förvaltning. Vad kan jag hjälpa med?",
                "intent": "greeting",
                "lead_score": 1,
                "confidence": 0.9
            },
            r"^(tack|tackar|tack så mycket)[\s!?]*$": {
                "response": "Varsågod! 😊 Fler frågor - bara fråga.",
                "intent": "gratitude",
                "lead_score": 1,
                "confidence": 0.9
            },
            r"^(hejdå|adjö|vi ses)[\s!?]*$": {
                "response": "Ha en bra dag! 👋",
                "intent": "goodbye",
                "lead_score": 1,
                "confidence": 0.9
            },

            # ============================================
            # CONTACT - Direct contact requests only
            # ============================================
            r"^(?!(.){30,})(kontakt|telefon|nummer|ring|mejl|e-post|email|adress)[\s ?!]*$": {
                "response": "Ring oss på 0793-006638 eller mejla info@vallhamragruppen.se. Vi finns i Johanneberg, Partille och Mölndal. 📍",
                "intent": "contact",
                "lead_score": 1,
                "confidence": 0.85
            },
            r"^(öppettider|när är ni öppna|öppet)[\s ?!]*$": {
                "response": "Mån-Fre 08:00-17:00. Akuta ärenden dygnet runt: ring jour på 0793-006638. ⏰",
                "intent": "hours",
                "lead_score": 1,
                "confidence": 0.9
            },

            # ============================================
            # CRITICAL EMERGENCIES - These must be caught immediately
            # ============================================
            r"(akut|brinner|brand|gasläcka|översvämning|vattenläcka.*(forsar|stort|akut)|inbrott.*pågående|skadegörelse.*pågående)": {
                "response": "Akut läge! 🚨 Ring 112 först vid fara för liv. Ring sedan jour på 0793-006638. Vad har hänt?",
                "intent": "emergency_critical",
                "lead_score": 5,
                "confidence": 0.95
            },
            r"(utelåst|låst.*ute|kommer.*inte.*in|tappat.*nyckel|nyckel.*borta|glömde.*nyckel).{0,30}!": {
                "response": "Utelåst? 🔑 Ring jour 0793-006638 nu. Vilken adress?",
                "intent": "lockout_emergency",
                "lead_score": 4,
                "confidence": 0.9
            },

            # ============================================
            # SIMPLE FAULT REPORT - Just the reporting mechanism
            # ============================================
            r"^hur (gör|fungerar) (jag|man) en felanmälan[\s ?!]*$": {
                "response": "Felanmälan: ring 0793-006638 eller använd formulär på hemsidan. 🛠️ För akuta ärenden, ring jour.",
                "intent": "how_to_report",
                "lead_score": 2,
                "confidence": 0.9
            },
        }

    def can_handle(self, message: str) -> bool:
        """
        Check if this is a VERY simple query we can handle locally.
        Most questions should return False to use RAG/LLM instead.
        """
        message_lower = message.lower()

        # Only handle if exact match to our very specific patterns
        for pattern in self.patterns.keys():
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True

        return False

    def generate(self, message: str, context: Optional[Dict] = None) -> Dict:
        """
        Generate a response using local rules

        Returns:
            Dict with: response, intent, confidence, lead_score, escalate
        """
        message_lower = message.lower()

        # Check each pattern
        for pattern, data in self.patterns.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                return {
                    "response": data["response"],
                    "intent": data["intent"],
                    "confidence": data["confidence"],
                    "lead_score": data["lead_score"],
                    "escalate": data["lead_score"] >= 4
                }

        # This shouldn't happen if can_handle is used first, but return fallback
        return {
            "response": None,  # Signal that we couldn't handle it
            "intent": "unknown",
            "confidence": 0.1,
            "lead_score": 1,
            "escalate": False,
            "should_use_llm": True  # Signal to use LLM instead
        }

    def is_simple_query(self, message: str) -> bool:
        """Quick check if this is a simple query we can handle"""
        return self.can_handle(message)


class HybridBot:
    """
    Hybrid bot that uses local model for VERY simple queries only
    and delegates everything else to LLM for intelligent responses
    """
    def __init__(self, local_model: LocalModel, anthropic_client=None):
        self.local_model = local_model
        self.anthropic_client = anthropic_client

    def generate(self, message: str, system_prompt: str, context: Optional[Dict] = None) -> Dict:
        """
        Generate response using best available model

        Args:
            message: User message
            system_prompt: System prompt for LLM
            context: Optional conversation context

        Returns:
            Dict with response and metadata
        """
        # Only use local model for VERY simple queries
        if self.local_model.is_simple_query(message):
            return self.local_model.generate(message, context)

        # Use Anthropic LLM for everything else
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=800,  # Increased for more detailed answers
                    temperature=0.5,  # Slightly higher for more natural responses
                    system=system_prompt,
                    messages=[{"role": "user", "content": message}]
                )

                return {
                    "response": response.content[0].text,
                    "intent": "llm_generated",
                    "confidence": 0.95,
                    "lead_score": 2,
                    "escalate": False,
                    "should_use_llm": True
                }
            except Exception as e:
                print(f"LLM Error: {e}")

        # Final fallback - return None to signal couldn't handle
        return {
            "response": None,
            "intent": "error",
            "confidence": 0.1,
            "lead_score": 1,
            "escalate": False,
            "should_use_llm": True
        }


# Pre-configured instance
_default_local_model: Optional[LocalModel] = None


def get_local_model(company_name: str = "Vallhamragruppen") -> LocalModel:
    """Get or create default local model instance"""
    global _default_local_model
    if _default_local_model is None:
        _default_local_model = LocalModel(company_name)
    return _default_local_model


if __name__ == "__main__":
    # Test the local model
    print("=" * 60)
    print("LOCAL MODEL - TEST")
    print("=" * 60)

    model = LocalModel()

    # These SHOULD be handled locally
    simple_queries = [
        "Hej!",
        "Tack!",
        "Kontakt",
        "Öppettider",
        "Akut! Vattenläcka everywhere!",
        "Utelåst!",
        "hur gör jag en felanmälan",
    ]

    # These should NOT be handled locally (need LLM)
    complex_queries = [
        "Har ni några lediga lägenheter just nu?",
        "Jag söker en 3:a i Göteborg – vad har ni?",
        "Vad ingår i hyran?",
        "Hur ansöker jag om en lägenhet?",
    ]

    print("\n--- SIMPLE (should handle) ---")
    for query in simple_queries:
        can_handle = model.can_handle(query)
        print(f"'{query}' -> {'✓ HANDLE' if can_handle else '✗ FALLTHROUGH'}")

    print("\n--- COMPLEX (should fall through to LLM) ---")
    for query in complex_queries:
        can_handle = model.can_handle(query)
        print(f"'{query}' -> {'✗ HANDLE (wrong!)' if can_handle else '✓ FALLTHROUGH (correct)'}")
