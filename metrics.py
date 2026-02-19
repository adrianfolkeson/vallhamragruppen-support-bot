"""
SUPPORT STARTER AI - METRICS ENGINE
===================================
Track, analyze, and report on all conversation metrics
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import json


class MetricType(Enum):
    """Types of metrics to track"""
    INTENT_DISTRIBUTION = "intent_distribution"
    ESCALATION_RATE = "escalation_rate"
    CONVERSION_RATE = "conversion_rate"
    AVG_RESOLUTION_TIME = "avg_resolution_time"
    AVG_LEAD_SCORE = "avg_lead_score"
    SENTIMENT_DISTRIBUTION = "sentiment_distribution"
    TOP_QUESTIONS = "top_questions"
    CONVERSION_TRIGGERS = "conversion_triggers"
    RESPONSE_TIME = "response_time"
    SATISFACTION_SCORE = "satisfaction_score"


@dataclass
class ConversationMetric:
    """Single conversation metric"""
    conversation_id: str
    started_at: str
    ended_at: Optional[str]
    duration_seconds: Optional[int]

    # Message counts
    total_messages: int
    user_messages: int
    bot_messages: int

    # Classification data
    intents: List[str]
    sentiments: List[str]
    lead_scores: List[int]

    # Outcomes
    escalated: bool
    escalated_reason: Optional[str]
    converted: bool
    conversion_action: Optional[str]
    resolved: bool

    # Quality
    satisfaction: Optional[int] = None  # 1-5 if collected

    # Metadata
    customer_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class AggregateMetrics:
    """Aggregated metrics for a time period"""
    period_start: str
    period_end: str
    total_conversations: int

    # Key metrics
    escalation_rate: float
    conversion_rate: float
    resolution_rate: float
    avg_resolution_time_seconds: float
    avg_lead_score: float
    avg_satisfaction: Optional[float]

    # Distributions
    intent_distribution: Dict[str, int]
    sentiment_distribution: Dict[str, int]

    # Top questions
    top_questions: List[tuple[str, int]]

    # Conversion triggers
    conversion_triggers: List[tuple[str, int]]

    # Response time metrics
    avg_response_time_ms: float
    p95_response_time_ms: float


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time"""
    timestamp: str
    active_conversations: int
    messages_last_hour: int
    escalations_today: int
    conversions_today: int
    avg_lead_score_today: float


class MetricsEngine:
    """
    Engine for tracking and analyzing conversation metrics
    """
    def __init__(self):
        self.conversations: Dict[str, ConversationMetric] = {}
        self.intent_counts: defaultdict = defaultdict(int)
        self.sentiment_counts: defaultdict = defaultdict(int)
        self.question_counts: defaultdict = defaultdict(int)
        self.conversion_triggers: defaultdict = defaultdict(int)
        self.response_times: List[float] = []

        # Hourly metrics
        self.hourly_metrics: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"conversations": 0, "escalations": 0, "conversions": 0}
        )

    def track_conversation_start(self, conversation_id: str,
                                 customer_id: Optional[str] = None,
                                 session_id: Optional[str] = None) -> None:
        """Track the start of a conversation"""
        self.conversations[conversation_id] = ConversationMetric(
            conversation_id=conversation_id,
            started_at=datetime.utcnow().isoformat(),
            ended_at=None,
            duration_seconds=None,
            total_messages=0,
            user_messages=0,
            bot_messages=0,
            intents=[],
            sentiments=[],
            lead_scores=[],
            escalated=False,
            escalated_reason=None,
            converted=False,
            conversion_action=None,
            resolved=False,
            customer_id=customer_id,
            session_id=session_id
        )

    def track_message(self, conversation_id: str, role: str,
                     intent: Optional[str] = None,
                     sentiment: Optional[str] = None,
                     lead_score: Optional[int] = None,
                     response_time_ms: Optional[float] = None) -> None:
        """Track a message in a conversation"""
        if conversation_id not in self.conversations:
            return

        conv = self.conversations[conversation_id]
        conv.total_messages += 1

        if role == "user":
            conv.user_messages += 1
        elif role == "bot":
            conv.bot_messages += 1

        # Track classification data
        if intent:
            conv.intents.append(intent)
            self.intent_counts[intent] += 1

        if sentiment:
            conv.sentiments.append(sentiment)
            self.sentiment_counts[sentiment] += 1

        if lead_score is not None:
            conv.lead_scores.append(lead_score)

        # Track response time
        if response_time_ms is not None:
            self.response_times.append(response_time_ms)

    def track_question(self, question: str) -> None:
        """Track a question asked by user"""
        # Normalize question for grouping
        normalized = question.lower().strip()
        # Remove some variations
        normalized = normalized.rstrip("?!")
        self.question_counts[normalized] += 1

    def track_escalation(self, conversation_id: str, reason: str) -> None:
        """Track when a conversation is escalated"""
        if conversation_id in self.conversations:
            conv = self.conversations[conversation_id]
            conv.escalated = True
            conv.escalated_reason = reason

            # Update hourly metrics
            hour_key = datetime.utcnow().strftime("%Y-%m-%d-%H")
            self.hourly_metrics[hour_key]["escalations"] += 1

    def track_conversion(self, conversation_id: str, action: str,
                        trigger: Optional[str] = None) -> None:
        """Track when a conversion occurs"""
        if conversation_id in self.conversations:
            conv = self.conversations[conversation_id]
            conv.converted = True
            conv.conversion_action = action

            if trigger:
                self.conversion_triggers[trigger] += 1

            # Update hourly metrics
            hour_key = datetime.utcnow().strftime("%Y-%m-%d-%H")
            self.hourly_metrics[hour_key]["conversions"] += 1

    def track_resolution(self, conversation_id: str, resolved: bool = True,
                        satisfaction: Optional[int] = None) -> None:
        """Track when a conversation is resolved"""
        if conversation_id in self.conversations:
            conv = self.conversations[conversation_id]
            conv.resolved = resolved
            conv.satisfaction = satisfaction
            conv.ended_at = datetime.utcnow().isoformat()

            # Calculate duration
            if conv.started_at:
                start = datetime.fromisoformat(conv.started_at)
                end = datetime.fromisoformat(conv.ended_at)
                conv.duration_seconds = int((end - start).total_seconds())

    def get_aggregate_metrics(self, period_start: Optional[datetime] = None,
                              period_end: Optional[datetime] = None) -> AggregateMetrics:
        """
        Get aggregated metrics for a time period

        Args:
            period_start: Start of period (defaults to 24 hours ago)
            period_end: End of period (defaults to now)

        Returns:
            AggregateMetrics with calculated metrics
        """
        if period_start is None:
            period_start = datetime.utcnow() - timedelta(hours=24)
        if period_end is None:
            period_end = datetime.utcnow()

        # Filter conversations in period
        period_convs = []
        for conv in self.conversations.values():
            conv_start = datetime.fromisoformat(conv.started_at)
            if period_start <= conv_start <= period_end:
                period_convs.append(conv)

        total = len(period_convs)
        if total == 0:
            return AggregateMetrics(
                period_start=period_start.isoformat(),
                period_end=period_end.isoformat(),
                total_conversations=0,
                escalation_rate=0.0,
                conversion_rate=0.0,
                resolution_rate=0.0,
                avg_resolution_time_seconds=0.0,
                avg_lead_score=0.0,
                avg_satisfaction=None,
                intent_distribution={},
                sentiment_distribution={},
                top_questions=[],
                conversion_triggers=[],
                avg_response_time_ms=0.0,
                p95_response_time_ms=0.0
            )

        # Calculate metrics
        escalated = sum(1 for c in period_convs if c.escalated)
        converted = sum(1 for c in period_convs if c.converted)
        resolved = sum(1 for c in period_convs if c.resolved)

        # Average lead score
        all_lead_scores = [s for c in period_convs for s in c.lead_scores]
        avg_lead = sum(all_lead_scores) / len(all_lead_scores) if all_lead_scores else 0

        # Average resolution time
        resolved_with_time = [c.duration_seconds for c in period_convs
                             if c.resolved and c.duration_seconds]
        avg_resolution = sum(resolved_with_time) / len(resolved_with_time) if resolved_with_time else 0

        # Satisfaction
        satisfactions = [c.satisfaction for c in period_convs if c.satisfaction]
        avg_sat = sum(satisfactions) / len(satisfactions) if satisfactions else None

        # Intent distribution
        intent_dist = dict(self.intent_counts)

        # Sentiment distribution
        sentiment_dist = dict(self.sentiment_counts)

        # Top questions
        top_questions = sorted(self.question_counts.items(),
                              key=lambda x: x[1], reverse=True)[:10]

        # Conversion triggers
        top_triggers = sorted(self.conversion_triggers.items(),
                             key=lambda x: x[1], reverse=True)[:10]

        # Response times
        avg_response = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        sorted_times = sorted(self.response_times)
        p95_response = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0

        return AggregateMetrics(
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            total_conversations=total,
            escalation_rate=escalated / total,
            conversion_rate=converted / total,
            resolution_rate=resolved / total,
            avg_resolution_time_seconds=avg_resolution,
            avg_lead_score=avg_lead,
            avg_satisfaction=avg_sat,
            intent_distribution=intent_dist,
            sentiment_distribution=sentiment_dist,
            top_questions=top_questions,
            conversion_triggers=top_triggers,
            avg_response_time_ms=avg_response,
            p95_response_time_ms=p95_response
        )

    def get_snapshot(self) -> MetricSnapshot:
        """Get current metrics snapshot"""
        now = datetime.utcnow()

        # Active conversations (started but not ended in last hour)
        active = sum(1 for c in self.conversations.values()
                    if c.ended_at is None or
                    (datetime.fromisoformat(c.ended_at) > now - timedelta(hours=1)))

        # Messages in last hour
        hour_key = now.strftime("%Y-%m-%d-%H")
        messages_last_hour = sum(
            c.total_messages for c in self.conversations.values()
            if datetime.fromisoformat(c.started_at) > now - timedelta(hours=1)
        )

        # Today's escalations and conversions
        today_key = now.strftime("%Y-%m-%d")
        escalations = sum(
            v["escalations"] for k, v in self.hourly_metrics.items()
            if k.startswith(today_key)
        )
        conversions = sum(
            v["conversions"] for k, v in self.hourly_metrics.items()
            if k.startswith(today_key)
        )

        # Today's average lead score
        today_convs = [c for c in self.conversations.values()
                      if datetime.fromisoformat(c.started_id).strftime("%Y-%m-%d") == today_key]
        all_scores = [s for c in today_convs for s in c.lead_scores]
        avg_lead = sum(all_scores) / len(all_scores) if all_scores else 0

        return MetricSnapshot(
            timestamp=now.isoformat(),
            active_conversations=active,
            messages_last_hour=messages_last_hour,
            escalations_today=escalations,
            conversions_today=conversions,
            avg_lead_score_today=avg_lead
        )

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive metrics report"""
        metrics = self.get_aggregate_metrics()

        return {
            "summary": {
                "total_conversations": metrics.total_conversations,
                "escalation_rate": f"{metrics.escalation_rate:.1%}",
                "conversion_rate": f"{metrics.conversion_rate:.1%}",
                "resolution_rate": f"{metrics.resolution_rate:.1%}",
            },
            "performance": {
                "avg_resolution_time": f"{metrics.avg_resolution_time_seconds:.0f}s",
                "avg_response_time": f"{metrics.avg_response_time_ms:.0f}ms",
                "p95_response_time": f"{metrics.p95_response_time_ms:.0f}ms",
                "avg_lead_score": f"{metrics.avg_lead_score:.1f}/5",
                "avg_satisfaction": f"{metrics.avg_satisfaction:.1f}/5" if metrics.avg_satisfaction else "N/A"
            },
            "insights": {
                "top_intents": dict(list(metrics.intent_distribution.items())[:5]),
                "sentiment_breakdown": metrics.sentiment_distribution,
                "top_questions": [{"question": q, "count": c} for q, c in metrics.top_questions[:5]],
                "conversion_triggers": [{"trigger": t, "count": c} for t, c in metrics.conversion_triggers[:5]]
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    def get_selling_points(self) -> List[str]:
        """
        Generate selling points based on metrics
        This is what you show to potential customers
        """
        metrics = self.get_aggregate_metrics()

        points = []

        # Calculate impressive stats
        if metrics.total_conversations > 100:
            automation_rate = (1 - metrics.escalation_rate) * 100
            points.append(f"✅ {automation_rate:.0f}% av alla ärenden löses automatiskt")

        if metrics.conversion_rate > 0.1:
            points.append(f"✅ {metrics.conversion_rate:.1%} konverteringsgrad från chatt till leads")

        if metrics.avg_resolution_time_seconds < 120:
            points.append(f"✅ Genomsnittlig lösningstid: {metrics.avg_resolution_time_seconds:.0f} sekunder")

        if metrics.avg_response_time_ms < 1000:
            points.append(f"✅ Svarstid under 1 sekund")

        if metrics.avg_satisfaction and metrics.avg_satisfaction >= 4:
            points.append(f"✅ Kundnöjdhet: {metrics.avg_satisfaction:.1f}/5")

        if not points:
            points.append("📊 Samlar in värdefull data för att optimera er support")

        return points


if __name__ == "__main__":
    # Test metrics engine
    print("=" * 60)
    print("METRICS ENGINE - TEST")
    print("=" * 60)

    metrics = MetricsEngine()

    # Simulate some conversations
    for i in range(10):
        conv_id = f"conv_{i}"
        metrics.track_conversation_start(conv_id)

        # Add some messages
        metrics.track_message(conv_id, "user", "pricing_question", "neutral", 3)
        metrics.track_message(conv_id, "bot", response_time_ms=450)
        metrics.track_question("Hur mycket kostar det?")

        if i % 3 == 0:
            metrics.track_conversion(conv_id, "booked_call", "pricing_question")
            metrics.track_resolution(conv_id, True, 5)
        elif i % 2 == 0:
            metrics.track_escalation(conv_id, "technical_issue")
            metrics.track_resolution(conv_id, True)
        else:
            metrics.track_resolution(conv_id, True, 4)

    # Generate report
    print("\n--- Metrics Report ---")
    report = metrics.generate_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))

    print("\n--- Selling Points ---")
    for point in metrics.get_selling_points():
        print(point)
