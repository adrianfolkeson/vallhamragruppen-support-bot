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
                "response": f"Du kan nå {company_name} på telefon 0793-006638 eller via email info@vallhamragruppen.se. Vi finns i Göteborg, Mölndal och Partille.",
                "intent": "contact",
                "lead_score": 1
            },
            r"\b(adress|plats|var|var finns ni|hitta|h whereabouts)\b": {
                "response": f"{company_name} verkar i Göteborg, Mölndal och Partille med omnejd. Kontorz: info@vallhamragruppen.se, Tel: 0793-006638.",
                "intent": "location",
                "lead_score": 1
            },
            r"\b(öppettider|när är ni öppna|öppet|öppettid|hours)\b": {
                "response": "Våra kontor har öppet måndag-fredag 08:00-17:00. För akuta ärenden utanför kontorstid, ring oss.",
                "intent": "hours",
                "lead_score": 1
            },
            r"\b(email|e-post|mejla|mail|adress)\b": {
                "response": "Du når oss på info@vallhamragruppen.se",
                "intent": "email",
                "lead_score": 1
            },

            # FAQ - Common issues
            r"\b(felanmälan|fel|anmäl|reparation|problem|fungerar inte|broken|issue)\b": {
                "response": "Felanmälan görs enklast via vår hemsida under 'Kontakta oss' eller genom att ringa 0793-006638. För akuta ärenden, ring vår jour.",
                "intent": "technical_issue",
                "lead_score": 2
            },

            # URGENT - Water issues - distinguish between critical flood and dripping
            r"\b(översvämning|vattenläcka.*(akut|stort|forsar)|brustet.*rör|står.*vatten|forsar.*vatten|emergency|flood)\b": {
                "response": "Jag förstår att du har en allvarlig vattenläcka! Stäng av vattnet om du kan (kranen under diskhon). Ring omedelbart vår jour på 0793-006638. Var finns läckan?",
                "intent": "water_critical",
                "lead_score": 2
            },
            r"\b(droppar|läcker|kran|diskmaskin|tvättmaskin|avlopp|vatten)\b": {
                "response": "Jag förstår att du har problem med vatten. För att hjälpa dig: är det en vattenläcka eller droppar det från en kran/apparat? Var i lägenheten är problemet?",
                "intent": "water_question",
                "lead_score": 2
            },

            # URGENT - Lost keys / Lockouts (CRITICAL - people locked out)
            r"\b(tappat.*nyckel|nyckel.*borta|glömde.*nyckel|utelåst|låst.*ute|kommer.*inte.*in|kan.*ej.*komma|låset.*går.*inte)\b": {
                "response": "Jag förstår att du har problem med nyckeln/låset. Är du utelåst just nu? Ring oss direkt på 0793-006638 för omedelbar hjälp. Vilken dörr gäller det?",
                "intent": "lockout_critical",
                "lead_score": 2
            },
            r"\b(nyckel|lås|dörr|låset)\b": {
                "response": "Jag hörde att du nämnde nyckel eller lås. Vad är problemet - har du tappat nyckeln, fungerar inte låset, eller är du utelåst?",
                "intent": "lock_question",
                "lead_score": 2
            },

            # URGENT - No heat (critical but not emergency)
            r"\b(ingen värme|kallt|fryser|elementen|element fungerar|dricks inte|inget varmt|det är kallt|kyla|elementen ej|värme ej)\b": {
                "response": "Jag förstår att det är kallt. Har du provat termostaten? Ring oss på 0793-006638 så hjälper vi dig att felsöka värmen. Akuta ärenden prioriteras.",
                "intent": "heating_issue",
                "lead_score": 2
            },

            # URGENT - No electricity
            r"\b(ingen ström|strömavbrott|slut|inte fungerar|mörkt|ljuset fungerar ej|elektricitet|el av|avbrott)\b": {
                "response": "Strömavbrott? Kontrollera först din säkringsskärm i trapphus. Är hela fastigheten drabbad? Ring 0793-006638 om det är akut.",
                "intent": "electric_issue",
                "lead_score": 2
            },

            # Broken things (medium urgency)
            r"\b(gått sönder|trasig sönder|tras|sönder|tillbörd sönder|har gått sönder)\b": {
                "response": "Jag förstår att något har gått sönder. Vad har hänt? Beskriv gärna vad som är trasigt så att vi kan hjälpa dig på bästa sätt. Ring 0793-006638 för snabb hjälp.",
                "intent": "damaged_item",
                "lead_score": 2
            },
            r"\b(vem är ni|vilka är ni|om företaget|bolaget|company)\b": {
                "response": f"{company_name} är ett fastighetsförvaltningsföretag som erbjuder drift och underhåll, ekonomisk förvaltning och hyresadministration för bostadsrättsföreningar och kommersiella fastigheter.",
                "intent": "about",
                "lead_score": 1
            },
            r"\b(tjänster|gör ni|erbjuder|service|services)\b": {
                "response": "Vi erbjuder fastighetsförvaltning inklusive drift och underhåll, ekonomisk förvaltning, hyresadministration och projektledning.",
                "intent": "services",
                "lead_score": 2
            },
            r"\b(hej|tjena|hallå|god dag|hello|hi|hey)\b": {
                "response": f"Hej! Välkommen till {company_name}. Hur kan jag hjälpa dig idag?",
                "intent": "greeting",
                "lead_score": 1
            },
            r"\b(tack|tackar|tacksam|thanks|thank)\b": {
                "response": "Välkommen! Om du har fler frågor är det bara att fråga.",
                "intent": "gratitude",
                "lead_score": 1
            },
            r"\b(hejdå|adjö|vi ses|bye|goodbye)\b": {
                "response": "Ha en bra dag! Välkommen tillbaka om du har fler frågor.",
                "intent": "goodbye",
                "lead_score": 1
            },

            # Booking & Meetings
            r"\b(boka|bokning|möte|visning|träff|meeting|book|appointment)\b": {
                "response": "Vad roligt att du vill boka ett möte! Du kan nå oss på 0793-006638 eller via info@vallhamragruppen.se. När passar det bäst för dig?",
                "intent": "booking_request",
                "lead_score": 5
            },
            r"\b(pris|kostar|kostnad|betala|price|pricing|how much)\b": {
                "response": "Prissättning sker individuellt baserat på fastighetens storlek och tjänsteomfattning. Vill du ha en kostnadsfri offert? Ring oss på 0793-006638.",
                "intent": "pricing_question",
                "lead_score": 3
            },
            r"\b(offert|offer|quote|prislista|price list)\b": {
                "response": "Vi ger gärna en kostnadsfri offert! Berätta gärna lite om din fastighet så kan vi ge dig en uppskattning. Du kan också ringa 0793-006638.",
                "intent": "pricing_question",
                "lead_score": 4
            },

            # Negative sentiment handling
            r"\b(arg|förbannad|dålig|terrible|horrible|hate)\b": {
                "response": "Jag förstår att du är frustrerad. Låt mig koppla dig till en person som kan hjälpa dig direkt. Ring oss på 0793-006638.",
                "intent": "complaint",
                "lead_score": 1
            },
            r"\b(chef|manager|ledning|överordnad|mänsklig|human|person)\b": {
                "response": "Självklart, jag kopplar dig till en kollega. Ring oss på 0793-006638 så hjälper vi dig direkt.",
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
