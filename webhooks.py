"""
SUPPORT STARTER AI - WEBHOOK & NOTIFICATION SYSTEM
===================================================
Send notifications, log conversations, and integrate with external systems
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import requests

from schemas import BotResponse, EscalationPacket, LeadData


class NotificationType(Enum):
    """Types of notifications"""
    NEW_CONVERSATION = "new_conversation"
    ESCALATION = "escalation"
    HIGH_LEAD = "high_lead"
    CONVERSION = "conversion"
    DAILY_SUMMARY = "daily_summary"
    ERROR = "error"


class WebhookDestination(Enum):
    """Webhook destination types"""
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"
    DISCORD_WEBHOOK = "discord_webhook"
    HTTP_ENDPOINT = "http_endpoint"


@dataclass
class WebhookConfig:
    """Configuration for a webhook destination"""
    destination_type: WebhookDestination
    enabled: bool = True

    # Email settings
    email_to: Optional[str] = None
    email_from: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

    # Webhook settings
    webhook_url: Optional[str] = None
    webhook_headers: Optional[Dict[str, str]] = None


@dataclass
class NotificationPayload:
    """Standard payload for notifications"""
    notification_type: NotificationType
    timestamp: str
    company_name: str
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EmailNotifier:
    """
    Send email notifications for important events
    """
    def __init__(self, config: WebhookConfig):
        self.config = config

    def send_notification(self, subject: str, body: str, html: bool = False) -> bool:
        """
        Send an email notification

        Args:
            subject: Email subject
            body: Email body
            html: Whether body is HTML

        Returns:
            True if sent successfully
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.email_from
            msg['To'] = self.config.email_to
            msg['Subject'] = subject

            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                if self.config.smtp_user and self.config.smtp_password:
                    server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Email send failed: {e}")
            return False

    def send_escalation_email(self, escalation: EscalationPacket) -> bool:
        """Send escalation notification email"""
        subject = f"🚨 Eskalering: {escalation.priority.upper()} - {escalation.conversation_id}"

        body = f"""
<html>
<body>
    <h2>Eskaleringsärende</h2>
    <table border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse;">
        <tr><td><strong>Prioritet:</strong></td><td>{escalation.priority.value.upper()}</td></tr>
        <tr><td><strong>Konversation ID:</strong></td><td>{escalation.conversation_id}</td></tr>
        <tr><td><strong>Intent:</strong></td><td>{escalation.intent}</td></tr>
        <tr><td><strong>Sentiment:</strong></td><td>{escalation.sentiment}</td></tr>
        <tr><td><strong>Lead Score:</strong></td><td>{escalation.lead_score}/5</td></tr>
        <tr><td><strong>Kundens namn:</strong></td><td>{escalation.customer_name or 'Ej angivet'}</td></tr>
        <tr><td><strong>Kundens email:</strong></td><td>{escalation.customer_email or 'Ej angivet'}</td></tr>
    </table>

    <h3>Sammanfattning</h3>
    <p>{escalation.summary}</p>

    <h3>Kundens ärende</h3>
    <p>{escalation.customer_issue}</p>

    <h3>Konversationshistorik</h3>
    <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">
{self._format_conversation_history(escalation.conversation_history)}
    </pre>
</body>
</html>
        """

        return self.send_notification(subject, body, html=True)

    def _format_conversation_history(self, history: List[Dict]) -> str:
        """Format conversation history for email"""
        lines = []
        for msg in history[-10:]:  # Last 10 messages
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')
            lines.append(f"[{role}] {content}")
        return "\n".join(lines)

    def send_lead_notification(self, lead: LeadData) -> bool:
        """Send high-lead notification email"""
        subject = f"🔥 Ny högintresserad lead (Score: {lead.lead_score}/5)"

        body = f"""
<html>
<body>
    <h2>Ny högintresserad lead</h2>
    <table border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse;">
        <tr><td><strong>Lead Score:</strong></td><td>{lead.lead_score}/5 - {lead.lead_stage.value.upper()}</td></tr>
        <tr><td><strong>Konversation ID:</strong></td><td>{lead.conversation_id}</td></tr>
        <tr><td><strong>Namn:</strong></td><td>{lead.name or 'Ej angivet'}</td></tr>
        <tr><td><strong>Email:</strong></td><td>{lead.email or 'Ej angivet'}</td></tr>
        <tr><td><strong>Företag:</strong></td><td>{lead.company or 'Ej angivet'}</td></tr>
    </table>

    <h3>Köpsignaler</h3>
    <ul>
        {"".join(f"<li>{signal}</li>" for signal in lead.triggered_signals)}
    </ul>

    <h3>Intresserade tjänster</h3>
    <ul>
        {"".join(f"<li>{service}</li>" for service in lead.interested_services) if lead.interested_services else "<li>Ingen specifik info</li>"}
    </ul>

    <h3>Rekommenderad åtgärd</h3>
    <p><strong>{lead.suggested_action or 'Kontakta kunden inom 24 timmar'}</strong></p>
    <p>CTA: {lead.suggested_cta or 'Ring kunden för bokning'}</p>
</body>
</html>
        """

        return self.send_notification(subject, body, html=True)


class SlackNotifier:
    """
    Send notifications to Slack
    """
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_message(self, text: str, blocks: Optional[List[Dict]] = None) -> bool:
        """Send message to Slack webhook"""
        try:
            payload = {"text": text}
            if blocks:
                payload["blocks"] = blocks

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Slack notification failed: {e}")
            return False

    def send_escalation(self, escalation: EscalationPacket) -> bool:
        """Send escalation notification to Slack"""
        color = {
            "critical": "#FF0000",
            "high": "#FF6600",
            "medium": "#FFCC00",
            "low": "#36A64F"
        }.get(escalation.priority.value, "#36A64F")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 Escalation: {escalation.priority.value.upper()}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Intent:*\n{escalation.intent}"},
                    {"type": "mrkdwn", "text": f"*Sentiment:*\n{escalation.sentiment}"},
                    {"type": "mrkdwn", "text": f"*Lead Score:*\n{escalation.lead_score}/5"},
                    {"type": "mrkdwn", "text": f"*Customer:*\n{escalation.customer_name or 'Unknown'}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{escalation.summary}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Issue:*\n{escalation.customer_issue}"
                }
            }
        ]

        return self.send_message("", blocks)

    def send_lead_alert(self, lead: LeadData) -> bool:
        """Send high-lead notification to Slack"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔥 New Hot Lead: {lead.lead_score}/5"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Name:*\n{lead.name or 'Unknown'}"},
                    {"type": "mrkdwn", "text": f"*Email:*\n{lead.email or 'Unknown'}"},
                    {"type": "mrkdwn", "text": f"*Company:*\n{lead.company or 'Unknown'}"},
                    {"type": "mrkdwn", "text": f"*Stage:*\n{lead.lead_stage.value}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Buying Signals:*\n" + "\n".join(f"• {s}" for s in lead.triggered_signals)
                }
            }
        ]

        return self.send_message("", blocks)


class ConversationLogger:
    """
    Log all conversations to file/database
    """
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    def log_conversation(self, session_id: str, messages: List[Dict],
                        metadata: Optional[Dict] = None) -> None:
        """Log a conversation to file"""
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(self.log_dir, f"conversations_{timestamp}.jsonl")

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "messages": messages,
            "metadata": metadata or {}
        }

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def log_event(self, event_type: str, session_id: str, data: Dict) -> None:
        """Log a single event"""
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(self.log_dir, f"events_{timestamp}.jsonl")

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "session_id": session_id,
            "data": data
        }

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def get_conversation_history(self, session_id: str,
                                 limit: int = 10) -> List[Dict]:
        """Retrieve conversation history for a session"""
        # Search through recent log files
        history = []
        for i in range(7):  # Search last 7 days
            date = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) -
                   __import__('datetime').timedelta(days=i))
            log_file = os.path.join(self.log_dir,
                                   f"conversations_{date.strftime('%Y%m%d')}.jsonl")

            if not os.path.exists(log_file):
                continue

            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get("session_id") == session_id:
                            history.extend(entry.get("messages", []))
                    except json.JSONDecodeError:
                        continue

        return history[-limit:]


class WebhookManager:
    """
    Main webhook manager that coordinates all notifications
    """
    def __init__(self):
        self.email_configs: Dict[str, WebhookConfig] = {}
        self.slack_webhooks: Dict[str, str] = {}
        self.logger = ConversationLogger()

    def add_email_destination(self, name: str, config: WebhookConfig) -> None:
        """Add an email notification destination"""
        self.email_configs[name] = config

    def add_slack_webhook(self, name: str, webhook_url: str) -> None:
        """Add a Slack webhook"""
        self.slack_webhooks[name] = webhook_url

    def notify_escalation(self, escalation: EscalationPacket,
                         destinations: Optional[List[str]] = None) -> bool:
        """Send escalation notifications to all configured destinations"""
        success = True

        # Log the escalation
        self.logger.log_event("escalation", escalation.conversation_id, {
            "priority": escalation.priority.value,
            "intent": escalation.intent,
            "sentiment": escalation.sentiment,
            "summary": escalation.summary
        })

        # Send emails
        for name, config in self.email_configs.items():
            if config.enabled and (destinations is None or name in destinations):
                notifier = EmailNotifier(config)
                if not notifier.send_escalation_email(escalation):
                    success = False

        # Send Slack notifications
        for name, webhook_url in self.slack_webhooks.items():
            if destinations is None or name in destinations:
                notifier = SlackNotifier(webhook_url)
                if not notifier.send_escalation(escalation):
                    success = False

        return success

    def notify_lead(self, lead: LeadData,
                   destinations: Optional[List[str]] = None) -> bool:
        """Send lead notifications to all configured destinations"""
        success = True

        # Log the lead
        self.logger.log_event("high_lead", lead.conversation_id, {
            "lead_score": lead.lead_score,
            "lead_stage": lead.lead_stage.value,
            "email": lead.email,
            "signals": lead.triggered_signals
        })

        # Send emails
        for name, config in self.email_configs.items():
            if config.enabled and (destinations is None or name in destinations):
                notifier = EmailNotifier(config)
                if not notifier.send_lead_notification(lead):
                    success = False

        # Send Slack notifications
        for name, webhook_url in self.slack_webhooks.items():
            if destinations is None or name in destinations:
                notifier = SlackNotifier(webhook_url)
                if not notifier.send_lead_alert(lead):
                    success = False

        return success

    def log_conversation(self, session_id: str, messages: List[Dict],
                        metadata: Optional[Dict] = None) -> None:
        """Log a conversation"""
        self.logger.log_conversation(session_id, messages, metadata)


# Singleton instance for easy access
_webhook_manager = None

def get_webhook_manager() -> WebhookManager:
    """Get the global webhook manager instance"""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager


def configure_from_env() -> WebhookManager:
    """
    Configure webhook manager from environment variables

    Environment variables:
    - EMAIL_ENABLED: true/false
    - EMAIL_TO: recipient email
    - EMAIL_FROM: sender email
    - SMTP_SERVER: SMTP server address
    - SMTP_PORT: SMTP port
    - SMTP_USER: SMTP username
    - SMTP_PASSWORD: SMTP password

    - SLACK_ENABLED: true/false
    - SLACK_WEBHOOK_URL: Slack webhook URL
    """
    manager = get_webhook_manager()

    # Configure email if enabled
    if os.getenv("EMAIL_ENABLED", "false").lower() == "true":
        email_config = WebhookConfig(
            destination_type=WebhookDestination.EMAIL,
            enabled=True,
            email_to=os.getenv("EMAIL_TO"),
            email_from=os.getenv("EMAIL_FROM"),
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER"),
            smtp_password=os.getenv("SMTP_PASSWORD")
        )
        manager.add_email_destination("default", email_config)

    # Configure Slack if enabled
    if os.getenv("SLACK_ENABLED", "false").lower() == "true":
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if webhook_url:
            manager.add_slack_webhook("default", webhook_url)

    return manager


if __name__ == "__main__":
    # Test webhook system
    print("=" * 60)
    print("WEBHOOK SYSTEM - TEST")
    print("=" * 60)

    # Create test escalation
    from escalation import EscalationContext, EscalationPriority, EscalationReason

    test_escalation = EscalationContext(
        escalation_id="test_001",
        conversation_id="conv_test",
        timestamp=datetime.now().isoformat(),
        priority=EscalationPriority.HIGH,
        reason=EscalationReason.ANGRY_CUSTOMER,
        summary="Kunden är frustrerad över tekniska problem",
        customer_issue="Inloggningen fungerar inte",
        detected_intent="technical_issue",
        customer_sentiment="frustrated",
        lead_score=2,
        customer_name="Test Testsson",
        customer_email="test@example.com",
        messages_summary=["user: Det fungerar inte!", "bot: Låter mig hjälpa..."]
    )

    # Create test lead
    from schemas import LeadData, ConversionStage
    test_lead = LeadData(
        conversation_id="conv_test",
        lead_score=5,
        lead_stage=ConversionStage.READY_TO_BUY,
        triggered_signals=["Prisfråga", "Bokningsförfrågan"],
        email="test@example.com",
        name="Test Testsson",
        company="Test AB",
        suggested_action="Ring inom 1 timme",
        suggested_cta="Boka demo"
    )

    print("\n--- Test Data Created ---")
    print("Escalation:", test_escalation.to_json()[:200] + "...")
    print("Lead:", test_lead.to_json()[:200] + "...")

    print("\n--- Configure from environment ---")
    print("Set these environment variables to enable notifications:")
    print("EMAIL_ENABLED=true")
    print("EMAIL_TO=recipient@example.com")
    print("EMAIL_FROM=sender@example.com")
    print("SMTP_SERVER=smtp.gmail.com")
    print("SMTP_PORT=587")
    print("SMTP_USER=your-email@gmail.com")
    print("SMTP_PASSWORD=your-app-password")
