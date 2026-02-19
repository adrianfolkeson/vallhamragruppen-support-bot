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
from chat_logger import LogManager, get_log_manager
from config_loader import load_config_or_default, BotConfig as ConfigBotConfig
from sheets_admin import HybridConfigLoader


@dataclass
class BotConfig:
    """
    Configuration wrapper - loads from JSON config file.
    Falls back to defaults if no config file is found.

    Multi-tenant options:
    - BotConfig()                      # Uses config/config.json or TENANT_ID env var
    - BotConfig(config_file="...")    # Specific config file
    - BotConfig(tenant_id="kund2")    # Loads config/tenants/kund2.json

    Google Sheets integration:
    - Set GOOGLE_SHEET_ID env var to load FAQ from Sheets
    - Set GOOGLE_CREDENTIALS_PATH to point to credentials JSON
    """
    # Delegate to loaded config from file
    _config: ConfigBotConfig = None
    tenant_id: str = None  # Track which tenant this config is for
    _sheets_data: Dict[str, Any] = None  # Cached data from Sheets

    def __init__(self, config_file: Optional[str] = None, tenant_id: Optional[str] = None,
                 use_sheets: bool = True):
        """Load config from JSON file"""
        # Determine config file path
        if config_file is None:
            tenant_id = tenant_id or os.getenv("TENANT_ID")
            if tenant_id:
                # Multi-tenant: look in config/tenants/{tenant_id}.json
                config_file = f"config/tenants/{tenant_id}.json"
            else:
                # Single-tenant: use config/config.json
                config_file = "config/config.json"

        self._config = load_config_or_default(config_file)
        self.tenant_id = tenant_id

        # Load FAQ/knowledge from Google Sheets if enabled
        if use_sheets and os.getenv("GOOGLE_SHEET_ID"):
            try:
                hybrid_loader = HybridConfigLoader(tenant_id=tenant_id, use_sheets=True)
                config_dict = hybrid_loader.load_config()
                self._sheets_data = {
                    "faq_data": config_dict.get("faq_data", []),
                    "knowledge_chunks": config_dict.get("knowledge_chunks", [])
                }
            except Exception as e:
                print(f"Warning: Could not load from Google Sheets: {e}")
                self._sheets_data = None
        else:
            self._sheets_data = None

    @property
    def COMPANY_NAME(self) -> str: return self._config.COMPANY_NAME
    @property
    def industry(self) -> str: return self._config.industry
    @property
    def locations(self) -> str: return self._config.locations
    @property
    def phone(self) -> str: return self._config.phone
    @property
    def contact_email(self) -> str: return self._config.contact_email
    @property
    def website(self) -> str: return self._config.website
    @property
    def business_hours(self) -> str: return self._config.business_hours
    @property
    def response_time(self) -> str: return self._config.response_time
    @property
    def services(self) -> str: return self._config.services
    @property
    def pricing(self) -> str: return self._config.pricing
    @property
    def faq_list(self) -> str: return self._config.faq_list
    @property
    def refund_policy(self) -> str: return self._config.refund_policy
    @property
    def cancellation_policy(self) -> str: return self._config.cancellation_policy
    @property
    def tone_style(self) -> str: return self._config.tone_style
    @property
    def booking_link(self) -> str: return self._config.booking_link
    @property
    def contact_form(self) -> str: return self._config.contact_form
    @property
    def anthropic_api_key(self) -> str: return self._config.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")
    @property
    def max_requests_per_minute(self) -> int: return self._config.max_requests_per_minute

    # Fault response templates
    @property
    def fault_water_critical(self) -> str: return self._config.fault_water_critical
    @property
    def fault_lockout(self) -> str: return self._config.fault_lockout
    @property
    def fault_general_critical(self) -> str: return self._config.fault_general_critical
    @property
    def fault_water_high(self) -> str: return self._config.fault_water_high
    @property
    def fault_heating_high(self) -> str: return self._config.fault_heating_high
    @property
    def fault_electric_high(self) -> str: return self._config.fault_electric_high
    @property
    def fault_general_high(self) -> str: return self._config.fault_general_high
    @property
    def fault_water_medium(self) -> str: return self._config.fault_water_medium
    @property
    def fault_appliance_medium(self) -> str: return self._config.fault_appliance_medium
    @property
    def fault_general_medium(self) -> str: return self._config.fault_general_medium
    @property
    def fault_general_low(self) -> str: return self._config.fault_general_low

    # Local model response templates
    @property
    def greeting_response(self) -> str: return self._config.greeting_response
    @property
    def contact_response(self) -> str: return self._config.contact_response
    @property
    def hours_response(self) -> str: return self._config.hours_response
    @property
    def emergency_critical_response(self) -> str: return self._config.emergency_critical_response
    @property
    def lockout_emergency_response(self) -> str: return self._config.lockout_emergency_response
    @property
    def how_to_report_response(self) -> str: return self._config.how_to_report_response

    # FAQ data from config or Sheets
    @property
    def faq_data(self) -> list:
        """Get FAQ data -优先级: Sheets > Config file"""
        if self._sheets_data and self._sheets_data.get("faq_data"):
            return self._sheets_data["faq_data"]
        return getattr(self._config, 'faq_data', [])

    @property
    def knowledge_chunks(self) -> list:
        """Get knowledge chunks - 优先级: Sheets > Config file"""
        if self._sheets_data and self._sheets_data.get("knowledge_chunks"):
            return self._sheets_data["knowledge_chunks"]
        return getattr(self._config, 'knowledge_chunks', [])


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
        self.local_model = LocalModel(config=self.config)
        self.log_manager = get_log_manager()  # Chat logging & notifications

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
        """Create knowledge base with company info and property management knowledge"""
        rag = SimpleRAG()

        # Load FAQ from config - replace placeholders with actual values
        replacements = {
            "{phone}": self.config.phone,
            "{email}": self.config.contact_email,
            "{locations}": self.config.locations,
            "{COMPANY_NAME}": self.config.COMPANY_NAME,
            "{website}": self.config.website,
            "{business_hours}": self.config.business_hours,
        }

        def replace_placeholders(text):
            """Replace placeholders in text with actual config values"""
            for placeholder, value in replacements.items():
                text = text.replace(placeholder, value)
            return text

        # Load FAQ data from config
        faq_data = []
        for faq in self.config.faq_data:
            faq_data.append({
                "question": replace_placeholders(faq["question"]),
                "answer": replace_placeholders(faq["answer"]),
                "keywords": faq["keywords"]
            })

        from rag import FAQManager
        faq_manager = FAQManager(rag)
        faq_manager.load_faq(faq_data)

        # Add knowledge chunks from config
        from rag import KnowledgeChunk

        # Load knowledge chunks from config
        for chunk_data in self.config.knowledge_chunks:
            rag.add_knowledge(KnowledgeChunk(
                id=chunk_data["id"],
                content=replace_placeholders(chunk_data["content"]),
                category=chunk_data.get("category", "general"),
                keywords=chunk_data.get("keywords", []),
                priority=chunk_data.get("priority", 2)
            ))

        return rag

    def _load_system_prompt(self) -> str:
        """Load and generate system prompt"""
        # Read the V2 template
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
            reply = "Meddelandet kunde inte bearbetas. Vänligen kontakta oss via telefon om problemet kvarstår."
            self._log_bot_response(session_id, reply, "security_block", False)
            return create_response(
                reply=reply,
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

        # Start or update chat log
        conv = self.log_manager.logger.get_conversation(session_id)
        if conv is None:
            customer_info = {
                "name": session.memory.get("customer_name", {}).get("value"),
                "email": session.memory.get("customer_email", {}).get("value"),
                "phone": session.memory.get("customer_phone", {}).get("value")
            }
            self.log_manager.start_conversation(session_id, customer_info)

        # Log user message
        self.log_manager.log_message(session_id, "user", message)

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

            reply = fault_result["response"] + follow_up
            self._log_bot_response(session_id, reply, "fault_report", is_urgent,
                                  urgency=report.urgency.value)
            return create_response(
                reply=reply,
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
            self._log_bot_response(session_id, local_result["response"],
                                  local_result["intent"], local_result["escalate"])
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

            self._log_bot_response(session_id, escalation_response,
                                  router_result.intent.value, True)
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

        # 14. Log bot response and create response
        self._log_bot_response(session_id, reply, router_result.intent.value, False)
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

    def _log_bot_response(self, session_id: str, reply: str, intent: str,
                          escalate: bool, urgency: str = None):
        """Log bot response to chat logger"""
        metadata = {"intent": intent}
        if escalate:
            metadata["escalated"] = True
        if urgency:
            metadata["urgency"] = urgency
        self.log_manager.log_message(session_id, "assistant", reply, **metadata)

        # Auto-end conversation if escalated (send notifications)
        if escalate and intent != "fault_report":  # fault reports handled separately
            self.log_manager.end_conversation(session_id, status="escalated")

    def _generate_response(self, message: str, prompt: str,
                          router_result, session) -> str:
        """Generate AI response using Anthropic or fallback"""
        if self.client:
            try:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=800,  # Increased for more detailed answers
                    temperature=0.5,  # Slightly higher for more natural responses
                    system=prompt,
                    messages=[{"role": "user", "content": message}]
                )
                return response.content[0].text
            except Exception as e:
                print(f"API Error: {e}")
                # Fall back to simple response

        # Fallback: Use RAG + rule-based response when API unavailable
        return self._get_fallback_response(message, router_result, session)

    def _get_fallback_response(self, message: str, router_result, session) -> str:
        """Get fallback response when API is unavailable - uses RAG for smart answers"""
        intent = router_result.intent.value
        sentiment = router_result.sentiment.value

        # First, try to get relevant FAQ from RAG
        rag_results = self.rag.retrieve(message, top_k=3)
        if rag_results.chunks and len(rag_results.chunks) > 0:
            # We found relevant knowledge - return the top result
            top_chunk = rag_results.chunks[0]
            response = top_chunk.content
            # Clean up FAQ format (remove "Q: ... A:" prefix)
            if "\nA: " in response:
                response = response.split("\nA: ")[1]
            # Remove any remaining "Q:" prefix
            if response.startswith("Q: "):
                response = response.split("A: ")[-1] if "A: " in response else response[3:]
            # Add a friendly closing if the response is short
            if len(response) < 200:
                response += "\n\nRing 0793-006638 för mer information eller visning."
            return response

        # Check for direct FAQ match using trigger phrases
        from rag import FAQManager
        faq_manager = FAQManager(self.rag)
        if router_result.trigger_phrases:
            faq_answer = faq_manager.get_answer(router_result.trigger_phrases[0])
            if faq_answer:
                return faq_answer

        # Rule-based responses for common intents
        if "pricing" in intent or "pris" in intent:
            return self.config.pricing

        if "booking" in intent or "boka" in intent:
            return f"Vad roligt att du vill boka! Ring {self.config.phone} så hittar vi en tid som passar."

        if sentiment == "angry":
            return "Jag förstår att detta är viktigt för dig. Ring 0793-006638 så hjälper en kollega dig direkt."

        if sentiment == "frustrated":
            return "Jag ber om ursäkt för besväret. Ring 0793-006638 så hjälper vi dig vidare."

        # Default response - friendly and directing to contact
        return f"Vad gäller? 🤔 Ring {self.config.phone} eller {self.config.contact_email} så hjälper vi dig direkt!"

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
               company_name: str = "Vallhamragruppen AB",
               tenant_id: Optional[str] = None) -> SupportStarterBot:
    """
    Quick function to create a bot

    Args:
        anthropic_api_key: Optional Anthropic API key (overrides env/config)
        company_name: Name of the company (only used if no config file found)
        tenant_id: Tenant ID for multi-tenant deployment

    Returns:
        Configured SupportStarterBot instance
    """
    config = BotConfig(tenant_id=tenant_id)

    # Override API key if provided
    if anthropic_api_key:
        config._config.anthropic_api_key = anthropic_api_key

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
