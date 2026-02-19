"""
SUPPORT STARTER AI - FAULT REPORT SYSTEM
=========================================
Handle fault reports with urgency detection and auto-escalation
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import re


class UrgencyLevel(Enum):
    """Urgency levels for fault reports"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FaultCategory(Enum):
    """Categories of faults"""
    WATER = "water"  # Vattenläcka, avlopp
    ELECTRICAL = "electrical"  # Elektriska problem
    HEATING = "heating"  # Värme, ventilation
    SECURITY = "security"  # Lås, inbrott
    STRUCTURAL = "structural"  # Byggnadsskador
    APPLIANCE = "appliance"  # Vitvaror, utrustning
    OTHER = "other"


@dataclass
class FaultReport:
    """Fault report data structure"""
    report_id: str
    session_id: str
    category: FaultCategory
    urgency: UrgencyLevel
    description: str
    location: str
    reporter_name: Optional[str] = None
    reporter_email: Optional[str] = None
    reporter_phone: Optional[str] = None
    property_id: Optional[str] = None
    photos: List[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.photos is None:
            self.photos = []


class FaultReportSystem:
    """
    System for collecting and managing fault reports
    """
    def __init__(self, config=None):
        if config:
            self.config = config
        else:
            from config_loader import load_config_or_default
            self.config = load_config_or_default()

        # Helper function to format responses
        def format_response(template):
            return template.format(phone=self.config.phone)

        # Store formatted responses
        self.responses = {
            "fault_water_critical": format_response(self.config.fault_water_critical),
            "fault_lockout": format_response(self.config.fault_lockout),
            "fault_general_critical": format_response(self.config.fault_general_critical),
            "fault_water_high": format_response(self.config.fault_water_high),
            "fault_heating_high": format_response(self.config.fault_heating_high),
            "fault_electric_high": format_response(self.config.fault_electric_high),
            "fault_general_high": format_response(self.config.fault_general_high),
            "fault_water_medium": format_response(self.config.fault_water_medium),
            "fault_appliance_medium": format_response(self.config.fault_appliance_medium),
            "fault_general_medium": format_response(self.config.fault_general_medium),
            "fault_general_low": format_response(self.config.fault_general_low),
        }

        # Urgency detection patterns
        self.urgency_patterns = {
            UrgencyLevel.CRITICAL: [
                r"\b(vattenläcka|översvämning|brinner|eld|brand|gasläcka|strömavbrott|inbrott|skadegörelse)\b",
                r"\b(flood|fire|burst|emergency|immediate|danger)\b",
                r"\b(akut|kritiskt|livsfarligt|oj)\b!+"
            ],
            UrgencyLevel.HIGH: [
                r"\b(ingen värme|inget vatten|kyla|fryser|låser inte fungerar|tappvattnet saknas)\b",
                r"\b(no heating|no water|broken lock|cannot enter)\b",
                r"\b(viktig|rush|hinner inte|fungerar inte alls)\b"
            ],
            UrgencyLevel.MEDIUM: [
                r"\b(läcker|droppar|låter|problem|fel|fungerar dåligt)\b",
                r"\b(leaking|noisy|issue|broken|not working)\b"
            ]
        }

        # Category detection patterns
        self.category_patterns = {
            FaultCategory.WATER: [
                r"\b(vatten|avlopp|diskmaskin|tvättmaskin|kran|toalett|spola|läcker|droppar)\b",
                r"\b(water|drain|dishwasher|washing machine|faucet|toilet|leak|drip)\b"
            ],
            FaultCategory.ELECTRICAL: [
                r"\b(ström|el|ljus|lampa|uttag|brytare|säkring|elektrisk|glimtar)\b",
                r"\b(power|electric|light|lamp|outlet|switch|fuse|spark)\b"
            ],
            FaultCategory.HEATING: [
                r"\b(värme|värme|element|ventilation|kyla|frys|kall|termostat)\b",
                r"\b(heating|radiator|ventilation|cold|freeze|thermostat)\b"
            ],
            FaultCategory.SECURITY: [
                r"\b(lås|nyckel|dörr|fönster|inbrott|larm|säkerhet)\b",
                r"\b(lock|key|door|window|break-in|alarm|security)\b"
            ],
            FaultCategory.STRUCTURAL: [
                r"\b(tak|vägg|golv|fönster|lucka|skada|spricka|läcker|in)\b",
                r"\b(roof|wall|floor|ceiling|damage|crack)\b"
            ],
            FaultCategory.APPLIANCE: [
                r"\b(spis|ugn|kyl|frys|diskmaskin|tvättmaskin|torktumlare)\b",
                r"\b(stove|oven|fridge|dishwasher|washer|dryer)\b"
            ]
        }

        # Required fields for complete report
        self.required_fields = ["description", "location"]

    def detect_urgency(self, text: str) -> UrgencyLevel:
        """
        Detect urgency level from text with smart classification

        CRITICAL: Immediate danger - flood, fire, gas leak, lockout, burst pipe
        HIGH: Important but not dangerous - no water, no heat, broken lock
        MEDIUM: Annoying but manageable - dripping tap, noisy appliance
        LOW: Minor issues - cosmetic damage, general questions
        """
        text_lower = text.lower()

        # CRITICAL - Life safety or property damage
        critical_patterns = [
            # Water disasters
            r"\b(översvämning|vattenläcka.*(akut|stort|forsar|strömmar)|brustet.*rör|vatten.*(står|forsar))\b",
            r"\b(flood|burst.*pipe|water.*everywhere|emergency)\b",
            # Fire/gas
            r"\b(brinner|brand|gasläcka|gas.*luktar|eld|rök|luktar.*gas)\b",
            r"\b(fire|smell.*gas|smoke|burning)\b",
            # Lockout - person locked out is critical
            r"\b(låst.*ute|utelåst|kommer.*inte.*in|tappat.*nyckel|nyckel.*borta|glömde.*nyckel|låset.*går.*inte)\b.*!(?:!|!)",
            r"\b(locked.*out|locked.*out.*my.*key|cannot.*enter|can.*t.*get.*in)\b",
            # Inbrott
            r"\b(inbrott|skadegörelse|krossat|försöker.*ta.*sig)\b",
            r"\b(break[- ]?in|burglary|vandalism)\b",
            # Explicit urgency markers with exclamation
            r"\b(akut|kritiskt|oj|hjälp|nödan|tvingas)\b!+"
        ]

        # HIGH - Important issues affecting comfort/safety but not immediate danger
        high_patterns = [
            # No water or heat
            r"\b(ingen.*varmvatten|inget.*vatten|vatten.*saknas|kranen.*ger.*inget)\b",
            r"\b(no.*water|no.*hot.*water|water.*out)\b",
            r"\b(ingen.*värme|elementen.*kalla|kyla.*inomhus|fryser.*inomhus|termostat.*inte|värme.*ej)\b",
            r"\b(no.*heating|freezing.*inside|radiator.*cold|can.*t.*get.*warm)\b",
            # Security issues (not lockout)
            r"\b(lås.*gått.*sönder|nyckel.*fast|dörr.*går.*inte.*öppna)\b",
            r"\b(broken.*lock|key.*stuck|door.*won.*t.*open)\b",
            # No electricity
            r"\b(ingen.*ström|strömavbrott|elektricitet.*borta|själva.*fastigheten.*ström)\b",
            r"\b(power.*out|no.*electricity|blackout)\b"
        ]

        # MEDIUM - Annoying issues, dripping, minor leaks
        medium_patterns = [
            r"\b(droppar|läcker|kran|droppande|läcker|lite.*vatten)\b",
            r"\b(leaking|dripping|drip|slow.*leak)\b",
            r"\b(låter|buller|konstig.*ljud|problem|fungerar.*dåligt)\b",
            r"\b(noisy|making.*sound|not.*working.*properly)\b"
        ]

        # Check critical first (most specific patterns first)
        for pattern in critical_patterns:
            if re.search(pattern, text_lower):
                return UrgencyLevel.CRITICAL

        # Then high
        for pattern in high_patterns:
            if re.search(pattern, text_lower):
                return UrgencyLevel.HIGH

        # Then medium
        for pattern in medium_patterns:
            if re.search(pattern, text_lower):
                return UrgencyLevel.MEDIUM

        # Default to low
        return UrgencyLevel.LOW

    def detect_category(self, text: str) -> FaultCategory:
        """Detect fault category from text"""
        text_lower = text.lower()

        scores = {}
        for category, patterns in self.category_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    score += 1
            if score > 0:
                scores[category] = score

        if scores:
            return max(scores, key=scores.get)
        return FaultCategory.OTHER

    def should_escalate_immediately(self, urgency: UrgencyLevel) -> bool:
        """Determine if fault should be escalated immediately"""
        return urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]

    def get_response_for_urgency(self, urgency: UrgencyLevel, category: FaultCategory, description: str) -> str:
        """
        Get appropriate response based on urgency and category
        Sounds like experienced property manager - direct, practical, asks right questions
        """
        # CRITICAL - Immediate action needed
        if urgency == UrgencyLevel.CRITICAL:
            if category == FaultCategory.WATER:
                return self.responses["fault_water_critical"]
            elif category == FaultCategory.SECURITY:
                return self.responses["fault_lockout"]
            else:
                return self.responses["fault_general_critical"]

        # HIGH - Important but not emergency
        elif urgency == UrgencyLevel.HIGH:
            if category == FaultCategory.WATER:
                return self.responses["fault_water_high"]
            elif category == FaultCategory.HEATING:
                return self.responses["fault_heating_high"]
            elif category == FaultCategory.ELECTRICAL:
                return self.responses["fault_electric_high"]
            else:
                return self.responses["fault_general_high"]

        # MEDIUM - Needs more info to determine urgency
        elif urgency == UrgencyLevel.MEDIUM:
            if category == FaultCategory.WATER:
                return self.responses["fault_water_medium"]
            elif category == FaultCategory.APPLIANCE:
                return self.responses["fault_appliance_medium"]
            else:
                return self.responses["fault_general_medium"]

        # LOW - General inquiry
        else:
            return self.responses["fault_general_low"]

    def collect_fault_report(self, message: str, session_data: Dict) -> Dict:
        """
        Collect and process a fault report

        Returns:
            Dict with report data and response
        """
        urgency = self.detect_urgency(message)
        category = self.detect_category(message)

        # Get the smart response based on urgency and category
        response = self.get_response_for_urgency(urgency, category, message)

        # Get reporter info from session if available
        reporter_name = session_data.get("customer_name")
        reporter_email = session_data.get("customer_email")
        reporter_phone = session_data.get("customer_phone")

        # Create report
        report = FaultReport(
            report_id=f"fault_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            session_id=session_data.get("session_id", "unknown"),
            category=category,
            urgency=urgency,
            description=message,
            location="",  # Will be collected if needed
            reporter_name=reporter_name,
            reporter_email=reporter_email,
            reporter_phone=reporter_phone
        )

        return {
            "report": report,
            "response": response,
            "escalate_immediately": self.should_escalate_immediately(urgency),
            "collect_more_info": self._needs_more_info(report)
        }

    def _needs_more_info(self, report: FaultReport) -> bool:
        """Check if we need to collect more information"""
        return (
            not report.location or
            not report.reporter_email or
            report.urgency in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]
        )

    def get_collection_questions(self, report: FaultReport) -> List[str]:
        """Get questions to ask for complete report"""
        questions = []

        if not report.location:
            questions.append("Vart finns problemet? (Adress, lägenhetsnummer, plats i fastigheten)")

        if not report.reporter_email:
            questions.append("Vilken e-postadress kan vi nå dig på?")

        if report.urgency in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]:
            if not report.reporter_phone:
                questions.append("Vilket telefonnummer kan vi nå dig på för akuta ärenden?")

        return questions

    def format_escalation_message(self, report: FaultReport) -> str:
        """Format fault report for escalation notification"""
        return f"""
AKUT FELANMÄLAN - {report.urgency.value.upper()}

Kategori: {report.category.value}
Beskrivning: {report.description}

Anmälare: {report.reporter_name or 'Ej angivet'}
Email: {report.reporter_email or 'Ej angivet'}
Telefon: {report.reporter_phone or 'Ej angivet'}

Plats: {report.location or 'Ej angivet'}

Tid: {report.timestamp}
        """.strip()


# Singleton instance
_fault_system: Optional[FaultReportSystem] = None


def get_fault_system() -> FaultReportSystem:
    """Get fault report system instance"""
    global _fault_system
    if _fault_system is None:
        _fault_system = FaultReportSystem()
    return _fault_system


if __name__ == "__main__":
    # Test the fault report system
    print("=" * 60)
    print("FAULT REPORT SYSTEM - TEST")
    print("=" * 60)

    system = FaultReportSystem()

    test_reports = [
        "Akut! Vattenläcka i köket, det forsar vatten överallt!",
        "Det är kallt i lägenheten, elementen fungerar inte.",
        "Diskmaskinen läcker lite vatten.",
        "Nyckeln går inte in i dörren, jag är låst ute!",
        "Det glimmar i lampan i hallen."
    ]

    for report_text in test_reports:
        print(f"\n{'-' * 40}")
        print(f"Report: {report_text}")

        result = system.collect_fault_report(
            report_text,
            {"session_id": "test_123"}
        )

        print(f"Urgency: {result['report'].urgency.value.upper()}")
        print(f"Category: {result['report'].category.value}")
        print(f"Escalate: {result['escalate_immediately']}")
        print(f"Response: {result['response']}")

        if result['collect_more_info']:
            questions = system.get_collection_questions(result['report'])
            print(f"Need info: {questions}")
