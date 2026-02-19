"""
SUPPORT STARTER AI - INTELLIGENT ROUTER
=======================================
Intent Classifier + Confidence Engine + Sentiment + Lead Scoring
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import re
import json


class IntentType(Enum):
    """Supported intent types"""
    PRICING_QUESTION = "pricing_question"
    HOW_IT_WORKS = "how_it_works"
    BOOKING_REQUEST = "booking_request"
    TECHNICAL_ISSUE = "technical_issue"
    REFUND_REQUEST = "refund_request"
    COMPLAINT = "complaint"
    FEATURE_REQUEST = "feature_request"
    INTEGRATION_QUESTION = "integration_question"
    GENERAL_INQUIRY = "general_inquiry"
    ESCALATION_DEMAND = "escalation_demand"
    LEGAL_THREAT = "legal_threat"
    UNKNOWN = "unknown"


class SentimentType(Enum):
    """Sentiment categories"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    SLIGHTLY_NEGATIVE = "slightly_negative"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"


@dataclass
class IntentResult:
    """Result from intent classification"""
    intent: IntentType
    confidence: float  # 0.0 to 1.0
    sentiment: SentimentType
    lead_score: int  # 1 to 5
    trigger_phrases: list[str]
    metadata: Dict[str, Any]


class IntelligentRouter:
    """
    Intelligent Intent Router with Confidence Engine
    """
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.sentiment_patterns = self._load_sentiment_patterns()
        self.lead_triggers = self._load_lead_triggers()

    def _load_intent_patterns(self) -> Dict[IntentType, list[dict]]:
        """Load pattern matching rules for each intent"""
        return {
            IntentType.PRICING_QUESTION: [
                {"patterns": [r"\bpris\b", r"\bpris(er|ning)?\b", r"\bkostar\b", r"\bhow much\b", r"\bpricing\b", r"\bprice\b", r"\bkostnad\b"], "weight": 1.0},
            ],
            IntentType.HOW_IT_WORKS: [
                {"patterns": [r"\bfungerar\b", r"\bfungerar det\b", r"\bhow does it work\b", r"\bhow do (i|you)\b", r"\bvad (gör|kan)\b"], "weight": 1.0},
            ],
            IntentType.BOOKING_REQUEST: [
                {"patterns": [r"\bboka\b", r"\bmöte\b", r"\bmeeting\b", r"\bcall\b", r"\bbok(a|ning)\b", r"\bschedule\b", r"\bdemo\b"], "weight": 1.0},
            ],
            IntentType.TECHNICAL_ISSUE: [
                {"patterns": [r"\bfungerar inte\b", r"\bbugg\b", r"\berror\b", r"\bcannot\b", r"\bdoesn'?t work\b", r"\bproblem\b", r"\bissue\b", r"\bcrash\b"], "weight": 1.0},
            ],
            IntentType.REFUND_REQUEST: [
                {"patterns": [r"\brefund\b", r"\bpengar tillbaka\b", r"\båterbetala\b", r"\bcancel\b", r"\bavsluta\b"], "weight": 1.0},
            ],
            IntentType.COMPLAINT: [
                {"patterns": [r"\bdålig\b", r"\bdåligt\b", r"\bhatar\b", r"\bful\b", r"\bterrible\b", r"\bhorrible\b", r"\bdisappointed\b"], "weight": 1.0},
            ],
            IntentType.FEATURE_REQUEST: [
                {"patterns": [r"\bkan ni\b", r"\bwould be nice\b", r"\bwish\b", r"\bfeature\b", r"\bfungera.*(?:som|like)\b"], "weight": 1.0},
            ],
            IntentType.INTEGRATION_QUESTION: [
                {"patterns": [r"\bintegrera\b", r"\bintegration\b", r"\bconnect\b", r"\bwork with\b", r"\bkoppla\b"], "weight": 1.0},
            ],
            IntentType.ESCALATION_DEMAND: [
                {"patterns": [r"\bschef\b", r"\bmanager\b", r"\btalk to\b", r"\bspeak to\b", r"\bboss\b", r"\bhuman\b"], "weight": 1.0},
            ],
            IntentType.LEGAL_THREAT: [
                {"patterns": [r"\blagar\b", r"\blagen\b", r"\blawyer\b", r"\blagf\b", r"\bkontakt(ar|era|)?\b.*konsumentverket\b", r"\barn\b"], "weight": 1.0},
            ],
        }

    def _load_sentiment_patterns(self) -> Dict[SentimentType, list[str]]:
        """Load sentiment detection patterns"""
        return {
            SentimentType.ANGRY: [
                r"\bidiots?\b", r"\bstupid\b", r"\buseless\b", r"\bwaste\b", r"\bnever.*again\b",
                r"\bful(b|t|a)\b", r"\bhorribel\b", r"\bvidrig\b", r"\bskäms\b"
            ],
            SentimentType.FRUSTRATED: [
                r"\bimpossible\b", r"\bcan't\b", r"\bcannot\b", r"\bwhy\b", r"\bhow many times\b",
                r"\bäntligen\b", r"\binte fungerar\b", r"\bkaos\b"
            ],
            SentimentType.POSITIVE: [
                r"\bgreat\b", r"\bamazing\b", r"\bawesome\b", r"\btack\b", r"\btacksam\b",
                r"\bperfect\b", r"\blove\b", r"\bhelpful\b", r"\bbra\b", r"\butmärkt\b"
            ],
        }

    def _load_lead_triggers(self) -> Dict[int, list[str]]:
        """Load lead scoring trigger phrases"""
        return {
            1: [
                r"\bhow does it work\b", r"\bvad.*kostar\b", r"\bpricing\b",
                r"\binformation\b"
            ],
            2: [
                r"\bimplement(era|ation)\b", r"\bsetup\b", r"\bkomma igång\b"
            ],
            3: [
                r"\bwe (are|need)\b", r"\bvi (behöver|söker)\b", r"\blooking for\b",
                r"\bintegrate\b", r"\bintegration\b"
            ],
            4: [
                r"\bboka\b", r"\bschedule\b", r"\bcallback\b", r"\bkontakta\b",
                r"\bdemo\b", r"\boffert\b"
            ],
            5: [
                r"\bbuy\b", r"\bköp(a)?\b", r"\bready to\b", r"\bsign up\b",
                r"\bstart(a)?\b nu\b", r"\bsubscribe\b"
            ]
        }

    def classify(self, message: str, conversation_history: Optional[list] = None) -> IntentResult:
        """
        Classify user message and return structured result

        Args:
            message: User input message
            conversation_history: Optional list of previous messages for context

        Returns:
            IntentResult with classification data
        """
        message_lower = message.lower()

        # 1. Detect Intent
        intent, confidence, trigger_phrases = self._detect_intent(message_lower)

        # 2. Detect Sentiment
        sentiment = self._detect_sentiment(message_lower)

        # 3. Calculate Lead Score
        lead_score = self._calculate_lead_score(message_lower, conversation_history)

        # 4. Build metadata
        metadata = self._build_metadata(message, conversation_history, intent, sentiment, lead_score)

        return IntentResult(
            intent=intent,
            confidence=confidence,
            sentiment=sentiment,
            lead_score=lead_score,
            trigger_phrases=trigger_phrases,
            metadata=metadata
        )

    def _detect_intent(self, message: str) -> tuple[IntentType, float, list[str]]:
        """Detect primary intent from message"""
        scores = {}
        matched_phrases = []

        for intent_type, pattern_groups in self.intent_patterns.items():
            score = 0.0
            intent_matches = []

            for group in pattern_groups:
                for pattern in group["patterns"]:
                    if re.search(pattern, message, re.IGNORECASE):
                        score += group["weight"]
                        intent_matches.append(pattern)

            if score > 0:
                scores[intent_type] = score
                matched_phrases.extend(intent_matches)

        if not scores:
            return IntentType.GENERAL_INQUIRY, 0.3, []

        # Get highest scoring intent
        best_intent = max(scores, key=scores.get)
        raw_score = scores[best_intent]

        # Normalize confidence to 0-1
        confidence = min(raw_score / 2.0, 1.0)

        return best_intent, confidence, matched_phrases

    def _detect_sentiment(self, message: str) -> SentimentType:
        """Detect sentiment from message"""
        # Check for angry indicators first
        if any(re.search(p, message, re.IGNORECASE) for p in self.sentiment_patterns[SentimentType.ANGRY]):
            return SentimentType.ANGRY

        # Check for frustrated indicators
        if any(re.search(p, message, re.IGNORECASE) for p in self.sentiment_patterns[SentimentType.FRUSTRATED]):
            return SentimentType.FRUSTRATED

        # Check for positive indicators
        if any(re.search(p, message, re.IGNORECASE) for p in self.sentiment_patterns[SentimentType.POSITIVE]):
            return SentimentType.POSITIVE

        # Check for slightly negative
        negative_words = [r"\bnot\b", r"\bdoesn'?t\b", r"\bwon'?t\b", r"\bnej\b", r"\binte\b"]
        if any(re.search(p, message, re.IGNORECASE) for p in negative_words):
            return SentimentType.SLIGHTLY_NEGATIVE

        return SentimentType.NEUTRAL

    def _calculate_lead_score(self, message: str, history: Optional[list]) -> int:
        """Calculate lead score from 1-5"""
        score = 0

        # Check message against trigger patterns
        for level, patterns in self.lead_triggers.items():
            if any(re.search(p, message, re.IGNORECASE) for p in patterns):
                score = max(score, level)

        # Boost score based on conversation history
        if history:
            # Multiple pricing questions = higher intent
            pricing_mentions = sum(1 for m in history[-5:] if re.search(r"\bpris\b|\bprice\b|\bpricing\b", m.lower()))
            if pricing_mentions >= 2:
                score = max(score, 3)

            # Previous booking intent
            if any(re.search(r"\bboka\b|\bbook\b", m.lower()) for m in history[-3:]):
                score = max(score, 4)

        # Check for company context
        company_indicators = [r"\bwe are\b", r"\bvi är\b", r"\bour company\b", r"\bföretag\b"]
        if any(re.search(p, message, re.IGNORECASE) for p in company_indicators):
            score = max(score, 3)

        return min(score, 5)

    def _build_metadata(self, message: str, history: Optional[list],
                       intent: IntentType, sentiment: SentimentType, lead_score: int) -> Dict[str, Any]:
        """Build metadata for the classification"""
        metadata = {
            "message_length": len(message),
            "has_urgent_indicators": bool(re.search(r"\burgent\b|\bbråttom\b|\basap\b", message, re.IGNORECASE)),
            "has_question": bool(re.search(r"\?", message)),
            "conversation_turns": len(history) if history else 0,
            "should_escalate": self._should_escalate(intent, sentiment, lead_score),
            "conversion_ready": lead_score >= 4 and sentiment != SentimentType.ANGRY,
        }

        return metadata

    def _should_escalate(self, intent: IntentType, sentiment: SentimentType, lead_score: int) -> bool:
        """Determine if conversation should be escalated"""
        return (
            intent in [IntentType.LEGAL_THREAT, IntentType.ESCALATION_DEMAND] or
            sentiment in [SentimentType.ANGRY] or
            (sentiment == SentimentType.FRUSTRATED and lead_score <= 2)
        )


# Standalone function for easy use
def classify_message(message: str, conversation_history: Optional[list] = None) -> Dict[str, Any]:
    """
    Quick function to classify a message and return dict result

    Args:
        message: User input message
        conversation_history: Optional list of previous messages

    Returns:
        Dictionary with classification results
    """
    router = IntelligentRouter()
    result = router.classify(message, conversation_history)

    return {
        "intent": result.intent.value,
        "confidence": result.confidence,
        "sentiment": result.sentiment.value,
        "lead_score": result.lead_score,
        "trigger_phrases": result.trigger_phrases,
        "metadata": result.metadata
    }


if __name__ == "__main__":
    # Test examples
    test_messages = [
        "Vad kostar er tjänst?",
        "Hur fungerar det?",
        "Boka ett möte med mig",
        "Det här fungerar inte alls!",
        "Vi letar efter en lösning för vårt företag",
        "Jag vill ha pengarna tillbaka!",
        "Kan ni integrera med vårt CRM?",
    ]

    print("=" * 60)
    print("INTELLIGENT ROUTER - TEST RESULTS")
    print("=" * 60)

    for msg in test_messages:
        result = classify_message(msg)
        print(f"\nMessage: {msg}")
        print(f"  Intent: {result['intent']} (confidence: {result['confidence']:.2f})")
        print(f"  Sentiment: {result['sentiment']}")
        print(f"  Lead Score: {result['lead_score']}/5")
        print(f"  Escalate: {result['metadata']['should_escalate']}")
