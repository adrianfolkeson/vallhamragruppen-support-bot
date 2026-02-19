"""
SUPPORT STARTER AI - CHAT LOGGING & NOTIFICATIONS
=================================================
Log conversations to file, send email transcripts, and sync to Google Sheets
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr


@dataclass
class ChatMessage:
    """Single message in conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    intent: Optional[str] = None
    urgency: Optional[str] = None
    lead_score: Optional[int] = None


@dataclass
class ConversationLog:
    """Complete conversation log"""
    session_id: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    started_at: str = None
    ended_at: Optional[str] = None
    messages: List[ChatMessage] = field(default_factory=list)
    escalated: bool = False
    fault_report: Optional[Dict] = None
    status: str = "active"  # active, resolved, escalated

    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.now().isoformat()

    def add_message(self, role: str, content: str, **metadata):
        """Add a message to the conversation"""
        # Filter metadata to only include ChatMessage fields
        allowed_fields = {"intent", "urgency", "lead_score"}
        filtered_metadata = {k: v for k, v in metadata.items() if k in allowed_fields}

        msg = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            **filtered_metadata
        )
        self.messages.append(msg)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage"""
        return {
            "session_id": self.session_id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "customer_phone": self.customer_phone,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "messages": [asdict(msg) for msg in self.messages],
            "escalated": self.escalated,
            "fault_report": self.fault_report,
            "status": self.status
        }


class ChatLogger:
    """
    Log conversations to file system and prepare for export
    """
    def __init__(self, log_dir: str = "chat_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Subdirectories
        self.sessions_dir = self.log_dir / "sessions"
        self.daily_dir = self.log_dir / "daily"
        self.export_dir = self.log_dir / "exports"

        for dir_path in [self.sessions_dir, self.daily_dir, self.export_dir]:
            dir_path.mkdir(exist_ok=True)

        # Active conversations (in-memory)
        self.active_conversations: Dict[str, ConversationLog] = {}

    def start_conversation(self, session_id: str, customer_info: Optional[Dict] = None) -> ConversationLog:
        """Start a new conversation log"""
        conv = ConversationLog(
            session_id=session_id,
            customer_name=customer_info.get("name") if customer_info else None,
            customer_email=customer_info.get("email") if customer_info else None,
            customer_phone=customer_info.get("phone") if customer_info else None,
        )
        self.active_conversations[session_id] = conv
        return conv

    def log_message(self, session_id: str, role: str, content: str, **metadata):
        """Log a message to active conversation"""
        if session_id not in self.active_conversations:
            self.start_conversation(session_id)

        conv = self.active_conversations[session_id]
        conv.add_message(role, content, **metadata)

        # Update metadata
        if "urgency" in metadata and metadata["urgency"] in ["high", "critical"]:
            conv.escalated = True
        if "fault_report" in metadata:
            conv.fault_report = metadata["fault_report"]
        if "intent" in metadata:
            # Track fault report intent
            if metadata["intent"] in ["emergency_critical", "lockout_emergency", "fault_report"]:
                conv.escalated = True

    def end_conversation(self, session_id: str, status: str = "resolved"):
        """End conversation and save to disk"""
        if session_id not in self.active_conversations:
            return None

        conv = self.active_conversations[session_id]
        conv.ended_at = datetime.now().isoformat()
        conv.status = status

        # Save to file
        self._save_conversation(conv)

        # Remove from active
        del self.active_conversations[session_id]

        return conv

    def _save_conversation(self, conv: ConversationLog):
        """Save conversation to multiple formats"""
        # JSON format - full session
        json_path = self.sessions_dir / f"{conv.session_id}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(conv.to_dict(), f, ensure_ascii=False, indent=2)

        # Daily log (append)
        date_str = datetime.now().strftime("%Y-%m-%d")
        daily_path = self.daily_dir / f"{date_str}.jsonl"
        with open(daily_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(conv.to_dict(), ensure_ascii=False) + "\n")

    def get_conversation(self, session_id: str) -> Optional[ConversationLog]:
        """Get conversation from memory or load from disk"""
        if session_id in self.active_conversations:
            return self.active_conversations[session_id]

        # Try loading from disk
        json_path = self.sessions_dir / f"{session_id}.json"
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            conv = ConversationLog(
                session_id=data["session_id"],
                customer_name=data.get("customer_name"),
                customer_email=data.get("customer_email"),
                customer_phone=data.get("customer_phone"),
                started_at=data.get("started_at"),
                ended_at=data.get("ended_at"),
                status=data.get("status", "resolved")
            )

            for msg_data in data.get("messages", []):
                msg = ChatMessage(**msg_data)
                conv.messages.append(msg)

            conv.escalated = data.get("escalated", False)
            conv.fault_report = data.get("fault_report")

            return conv

        return None

    def get_conversations_for_export(self, date: Optional[str] = None) -> List[Dict]:
        """Get conversations for export to email/Google Sheets"""
        if date:
            daily_path = self.daily_dir / f"{date}.jsonl"
            if daily_path.exists():
                conversations = []
                with open(daily_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        conversations.append(json.loads(line))
                return conversations
        else:
            # Return all active conversations from memory
            return [conv.to_dict() for conv in self.active_conversations.values()]

    def export_to_csv(self, date: Optional[str] = None) -> str:
        """Export conversations to CSV format for Google Sheets import"""
        conversations = self.get_conversations_for_export(date)

        csv_path = self.export_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Session ID", "Date", "Customer Name", "Customer Email",
                "Customer Phone", "Status", "Escalated", "Message Count",
                "First Message", "Last Message"
            ])

            for conv in conversations:
                messages = conv.get("messages", [])
                first_msg = messages[0]["content"] if messages else ""
                last_msg = messages[-1]["content"] if messages else ""

                writer.writerow([
                    conv.get("session_id", ""),
                    conv.get("started_at", "")[:10],  # Just the date
                    conv.get("customer_name", ""),
                    conv.get("customer_email", ""),
                    conv.get("customer_phone", ""),
                    conv.get("status", ""),
                    conv.get("escalated", ""),
                    len(messages),
                    first_msg[:100] + "..." if len(first_msg) > 100 else first_msg,
                    last_msg[:100] + "..." if len(last_msg) > 100 else last_msg
                ])

        return str(csv_path)


class EmailNotifier:
    """
    Send email notifications and chat transcripts
    """
    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = 587,
        smtp_user: str = None,
        smtp_password: str = None,
        from_email: str = None,
        from_name: str = "Vallhamragruppen"
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("FROM_EMAIL", "info@vallhamragruppen.se")
        self.from_name = from_name

    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return all([self.smtp_host, self.smtp_user, self.smtp_password])

    def send_transcript(
        self,
        to_email: str,
        conversation: ConversationLog,
        subject: Optional[str] = None
    ) -> bool:
        """Send conversation transcript to email"""
        if not self.is_configured():
            print("Email not configured - skipping transcript send")
            return False

        if not subject:
            subject = f"Chattlogg: {conversation.session_id}"

        # Build email body
        body = self._format_transcript(conversation)

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = formataddr((self.from_name, self.from_email))
            msg["To"] = to_email

            # Plain text version
            text_part = MIMEText(body, "plain", "utf-8")
            msg.attach(text_part)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"Transcript sent to {to_email}")
            return True

        except Exception as e:
            print(f"Failed to send transcript: {e}")
            return False

    def send_admin_notification(
        self,
        admin_email: str,
        conversation: ConversationLog,
        alert_type: str = "escalation"
    ) -> bool:
        """Send admin notification for escalated conversations"""
        if not self.is_configured():
            return False

        subject_map = {
            "escalation": "Eskalerad konversation: Vallhamragruppen",
            "fault": "Felanmälan: Vallhamragruppen",
            "lead": "Ny lead: Vallhamragruppen"
        }

        subject = subject_map.get(alert_type, "Ny notis: Vallhamragruppen")

        body = f"""
Viktigt: {alert_type.upper()}

Session: {conversation.session_id}
Tid: {conversation.started_at}

Kund:
{conversation.customer_name or 'Ej angivet'}
Email: {conversation.customer_email or 'Ej angivet'}
Telefon: {conversation.customer_phone or 'Ej angivet'}

Senaste meddelande:
{conversation.messages[-1].content if conversation.messages else 'Inga'}

---
Skickat från Vallhamragruppen AI Support
"""

        try:
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = formataddr((self.from_name, self.from_email))
            msg["To"] = admin_email

            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"Admin notification sent to {admin_email}")
            return True

        except Exception as e:
            print(f"Failed to send admin notification: {e}")
            return False

    def _format_transcript(self, conv: ConversationLog) -> str:
        """Format conversation as readable transcript"""
        lines = [
            "=" * 50,
            "Chattlogg - Vallhamragruppen",
            "=" * 50,
            f"Session: {conv.session_id}",
            f"Starttid: {conv.started_at}",
            f"Sluttid: {conv.ended_at or 'Pågående'}",
            f"Status: {conv.status}",
            "",
            "-" * 50,
            "MEDDELANDEN",
            "-" * 50,
        ]

        for msg in conv.messages:
            role_name = "Kund" if msg.role == "user" else "Assistent"
            timestamp = msg.timestamp.split("T")[1][:8] if "T" in msg.timestamp else msg.timestamp
            lines.append(f"\n[{timestamp}] {role_name}:")
            lines.append(msg.content)

        lines.extend([
            "",
            "-" * 50,
            "Skickat från Vallhamragruppen"
        ])

        return "\n".join(lines)


class GoogleSheetsLogger:
    """
    Integration with Google Sheets for conversation data

    NOTE: This requires Google Cloud credentials and the Google Sheets API.
    Setup instructions:
    1. Create a Google Cloud project
    2. Enable Google Sheets API
    3. Create a service account with sheets.googleapis.com scope
    4. Download credentials JSON
    5. Set GOOGLE_SHEETS_CREDENTIALS environment variable to the JSON file path
    6. Share your sheet with the service account email
    """

    def __init__(self, spreadsheet_id: str = None, sheet_name: str = "Chattloggar"):
        self.spreadsheet_id = spreadsheet_id or os.getenv("GOOGLE_SHEETS_ID")
        self.sheet_name = sheet_name
        self._service = None

    def is_configured(self) -> bool:
        """Check if Google Sheets is configured"""
        try:
            import google.auth
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

            return bool(credentials_path and self.spreadsheet_id)

        except ImportError:
            return False

    def _get_service(self):
        """Get Google Sheets service (lazy loading)"""
        if self._service is not None:
            return self._service

        try:
            import google.auth
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

            if not credentials_path:
                raise ValueError("GOOGLE_SHEETS_CREDENTIALS not set")

            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )

            self._service = build("sheets", "v4", credentials=credentials)
            return self._service

        except ImportError:
            print("Google libraries not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            return None

    def log_conversation(self, conversation: ConversationLog) -> bool:
        """Append conversation to Google Sheets"""
        if not self.is_configured():
            print("Google Sheets not configured")
            return False

        try:
            service = self._get_service()
            if not service:
                return False

            # Prepare row data
            row = [
                conversation.session_id,
                conversation.started_at,
                conversation.customer_name or "",
                conversation.customer_email or "",
                conversation.customer_phone or "",
                conversation.status,
                "Ja" if conversation.escalated else "Nej",
                len(conversation.messages),
                conversation.messages[-1].content[:100] if conversation.messages else ""
            ]

            # Append to sheet
            body = {"values": [row]}
            range_name = f"{self.sheet_name}!A:I"

            service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()

            print(f"Logged conversation {conversation.session_id} to Google Sheets")
            return True

        except Exception as e:
            print(f"Failed to log to Google Sheets: {e}")
            return False

    def create_sheet_if_not_exists(self) -> bool:
        """Create sheet with headers if it doesn't exist"""
        if not self.is_configured():
            return False

        try:
            service = self._get_service()
            if not service:
                return False

            # Check if sheet exists
            spreadsheet = service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()

            sheet_exists = any(
                sheet["properties"]["title"] == self.sheet_name
                for sheet in spreadsheet["sheets"]
            )

            if not sheet_exists:
                # Create new sheet with headers
                requests = [{
                    "addSheet": {
                        "properties": {
                            "title": self.sheet_name,
                            "gridProperties": {"rowCount": 1000, "columnCount": 9}
                        }
                    }
                }]

                service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={"requests": requests}
                ).execute()

                # Add headers
                headers = [
                    ["Session ID", "Starttid", "Kundnamn", "Email", "Telefon",
                     "Status", "Eskalerad", "Antal meddelanden", "Senaste meddelande"]
                ]

                service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.sheet_name}!A1:I1",
                    valueInputOption="USER_ENTERED",
                    body={"values": headers}
                ).execute()

                print(f"Created sheet '{self.sheet_name}' with headers")

            return True

        except Exception as e:
            print(f"Failed to create sheet: {e}")
            return False


class LogManager:
    """
    Main logging manager that combines file logging, email, and Google Sheets
    """
    def __init__(
        self,
        log_dir: str = "chat_logs",
        email_config: Optional[Dict] = None,
        sheets_config: Optional[Dict] = None
    ):
        self.logger = ChatLogger(log_dir)
        self.email = EmailNotifier(**(email_config or {}))
        self.sheets = GoogleSheetsLogger(**(sheets_config or {}))

    def start_conversation(self, session_id: str, customer_info: Optional[Dict] = None) -> ConversationLog:
        """Start new conversation"""
        return self.logger.start_conversation(session_id, customer_info)

    def log_message(self, session_id: str, role: str, content: str, **metadata):
        """Log a message"""
        self.logger.log_message(session_id, role, content, **metadata)

    def end_conversation(
        self,
        session_id: str,
        status: str = "resolved",
        send_transcript: bool = True,
        log_to_sheets: bool = True
    ) -> Optional[ConversationLog]:
        """End conversation and handle exports"""
        conv = self.logger.end_conversation(session_id, status)

        if not conv:
            return None

        # Send transcript to customer if email available
        if send_transcript and conv.customer_email:
            self.email.send_transcript(conv.customer_email, conv)

        # Send admin notification for escalated conversations
        if conv.escalated and os.getenv("ADMIN_EMAIL"):
            self.email.send_admin_notification(
                os.getenv("ADMIN_EMAIL"),
                conv,
                "escalation"
            )

        # Log to Google Sheets if configured
        if log_to_sheets:
            self.sheets.log_conversation(conv)

        return conv


# Singleton instance
_default_log_manager: Optional[LogManager] = None


def get_log_manager() -> LogManager:
    """Get default log manager instance"""
    global _default_log_manager
    if _default_log_manager is None:
        _default_log_manager = LogManager()
    return _default_log_manager


if __name__ == "__main__":
    # Test the logging system
    print("=" * 60)
    print("CHAT LOGGER - TEST")
    print("=" * 60)

    log_mgr = LogManager()

    # Simulate a conversation
    session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    log_mgr.start_conversation(session_id, {
        "name": "Test Testsson",
        "email": "test@example.com",
        "phone": "070-123 45 67"
    })

    log_mgr.log_message(session_id, "user", "Hej, jag har en vattenläcka!")
    log_mgr.log_message(session_id, "assistant", "Vattenläcka! 💧 Stäng av vattnet...", urgency="critical")

    conv = log_mgr.end_conversation(session_id, status="resolved")

    print(f"\nSession logged: {conv.session_id}")
    print(f"Messages: {len(conv.messages)}")
    print(f"Status: {conv.status}")
    print(f"Escalated: {conv.escalated}")

    # Export to CSV
    csv_path = log_mgr.logger.export_to_csv()
    print(f"\nCSV exported: {csv_path}")
