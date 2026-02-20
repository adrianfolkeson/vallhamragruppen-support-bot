"""
SUPPORT STARTER AI - FAULT REPORT SYSTEM
=========================================
Handle fault reports with urgency detection and auto-escalation
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re
import os


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
    NOISE = "noise"  # Buller, störningar från grannar
    OTHER = "other"


@dataclass
class FaultReport:
    """Fault report data structure"""
    report_id: str
    session_id: str
    category: FaultCategory
    urgency: UrgencyLevel
    description: str
    location: str = ""
    reporter_name: Optional[str] = None
    reporter_email: Optional[str] = None
    reporter_phone: Optional[str] = None
    property_id: Optional[str] = None
    photos: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "collecting"  # collecting, complete, sent

    def is_complete(self) -> bool:
        """Check if all required info is collected"""
        return bool(
            self.description and
            self.location and
            (self.reporter_email or self.reporter_phone)
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/email"""
        return {
            "report_id": self.report_id,
            "session_id": self.session_id,
            "category": self.category.value if isinstance(self.category, FaultCategory) else self.category,
            "urgency": self.urgency.value if isinstance(self.urgency, UrgencyLevel) else self.urgency,
            "description": self.description,
            "location": self.location,
            "reporter_name": self.reporter_name or "Ej angivet",
            "reporter_email": self.reporter_email or "Ej angivet",
            "reporter_phone": self.reporter_phone or "Ej angivet",
            "timestamp": self.timestamp,
            "status": self.status
        }


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

        # Store in-progress reports by session
        self.pending_reports: Dict[str, FaultReport] = {}

        # Email configuration (from environment)
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_pass = os.getenv("SMTP_PASS", "")
        self.admin_email = os.getenv("ADMIN_EMAIL", self.config.contact_email)

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
            "fault_noise_medium": format_response(getattr(self.config, 'fault_noise_medium',
                "Störningar! 👂 Det är tråkigt att du blir störd. Jag noterar detta och vidarebefordrar till fastighetsförvaltaren.")),
            "fault_general_medium": format_response(self.config.fault_general_medium),
            "fault_general_low": format_response(self.config.fault_general_low),
            "info_collected": "Tack! Jag har nu all information jag behöver. 📝 Felanmälan är skapad och kommer skickas till fastighetsförvaltaren. Vi återkommer så snart vi kan!",
            "waiting_for_info": "Uppfattat, jag noterar detta. "
        }

        # Category detection patterns
        self.category_patterns = {
            FaultCategory.WATER: [
                r"(vatten|avlopp|diskmaskin|tvättmaskin|kran|toalett|spola|läcker|droppar)",
                r"(water|drain|dishwasher|washing.*?machine|faucet|toilet|leak|drip)"
            ],
            FaultCategory.ELECTRICAL: [
                r"(ström|ljus|lampa|uttag|brytare|säkring|elektrisk|glimra|strömavbrott)",
                r"(power|electric|light|lamp|outlet|switch|fuse|spark|blackout)"
            ],
            FaultCategory.HEATING: [
                r"(element|ventilation|termostat|radiator|kyla.*?inomhus|fryser.*?inomhus|ingen.*värme)",
                r"(heating|radiator|thermostat|freezing.*?inside|no.*?heat)"
            ],
            FaultCategory.SECURITY: [
                r"(utelåst|låst.*ute|nyckel|lås|inbrott|skadegörelse|larm)",
                r"(lock.*?out|locked.*?out|break.?in|burglary|vandalism|alarm)"
            ],
            FaultCategory.STRUCTURAL: [
                r"(tak|vägg|golv|taklucka|spricka|skada|väggbeklädnad)",
                r"(roof|wall|floor|ceiling|crack|damage)"
            ],
            FaultCategory.APPLIANCE: [
                r"(spis|ugn|kylskåp|frys|diskmaskin|tvättmaskin|torktumlare)",
                r"(stove|oven|fridge|dishwasher|washing.*?machine|dryer)"
            ],
            FaultCategory.NOISE: [
                r"(granne|grannar|stör|musik|buller|ljud|hög.*|horn|skrik|bråk|fest|partaj|duns|bank|smäll)",
                r"(neighbor|noise|loud|music|party|shouting|fighting)"
            ]
        }

    def detect_urgency(self, text: str) -> UrgencyLevel:
        """Detect urgency level from text"""
        text_lower = text.lower()

        # CRITICAL - Life safety or property damage
        critical_patterns = [
            r"\b(översvämning|(akut|stort|forsar|strömmar).*vattenläcka|vattenläcka.*(akut|stort|forsar|strömmar)|brustet.*rör|vatten.*(står|forsar))\b",
            r"\b(brinner|brand|gasläcka|gas.*luktar|eld|rök|luktar.*gas)\b",
            r"\b(låst.*ute|utelåst|kommer.*inte.*in|tappat.*nyckel|nyckel.*borta|glömde.*nyckel|låset.*går.*inte)\b",
            r"\b(inbrott|skadegörelse|krossat|försöker.*ta.*sig)\b",
            r"\b(akut|kritiskt|oj|hjälp|nödan|tvingas)\b!+"
        ]

        # HIGH - Important issues affecting comfort/safety
        high_patterns = [
            r"\b(ingen.*varmvatten|inget.*vatten|vatten.*saknas|kranen.*ger.*inget)\b",
            r"\b(ingen.*värme|elementen.*kalla|kyla.*inomhus|fryser.*inomhus|termostat.*inte|värme.*ej)\b",
            r"\b(lås.*gått.*sönder|nyckel.*fast|dörr.*går.*inte.*öppna)\b",
            r"\b(ingen.*ström|strömavbrott|elektricitet.*borta|själva.*fastigheten.*ström)\b"
        ]

        # MEDIUM - Annoying issues
        medium_patterns = [
            r"\b(droppar|läcker|kran|droppande|läcker|lite.*vatten)\b",
            r"\b(låter|buller|konstig.*ljud|problem|fungerar.*dåligt)\b",
            r"\b(granne|grannar|musik|stör|bråk|fest|partaj|skrik|ljud|hög.*|natt)\b",
            r"\b(anmälan|felanmälan|anmäla|reparation|trasig|trasigt|fungerar.*ej|gått.*sönder)\b"
        ]

        for pattern in critical_patterns:
            if re.search(pattern, text_lower):
                return UrgencyLevel.CRITICAL

        for pattern in high_patterns:
            if re.search(pattern, text_lower):
                return UrgencyLevel.HIGH

        for pattern in medium_patterns:
            if re.search(pattern, text_lower):
                return UrgencyLevel.MEDIUM

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

    def get_response_for_urgency(self, urgency: UrgencyLevel, category: FaultCategory) -> str:
        """Get appropriate response based on urgency and category"""
        if urgency == UrgencyLevel.CRITICAL:
            if category == FaultCategory.WATER:
                return self.responses["fault_water_critical"]
            elif category == FaultCategory.SECURITY:
                return self.responses["fault_lockout"]
            else:
                return self.responses["fault_general_critical"]

        elif urgency == UrgencyLevel.HIGH:
            if category == FaultCategory.WATER:
                return self.responses["fault_water_high"]
            elif category == FaultCategory.HEATING:
                return self.responses["fault_heating_high"]
            elif category == FaultCategory.ELECTRICAL:
                return self.responses["fault_electric_high"]
            else:
                return self.responses["fault_general_high"]

        elif urgency == UrgencyLevel.MEDIUM:
            if category == FaultCategory.WATER:
                return self.responses["fault_water_medium"]
            elif category == FaultCategory.APPLIANCE:
                return self.responses["fault_appliance_medium"]
            elif category == FaultCategory.NOISE:
                return self.responses["fault_noise_medium"]
            else:
                return self.responses["fault_general_medium"]

        else:
            return self.responses["fault_general_low"]

    def collect_fault_report(self, message: str, session_data: Dict) -> Dict:
        """
        Collect and process a fault report.
        If there's a pending report for this session, try to update it.
        """
        session_id = session_data.get("session_id", "unknown")

        # Check if there's a pending report for this session
        if session_id in self.pending_reports:
            report = self.pending_reports[session_id]

            # Try to extract info from the message
            extracted = self._extract_info_from_message(message)

            # Update report with extracted info
            if extracted.get("location") and not report.location:
                report.location = extracted["location"]
            if extracted.get("email") and not report.reporter_email:
                report.reporter_email = extracted["email"]
            if extracted.get("phone") and not report.reporter_phone:
                report.reporter_phone = extracted["phone"]
            if extracted.get("name") and not report.reporter_name:
                report.reporter_name = extracted["name"]

            # Also append to description if it looks like additional info
            if message.lower() not in report.description.lower():
                if report.description:
                    report.description += f"\n\nTilläggsinfo: {message}"
                else:
                    report.description = message

            # Check if report is now complete
            if report.is_complete():
                report.status = "complete"
                del self.pending_reports[session_id]

                # Send email and log to sheets
                self._send_report_email(report)
                self._log_to_google_sheets(report)

                return {
                    "report": report,
                    "response": self.responses["info_collected"],
                    "escalate_immediately": self.should_escalate_immediately(report.urgency),
                    "collect_more_info": False,
                    "is_new_report": False,
                    "is_complete": True
                }

            # Still need more info
            questions = self.get_collection_questions(report)
            follow_up = "\n\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))

            return {
                "report": report,
                "response": self.responses["waiting_for_info"] + follow_up,
                "escalate_immediately": False,
                "collect_more_info": True,
                "is_new_report": False,
                "is_complete": False
            }

        # New fault report
        urgency = self.detect_urgency(message)
        category = self.detect_category(message)

        # Get the smart response based on urgency and category
        response = self.get_response_for_urgency(urgency, category)

        # Get reporter info from session if available
        reporter_name = session_data.get("customer_name")
        reporter_email = session_data.get("customer_email")
        reporter_phone = session_data.get("customer_phone")

        # Extract info from message
        extracted = self._extract_info_from_message(message)

        # Create report
        report = FaultReport(
            report_id=f"fault_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            session_id=session_id,
            category=category,
            urgency=urgency,
            description=message,
            location=extracted.get("location", ""),
            reporter_name=reporter_name or extracted.get("name"),
            reporter_email=reporter_email or extracted.get("email"),
            reporter_phone=reporter_phone or extracted.get("phone")
        )

        # Check if complete or needs more info
        if report.is_complete():
            report.status = "complete"
            self._send_report_email(report)
            self._log_to_google_sheets(report)
            return {
                "report": report,
                "response": self.responses["info_collected"],
                "escalate_immediately": self.should_escalate_immediately(urgency),
                "collect_more_info": False,
                "is_new_report": True,
                "is_complete": True
            }

        # Need more info - store as pending
        self.pending_reports[session_id] = report
        questions = self.get_collection_questions(report)
        follow_up = "\n\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))

        return {
            "report": report,
            "response": response + follow_up,
            "escalate_immediately": self.should_escalate_immediately(urgency),
            "collect_more_info": True,
            "is_new_report": True,
            "is_complete": False
        }

    def _extract_info_from_message(self, message: str) -> Dict[str, str]:
        """Extract potential info like email, phone, location from message"""
        result = {}

        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
        if email_match:
            result["email"] = email_match.group()

        # Phone (Swedish formats)
        phone_patterns = [
            r'\b0[0-9]{1,3}[- ]?[0-9]{3}[- ]?[0-9]{2}[- ]?[0-9]{2}\b',
            r'\b0[0-9]{2,3}[- ]?[0-9]{5,7}\b',
            r'\b07[0,2,3,6,9][- ]?[0-9]{3}[- ]?[0-9]{2}[- ]?[0-9]{2}\b'
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, message)
            if match:
                result["phone"] = match.group()
                break

        # Location/apartment number patterns
        location_patterns = [
            r'(?:lägenhetsnummer|lgh|lägenhet)\s*:?\s*([A-Za-z0-9\s]+?)(?:\.|,|\s|$)',
            r'([A-Z][a-z]+(?:sgatan|vägen|gatan))\s*(\d+)',
            r'(?:i|på)\s+(?:lägenhet|lgh)\s*(\d+)',
            r'(?:bor i|adress|ligger)\s+([A-Z][a-z]+(?:sgatan|vägen|gatan))?\s*(\d+)?',
            r'lgh\s*(\d+)',
        ]
        for pattern in location_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                result["location"] = match.group(0).strip()
                break

        return result

    def should_escalate_immediately(self, urgency: UrgencyLevel) -> bool:
        """Determine if fault should be escalated immediately"""
        return urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]

    def get_collection_questions(self, report: FaultReport) -> List[str]:
        """Get questions to ask for complete report"""
        questions = []

        if not report.location:
            questions.append("Vilken adress och lägenhetsnummer gäller det?")

        if not report.reporter_email and not report.reporter_phone:
            questions.append("Vilket telefonnummer eller e-postadress kan vi nå dig på?")

        return questions

    def _send_report_email(self, report: FaultReport) -> bool:
        """Send fault report via email"""
        try:
            if not self.admin_email:
                print(f"No admin email configured, skipping email for report {report.report_id}")
                return False

            # Format email body
            body = f"""
FELANMÄLAN - {report.report_id}

Kategori: {report.category.value.upper()}
Urgens: {report.urgency.value.upper()}

BESKRIVNING:
{report.description}

PLATS:
{report.location or 'Ej angivet'}

ANMÄLARE:
Namn: {report.reporter_name or 'Ej angivet'}
E-post: {report.reporter_email or 'Ej angivet'}
Telefon: {report.reporter_phone or 'Ej angivet'}

Session ID: {report.session_id}
Tid: {report.timestamp}

---
Skickat från Vallhamragruppens AI-kundtjänst
"""
            # Log email content
            print(f"Email for report {report.report_id}:")
            print(f"To: {self.admin_email}")
            print(f"Subject: Felanmälan - {report.category.value.upper()} - {report.urgency.value.upper()}")
            print(f"Body:\n{body}")

            # Try to send email if SMTP is configured
            if self.smtp_host and self.smtp_host != "":
                from email.message import EmailMessage
                import smtplib

                msg = EmailMessage()
                msg["Subject"] = f"Felanmälan - {report.category.value.upper()} - {report.urgency.value.upper()}"
                msg["From"] = self.smtp_user if self.smtp_user else self.admin_email
                msg["To"] = self.admin_email
                msg.set_content(body)

                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    if self.smtp_user and self.smtp_pass:
                        server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(msg)
                print(f"Email sent successfully for report {report.report_id}")
                return True
            else:
                print(f"SMTP not configured, email would be sent to: {self.admin_email}")
                return True

        except Exception as e:
            print(f"Failed to send email for report {report.report_id}: {e}")
            return False

    def _log_to_google_sheets(self, report: FaultReport) -> bool:
        """Log fault report to Google Sheets"""
        try:
            import os

            sheet_id = os.getenv("GOOGLE_SHEET_ID")
            if not sheet_id:
                print(f"No Google Sheet configured, skipping Sheets log for report {report.report_id}")
                return False

            # For now, just log the data that would be sent
            print(f"Would log to Google Sheet '{sheet_id}': {report.to_dict()}")
            return True

        except Exception as e:
            print(f"Failed to log to Google Sheets: {e}")
            return False

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
