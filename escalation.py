"""
SUPPORT STARTER AI - SMART ESCALATION SYSTEM
=============================================
Intelligent escalation with full context for human agents
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json


class EscalationPriority(Enum):
    """Escalation priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationReason(Enum):
    """Reasons for escalation"""
    LEGAL_THREAT = "legal_threat"
    ANGRY_CUSTOMER = "angry_customer"
    TECHNICAL_ISSUE = "technical_issue"
    REFUND_DISPUTE = "refund_dispute"
    MANAGER_REQUEST = "manager_request"
    COMPLEX_CASE = "complex_case"
    BILLING_ERROR = "billing_error"
    CONTRACTUAL = "contractual"
    UNKNOWN = "unknown"


@dataclass
class EscalationContext:
    """
    Full context package for human agents
    """
    # Basic info
    escalation_id: str
    conversation_id: str
    timestamp: str
    priority: EscalationPriority
    reason: EscalationReason

    # AI-generated summary
    summary: str
    customer_issue: str

    # Classification data
    detected_intent: str
    customer_sentiment: str
    lead_score: int

    # Customer information
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_company: Optional[str] = None
    order_number: Optional[str] = None

    # Conversation context
    conversation_turns: int = 0
    duration_seconds: Optional[int] = None
    messages_summary: List[str] = None

    # Additional context
    buying_signals: List[str] = None
    objections: List[str] = None
    attempted_solutions: List[str] = None

    # Suggested actions for human agent
    suggested_actions: List[str] = None

    def __post_init__(self):
        if self.messages_summary is None:
            self.messages_summary = []
        if self.buying_signals is None:
            self.buying_signals = []
        if self.objections is None:
            self.objections = []
        if self.attempted_solutions is None:
            self.attempted_solutions = []
        if self.suggested_actions is None:
            self.suggested_actions = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data["priority"] = self.priority.value
        data["reason"] = self.reason.value
        return data

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class EscalationEngine:
    """
    Engine for determining when and how to escalate
    """
    def __init__(self):
        self.escalation_rules = self._load_rules()

    def _load_rules(self) -> Dict[EscalationReason, Dict[str, Any]]:
        """Load escalation rules"""
        return {
            EscalationReason.LEGAL_THREAT: {
                "priority": EscalationPriority.CRITICAL,
                "auto_escalate": True,
                "notify": ["legal", "management"],
                "response_template": "Jag kopplar dig direkt till vår jurist."
            },
            EscalationReason.ANGRY_CUSTOMER: {
                "priority": EscalationPriority.HIGH,
                "auto_escalate": True,
                "notify": ["support_lead"],
                "response_template": "Jag förstår att du är frustrerad. Låt mig koppla dig till en chef som kan hjälpa dig direkt."
            },
            EscalationReason.TECHNICAL_ISSUE: {
                "priority": EscalationPriority.MEDIUM,
                "auto_escalate": False,  # Try to solve first
                "notify": ["technical"],
                "response_template": "Detta verkar vara ett tekniskt problem. Jag eskalerar detta till vårt tekniska team."
            },
            EscalationReason.REFUND_DISPUTE: {
                "priority": EscalationPriority.HIGH,
                "auto_escalate": True,
                "notify": ["billing", "support"],
                "response_template": "Jag förstår angående din återbetalning. Låt mig koppla dig till vår avdelning som hanterar detta."
            },
            EscalationReason.MANAGER_REQUEST: {
                "priority": EscalationPriority.HIGH,
                "auto_escalate": True,
                "notify": ["support_lead"],
                "response_template": "Självklart, jag kopplar dig till en chef."
            },
            EscalationReason.COMPLEX_CASE: {
                "priority": EscalationPriority.MEDIUM,
                "auto_escalate": False,
                "notify": ["support"],
                "response_template": "Detta är en lite mer komplex fråga. Låt mig koppla dig till rätt person."
            },
            EscalationReason.BILLING_ERROR: {
                "priority": EscalationPriority.HIGH,
                "auto_escalate": True,
                "notify": ["billing"],
                "response_template": "Jag ser att det är ett problem med din betalning. Jag eskalerar detta direkt."
            },
            EscalationReason.CONTRACTUAL: {
                "priority": EscalationPriority.HIGH,
                "auto_escalate": True,
                "notify": ["legal", "sales"],
                "response_template": "När det gäller avtal och kontrakt kopplar jag dig till rätt person."
            }
        }

    def should_escalate(self, intent: str, sentiment: str, lead_score: int,
                       conversation_turns: int, message: str) -> tuple[bool, Optional[EscalationReason]]:
        """
        Determine if conversation should be escalated

        Returns:
            Tuple of (should_escalate, reason)
        """
        # Legal threat
        if any(word in message.lower() for word in ["lagar", "advokat", "konsumentverket", "polisen", "stämma"]):
            return True, EscalationReason.LEGAL_THREAT

        # Angry customer
        if sentiment == "angry":
            return True, EscalationReason.ANGRY_CUSTOMER

        # Manager request
        if any(word in message.lower() for word in ["chef", "manager", "ledning", "överordnad"]):
            return True, EscalationReason.MANAGER_REQUEST

        # Technical issue after multiple attempts
        if intent == "technical_issue" and conversation_turns > 3:
            return True, EscalationReason.TECHNICAL_ISSUE

        # Refund dispute
        if intent == "refund_request" and sentiment in ["frustrated", "angry"]:
            return True, EscalationReason.REFUND_DISPUTE

        # Complex case (many turns without resolution)
        if conversation_turns > 8:
            return True, EscalationReason.COMPLEX_CASE

        # Billing issue
        if any(word in message.lower() for word in ["faktureringsfel", "felaktig betalning", "dragen pengar"]):
            return True, EscalationReason.BILLING_ERROR

        # Contractual
        if any(word in message.lower() for word in ["avtal", "kontrakt", "bindande"]):
            return True, EscalationReason.CONTRACTUAL

        return False, None

    def create_escalation_packet(self, conversation_data: Dict[str, Any],
                                 reason: EscalationReason) -> EscalationContext:
        """
        Create full escalation packet for human agents

        Args:
            conversation_data: All conversation data
            reason: Reason for escalation

        Returns:
            EscalationContext with all relevant information
        """
        rule = self.escalation_rules[reason]

        # Generate AI summary
        summary = self._generate_summary(conversation_data, reason)

        # Extract customer issue
        customer_issue = self._extract_customer_issue(conversation_data)

        # Build escalation context
        return EscalationContext(
            escalation_id=f"esc_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            conversation_id=conversation_data.get("conversation_id", "unknown"),
            timestamp=datetime.utcnow().isoformat(),
            priority=rule["priority"],
            reason=reason,
            summary=summary,
            customer_issue=customer_issue,
            detected_intent=conversation_data.get("current_intent", "unknown"),
            customer_sentiment=conversation_data.get("current_sentiment", "unknown"),
            lead_score=conversation_data.get("lead_score", 0),
            customer_name=conversation_data.get("customer_name"),
            customer_email=conversation_data.get("customer_email"),
            customer_phone=conversation_data.get("customer_phone"),
            customer_company=conversation_data.get("customer_company"),
            order_number=conversation_data.get("order_number"),
            conversation_turns=conversation_data.get("message_count", 0),
            duration_seconds=conversation_data.get("duration_seconds"),
            messages_summary=self._summarize_messages(conversation_data.get("messages", [])),
            buying_signals=conversation_data.get("buying_signals", []),
            objections=conversation_data.get("objections", []),
            attempted_solutions=conversation_data.get("attempted_solutions", []),
            suggested_actions=self._generate_suggested_actions(reason, conversation_data)
        )

    def _generate_summary(self, conversation_data: Dict[str, Any],
                         reason: EscalationReason) -> str:
        """Generate AI summary of conversation for human agent"""
        intent = conversation_data.get("current_intent", "unknown")
        sentiment = conversation_data.get("current_sentiment", "unknown")
        turns = conversation_data.get("message_count", 0)

        summaries = {
            EscalationReason.LEGAL_THREAT: f"Kunden har nämnt legala åtgärder. Detta kräver omedelbar hantering av jurist.",
            EscalationReason.ANGRY_CUSTOMER: f"Kunden är mycket frustrerad/arg ({sentiment}). Har samtalat i {turns} rundor utan lösning.",
            EscalationReason.TECHNICAL_ISSUE: f"Tekniskt problem som inte kunnat lösas efter {turns} försök.",
            EscalationReason.REFUND_DISPUTE: f"Kunden vill ha återbetalning och är {sentiment}. Kräver manuell hantering.",
            EscalationReason.MANAGER_REQUEST: f"Kunden har specifikt begärt att prata med en chef.",
            EscalationReason.COMPLEX_CASE: f"Komplext ärende som kräver {turns}+ samtal och mänsklig bedömning.",
            EscalationReason.BILLING_ERROR: f"Fel i betalningssystemet som kräver omedelbar åtgärd.",
            EscalationReason.CONTRACTUAL: f"Frågor rörande avtal/kontrakt som kräver juridisk kompetens."
        }

        return summaries.get(reason, f"Eskalering efter {turns} samtal. Intent: {intent}, Sentiment: {sentiment}")

    def _extract_customer_issue(self, conversation_data: Dict[str, Any]) -> str:
        """Extract the core customer issue"""
        messages = conversation_data.get("messages", [])
        if not messages:
            return "Ingen beskrivning tillgänglig"

        # Get the first user message as the primary issue
        for msg in messages:
            if msg.get("role") == "user":
                return msg.get("content", "")[:200]

        return "Ej specificerat"

    def _summarize_messages(self, messages: List[Dict[str, str]]) -> List[str]:
        """Create a summary of messages"""
        summaries = []
        for msg in messages[-5:]:  # Last 5 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:100]
            summaries.append(f"{role}: {content}...")
        return summaries

    def _generate_suggested_actions(self, reason: EscalationReason,
                                    conversation_data: Dict[str, Any]) -> List[str]:
        """Generate suggested actions for human agent"""
        actions = []

        # Always suggest reading the conversation
        actions.append("Läs igenom konversationen för kontext")

        # Reason-specific actions
        if reason == EscalationReason.ANGRY_CUSTOMER:
            actions.extend([
                "Bekräfta kundens känslor",
                "Erbjud kompensation/lösning snabbt",
                "Följ upp personligen inom 24h"
            ])
        elif reason == EscalationReason.TECHNICAL_ISSUE:
            actions.extend([
                "Samla in felmeddelanden/loggar",
                "Kontakta tekniska teamet",
                "Ge kunden tidsuppskattning"
            ])
        elif reason == EscalationReason.REFUND_DISPUTE:
            actions.extend([
                "Verifiera köp och betalningsstatus",
                "Kontrollera refund policy",
                "Gör bedömning baserat på policy"
            ])
        elif reason == EscalationReason.LEGAL_THREAT:
            actions.extend([
                "Omedelbar kontakt med juridik",
                "Dokumentera allting noga",
                "Svara ej innan konsulterat jurist"
            ])

        return actions

    def get_escalation_response(self, reason: EscalationReason,
                                contact_info: str = None) -> str:
        """Get the response message to send to user when escalating"""
        rule = self.escalation_rules[reason]
        response = rule["response_template"]

        if contact_info:
            response += f"\n\nDu kan också nå oss direkt på {contact_info}."

        return response


class EscalationNotifier:
    """
    Handle notifications when escalation occurs
    """
    def __init__(self):
        self.notification_channels = []

    def add_channel(self, channel_type: str, config: Dict[str, Any]) -> None:
        """Add a notification channel"""
        self.notification_channels.append({
            "type": channel_type,
            "config": config
        })

    def notify(self, escalation: EscalationContext) -> bool:
        """
        Send notifications for escalation

        Returns:
            True if notification sent successfully
        """
        # This would integrate with email, Slack, Teams, etc.
        # For now, just return True
        return True


if __name__ == "__main__":
    # Test escalation system
    print("=" * 60)
    print("SMART ESCALATION SYSTEM - TEST")
    print("=" * 60)

    engine = EscalationEngine()

    # Test escalation decision
    print("\n--- Escalation Decision Tests ---")
    test_cases = [
        {
            "intent": "pricing_question",
            "sentiment": "neutral",
            "lead_score": 3,
            "conversation_turns": 2,
            "message": "Vad kostar det?"
        },
        {
            "intent": "technical_issue",
            "sentiment": "frustrated",
            "lead_score": 2,
            "conversation_turns": 5,
            "message": "Det fungerar fortfarande inte!"
        },
        {
            "intent": "legal_threat",
            "sentiment": "angry",
            "lead_score": 1,
            "conversation_turns": 1,
            "message": "Annars lämnar jag in en anmälan till konsumentverket"
        },
        {
            "intent": "refund_request",
            "sentiment": "frustrated",
            "lead_score": 1,
            "conversation_turns": 3,
            "message": "Jag vill ha pengarna tillbaka nu!"
        }
    ]

    for i, case in enumerate(test_cases, 1):
        should_escalate, reason = engine.should_escalate(
            case["intent"], case["sentiment"], case["lead_score"],
            case["conversation_turns"], case["message"]
        )
        print(f"\nTest {i}: {case['message']}")
        print(f"  Escalate: {should_escalate}")
        if reason:
            print(f"  Reason: {reason.value}")
            print(f"  Priority: {engine.escalation_rules[reason]['priority'].value}")

    # Test escalation packet creation
    print("\n--- Escalation Packet Example ---")
    conversation_data = {
        "conversation_id": "conv_12345",
        "current_intent": "technical_issue",
        "current_sentiment": "frustrated",
        "lead_score": 2,
        "customer_name": "Anders Andersson",
        "customer_email": "anders@example.com",
        "message_count": 5,
        "messages": [
            {"role": "user", "content": "Hej, jag har problem med inloggningen"},
            {"role": "bot", "content": "Jag hjälper dig med det..."},
            {"role": "user", "content": "Det fungerar inte!"},
            {"role": "bot", "content": "Låt mig kolla..."},
            {"role": "user", "content": "Fjärde gången nu, jag vill prata med en människa!"}
        ],
        "buying_signals": [],
        "objections": ["Tekniska problem"],
        "attempted_solutions": ["Basic troubleshooting"]
    }

    packet = engine.create_escalation_packet(
        conversation_data,
        EscalationReason.TECHNICAL_ISSUE
    )
    print(packet.to_json())
