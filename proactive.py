"""
SUPPORT STARTER AI - PROACTIVE SUPPORT & MICRO-CONVERSIONS
===========================================================
Proactive engagement and micro-conversion engine
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import time


class InactivityTrigger(Enum):
    """Types of inactivity triggers"""
    SHORT = 20  # seconds
    MEDIUM = 45  # seconds
    LONG = 90  # seconds


class ConversionStep(Enum):
    """Micro-conversion funnel steps"""
    AWARENESS = "awareness"  # User is browsing
    ENGAGED = "engaged"  # User asked a question
    INTERESTED = "interested"  # User asked about pricing/features
    CONSIDERING = "considering"  # Multiple questions, high engagement
    READY = "ready"  # Showing buying signals
    CONVERTING = "converting"  # In booking process


@dataclass
class ProactiveMessage:
    """A proactive message to send"""
    message: str
    trigger_type: str  # "inactivity", "intent", "timing", "exit_intent"
    priority: int
    conversion_step: ConversionStep
    suggested_actions: Optional[List[str]] = None


@dataclass
class MicroConversion:
    """A micro-conversion step"""
    step_id: str
    name: str
    message: str
    trigger_conditions: Dict[str, Any]
    success_action: str  # What happens on success
    next_step: Optional[str] = None


class ProactiveSupportEngine:
    """
    Engine for proactive customer engagement
    """
    def __init__(self):
        self.inactivity_threshold = 30  # seconds
        self.max_proactive_messages = 2  # Per session
        self.conversion_funnel = {}

    def check_inactivity(self, session_id: str, last_message_time: float,
                        lead_score: int, conversation_depth: int) -> Optional[ProactiveMessage]:
        """
        Check if should send proactive message based on inactivity

        Args:
            session_id: Unique session identifier
            last_message_time: Timestamp of last message
            lead_score: Current lead score
            conversation_depth: Number of messages exchanged

        Returns:
            ProactiveMessage if should send, None otherwise
        """
        inactive_seconds = time.time() - last_message_time

        # Don't be too proactive early in conversation
        if conversation_depth < 2 and inactive_seconds < 45:
            return None

        # Inactivity-based triggers
        if inactive_seconds >= 30:
            return self._get_inactivity_message(lead_score, conversation_depth)

        return None

    def _get_inactivity_message(self, lead_score: int, depth: int) -> Optional[ProactiveMessage]:
        """Get appropriate proactive message based on context"""
        if lead_score >= 4:
            return ProactiveMessage(
                message="Ser att du är intresserad! Vill du boka ett kort möte så jag kan visa exakt hur det skulle fungera för er?",
                trigger_type="inactivity",
                priority=1,
                conversion_step=ConversionStep.READY,
                suggested_actions=["Ja, boka möte", "Nej tack, fortsätt chatta"]
            )

        if depth >= 4:
            return ProactiveMessage(
                message="Jag finns här om du behöver mer information. Vad är viktigast för dig just nu?",
                trigger_type="inactivity",
                priority=2,
                conversion_step=ConversionStep.CONSIDERING,
                suggested_actions=["Pris", "Funktioner", "Implementation"]
            )

        if depth >= 2:
            return ProactiveMessage(
                message="Behöver du hjälp med något specifikt? Jag kan svara på frågor om pris, funktioner eller hur det fungerar.",
                trigger_type="inactivity",
                priority=3,
                conversion_step=ConversionStep.ENGAGED,
                suggested_actions=["Hur fungerar det?", "Priser", "Funktioner"]
            )

        return None

    def should_offer_help(self, session_data: Dict[str, Any]) -> Optional[ProactiveMessage]:
        """
        Determine if should offer proactive help based on session state

        Args:
            session_data: Session data including messages, intent history, etc.

        Returns:
            ProactiveMessage if should offer help
        """
        # Check for confused user (same question asked twice)
        messages = session_data.get("messages", [])
        user_messages = [m["content"].lower() for m in messages if m["role"] == "user"]

        if len(user_messages) >= 3:
            # Check for similar messages
            recent = user_messages[-3:]
            if len(set(recent)) <= 1:  # Same message repeated
                return ProactiveMessage(
                    message="Jag förstår att du vill ha hjälp med detta. Låt mig förtydliga eller så kopplar jag dig till en kollega.",
                    trigger_type="confusion",
                    priority=1,
                    conversion_step=ConversionStep.ENGAGED
                )

        # Check for pricing exploration (multiple pricing questions)
        pricing_count = sum(1 for m in user_messages if "pris" in m or "price" in m or "kostar" in m)
        if pricing_count >= 2:
            return ProactiveMessage(
                message="Du har ställt några frågor om prissättning. Vill du att jag skickar en prislista eller boka ett möte för att gå igenom vad som passar er bäst?",
                trigger_type="pricing_exploration",
                priority=1,
                conversion_step=ConversionStep.INTERESTED,
                suggested_actions=["Skicka prislista", "Boka möte", "Fortsätt chatta"]
            )

        return None


class MicroConversionEngine:
    """
    Engine for micro-conversions - small steps that lead to conversion
    """
    def __init__(self):
        self.funnel = {
            ConversionStep.AWARENESS: [
                MicroConversion(
                    step_id="welcome_offer",
                    name="Välkomnerbjudande",
                    message="Hej! Jag hjälper dig gärna att hitta rätt lösning. Vad letar du efter?",
                    trigger_conditions={"first_visit": True},
                    success_action="show_categories",
                    next_step="ENGAGED"
                )
            ],
            ConversionStep.ENGAGED: [
                MicroConversion(
                    step_id="category_selection",
                    name="Kategorival",
                    message="Vilket område är mest intressant för dig?",
                    trigger_conditions={"messages": 2},
                    success_action="record_interest",
                    next_step="INTERESTED"
                )
            ],
            ConversionStep.INTERESTED: [
                MicroConversion(
                    step_id="value_proposition",
                    name="Värdeerbjudande",
                    message="Baserat på ditt intresse skulle jag rekommendera att vi tar ett kort samtal om hur detta kan hjälpa just er.",
                    trigger_conditions={"intent": ["pricing_question", "how_it_works"]},
                    success_action="soft_cta",
                    next_step="CONSIDERING"
                )
            ],
            ConversionStep.CONSIDERING: [
                MicroConversion(
                    step_id="social_proof",
                    name="Sociala bevis",
                    message="Företag i din bransch ser ofta 40% bättre effekt med vår lösning. Vill du se några case?",
                    trigger_conditions={"lead_score": 3},
                    success_action="show_case_study",
                    next_step="READY"
                )
            ],
            ConversionStep.READY: [
                MicroConversion(
                    step_id="booking_soft",
                    name="Mjuk boknings-CTA",
                    message="Ett 15-minuters samtal brukar räcka för att se om vi är en bra match. När passar dig?",
                    trigger_conditions={"lead_score": 4},
                    success_action="show_calendar",
                    next_step="CONVERTING"
                )
            ]
        }

    def get_next_step(self, current_step: ConversionStep,
                     session_data: Dict[str, Any]) -> Optional[MicroConversion]:
        """
        Get the next micro-conversion step

        Args:
            current_step: Current conversion step
            session_data: Session data for trigger evaluation

        Returns:
            Next MicroConversion if applicable
        """
        steps = self.funnel.get(current_step, [])

        for step in steps:
            if self._check_triggers(step.trigger_conditions, session_data):
                return step

        # If no specific step matches, try to advance
        if current_step != ConversionStep.CONVERTING:
            next_steps = self.funnel.get(current_step, [])
            if next_steps:
                return next_steps[0]

        return None

    def _check_triggers(self, conditions: Dict[str, Any], session_data: Dict[str, Any]) -> bool:
        """Check if trigger conditions are met"""
        for key, value in conditions.items():
            if key == "first_visit":
                if value and session_data.get("message_count", 0) <= 1:
                    return True
            elif key == "messages":
                if session_data.get("message_count", 0) >= value:
                    return True
            elif key == "intent":
                current_intent = session_data.get("current_intent")
                if current_intent in value:
                    return True
            elif key == "lead_score":
                if session_data.get("lead_score", 0) >= value:
                    return True

        return False

    def get_conversion_cta(self, lead_score: int, sentiment: str) -> str:
        """
        Get appropriate CTA based on lead score and sentiment

        Args:
            lead_score: Current lead score (1-5)
            sentiment: Current sentiment

        Returns:
            Appropriate call-to-action message
        """
        if sentiment == "angry":
            return "Jag förstår att du är frustrerad. Låt mig koppla dig till en människa som kan hjälpa dig direkt."

        if lead_score >= 5:
            return "Perfekt! Du verkar veta vad du letar efter. Boka ett möte så sätter vi igång direkt."

        if lead_score >= 4:
            return " låter som att detta skulle passa er bra. Vill du boka ett kort introduktionsmöte?"

        if lead_score >= 3:
            return "Jag kan berätta mer om hur detta skulle fungera för er. Vill du att jag skickar mer information?"

        return "Om du har några frågor är det bara att fråga. Jag hjälper dig gärna!"

    def get_suggested_actions(self, lead_score: int, intent: str) -> List[str]:
        """
        Get suggested quick-reply buttons based on context

        Args:
            lead_score: Current lead score
            intent: Current intent

        Returns:
            List of suggested action labels
        """
        if intent == "pricing_question":
            return [
                "Se priser",
                "Boka möte",
                "Jämför paket"
            ]

        if intent == "how_it_works":
            return [
                "Hur fungerar det?",
                "Se demo",
                "Implementation"
            ]

        if lead_score >= 4:
            return [
                "Boka möte",
                "Se priser",
                "Kontakta mig"
            ]

        if lead_score >= 2:
            return [
                "Mer information",
                "Kostnad",
                "Funktioner"
            ]

        return [
            "Hur fungerar det?",
            "Priser",
            "Kontakta support"
        ]


if __name__ == "__main__":
    # Test proactive support
    print("=" * 60)
    print("PROACTIVE SUPPORT & MICRO-CONVERSIONS - TEST")
    print("=" * 60)

    proactive = ProactiveSupportEngine()
    micro_conv = MicroConversionEngine()

    # Test 1: Inactivity trigger
    print("\n--- Test 1: Inactivity Trigger ---")
    result = proactive.check_inactivity(
        "session_123",
        time.time() - 35,  # 35 seconds inactive
        lead_score=4,
        conversation_depth=5
    )
    if result:
        print(f"Message: {result.message}")
        print(f"Step: {result.conversion_step.value}")

    # Test 2: Micro-conversion funnel
    print("\n--- Test 2: Micro-Conversion Funnel ---")
    session_data = {
        "message_count": 3,
        "current_intent": "pricing_question",
        "lead_score": 3
    }
    step = micro_conv.get_next_step(ConversionStep.INTERESTED, session_data)
    if step:
        print(f"Step: {step.name}")
        print(f"Message: {step.message}")

    # Test 3: CTA generation
    print("\n--- Test 3: CTA Generation ---")
    for score in range(1, 6):
        cta = micro_conv.get_conversion_cta(score, "neutral")
        print(f"Lead score {score}: {cta}")

    # Test 4: Suggested actions
    print("\n--- Test 4: Suggested Actions ---")
    actions = micro_conv.get_suggested_actions(4, "pricing_question")
    print(f"Actions: {actions}")
