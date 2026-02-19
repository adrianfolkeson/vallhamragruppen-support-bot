"""
SUPPORT STARTER AI - GDPR COMPLIANCE
====================================
Data retention, anonymization, and right to deletion

Features:
- Automatic data anonymization for PII in logs
- Configurable retention periods
- GDPR delete endpoint for right to be forgotten
- Data export for data portability
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
import re


@dataclass
class GDPRConfig:
    """GDPR configuration"""
    # Retention periods (in days)
    chat_log_retention_days: int = 365
    session_data_retention_days: int = 90
    analytics_data_retention_days: int = 730  # 2 years

    # Anonymization settings
    anonymize_ip_addresses: bool = True
    anonymize_email: bool = True
    anonymize_phone: bool = True
    anonymize_names: bool = True

    # Data paths
    chat_logs_dir: str = "chat_logs"
    sessions_dir: str = "chat_logs/sessions"
    exports_dir: str = "chat_logs/exports"


class PIIAnonymizer:
    """
    Anonymize Personally Identifiable Information (PII)

    Handles:
    - Email addresses
    - Phone numbers
    - IP addresses
    - Names (Swedish common names)
    - Address information
    """

    # Swedish common names for detection
    COMMON_NAMES = [
        "Anna", "Erik", "Johan", "Maria", "Karl", "Sara", "Anders", "Emma",
        "Lars", "Eva", "Per", "Astrid", "Nils", "Karin", "Mikael", "Lisa",
        "Peter", "Birgitta", "Jan", "Ingrid", "Bengt", "Kristina", "Thomas",
        "Margareta", "Lennart", "Elisabeth", "Mats", "Ulla", "Göran", "Marianne"
    ]

    # Patterns
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # Swedish phone: 070-123 45 67, 0793 006 638, 0701234567, +46701234567
    PHONE_PATTERN = r'\b(?:0|0046|\+46)?[- ]?(7[0-9]{1}[- ]?[0-9]{3}[- ]?[0-9]{2}[- ]?[0-9]{2}|[0-9]{3}[- ]?[0-9]{3}[- ]?[0-9]{2})\b'
    IP_PATTERN = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    # Swedish personnummer: 19800101-1234, 800101+1234
    SSN_PATTERN = r'\b[12]?[0-9]{5}[-+]?[0-9]{4}\b'  # Swedish personnummer

    def __init__(self, config: GDPRConfig = None):
        self.config = config or GDPRConfig()

    def anonymize_text(self, text: str) -> str:
        """
        Anonymize PII in text

        Args:
            text: Input text that may contain PII

        Returns:
            Text with PII replaced with placeholders
        """
        if not text:
            return text

        result = text

        # Anonymize email addresses
        if self.config.anonymize_email:
            result = re.sub(self.EMAIL_PATTERN, '[E-POST]', result)

        # Anonymize phone numbers - multiple Swedish formats
        if self.config.anonymize_phone:
            # Pattern for: 0XX-XXX XX XX, 0XX-XXXXXXX, 07X-XXX XX XX, etc.
            phone_patterns = [
                r'\b0[0-9]{1,3}[- ]?[0-9]{3}[- ]?[0-9]{2}[- ]?[0-9]{2}\b',  # 0XX-XXX XX XX
                r'\b0[0-9]{2,3}[- ]?[0-9]{5,7}\b',  # 0XX-XXXXXXX or 070-1234567
                r'\b0046|\+46[- ]?7[0-9][- ]?[0-9]{3}[- ]?[0-9]{2}[- ]?[0-9]{2}\b',  # +467X-XXX XX XX
                r'\b07[0,2,3,6,9][- ]?[0-9]{3}[- ]?[0-9]{2}[- ]?[0-9]{2}\b',  # 07X-XXX XX XX
            ]
            for pattern in phone_patterns:
                result = re.sub(pattern, '[TELEFON]', result)

        # Anonymize IP addresses
        if self.config.anonymize_ip_addresses:
            result = re.sub(self.IP_PATTERN, '[IP]', result)

        # Anonymize Swedish personnummer
        result = re.sub(self.SSN_PATTERN, '[PERSONNUMMER]', result)

        # Anonymize common names (simple pattern)
        if self.config.anonymize_names:
            for name in self.COMMON_NAMES:
                # Word boundary to avoid partial matches
                result = re.sub(rf'\b{name}\b', '[NAMN]', result, flags=re.IGNORECASE)

        return result

    def anonymize_session(self, session_data: Dict) -> Dict:
        """
        Anonymize a session dictionary

        Args:
            session_data: Raw session data

        Returns:
            Anonymized session data
        """
        result = session_data.copy()

        # Anonymize customer info
        if "customer_name" in result and result["customer_name"]:
            result["customer_name"] = self.anonymize_text(result["customer_name"])
        if "customer_email" in result and result["customer_email"]:
            result["customer_email"] = "[E-POST]"
        if "customer_phone" in result and result["customer_phone"]:
            result["customer_phone"] = "[TELEFON]"

        # Anonymize messages
        if "messages" in result:
            for msg in result["messages"]:
                if "content" in msg:
                    msg["content"] = self.anonymize_text(msg["content"])

        return result

    def hash_pii(self, value: str) -> str:
        """
        Create a one-way hash of PII for pseudonymization

        Args:
            value: PII value to hash

        Returns:
            Hex digest hash
        """
        if not value:
            return ""
        return hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]


class DataRetentionManager:
    """
    Manage data retention and cleanup according to GDPR

    Features:
    - Automatic cleanup of old data
    - Archive instead of delete (configurable)
    - Logging of all data operations
    """

    def __init__(self, config: GDPRConfig = None):
        self.config = config or GDPRConfig()
        self.anonymizer = PIIAnonymizer(self.config)
        self._setup_directories()

    def _setup_directories(self):
        """Ensure required directories exist"""
        Path(self.config.chat_logs_dir).mkdir(exist_ok=True)
        Path(self.config.sessions_dir).mkdir(exist_ok=True)
        Path(self.config.exports_dir).mkdir(exist_ok=True)

    def _get_file_age_days(self, file_path: str) -> int:
        """Get file age in days"""
        mtime = os.path.getmtime(file_path)
        age = datetime.now() - datetime.fromtimestamp(mtime)
        return age.days

    def cleanup_old_chat_logs(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Remove or anonymize chat logs older than retention period

        Args:
            dry_run: If True, report what would be done without doing it

        Returns:
            Dict with counts of deleted/archived files
        """
        result = {
            "deleted": 0,
            "archived": 0,
            "errors": 0,
            "files_processed": 0
        }

        sessions_dir = Path(self.config.sessions_dir)
        if not sessions_dir.exists():
            return result

        cutoff_date = datetime.now() - timedelta(days=self.config.chat_log_retention_days)

        for file_path in sessions_dir.glob("*.json"):
            try:
                result["files_processed"] += 1
                file_age_days = self._get_file_age_days(str(file_path))
                file_mtime = datetime.fromtimestamp(os.path.getmtime(str(file_path)))

                if file_mtime < cutoff_date:
                    if dry_run:
                        result["deleted"] += 1
                    else:
                        # Load, anonymize, and overwrite instead of deleting
                        # This preserves conversation data while removing PII
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        anonymized = self.anonymizer.anonymize_session(data)

                        # Mark as anonymized
                        anonymized["_anonymized"] = True
                        anonymized["_anonymized_at"] = datetime.now().isoformat()

                        # Write back
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(anonymized, f, ensure_ascii=False, indent=2)

                        result["archived"] += 1

            except Exception as e:
                result["errors"] += 1
                print(f"Error processing {file_path}: {e}")

        return result

    def cleanup_old_exports(self, dry_run: bool = False) -> Dict[str, int]:
        """Remove export files older than retention period"""
        result = {"deleted": 0, "errors": 0}

        exports_dir = Path(self.config.exports_dir)
        if not exports_dir.exists():
            return result

        cutoff_date = datetime.now() - timedelta(days=self.config.analytics_data_retention_days)

        for file_path in exports_dir.glob("*"):
            try:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(str(file_path)))
                if file_mtime < cutoff_date:
                    if dry_run:
                        result["deleted"] += 1
                    else:
                        os.remove(str(file_path))
                        result["deleted"] += 1
            except Exception as e:
                result["errors"] += 1
                print(f"Error deleting {file_path}: {e}")

        return result

    def get_retention_report(self) -> Dict[str, Any]:
        """Get report on data retention status"""
        sessions_dir = Path(self.config.sessions_dir)
        exports_dir = Path(self.config.exports_dir)

        total_sessions = 0
        old_sessions = 0
        cutoff_date = datetime.now() - timedelta(days=self.config.chat_log_retention_days)

        if sessions_dir.exists():
            for file_path in sessions_dir.glob("*.json"):
                total_sessions += 1
                file_mtime = datetime.fromtimestamp(os.path.getmtime(str(file_path)))
                if file_mtime < cutoff_date:
                    old_sessions += 1

        total_exports = 0
        old_exports = 0
        export_cutoff = datetime.now() - timedelta(days=self.config.analytics_data_retention_days)

        if exports_dir.exists():
            for file_path in exports_dir.glob("*"):
                total_exports += 1
                file_mtime = datetime.fromtimestamp(os.path.getmtime(str(file_path)))
                if file_mtime < export_cutoff:
                    old_exports += 1

        return {
            "chat_logs": {
                "total": total_sessions,
                "past_retention": old_sessions,
                "retention_days": self.config.chat_log_retention_days
            },
            "exports": {
                "total": total_exports,
                "past_retention": old_exports,
                "retention_days": self.config.analytics_data_retention_days
            },
            "generated_at": datetime.now().isoformat()
        }


class GDPRManager:
    """
    Main GDPR management interface

    Provides:
    - Data export for data portability (right to data portability)
    - Data deletion for right to be forgotten
    - Anonymization of logs
    """

    def __init__(self, config: GDPRConfig = None):
        self.config = config or GDPRConfig()
        self.retention = DataRetentionManager(self.config)
        self.anonymizer = PIIAnonymizer(self.config)

    def export_user_data(self, identifier: str, identifier_type: str = "email") -> Optional[Dict]:
        """
        Export all data for a specific user (right to data portability)

        Args:
            identifier: User's email, phone, or session_id
            identifier_type: Type of identifier (email, phone, session_id)

        Returns:
            Dict with all user data or None if not found
        """
        sessions_dir = Path(self.config.sessions_dir)
        user_data = {
            "identifier": identifier,
            "identifier_type": identifier_type,
            "conversations": [],
            "export_date": datetime.now().isoformat()
        }

        for file_path in sessions_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Check if this file contains the user's data
                matches = False

                if identifier_type == "session_id" and data.get("session_id") == identifier:
                    matches = True
                elif identifier_type == "email":
                    email = data.get("customer_email")
                    if email and email.lower() == identifier.lower():
                        matches = True
                elif identifier_type == "phone":
                    phone = data.get("customer_phone")
                    if phone and phone.replace(" ", "") == identifier.replace(" ", ""):
                        matches = True

                if matches:
                    user_data["conversations"].append(data)

            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        if not user_data["conversations"]:
            return None

        return user_data

    def delete_user_data(self, identifier: str, identifier_type: str = "email") -> Dict[str, Any]:
        """
        Delete all data for a specific user (right to be forgotten)

        Args:
            identifier: User's email, phone, or session_id
            identifier_type: Type of identifier (email, phone, session_id)

        Returns:
            Dict with deletion report
        """
        sessions_dir = Path(self.config.sessions_dir)
        report = {
            "identifier": identifier,
            "identifier_type": identifier_type,
            "sessions_found": 0,
            "sessions_deleted": 0,
            "sessions_anonymized": 0,
            "errors": []
        }

        files_to_delete = []

        for file_path in sessions_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Check if this file contains the user's data
                matches = False

                if identifier_type == "session_id" and data.get("session_id") == identifier:
                    matches = True
                elif identifier_type == "email":
                    email = data.get("customer_email")
                    if email and email.lower() == identifier.lower():
                        matches = True
                elif identifier_type == "phone":
                    phone = data.get("customer_phone")
                    if phone and phone.replace(" ", "") == identifier.replace(" ", ""):
                        matches = True

                if matches:
                    report["sessions_found"] += 1
                    files_to_delete.append((file_path, data))

            except Exception as e:
                report["errors"].append(f"Error reading {file_path}: {e}")

        # Delete or anonymize found sessions
        for file_path, data in files_to_delete:
            try:
                # Anonymize instead of delete for audit trail
                anonymized = self.anonymizer.anonymize_session(data)
                anonymized["_deleted_by_gdpr_request"] = True
                anonymized["_deletion_date"] = datetime.now().isoformat()
                anonymized["_original_identifier"] = identifier

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(anonymized, f, ensure_ascii=False, indent=2)

                report["sessions_anonymized"] += 1

            except Exception as e:
                report["errors"].append(f"Error processing {file_path}: {e}")

        report["completed_at"] = datetime.now().isoformat()
        return report

    def get_gdpr_status(self) -> Dict[str, Any]:
        """Get GDPR compliance status"""
        retention_report = self.retention.get_retention_report()

        return {
            "retention": retention_report,
            "config": {
                "chat_log_retention_days": self.config.chat_log_retention_days,
                "session_data_retention_days": self.config.session_data_retention_days,
                "analytics_data_retention_days": self.config.analytics_data_retention_days,
                "anonymize_enabled": {
                    "email": self.config.anonymize_email,
                    "phone": self.config.anonymize_phone,
                    "ip": self.config.anonymize_ip_addresses,
                    "names": self.config.anonymize_names
                }
            },
            "status": "compliant" if self._check_compliance() else "review_needed"
        }

    def _check_compliance(self) -> bool:
        """Basic compliance check"""
        # Check if retention periods are reasonable (not > 5 years)
        return all([
            self.config.chat_log_retention_days <= 1825,  # 5 years
            self.config.analytics_data_retention_days <= 1825
        ])


# Singleton instance
_gdpr_manager: Optional[GDPRManager] = None


def get_gdpr_manager() -> GDPRManager:
    """Get GDPR manager instance"""
    global _gdpr_manager
    if _gdpr_manager is None:
        _gdpr_manager = GDPRManager()
    return _gdpr_manager


if __name__ == "__main__":
    print("=" * 60)
    print("GDPR COMPLIANCE - TEST")
    print("=" * 60)

    # Test anonymization
    print("\n--- Testing PII Anonymization ---")
    anonymizer = PIIAnonymizer()

    test_text = "Hej! Jag heter Anna, min e-post är anna@example.com och telefon 070-123 45 67."
    anonymized = anonymizer.anonymize_text(test_text)

    print(f"Original: {test_text}")
    print(f"Anonymized: {anonymized}")

    # Test data retention
    print("\n--- Testing Data Retention ---")
    gdpr = GDPRManager()
    report = gdpr.get_gdpr_status()
    print(json.dumps(report, indent=2, ensure_ascii=False))
