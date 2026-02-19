"""
SUPPORT STARTER AI - CONVERSATION MEMORY SYSTEM
===============================================
Smart memory for personalized, contextual conversations
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import json


class MemoryEventType(Enum):
    """Types of memory events"""
    USER_INFO = "user_info"
    ISSUE_CATEGORY = "issue_category"
    BUYING_SIGNAL = "buying_signal"
    OBJECTION = "objection"
    PREFERENCE = "preference"
    INTERACTION = "interaction"


@dataclass
class MemoryEvent:
    """A single memory event"""
    event_type: MemoryEventType
    key: str
    value: Any
    timestamp: str
    confidence: float = 1.0


@dataclass
class ConversationSession:
    """A single conversation session"""
    session_id: str
    started_at: str
    last_activity: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Conversation state
    current_intent: Optional[str] = None
    current_sentiment: Optional[str] = None
    lead_score: int = 1
    escalation_count: int = 0
    resolved: bool = False

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Add a message to the conversation"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        })
        self.last_activity = datetime.utcnow().isoformat()

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent messages"""
        return self.messages[-limit:]

    def update_memory(self, key: str, value: Any, event_type: MemoryEventType = MemoryEventType.INTERACTION) -> None:
        """Update memory with new information"""
        self.memory[key] = {
            "value": value,
            "event_type": event_type.value,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_memory_summary(self) -> str:
        """Get a summary of stored memory for prompt injection"""
        if not self.memory:
            return ""

        parts = []
        for key, data in self.memory.items():
            parts.append(f"- {key}: {data['value']}")

        return "Customer Information:\n" + "\n".join(parts)


class ConversationMemory:
    """
    Manages conversation memory and sessions
    """
    def __init__(self, session_timeout_minutes: int = 60):
        self.sessions: Dict[str, ConversationSession] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.global_memory: Dict[str, Any] = {}  # Cross-session memory

    def get_or_create_session(self, session_id: str) -> ConversationSession:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationSession(
                session_id=session_id,
                started_at=datetime.utcnow().isoformat(),
                last_activity=datetime.utcnow().isoformat()
            )
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str,
                   intent: Optional[str] = None,
                   sentiment: Optional[str] = None,
                   lead_score: Optional[int] = None) -> ConversationSession:
        """Add a message and update session state"""
        session = self.get_or_create_session(session_id)

        metadata = {}
        if intent:
            metadata["intent"] = intent
            session.current_intent = intent
        if sentiment:
            metadata["sentiment"] = sentiment
            session.current_sentiment = sentiment
        if lead_score is not None:
            metadata["lead_score"] = lead_score
            session.lead_score = max(session.lead_score, lead_score)

        session.add_message(role, content, metadata)
        return session

    def extract_and_store_info(self, session_id: str, info_type: str, value: str) -> None:
        """Extract and store information from conversation"""
        session = self.get_or_create_session(session_id)

        # Store based on type
        if info_type == "name":
            session.update_memory("customer_name", value, MemoryEventType.USER_INFO)
            self.global_memory[f"{session_id}_name"] = value
        elif info_type == "email":
            session.update_memory("customer_email", value, MemoryEventType.USER_INFO)
            self.global_memory[f"{session_id}_email"] = value
        elif info_type == "phone":
            session.update_memory("customer_phone", value, MemoryEventType.USER_INFO)
        elif info_type == "company":
            session.update_memory("customer_company", value, MemoryEventType.USER_INFO)
        elif info_type == "issue_category":
            session.update_memory("primary_issue", value, MemoryEventType.ISSUE_CATEGORY)
        elif info_type == "buying_signal":
            signals = session.memory.get("buying_signals", [])
            if signals:
                signals.append(value)
            else:
                signals = [value]
            session.update_memory("buying_signals", signals, MemoryEventType.BUYING_SIGNAL)
        elif info_type == "objection":
            objections = session.memory.get("objections", [])
            if objections:
                objections.append(value)
            else:
                objections = [value]
            session.update_memory("objections", objections, MemoryEventType.OBJECTION)

    def get_contextual_prompt_addition(self, session_id: str) -> str:
        """
        Generate contextual addition for the prompt based on memory
        This makes the bot feel more human by remembering context
        """
        session = self.sessions.get(session_id)
        if not session:
            return ""

        parts = []

        # Add customer info if available
        if "customer_name" in session.memory:
            name = session.memory["customer_name"]["value"]
            parts.append(f"Customer's name is {name}.")

        # Add conversation context
        if len(session.messages) > 2:
            parts.append(f"You are {len(session.messages)} messages into this conversation.")

        # Add issue context if known
        if "primary_issue" in session.memory:
            issue = session.memory["primary_issue"]["value"]
            parts.append(f"The main issue is: {issue}")

        # Add buying signals context
        if "buying_signals" in session.memory:
            signals = session.memory["buying_signals"]["value"]
            if signals:
                parts.append(f"Customer has shown interest in: {', '.join(signals)}")

        # Add recent context reference
        if len(session.messages) >= 4:
            parts.append("Acknowledge previous context when relevant to build continuity.")

        if parts:
            return "\n\n## CONVERSATION CONTEXT\n" + "\n".join(parts) + "\n"

        return ""

    def get_personalized_greeting(self, session_id: str) -> str:
        """Get personalized greeting based on memory"""
        session = self.sessions.get(session_id)
        if not session:
            return "Hej! Hur kan jag hjälpa dig idag?"

        if "customer_name" in session.memory:
            name = session.memory["customer_name"]["value"]
            msg_count = len([m for m in session.messages if m["role"] == "user"])
            if msg_count > 2:
                return f"Hej {name}! Hur kan jag hjälpa dig vidare?"
            return f"Hej {name}! Välkommen!"

        return "Hej! Hur kan jag hjälpa dig idag?"

    def cleanup_old_sessions(self) -> int:
        """Remove sessions that have timed out"""
        now = datetime.utcnow()
        to_remove = []

        for session_id, session in self.sessions.items():
            last_activity = datetime.fromisoformat(session.last_activity)
            if now - last_activity > self.session_timeout:
                to_remove.append(session_id)

        for session_id in to_remove:
            del self.sessions[session_id]

        return len(to_remove)

    def get_session_for_escalation(self, session_id: str) -> Dict[str, Any]:
        """Get session data formatted for escalation"""
        session = self.sessions.get(session_id)
        if not session:
            return {}

        return {
            "session_id": session.session_id,
            "customer_info": {
                "name": session.memory.get("customer_name", {}).get("value"),
                "email": session.memory.get("customer_email", {}).get("value"),
                "phone": session.memory.get("customer_phone", {}).get("value"),
                "company": session.memory.get("customer_company", {}).get("value"),
            },
            "conversation_summary": self._generate_summary(session),
            "messages": session.messages,
            "metadata": {
                "intent": session.current_intent,
                "sentiment": session.current_sentiment,
                "lead_score": session.lead_score,
                "issue": session.memory.get("primary_issue", {}).get("value"),
                "buying_signals": session.memory.get("buying_signals", {}).get("value", []),
                "objections": session.memory.get("objections", {}).get("value", []),
            }
        }

    def _generate_summary(self, session: ConversationSession) -> str:
        """Generate a summary of the conversation"""
        if not session.messages:
            return "Empty conversation"

        # Get user messages only
        user_messages = [m["content"] for m in session.messages if m["role"] == "user"]

        if len(user_messages) == 1:
            return f"Customer said: {user_messages[0][:100]}..."

        return f"Conversation with {len(user_messages)} messages. Last message: {user_messages[-1][:100]}..."


# Info extraction patterns
INFO_PATTERNS = {
    "name": [
        r"(?:jag heter|mitt namn är|it's|i'm|i am|name is)\s+([A-Z][a-z]+)",
        r"^(Hej|Hey|Hi)\s*,?\s*([A-Z][a-z]+)",
    ],
    "email": [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    ],
    "phone": [
        r"\b(?:\+?46|0)[0-9]{7,10}\b",
        r"\b[0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{2,}\b",
    ],
    "company": [
        r"(?:på|at|från|from)\s+([A-Z][A-Za-zåäöÅÄÖ]+(?:\s+(?:AB|HB|Group|iQ)))",
    ]
}


def extract_info_from_message(message: str) -> List[tuple[str, str]]:
    """
    Extract structured information from user message

    Returns:
        List of (info_type, value) tuples
    """
    import re
    results = []

    for info_type, patterns in INFO_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                value = match.group(1) if match.lastindex and match.group(1) else match.group(0)
                results.append((info_type, value.strip()))

    return results


if __name__ == "__main__":
    # Test the memory system
    print("=" * 60)
    print("CONVERSATION MEMORY - TEST")
    print("=" * 60)

    memory = ConversationMemory()
    session_id = "test_session_123"

    # Simulate a conversation
    messages = [
        ("user", "Hej! Jag heter Anders"),
        ("bot", "Hej Anders! Hur kan jag hjälpa dig?"),
        ("user", "Vad kostar er tjänst?", "pricing_question", "neutral", 3),
        ("bot", "Våra priser startar på 299 kr/månad..."),
        ("user", "Kan ni integrera med vårt CRM-system?", "integration_question", "neutral", 4),
        ("bot", "Ja absolut! Vi integrerar med de flesta..."),
        ("user", "anders@foretag.se - skicka mer info", "booking_request", "positive", 5),
    ]

    for msg in messages:
        if len(msg) == 2:
            role, content = msg
            memory.add_message(session_id, role, content)
        else:
            role, content, intent, sentiment, score = msg
            memory.add_message(session_id, role, content, intent, sentiment, score)

        # Extract info
        if msg[0] == "user":
            for info_type, value in extract_info_from_message(msg[1]):
                memory.extract_and_store_info(session_id, info_type, value)
                print(f"  Extracted: {info_type} = {value}")

    print("\n--- Session Summary ---")
    session = memory.sessions[session_id]
    print(f"Customer Name: {session.memory.get('customer_name', {}).get('value', 'Unknown')}")
    print(f"Customer Email: {session.memory.get('customer_email', {}).get('value', 'Unknown')}")
    print(f"Lead Score: {session.lead_score}")
    print(f"Current Intent: {session.current_intent}")
    print(f"Current Sentiment: {session.current_sentiment}")

    print("\n--- Contextual Addition ---")
    print(memory.get_contextual_prompt_addition(session_id))

    print("\n--- Escalation Data ---")
    escalation_data = memory.get_session_for_escalation(session_id)
    print(json.dumps(escalation_data, indent=2, ensure_ascii=False))
