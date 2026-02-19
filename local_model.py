"""
SUPPORT STARTER AI - LOCAL FALLBACK MODEL
==========================================
Rule-based responses for simple queries - no LLM needed
"""

from typing import Optional, Dict, List, Tuple
import re


class LocalModel:
    """
    Rule-based model for handling simple queries without calling external APIs.
    Much faster and free for common questions.
    """
    def __init__(self, company_name: str = "Vallhamragruppen AB"):
        self.company_name = company_name

        # Simple query patterns with direct responses
        self.patterns = {
            # Contact & Location
            r"\b(kontakt|telefon|ring|nummer|phone|call)\b": {
                "response": "Ring oss på 0793-006638 eller mejla info@vallhamragruppen.se. Vi finns i Johanneberg, Partille och Mölndal.",
                "intent": "contact",
                "lead_score": 1
            },
            r"\b(adress|plats|var|var finns ni|hitta)\b": {
                "response": "Vi verkar i Johanneberg, Partille och Mölndal. Kontakt: 0793-006638, info@vallhamragruppen.se",
                "intent": "location",
                "lead_score": 1
            },
            r"\b(öppettider|när är ni öppna|öppet|öppettid|hours)\b": {
                "response": "Mån-Fre 08:00-17:00. Akuta ärenden: ring jour på 0793-006638.",
                "intent": "hours",
                "lead_score": 1
            },
            r"\b(email|e-post|mejla|mail|adress)\b": {
                "response": "info@vallhamragruppen.se",
                "intent": "email",
                "lead_score": 1
            },

            # FAQ - Common issues
            r"\b(felanmälan|fel|anmäl|reparation|problem|fungerar inte|broken|issue)\b": {
                "response": "Felanmälan: ring 0793-006638 eller använd formulär på hemsidan. Akuta ärenden prioriteras.",
                "intent": "technical_issue",
                "lead_score": 2
            },

            # URGENT - Water issues - distinguish between critical flood and dripping
            r"\b(översvämning|vattenläcka.*(akut|stort|forsar)|brustet.*rör|står.*vatten|forsar.*vatten|emergency|flood)\b": {
                "response": "Vattenläcka - stäng av vattnet under diskhon. Ring jour 0793-006638 direkt. Var läcker det?",
                "intent": "water_critical",
                "lead_score": 2
            },
            r"\b(droppar|läcker|kran|diskmaskin|tvättmaskin|avlopp|vatten)\b": {
                "response": "Vattenproblem. Läcka eller droppande kran? Var i lägenheten? Är det farligt för el eller golv? Ring 0793-006638.",
                "intent": "water_question",
                "lead_score": 2
            },

            # URGENT - Lost keys / Lockouts
            r"\b(tappat.*nyckel|nyckel.*borta|glömde.*nyckel|utelåst|låst.*ute|kommer.*inte.*in|kan.*ej.*komma|låset.*går.*inte)\b": {
                "response": "Utelåst? Ring jour 0793-006638 nu. Vilken adress?",
                "intent": "lockout_critical",
                "lead_score": 2
            },
            r"\b(nyckel|lås|dörr|låset)\b": {
                "response": "Nyckel- eller låsproblem. Tappad nyckel eller trasigt lås? Ring 0793-006638.",
                "intent": "lock_question",
                "lead_score": 2
            },

            # URGENT - No heat
            r"\b(ingen värme|kallt|fryser|elementen|element fungerar|dricks inte|inget varmt|det är kallt|kyla|elementen ej|värme ej)\b": {
                "response": "Ingen värme. Kollat termostaten på elementen? Gäller ett element eller hela lägenheten? Ring 0793-006638.",
                "intent": "heating_issue",
                "lead_score": 2
            },

            # URGENT - No electricity
            r"\b(ingen ström|strömavbrott|slut|inte fungerar|mörkt|ljuset fungerar ej|elektricitet|el av|avbrott)\b": {
                "response": "Strömproblem. Kolla säkringsskärmet i trapphus först. Gäller hela lägenheten? Ring 0793-006638.",
                "intent": "electric_issue",
                "lead_score": 2
            },

            # Broken things
            r"\b(gått sönder|trasig sönder|tras|sönder|tillbörd sönder|har gått sönder)\b": {
                "response": "Gått sönder. Vad har hänt? Är det farligt? Ring 0793-006638.",
                "intent": "damaged_item",
                "lead_score": 2
            },
            r"\b(vem är ni|vilka är ni|om företaget|bolaget|company)\b": {
                "response": f"{company_name} förvaltar fastigheter - drift, underhåll, ekonomi och hyresadministration för bostadsrättsföreningar och kommersiella fastigheter.",
                "intent": "about",
                "lead_score": 1
            },
            r"\b(tjänster|gör ni|erbjuder|service|services)\b": {
                "response": "Fastighetsförvaltning: drift och underhåll, ekonomisk förvaltning, hyresadministration, projektledning.",
                "intent": "services",
                "lead_score": 2
            },
            r"\b(hej|tjena|hallå|god dag|hello|hi|hey)\b": {
                "response": "Hej! Vallhamragruppen här. Vad kan jag hjälpa med?",
                "intent": "greeting",
                "lead_score": 1
            },
            r"\b(tack|tackar|tacksam|thanks|thank)\b": {
                "response": "Varsågod! Fler frågor - bara fråga.",
                "intent": "gratitude",
                "lead_score": 1
            },
            r"\b(hejdå|adjö|vi ses|bye|goodbye)\b": {
                "response": "Ha en bra dag!",
                "intent": "goodbye",
                "lead_score": 1
            },

            # Booking & Meetings
            r"\b(boka|bokning|möte|visning|träff|meeting|book|appointment)\b": {
                "response": "Boka möte: ring 0793-006638 eller info@vallhamragruppen.se. När passar?",
                "intent": "booking_request",
                "lead_score": 5
            },
            r"\b(pris|kostar|kostnad|betala|price|pricing|how much)\b": {
                "response": "Pris sätts individuellt efter fastighet och tjänsteomfattning. Offert? Ring 0793-006638.",
                "intent": "pricing_question",
                "lead_score": 3
            },
            r"\b(offert|offer|quote|prislista|price list)\b": {
                "response": "Kostnadsfri offert. Berätta om fastigheten så hjälper vi dig. Ring 0793-006638.",
                "intent": "pricing_question",
                "lead_score": 4
            },

            # Negative sentiment
            r"\b(arg|förbannad|dålig|terrible|horrible|hate)\b": {
                "response": "Jag förstår. Ring 0793-006638 så hjälper en kollega dig direkt.",
                "intent": "complaint",
                "lead_score": 1
            },
            r"\b(chef|manager|ledning|överordnad|mänsklig|human|person)\b": {
                "response": "Självklart. Ring 0793-006638 så hjälper vi dig.",
                "intent": "escalation_demand",
                "lead_score": 1
            },
        }

    def can_handle(self, message: str) -> bool:
        """Check if this message can be handled by local model"""
        message_lower = message.lower()

        # Check each pattern
        for pattern in self.patterns.keys():
            if re.search(pattern, message_lower):
                return True

        return False

    def generate(self, message: str, context: Optional[Dict] = None) -> Dict:
        """
        Generate a response using local rules

        Returns:
            Dict with: response, intent, confidence, lead_score, escalate
        """
        message_lower = message.lower()

        # Check each pattern (more specific first)
        for pattern, data in self.patterns.items():
            if re.search(pattern, message_lower):
                return {
                    "response": data["response"],
                    "intent": data["intent"],
                    "confidence": 0.85,  # High confidence for pattern matches
                    "lead_score": data["lead_score"],
                    "escalate": data["intent"] in ["complaint", "escalation_demand"]
                }

        # Fallback
        return {
            "response": f"Tack för ditt meddelande. För att ge dig bästa möjliga hjälp, kontakta oss på 0793-006638 eller info@vallhamragruppen.se.",
            "intent": "unknown",
            "confidence": 0.3,
            "lead_score": 1,
            "escalate": False
        }

    def is_simple_query(self, message: str) -> bool:
        """Quick check if this is a simple query we can handle"""
        return self.can_handle(message)


class HybridBot:
    """
    Hybrid bot that uses local model for simple queries
    and falls back to LLM for complex ones
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
        # Try local model first for simple queries
        if self.local_model.is_simple_query(message):
            return self.local_model.generate(message, context)

        # Fall back to Anthropic for complex queries
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    temperature=0.4,
                    system=system_prompt,
                    messages=[{"role": "user", "content": message}]
                )

                return {
                    "response": response.content[0].text,
                    "intent": "complex",
                    "confidence": 0.9,
                    "lead_score": 2,
                    "escalate": False
                }
            except Exception as e:
                print(f"LLM Error: {e}")

        # Final fallback
        return self.local_model.generate(message, context)


# Pre-configured instance
_default_local_model: Optional[LocalModel] = None


def get_local_model(company_name: str = "Vallhamragruppen AB") -> LocalModel:
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

    test_queries = [
        "Hej!",
        "Hur gör jag en felanmälan?",
        "Vad är er adress?",
        "Hur mycket kostar det?",
        "Jag vill boka ett möte",
        "Tack!",
        "Det här är hemskt!"
    ]

    for query in test_queries:
        result = model.generate(query)
        print(f"\nQ: {query}")
        print(f"A: {result['response']}")
        print(f"   Intent: {result['intent']}, Confidence: {result['confidence']}, Lead: {result['lead_score']}")
