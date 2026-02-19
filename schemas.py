"""
SUPPORT STARTER AI - STRUCTURED JSON OUTPUT SCHEMAS
====================================================
All responses are structured JSON for backend automation
"""

from enum import Enum
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass, asdict
from datetime import datetime
import json


class ActionType(Enum):
    """Action types for bot responses"""
    NONE = "none"
    ESCALATE = "escalate"
    BOOK_CALL = "book_call"
    COLLECT_INFO = "collect_info"
    SEND_EMAIL = "send_email"
    CREATE_TICKET = "create_ticket"
    TAG_LEAD = "tag_lead"
    PROACTIVE_OFFER = "proactive_offer"


@dataclass
class BotResponse:
    """
    Standard structured response from the AI bot
    This enables backend automation and CRM integration
    """
    # Core response
    reply: str  # The actual message to show user
    action: Literal["none", "escalate", "book_call", "collect_info", "send_email", "create_ticket", "tag_lead", "proactive_offer"]

    # Classification (from router)
    intent: str
    confidence: float  # 0.0 to 1.0
    sentiment: str
    lead_score: int  # 1 to 5

    # Flags for automation
    escalate: bool
    requires_followup: bool
    conversion_ready: bool
    urgency: Literal["low", "medium", "high", "critical"]

    # Additional data
    suggested_responses: Optional[list[str]] = None  # Quick reply buttons
    collected_info: Optional[Dict[str, str]] = None  # Info gathered from user
    escalation_summary: Optional[str] = None  # Summary for human agent
    micro_conversion_step: Optional[str] = None  # Next small conversion step

    # Timestamps
    timestamp: str = None
    response_time_ms: Optional[int] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class EscalationPacket:
    """
    When escalating to human, send a complete packet
    """
    conversation_id: str
    summary: str  # AI-generated summary of issue
    customer_issue: str  # The actual problem
    intent: str
    sentiment: str
    lead_score: int
    priority: Literal["low", "medium", "high", "critical"]
    conversation_history: list[Dict[str, str]]

    # Customer info (if collected)
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    order_number: Optional[str] = None

    # Metadata
    timestamp: str = None
    bot_confidence: float = None
    reason_for_escalation: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class LeadData:
    """
    Lead scoring and CRM data packet
    """
    conversation_id: str
    lead_score: int  # 1 to 5
    lead_stage: Literal["awareness", "consideration", "decision", "ready_to_buy"]

    # Triggered buying signals
    triggered_signals: list[str]

    # Contact info (if provided)
    email: Optional[str] = None
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None

    # Interest data
    interested_services: list[str] = None
    questions_asked: list[str] = None
    objections: list[str] = None

    # Suggested next action
    suggested_action: Optional[str] = None
    suggested_cta: Optional[str] = None

    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.interested_services is None:
            self.interested_services = []
        if self.questions_asked is None:
            self.questions_asked = []
        if self.objections is None:
            self.objections = []

    def should_notify_sales(self) -> bool:
        """Determine if sales team should be notified"""
        return self.lead_score >= 4 and self.email is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class ConversationMetrics:
    """
    Metrics for tracking conversation performance
    """
    conversation_id: str

    # Counts
    total_messages: int
    user_messages: int
    bot_messages: int

    # Classification stats
    intents_detected: list[str]
    avg_confidence: float
    sentiment_progression: list[str]

    # Lead scoring
    initial_lead_score: int
    final_lead_score: int
    lead_score_change: int

    # Timing
    started_at: str
    ended_at: Optional[str] = None
    duration_seconds: Optional[int] = None

    # Outcomes
    escalated: bool = False
    converted: bool = False
    resolved: bool = False
    conversion_action: Optional[str] = None

    # Quality
    user_satisfaction: Optional[str] = None  # If collected

    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.ended_at and self.started_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.ended_at)
            self.duration_seconds = int((end - start).total_seconds())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# Helper function to create response
def create_response(
    reply: str,
    intent: str,
    confidence: float,
    sentiment: str,
    lead_score: int,
    escalate: bool = False,
    action: str = "none",
    **kwargs
) -> BotResponse:
    """
    Helper to create a BotResponse with common values

    Args:
        reply: Message to user
        intent: Detected intent
        confidence: Confidence score
        sentiment: Detected sentiment
        lead_score: Lead score 1-5
        escalate: Should escalate
        action: Action type
        **kwargs: Additional fields

    Returns:
        BotResponse object
    """
    # Determine urgency based on sentiment and escalate flag
    if escalate or sentiment == "angry":
        urgency = "critical"
    elif sentiment == "frustrated":
        urgency = "high"
    elif lead_score >= 4:
        urgency = "medium"
    else:
        urgency = "low"

    return BotResponse(
        reply=reply,
        action=action,
        intent=intent,
        confidence=confidence,
        sentiment=sentiment,
        lead_score=lead_score,
        escalate=escalate,
        requires_followup=kwargs.get("requires_followup", lead_score >= 3),
        conversion_ready=lead_score >= 4 and sentiment not in ["angry", "frustrated"],
        urgency=urgency,
        **kwargs
    )


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("STRUCTURED OUTPUT SCHEMAS - EXAMPLES")
    print("=" * 60)

    # Example 1: Simple pricing question
    response1 = create_response(
        reply="Våra priser startar på 299 kr/månad. Vill du veta mer om vad som ingår?",
        intent="pricing_question",
        confidence=0.92,
        sentiment="neutral",
        lead_score=3,
        escalate=False,
        action="none",
        suggested_responses=[
            "Ja, berätta mer",
            "Boka ett möte",
            "Nej tack"
        ]
    )
    print("\nExample 1 - Pricing Question:")
    print(response1.to_json())

    # Example 2: Escalation packet
    escalation = EscalationPacket(
        conversation_id="conv_12345",
        summary="Kunden är frustrerad över att deras data inte synkoras korrekt.",
        customer_issue="Data synkroniseras inte mellan plattformarna",
        intent="technical_issue",
        sentiment="frustrated",
        lead_score=2,
        priority="high",
        conversation_history=[
            {"role": "user", "content": "Varför synkas inte min data?"},
            {"role": "bot", "content": "Låt mig hjälpa dig med det..."},
            {"role": "user", "content": "Det här är fjärde gången, jag vill prata med en människa!"}
        ],
        customer_email="kund@exempel.se",
        reason_for_escalation="Kunden kräver människa och är frustrerad"
    )
    print("\nExample 2 - Escalation Packet:")
    print(escalation.to_json())

    # Example 3: Lead data
    lead = LeadData(
        conversation_id="conv_67890",
        lead_score=5,
        lead_stage="ready_to_buy",
        triggered_signals=["Prisfråga", "Bokningsförfrågan", "Företagskontext"],
        email="kontakt@foretag.se",
        company="Exempel AB",
        interested_services=["Support Starter AI", "Metrics Engine"],
        suggested_action="Ring kunden inom 1 timme",
        suggested_cta="Boka demo"
    )
    print("\nExample 3 - Lead Data:")
    print(lead.to_json())
