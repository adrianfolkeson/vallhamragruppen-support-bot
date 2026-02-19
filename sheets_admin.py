"""
SUPPORT STARTER AI - GOOGLE SHEETS ADMIN PANEL
==============================================
Load FAQ and knowledge chunks from Google Sheets for easy editing
without touching code or config files.

Benefits:
- Edit FAQs via spreadsheet interface
- No code deployment needed to update content
- Version history built into Sheets
- Multiple editors can collaborate
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Try importing Google Sheets API, fall back to mock for development
try:
    import google.auth
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    print("Warning: Google API libraries not installed. Run:")
    print("  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")


@dataclass
class FAQEntry:
    """FAQ entry from Sheets or config"""
    question: str
    answer: str
    keywords: List[str]
    category: str = "general"
    priority: int = 2
    enabled: bool = True

    def to_dict(self) -> Dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "keywords": self.keywords,
            "category": self.category,
            "priority": self.priority
        }


@dataclass
class KnowledgeChunk:
    """Knowledge chunk from Sheets or config"""
    id: str
    content: str
    category: str = "general"
    keywords: List[str] = None
    priority: int = 2

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "keywords": self.keywords,
            "priority": self.priority
        }


class SheetsAdmin:
    """
    Load FAQ and knowledge from Google Sheets.

    Sheet structure (FAQ tab):
    | Question | Answer | Keywords | Category | Priority | Enabled |
    |----------|--------|----------|----------|----------|---------|
    | Hur gör... | Ring... | felanmälan | support | 3 | TRUE |

    Sheet structure (Knowledge tab):
    | ID | Content | Category | Keywords | Priority |
    |----|---------|----------|----------|----------|
    | company_info | COMPANY:... | contact | kontakt | 3 |
    """

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    def __init__(self, sheet_id: Optional[str] = None, credentials_path: Optional[str] = None):
        """
        Initialize Sheets admin

        Args:
            sheet_id: Google Sheet ID (from URL)
            credentials_path: Path to credentials JSON file
        """
        self.sheet_id = sheet_id or os.getenv("GOOGLE_SHEET_ID")
        self.credentials_path = credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH", "google-credentials.json")
        self.service = None

        if SHEETS_AVAILABLE and self.sheet_id:
            self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        if not os.path.exists(self.credentials_path):
            print(f"Warning: Credentials file not found at {self.credentials_path}")
            print("To enable Sheets admin:")
            print("1. Go to https://console.cloud.google.com/")
            print("2. Create a project and enable Sheets API")
            print("3. Create OAuth credentials (Desktop app)")
            print("4. Download JSON and save as google-credentials.json")
            return

        try:
            creds = None
            # The file token.json stores the user's access and refresh tokens
            token_path = self.credentials_path.replace('.json', '-token.json')

            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)

            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            self.service = build('sheets', 'v4', credentials=creds)
            print(f"Connected to Google Sheets: {self.sheet_id}")

        except Exception as e:
            print(f"Error authenticating with Google Sheets: {e}")

    def load_faq_from_sheets(self, sheet_name: str = "FAQ") -> List[FAQEntry]:
        """Load FAQ entries from Sheets"""
        if not self.service:
            return []

        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=sheet_name
            ).execute()

            values = result.get('values', [])
            if not values or len(values) < 2:
                return []

            # Skip header row
            faqs = []
            for row in values[1:]:
                if len(row) < 2:
                    continue

                # Parse row: Question, Answer, Keywords, Category, Priority, Enabled
                question = row[0] if len(row) > 0 else ""
                answer = row[1] if len(row) > 1 else ""
                keywords_str = row[2] if len(row) > 2 else ""
                category = row[3] if len(row) > 3 else "general"
                priority = int(row[4]) if len(row) > 4 and row[4].isdigit() else 2
                enabled = str(row[5]).upper() == "TRUE" if len(row) > 5 else True

                if not question or not answer or not enabled:
                    continue

                # Parse keywords from comma-separated string
                keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]

                faqs.append(FAQEntry(
                    question=question,
                    answer=answer,
                    keywords=keywords,
                    category=category,
                    priority=priority,
                    enabled=enabled
                ))

            return faqs

        except HttpError as e:
            print(f"Error loading FAQ from Sheets: {e}")
            return []

    def load_knowledge_from_sheets(self, sheet_name: str = "Knowledge") -> List[KnowledgeChunk]:
        """Load knowledge chunks from Sheets"""
        if not self.service:
            return []

        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=sheet_name
            ).execute()

            values = result.get('values', [])
            if not values or len(values) < 2:
                return []

            # Skip header row
            chunks = []
            for row in values[1:]:
                if len(row) < 2:
                    continue

                # Parse row: ID, Content, Category, Keywords, Priority
                chunk_id = row[0] if len(row) > 0 else ""
                content = row[1] if len(row) > 1 else ""
                category = row[2] if len(row) > 2 else "general"
                keywords_str = row[3] if len(row) > 3 else ""
                priority = int(row[4]) if len(row) > 4 and row[4].isdigit() else 2

                if not chunk_id or not content:
                    continue

                # Parse keywords
                keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]

                chunks.append(KnowledgeChunk(
                    id=chunk_id,
                    content=content,
                    category=category,
                    keywords=keywords,
                    priority=priority
                ))

            return chunks

        except HttpError as e:
            print(f"Error loading knowledge from Sheets: {e}")
            return []

    def load_all_from_sheets(self) -> Dict[str, Any]:
        """Load all content from Sheets"""
        return {
            "faq_data": [faq.to_dict() for faq in self.load_faq_from_sheets()],
            "knowledge_chunks": [chunk.to_dict() for chunk in self.load_knowledge_from_sheets()]
        }

    def export_to_sheets_template(self, output_path: str = "sheets_template.xlsx"):
        """
        Generate a template file for import to Google Sheets

        Creates an Excel file with proper structure that can be uploaded
        """
        try:
            import openpyxl
            from openpyxl import Workbook

            wb = Workbook()

            # FAQ Sheet
            ws_faq = wb.active
            ws_faq.title = "FAQ"
            ws_faq.append(["Question", "Answer", "Keywords", "Category", "Priority", "Enabled"])

            # Add example FAQ entries
            example_faqs = [
                ["Hur gör jag en felanmälan?", "Ring {phone} eller använd kontaktformuläret.", "felanmälan, fel", "support", "3", "TRUE"],
                ["Vilka områden verkar ni i?", "Vi verkar i {locations}.", "område, var", "general", "2", "TRUE"],
                ["Hur snabbt får man svar?", "Vi svarar inom 24 timmar.", "snabbt, tid, svar", "general", "2", "TRUE"],
            ]
            for faq in example_faqs:
                ws_faq.append(faq)

            # Knowledge Sheet
            ws_kb = wb.create_sheet("Knowledge")
            ws_kb.append(["ID", "Content", "Category", "Keywords", "Priority"])

            example_chunks = [
                ["company_info", "COMPANY: {COMPANY_NAME}. Phone: {phone}.", "contact", "kontakt, phone", "3"],
                ["services", "Vi erbjuder fastighetsförvaltning...", "services", "tjänster", "2"],
            ]
            for chunk in example_chunks:
                ws_kb.append(chunk)

            wb.save(output_path)
            print(f"Template saved to {output_path}")
            print("Upload this file to Google Sheets and share with your team!")

        except ImportError:
            print("openpyxl not installed. Run: pip install openpyxl")


class HybridConfigLoader:
    """
    Load configuration from multiple sources with priority:
    1. Google Sheets (if enabled and available)
    2. Tenant config file (config/tenants/{tenant}.json)
    3. Default config (config/config.json)
    4. Built-in defaults
    """

    def __init__(self, tenant_id: Optional[str] = None, use_sheets: bool = True):
        self.tenant_id = tenant_id
        self.use_sheets = use_sheets and os.getenv("GOOGLE_SHEET_ID")
        self.sheets_admin = None

        if self.use_sheets:
            self.sheets_admin = SheetsAdmin()

    def load_config(self) -> Dict[str, Any]:
        """Load merged configuration from all sources"""
        # Start with base config from file
        from config_loader import load_config_or_default

        if self.tenant_id:
            config_path = f"config/tenants/{self.tenant_id}.json"
        else:
            config_path = "config/config.json"

        base_config = load_config_or_default(config_path)
        config_dict = base_config.to_dict()

        # Override FAQ/knowledge from Sheets if enabled
        if self.use_sheets and self.sheets_admin and self.sheets_admin.service:
            sheets_data = self.sheets_admin.load_all_from_sheets()

            if sheets_data["faq_data"]:
                config_dict["faq_data"] = sheets_data["faq_data"]
                print(f"Loaded {len(sheets_data['faq_data'])} FAQ entries from Google Sheets")

            if sheets_data["knowledge_chunks"]:
                config_dict["knowledge_chunks"] = sheets_data["knowledge_chunks"]
                print(f"Loaded {len(sheets_data['knowledge_chunks'])} knowledge chunks from Google Sheets")

        return config_dict


# Convenience functions
def get_sheets_admin() -> Optional[SheetsAdmin]:
    """Get Sheets admin instance if configured"""
    if os.getenv("GOOGLE_SHEET_ID") and SHEETS_AVAILABLE:
        return SheetsAdmin()
    return None


def sync_sheets_to_config(sheet_id: str, output_path: str = "config/sheets_sync.json"):
    """
    Sync content from Google Sheets to a config file

    This allows you to:
    1. Edit content in Google Sheets
    2. Run this sync function
    3. Commit the resulting JSON to git (optional)
    """
    admin = SheetsAdmin(sheet_id=sheet_id)

    if not admin.service:
        print("Could not connect to Google Sheets")
        return None

    data = admin.load_all_from_sheets()

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Synced Sheets content to {output_path}")
    print(f"  - {len(data['faq_data'])} FAQ entries")
    print(f"  - {len(data['knowledge_chunks'])} knowledge chunks")

    return data


if __name__ == "__main__":
    print("=" * 60)
    print("SHEETS ADMIN - TEST")
    print("=" * 60)

    # Test template generation
    admin = SheetsAdmin()
    admin.export_to_sheets_template("sheets_template.xlsx")

    # Test hybrid loading
    print("\n--- Testing Hybrid Config Loader ---")
    hybrid = HybridConfigLoader(tenant_id="vallhamra", use_sheets=False)
    config = hybrid.load_config()
    print(f"Loaded config with {len(config.get('faq_data', []))} FAQ entries")
    print(f"Loaded config with {len(config.get('knowledge_chunks', []))} knowledge chunks")
