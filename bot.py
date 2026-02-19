"""
SUPPORT STARTER AI - MAIN BOT SYSTEM
=====================================
Complete AI support bot with all features integrated
"""

import os
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

# Import all our modules
from router import IntelligentRouter, classify_message
from schemas import BotResponse, EscalationPacket, LeadData, create_response
from rag import SimpleRAG, create_sample_knowledge_base
from memory import ConversationMemory, extract_info_from_message, MemoryEventType
from security import SecurityManager, SecurityLevel
from proactive import ProactiveSupportEngine, MicroConversionEngine
from escalation import EscalationEngine, EscalationReason
from metrics import MetricsEngine
from fault_reports import FaultReportSystem, get_fault_system
from local_model import LocalModel


@dataclass
class BotConfig:
    """Configuration for the bot"""
    # Company info
    COMPANY_NAME: str = "Vallhamragruppen AB"
    industry: str = "Fastighetsförvaltning"
    locations: str = "Göteborg, Mölndal, Partille"
    phone: str = "0793-006638"
    contact_email: str = "info@vallhamragruppen.se"
    website: str = "https://vallhamragruppen.se"
    business_hours: str = "Mån-Fre 08:00-17:00"
    response_time: str = "24 timmar"

    # Services
    services: str = """
    Vi erbjuder fastighetsförvaltning för både bostadsrättsföreningar och
    kommersiella fastigheter. Tjänster inkluderar: drift och underhåll,
    ekonomisk förvaltning, hyresadministration, och projektledning.
    """

    # Pricing
    pricing: str = """
    Prissättning sker individuellt baserat på fastighetens storlek och
    omfattning av tjänster. Kontakta oss för offert.
    """

    # FAQ
    faq_list: str = """
    Q: Hur gör jag en felanmälan?
    A: Felanmälan görs enklast via vår hemsida under "Kontakta oss" eller
       genom att ringa oss på 0793-006638.

    Q: Vilka områden verkar ni i?
    A: Vi verkar främst i Göteborg, Mölndal och Partille.

    Q: Hanterar ni bostadsrättsföreningar?
    A: Ja, vi har lång erfarenhet av att förvalta bostadsrättsföreningar.

    Q: Hur snabbt får man svar?
    A: Akuta ärenden hanteras samma dag. Övriga ärenden svarar vi på inom 24 timmar.
    """

    # Policies
    refund_policy: str = "Ej tillämpligt för tjänster"
    cancellation_policy: str = "Uppsägningstid enligt avtal"

    # Style
    tone_style: str = "Professionell, vänlig, direkt"
    booking_link: str = "https://vallhamragruppen.se/kontakt"
    contact_form: str = "https://vallhamragruppen.se/kontakt"

    # API
    anthropic_api_key: str = ""

    # Rate limiting
    max_requests_per_minute: int = 60


class SupportStarterBot:
    """
    Main AI Support Bot with all features integrated
    """
    def __init__(self, config: Optional[BotConfig] = None):
        self.config = config or BotConfig()

        # Initialize all components
        self.router = IntelligentRouter()
        self.memory = ConversationMemory()
        self.security = SecurityManager(max_requests_per_minute=self.config.max_requests_per_minute)
        self.proactive = ProactiveSupportEngine()
        self.micro_conversions = MicroConversionEngine()
        self.escalation_engine = EscalationEngine()
        self.metrics = MetricsEngine()
        self.fault_system = FaultReportSystem()
        self.local_model = LocalModel(company_name=self.config.COMPANY_NAME)

        # Initialize RAG with knowledge base
        self.rag = self._create_knowledge_base()

        # Load system prompt
        self.system_prompt = self._load_system_prompt()

        # Setup Anthropic client if API key provided
        self.client = None
        if self.config.anthropic_api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.config.anthropic_api_key)
            except ImportError:
                print("Warning: anthropic package not installed. Run: pip install anthropic")

    def _create_knowledge_base(self) -> SimpleRAG:
        """Create knowledge base with company info"""
        rag = SimpleRAG()

        # Add company-specific FAQ
        faq_data = [
            {
                "question": "Hur gör jag en felanmälan?",
                "answer": "Felanmälan görs enklast via vår hemsida under 'Kontakta oss' eller genom att ringa oss på 0793-006638. För akuta ärenden utanför kontorstid, ring vår jour.",
                "keywords": ["felanmälan", "fel", "reparation", "jour"]
            },
            {
                "question": "Vilka områden verkar ni i?",
                "answer": "Vi verkar främst i Göteborg, Mölndal och Partille med omnejd.",
                "keywords": ["område", "plats", "location", "var", "stad"]
            },
            {
                "question": "Hanterar ni bostadsrättsföreningar?",
                "answer": "Ja, vi har lång erfarenhet av att förvalta bostadsrättsföreningar. Vi tar hand om allt från daglig drift till ekonomisk förvaltning.",
                "keywords": ["bostadsrätt", "förening", "brf", "förvaltning"]
            },
            {
                "question": "Hur snabbt får man svar?",
                "answer": "Akuta ärenden hanteras samma dag. Övriga ärenden svarar vi på inom 24 timmar på vardagar.",
                "keywords": ["snabbt", "tid", "svar", "respons"]
            },
            {
                "question": "Vad kostar er förvaltning?",
                "answer": "Prissättning sker individuellt baserat på fastighetens storlek och omfattning av tjänster. Kontakta oss för en kostnadsfri offert.",
                "keywords": ["pris", "kostnad", "betala", "offert"]
            }
        ]

        from rag import FAQManager
        faq_manager = FAQManager(rag)
        faq_manager.load_faq(faq_data)

        # Add company info as knowledge chunks
        from rag import KnowledgeChunk
        rag.add_knowledge(KnowledgeChunk(
            id="company_info",
            content=f"COMPANY: {self.config.COMPANY_NAME}. Phone: {self.config.phone}. Email: {self.config.contact_email}. Website: {self.config.website}. Business hours: {self.config.business_hours}.",
            category="contact",
            keywords=["kontakt", "ring", "mejl", "telefon", "öppettider"],
            priority=3
        ))

        return rag

    def _load_system_prompt(self) -> str:
        """Load and generate system prompt"""
        # Read the V2 template
        template_path = os.path.join(os.path.dirname(__file__), "SUPPORT_STARTER_V2.md")

        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()

            # Replace placeholders
            replacements = {
                "{COMPANY_NAME}": self.config.COMPANY_NAME,
                "{industry}": self.config.industry,
                "{locations}": self.config.locations,
                "{phone}": self.config.phone,
                "{contact_email}": self.config.contact_email,
                "{website}": self.config.website,
                "{business_hours}": self.config.business_hours,
                "{response_time}": self.config.response_time,
                "{services}": self.config.services,
                "{pricing}": self.config.pricing,
                "{faq_list}": self.config.faq_list,
                "{refund_policy}": self.config.refund_policy,
                "{cancellation_policy}": self.config.cancellation_policy,
                "{tone_style}": self.config.tone_style,
                "{booking_link}": self.config.booking_link,
                "{contact_form}": self.config.contact_form,
                "{date}": datetime.now().strftime("%Y-%m-%d")
            }

            prompt = template
            for key, value in replacements.items():
                prompt = prompt.replace(key, str(value))

            return prompt
        else:
            # Fallback simple prompt
            return f"""Du är en hjälpsam kundtjänstassistent för {self.config.COMPANY_NAME}.

Använd endast följande information för att svara:
- Företag: {self.config.COMPANY_NAME}
- Telefon: {self.config.phone}
- Email: {self.config.contact_email}
- Tjänster: {self.config.services}

Svara på svenska, var professionell och trevlig. Om du inte vet svaret, säg att du inte kan ge felaktig information och föreslå kontakt med kundtjänst."""

    def process_message(self, message: str, session_id: str,
                       conversation_history: Optional[List[Dict]] = None) -> BotResponse:
        """
        Process a user message and return a structured response

        Args:
            message: User input message
            session_id: Unique session identifier
            conversation_history: Optional list of previous messages

        Returns:
            BotResponse with reply and metadata
        """
        start_time = time.time()

        # 1. Security check
        allowed, sanitized_message, security_error = self.security.process_input(message, session_id)
        if not allowed:
            return create_response(
                reply="Meddelandet kunde inte bearbetas. Vänligen kontakta oss via telefon om problemet kvarstår.",
                intent="security_block",
                confidence=1.0,
                sentiment="neutral",
                lead_score=1,
                escalate=False,
                action="none"
            )

        message = sanitized_message

        # 2. Get or create session
        session = self.memory.get_or_create_session(session_id)
        self.metrics.track_conversation_start(session_id)

        # 3. Check for FAULT REPORTS first (all urgent issues like water leaks, lockouts, etc.)
        fault_result = self.fault_system.collect_fault_report(
            message,
            {
                "session_id": session_id,
                "customer_name": session.memory.get("customer_name", {}).get("value"),
                "customer_email": session.memory.get("customer_email", {}).get("value"),
                "customer_phone": session.memory.get("customer_phone", {}).get("value")
            }
        )

        # Check if this is a fault report (any urgency level above LOW)
        # LOW urgency is "just asking" - continue to normal flow
        # MEDIUM+ urgency means there's an actual issue - handle with fault response
        if fault_result["report"].urgency != fault_result["report"].urgency.LOW:
            report = fault_result["report"]
            is_urgent = report.urgency in [report.urgency.CRITICAL, report.urgency.HIGH]

            # Track metrics
            if is_urgent:
                self.metrics.track_escalation(session_id, "fault_" + report.urgency.value)

            # Save fault report to persistent storage
            try:
                from persistent_memory import get_persistent_memory
                mem = get_persistent_memory()
                mem.save_fault_report({
                    "report_id": fault_result["report"].report_id,
                    "category": fault_result["report"].category.value,
                    "urgency": fault_result["report"].urgency.value,
                    "description": fault_result["report"].description,
                    "session_id": session_id,
                    "reporter_email": fault_result["report"].reporter_email,
                    "reporter_phone": fault_result["report"].reporter_phone
                })
            except:
                pass  # Continue without persistence if unavailable

            # Check if we need more info
            if fault_result["collect_more_info"]:
                questions = self.fault_system.get_collection_questions(fault_result["report"])
                follow_up = "\n\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
            else:
                follow_up = ""

            return create_response(
                reply=fault_result["response"] + follow_up,
                intent="fault_report",
                confidence=0.95,
                sentiment="neutral" if report.urgency != report.urgency.CRITICAL else "frustrated",
                lead_score=2,
                escalate=is_urgent,
                action="collect_info"
            )

        # 4. Check if local model can handle this (faster, no API cost)
        if self.local_model.can_handle(message):
            local_result = self.local_model.generate(message)
            return create_response(
                reply=local_result["response"],
                intent=local_result["intent"],
                confidence=local_result["confidence"],
                sentiment="neutral",
                lead_score=local_result["lead_score"],
                escalate=local_result["escalate"],
                action="escalate" if local_result["escalate"] else "none"
            )

        # 5. Classify intent
        router_result = self.router.classify(message, conversation_history)

        # 6. Update metrics
        self.metrics.track_message(
            session_id, "user",
            intent=router_result.intent.value,
            sentiment=router_result.sentiment.value,
            lead_score=router_result.lead_score
        )

        # 7. Extract and store info
        for info_type, value in extract_info_from_message(message):
            self.memory.extract_and_store_info(session_id, info_type, value)

        # 8. Check for escalation
        should_escalate, escalation_reason = self.escalation_engine.should_escalate(
            router_result.intent.value,
            router_result.sentiment.value,
            router_result.lead_score,
            len(session.messages),
            message
        )

        if should_escalate:
            # Handle escalation
            escalation_packet = self.escalation_engine.create_escalation_packet(
                {
                    "conversation_id": session_id,
                    "current_intent": router_result.intent.value,
                    "current_sentiment": router_result.sentiment.value,
                    "lead_score": router_result.lead_score,
                    "customer_name": session.memory.get("customer_name", {}).get("value"),
                    "customer_email": session.memory.get("customer_email", {}).get("value"),
                    "message_count": len(session.messages),
                    "messages": session.messages
                },
                escalation_reason
            )

            escalation_response = self.escalation_engine.get_escalation_response(
                escalation_reason,
                self.config.phone
            )

            self.metrics.track_escalation(session_id, escalation_reason.value)

            return create_response(
                reply=escalation_response,
                intent=router_result.intent.value,
                confidence=router_result.confidence,
                sentiment=router_result.sentiment.value,
                lead_score=router_result.lead_score,
                escalate=True,
                action="escalate",
                escalation_summary=escalation_packet.summary
            )

        # 7. Get relevant context from RAG
        rag_context = self.rag.retrieve(message, top_k=2)

        # 8. Get memory context
        memory_context = self.memory.get_contextual_prompt_addition(session_id)

        # 9. Build full prompt for AI
        full_prompt = self.system_prompt + "\n\n" + rag_context.combined_text + memory_context

        # 10. Generate response
        reply = self._generate_response(message, full_prompt, router_result, session)

        # 11. Check for conversion
        if router_result.lead_score >= 4:
            self.metrics.track_conversion(session_id, "high_lead", "lead_score_4+")

        # 12. Update metrics
        self.metrics.track_message(session_id, "bot", response_time_ms=(time.time() - start_time) * 1000)
        self.memory.add_message(session_id, "user", message,
                               intent=router_result.intent.value,
                               sentiment=router_result.sentiment.value,
                               lead_score=router_result.lead_score)
        self.memory.add_message(session_id, "bot", reply)

        # 13. Get suggested actions
        suggested_actions = self.micro_conversions.get_suggested_actions(
            router_result.lead_score,
            router_result.intent.value
        )

        # 14. Create response
        return create_response(
            reply=reply,
            intent=router_result.intent.value,
            confidence=router_result.confidence,
            sentiment=router_result.sentiment.value,
            lead_score=router_result.lead_score,
            escalate=False,
            action="book_call" if router_result.lead_score >= 4 else "none",
            suggested_responses=suggested_actions[:3]
        )

    def _generate_response(self, message: str, prompt: str,
                          router_result, session) -> str:
        """Generate AI response using Anthropic or fallback"""
        if self.client:
            try:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    temperature=0.4,
                    system=prompt,
                    messages=[{"role": "user", "content": message}]
                )
                return response.content[0].text
            except Exception as e:
                print(f"API Error: {e}")
                # Fall back to simple response

        # Fallback: Simple rule-based response
        return self._get_fallback_response(router_result, session)

    def _get_fallback_response(self, router_result, session) -> str:
        """Get fallback response when API is unavailable"""
        intent = router_result.intent.value
        sentiment = router_result.sentiment.value

        # Check for direct FAQ match
        from rag import FAQManager
        faq_manager = FAQManager(self.rag)
        faq_answer = faq_manager.get_answer(router_result.trigger_phrases[0] if router_result.trigger_phrases else "")
        if faq_answer:
            return faq_answer

        # Rule-based responses
        if "pricing" in intent or "pris" in intent:
            return self.config.pricing

        if "booking" in intent or "boka" in intent:
            return f"Vill du boka ett möte eller en visning? Du kan nå oss på {self.config.phone} eller via vår hemsida."

        if sentiment == "angry":
            return "Jag förstår att detta är viktigt för dig. Låt mig koppla dig till en kollega som kan hjälpa dig direkt."

        if sentiment == "frustrated":
            return "Jag ber om ursäkt för besväret. Låt mig hjälpa dig vidare. Kan du beskriva vad du behöver hjälp med?"

        # Default response
        return f"Tack för ditt meddelande. För att ge dig bästa möjliga hjälp, kontakta oss på {self.config.phone} eller {self.config.contact_email}."

    def check_proactive_message(self, session_id: str) -> Optional[str]:
        """Check if should send proactive message"""
        session = self.memory.sessions.get(session_id)
        if not session or not session.messages:
            return None

        last_message_time = datetime.fromisoformat(session.last_activity).timestamp()
        result = self.proactive.check_inactivity(
            session_id,
            last_message_time,
            session.lead_score,
            len(session.messages)
        )

        return result.message if result else None

    def get_metrics_report(self) -> Dict[str, Any]:
        """Get metrics report"""
        return self.metrics.generate_report()


# Convenience function for quick usage
def create_bot(anthropic_api_key: Optional[str] = None,
               company_name: str = "Vallhamragruppen AB") -> SupportStarterBot:
    """
    Quick function to create a bot

    Args:
        anthropic_api_key: Optional Anthropic API key
        company_name: Name of the company

    Returns:
        Configured SupportStarterBot instance
    """
    config = BotConfig(
        COMPANY_NAME=company_name,
        anthropic_api_key=anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")
    )
    return SupportStarterBot(config)


if __name__ == "__main__":
    # Test the bot
    print("=" * 60)
    print("SUPPORT STARTER AI - MAIN BOT TEST")
    print("=" * 60)

    # Create bot (without API key for testing)
    bot = create_bot()

    # Test messages
    test_messages = [
        "Hej! Hur gör jag en felanmälan?",
        "Vad kostar er förvaltning?",
        "Jag vill boka ett möte",
        "Det här fungerar inte alls! Jag vill prata med en chef!"
    ]

    for i, msg in enumerate(test_messages, 1):
        print(f"\n{'-' * 40}")
        print(f"User: {msg}")

        response = bot.process_message(msg, f"test_session_{i}")

        print(f"Bot: {response.reply}")
        print(f"Intent: {response.intent} (confidence: {response.confidence:.2f})")
        print(f"Sentiment: {response.sentiment}")
        print(f"Lead Score: {response.lead_score}/5")
        print(f"Escalate: {response.escalate}")

        if response.suggested_responses:
            print(f"Suggested: {response.suggested_responses}")

    # Show metrics
    print("\n" + "=" * 60)
    print("METRICS REPORT")
    print("=" * 60)
    report = bot.get_metrics_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
