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
    locations: str = "Johanneberg, Partille, Mölndal"
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
    A: Vi verkar främst i Johanneberg, Partille och Mölndal.

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
        """Create knowledge base with company info and property management knowledge"""
        rag = SimpleRAG()

        # Add comprehensive FAQ
        faq_data = [
            # Basic contact & info
            {
                "question": "Hur gör jag en felanmälan?",
                "answer": "Felanmälan görs enklast via vår hemsida under 'Kontakta oss' eller genom att ringa oss på 0793-006638. För akuta ärenden utanför kontorstid, ring vår jour.",
                "keywords": ["felanmälan", "fel", "reparation", "jour"]
            },
            {
                "question": "Vilka områden verkar ni i?",
                "answer": "Vi verkar främst i Johanneberg, Partille och Mölndal med omnejd.",
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
            },

            # Property Management - Technical
            {
                "question": "Vad ingår i fastighetsförvaltning?",
                "answer": "Fastighetsförvaltning inkluderar: drift och underhåll, ekonomisk förvaltning, hyresadministration, styrelsesupport för BRF:er, projektledning vid renoveringar, och jour dygnet runt för akuta ärenden.",
                "keywords": ["tjänster", "förvaltning", "ingår", "omfatt"]
            },
            {
                "question": "Vem ansvarar för vitvaror i lägenheten?",
                "answer": "Vitvaror som ägaren själv köpt (t.ex. diskmaskin, tvättmaskin) är hyresgästens/ägarens ansvar. Fastighetsägaren ansvarar för inkopplade vitvaror som ingår i lägenheten (ofta kyl/frys i vissa nybyggnationer). Vid osäkerhet, kontakta oss.",
                "keywords": ["vitvaror", "ansvar", "diskmaskin", "tvättmaskin", "kyl", "frys"]
            },
            {
                "question": "Vem byter glödlampor och lampor?",
                "answer": "Hyresgäst/ägare byter självvanliga glödlampor och LED-lampor. Sitter armaturen fast i tak/vägg och går ej att lossa är det fastighetsägarens ansvar.",
                "keywords": ["lampa", "glödlampa", "belysning", "byt", "ansvar"]
            },
            {
                "question": "Vad gör jag om det droppar vatten?",
                "answer": "Droppar det från en kran eller armatur, försök täta med handduk. Är det en vattenläcka från rör, stäng av ventilen under diskhon och ring jour på 0793-006638. Oavsätt - kontrollera om vatten når eluttag.",
                "keywords": ["vatten", "dropp", "läcka", "kran", "akut"]
            },
            {
                "question": "Vem ansvarar för fönsterputs?",
                "answer": "Hyresgäst/ägare putsar själva invändigt. Utvändig putsning och fönster på höga våningar sköts av fastighetsägaren med jämna mellanrum.",
                "keywords": ["fönster", "puts", "städ", "rent"]
            },

            # Property Management - Tenant/Landlord
            {
                "question": "Får jag hyra ut min lägenhet i andra hand?",
                "answer": "Andrahandsuthyrning kräver godkännande från bostadsrättsförening eller hyresvärd. Kontakta oss på 0793-006638 för ansökan och information om processen.",
                "keywords": ["andrahand", "andra hand", "hyra ut", "andrahandsuthyrning"]
            },
            {
                "question": "Vem ansvarar för brf-lokalerna?",
                "answer": "Bostadsrättsföreningen äger och ansvarar för alla gemensamma ytor: trapphus, källare, vind, tvättstugor, utvändiga markytor, etc. Medlemmarna äger sina lägenheter genom andelar i föreningen.",
                "keywords": ["brf", "bostadsrätt", "ansvar", "gemensam", "lokal"]
            },
            {
                "question": "Vad är en underhållsplan?",
                "answer": "En underhållsplan är ett dokument som beskriver fastighetens skick och planerade underhållsåtgärder de kommande 10-25 åren. Den är obligatorisk för bostadsrättsföreningar och viktig för ekonomisk planering.",
                "keywords": ["underhållsplan", "plan", "underhåll", "besiktning", "brf"]
            },

            # Heating, Water, Ventilation
            {
                "question": "Elementet är kallt, vad göra?",
                "answer": "Kolla först att termostaten står på tillräckligt. Om elementet är kallt medan andra i lägenheten är varma kan det vara luft i systemet - försök lufta det. Hjälper ej? Ring 0793-006638.",
                "keywords": ["element", "kallt", "värme", "lufta", "termostat"]
            },
            {
                "question": "Hur luftrar jag elementet?",
                "answer": "Vänta tills elementet är varmt. Använd en nyckel/ventilnyckel (eller plånbok) för att vrida på luftskruven på sidan av elementet tills det comes en liten stråle vatten. Stäng sedan till.",
                "keywords": ["lufta", "element", "värme", "instruktion"]
            },
            {
                "question": "Ventilationen dålig, vad göra?",
                "answer": "Kolla att ventilationsdon i tak/vägg är öppna och inte täckta. Rengör vid behov. Känner du ändå dålig ventilation, ring 0793-006638 för besiktning.",
                "keywords": ["ventilation", "fläkt", "luft", "dålig", "fukt"]
            },
            {
                "question": "Vad är normal inomhustemperatur?",
                "answer": "Enligt gällande regler ska inomhustemperaturen vara minst 20°C under vintersäsong (oktober-april). Vid permanent temperatur under 18°C bör du kontakta oss.",
                "keywords": ["temperatur", "värme", "kallt", "inomhus", "gräns"]
            },

            # Keys, Locks, Security
            {
                "question": "Jag har tappat min nyckel, vad göra?",
                "answer": "Är du utelåst, ring jour på 0793-006638 direkt för akut hjälp. Ej utelåst men nyckel borta? Ring 0793-006638 för att beställa ny nyckel/låsbyte. Kostnad kan debiteras vid förlorad nyckel.",
                "keywords": ["nyckel", "tappat", "borta", "utelåst", "lås"]
            },
            {
                "question": "Låset går inte att öppna, vad göra?",
                "answer": "Är nyckel runt? Proba varsamt. Ej? Det kan vara fruset vinter - värm med hårfön. Ej hjälp? Ring jour 0793-006638.",
                "keywords": ["lås", "dörr", "öppna", "fast", "problem"]
            },
            {
                "question": "Får jag byta låset själv?",
                "answer": "Nej, låsbyten måste göras av behörig låsinstallatör som anlitas av fastighetsägaren. Själv installerade lås godkänns ej och kan behöva bytas ut på din kostnad.",
                "keywords": ["lås", "byt", "byta", "själv", "installera"]
            },
            {
                "question": "Vad göra vid inbrott?",
                "answer": "1. Ring polisen 114 14 för anmälan. 2. Ring oss på 0793-006638 för att rapportera skadan och säkra fastigheten. 3. Kontakta ditt försäkringsbolag.",
                "keywords": ["inbrott", "stöld", "skada", "polis", "anmäl"]
            },

            # Common property issues
            {
                "question": "Avloppet är stoppat, vad göra?",
                "answer": "Kolla först om det är golvbrunnen (vanligast i badrum) - rensa hår och smuts. Ej hjälp eller gäller köksavlopp? Ring 0793-006638. Avstängning och rot-avdrag kan gälla.",
                "keywords": ["avlopp", "stop", "propp", "vatten", "backar"]
            },
            {
                "question": "Mögel och fukt i bostad?",
                "answer": "Fukt och mögel är allvarligt. Vid misstanke om fuktskada, ring 0793-006638 direkt för besiktning. Ventilera inte överdrivet - fuktens källa måste identifieras.",
                "keywords": ["fukt", "mögel", "lukt", "luktar", "fuktig"]
            },
            {
                "question": "Vem ansvarar för snöröjning?",
                "answer": "Fastighetsägaren ansvarar för snöröjning och halkbekämpning på gemensamma ytor och vid entréer. Hyresgästen/ägare sköter sin egen parkering/balkong om inte annat överenskommits.",
                "keywords": ["snö", "snöröjning", "halka", "is", "vinter"]
            },
            {
                "question": "Grannar stör med ljud, vad göra?",
                "answer": "Vid akut nattstörning (22-06): ring jour på 0793-006638. Dagtid: kontakta grannen först eller ring oss på 0793-006638 för medling.",
                "keywords": ["stör", "oljud", "granne", "ljud", "natt"]
            },

            # Insurance & Damage
            {
                "question": "Gäller min hemförsäkring vid skada?",
                "answer": "Hemförsäkring gäller för din egendom (möbler, kläder, etc). Fastigheten är oftast försäkrad genom fastighetsägarens fastighetsförsäkring. Vid skada - kontakta ditt försäkringsbolag och oss.",
                "keywords": ["försäkring", "hemförsäkring", "skada", "ansvar"]
            },
            {
                "question": "Vem betalar vid vattenskada?",
                "answer": "Fastighetsägarens fastighetsförsäkring gäller för skador på fastigheten (golv, väggar, fast inredning). Din hemförsäkring gäller för dina saker. Vid vattenskada - ring jour 0793-006638 direkt för att begränsa skadan.",
                "keywords": ["vattenskada", "vatten", "läcka", "försäkring", "betala"]
            },

            # Moving & Administration
            {
                "question": "Hur gör jag en flyttanmälan?",
                "answer": "Kontakta oss på 0793-006638 minst en månad innan flytt. För BRF-medlemmar: kontakta även föreningen för överlåtelsebeslut. Nycklar överlämnas på överenskommen tid.",
                "keywords": ["flytt", "utflytt", "inflytt", "flyttanmälan", "nyckel"]
            },
            {
                "question": "Vad är en besiktning?",
                "answer": "Besiktning innebär att en besiktningsman granskar fastigheten för att identifiera skador, underhållsbehov och ålder på olika delar. Det görs vid överlåtelse, renovering, eller periodiskt för underhållsplanering.",
                "keywords": ["besiktning", "besiktiga", "genomgång", "skick"]
            },

            # Commercial properties
            {
                "question": "Hanterar ni kommersiella fastigheter?",
                "answer": "Ja, vi förvaltar kommersiella fastigheter såsom kontor, butiker, lager och industri. Vi erbjuder skräddarsydda lösningar beroende på verksamhetens behov.",
                "keywords": ["kommersiell", "lokal", "kontor", "butik", "företag"]
            },
            {
                "question": "Vad ingår i lokalvård för kontor?",
                "answer": "Lokalvård kan inkludera: städning, fönsterputs, toalettstädning, pappershantering, och grönyteskötsel. Vi skräddarsyr avtal efter behov.",
                "keywords": ["lokalvård", "städ", "kontor", "lokal"]
            },
        ]

        from rag import FAQManager
        faq_manager = FAQManager(rag)
        faq_manager.load_faq(faq_data)

        # Add company info as knowledge chunks
        from rag import KnowledgeChunk

        # Company contact info
        rag.add_knowledge(KnowledgeChunk(
            id="company_info",
            content=f"COMPANY: {self.config.COMPANY_NAME}. Phone: {self.config.phone}. Email: {self.config.contact_email}. Website: {self.config.website}. Business hours: {self.config.business_hours}. Locations: Johanneberg, Partille, Mölndal.",
            category="contact",
            keywords=["kontakt", "ring", "mejl", "telefon", "öppettider", "adress", "plats"],
            priority=3
        ))

        # Property management industry knowledge
        rag.add_knowledge(KnowledgeChunk(
            id="property_management_basics",
            content="Fastighetsförvaltning innefattar: 1) Drift - dagliga operativa åtgärder som städning, trädgård, belysning. 2) Underhåll - förebyggande och avhjälpande underhåll av byggnad, installationer, mark. 3) Ekonomisk förvaltning - bokföring, budget, fakturering, årsredovisning. 4) Hyresadministration - kontrakt, hyresavisering, förhandling. 5) Styrelsesupport - för BRF:er med protokoll, stadgar, årsmöten.",
            category="industry",
            keywords=["förvaltning", "fastighet", "drift", "underhåll", "ekonomi", "tjänster"],
            priority=2
        ))

        rag.add_knowledge(KnowledgeChunk(
            id="tenant_landlord_responsibility",
            content="ANSVARSFÖRDELNING: Hyresgäst/Ägare ansvarar för: bostadsinredning (tapeter, golv), egna vitvaror, glödlampor, lätta reparationer (skruva upp luckor, byta packningar kran), borstädningsutrustning, egen säkring. Fastighetsägare ansvarar för: byggnadskonstruktion, tak, fasad, fönster (utom renhållning), VVS-installationer (rör, element), el-central, stammar, gemensamma ytor, mark och grönytor, fastighetsnära parkering.",
            category="responsibility",
            keywords=["ansvar", "vem", "hyresgäst", "fastighetsägare", "reparation", "underhåll"],
            priority=3
        ))

        rag.add_knowledge(KnowledgeChunk(
            id="emergency_urgency_levels",
            content="AKUTGRUPPER: 1) Kritiskt - omedelbar fara för liv/egendom: brand, gasläcka, översvämning, inbrott pågående. Ring 112 + jour 0793-006638. 2) Högt - påverkar boständ/tjänst betydande: ingen värme vinter, inget vatten, strömavbrott hela fastigheten, utelåsning. Ring jour 0793-006638. 3) Medium - besvärande men ej akut: droppande kran, svaga ventilation, trasig armatur. Ring 0793-006638 vardagstid. 4) Lågt - önskemål/frågor: allmän info, bokning, ärenden som kan vänta.",
            category="emergency",
            keywords=["akut", "urgens", "jour", "prioriter", "kritiskt"],
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
        return f"Vad gäller? Ring {self.config.phone} eller {self.config.contact_email} så hjälper vi dig."

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
