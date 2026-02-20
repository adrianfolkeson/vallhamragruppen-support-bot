"""
SUPPORT STARTER AI - INTEGRATIONS
===================================
Webhook integrations for third-party services
"""

import os
import json
import httpx
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


class IntegrationConfig:
    """Configuration for external integrations"""

    # Zapier
    ZAPIER_WEBHOOK_URL: str = os.getenv("ZAPIER_WEBHOOK_URL", "")
    ZAPIER_API_KEY: str = os.getenv("ZAPIER_API_KEY", "")

    # Slack
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#support")

    # HubSpot
    HUBSPOT_API_KEY: str = os.getenv("HUBSPOT_API_KEY", "")
    HUBSPOT_PORTAL_ID: str = os.getenv("HUBSPOT_PORTAL_ID", "")

    # Google Sheets
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")


@dataclass
class IntegrationEvent:
    """Standard event for integrations"""
    event_type: str  # "conversation_started", "lead_created", "fault_reported", etc.
    timestamp: str
    session_id: str
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "data": self.data
        }


class ZapierIntegration:
    """Zapier webhook integration"""

    def __init__(self):
        self.webhook_url = IntegrationConfig.ZAPIER_WEBHOOK_URL
        self.api_key = IntegrationConfig.ZAPIER_API_KEY

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    def send_event(self, event: IntegrationEvent) -> bool:
        """Send event to Zapier webhook"""
        if not self.is_configured():
            return False

        try:
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            response = httpx.post(
                self.webhook_url,
                json=event.to_dict(),
                headers=headers,
                timeout=10.0
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Zapier integration error: {e}")
            return False


class SlackIntegration:
    """Slack webhook integration"""

    def __init__(self):
        self.webhook_url = IntegrationConfig.SLACK_WEBHOOK_URL
        self.bot_token = IntegrationConfig.SLACK_BOT_TOKEN
        self.default_channel = IntegrationConfig.SLACK_CHANNEL

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    def send_message(self, channel: str, text: str, blocks: List[Dict] = None) -> bool:
        """Send message to Slack channel"""
        if not self.is_configured():
            return False

        try:
            payload = {
                "text": text,
                "channel": channel
            }
            if blocks:
                payload["blocks"] = blocks

            response = httpx.post(
                self.webhook_url,
                json=payload,
                timeout=10.0
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Slack integration error: {e}")
            return False

    def notify_lead(self, lead_data: Dict[str, Any]) -> bool:
        """Notify about new lead"""
        text = f"🔥 Ny Lead! *{lead_data.get('name', 'Okänd')}* - {lead_data.get('score', 0)}/5"

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{lead_data.get('name', 'Okänd')}* ({lead_data.get('score', 0)}/5)\n"
                           f"📧 {lead_data.get('email', 'Ingen e-post')}\n"
                           f"📞 {lead_data.get('phone', 'Inget telefon')}\n"
                           f"📝 {lead_data.get('interest', 'Okänt intresse')}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Kontakt"},
                        "url": f"tel:{lead_data.get('phone', '')}"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Mejla"},
                        "url": f"mailto:{lead_data.get('email', '')}"
                    }
                ]
            }
        ]

        return self.send_message(self.default_channel, text, blocks)

    def notify_fault_report(self, fault_data: Dict[str, Any]) -> bool:
        """Notify about fault report"""
        urgency_emoji = {
            "CRITICAL": "🚨",
            "HIGH": "⚠️",
            "MEDIUM": "⚡",
            "LOW": "📝"
        }

        emoji = urgency_emoji.get(fault_data.get("urgency", "MEDIUM"), "📝")
        category = fault_data.get("category", "Annat")

        text = f"{emoji} Felanmälan - {category}\n" \
                 f"Läge: {fault_data.get('location', 'Okänd')}"

        blocks = [
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Kategori*\n{category}"},
                    {"type": "mrkdwn", "text": f"*Urgens*\n{fault_data.get('urgency', 'MEDIUM')}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": fault_data.get("description", "Ingen beskrivning")[:300]
                }
            }
        ]

        return self.send_message(self.default_channel, text, blocks)


class HubSpotIntegration:
    """HubSpot CRM integration"""

    def __init__(self):
        self.api_key = IntegrationConfig.HUBSPOT_API_KEY
        self.portal_id = IntegrationConfig.HUBSPOT_PORTAL_ID
        self.base_url = "https://api.hubapi.com"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def create_contact(self, email: str, first_name: str = "", last_name: str = "",
                      phone: str = "", properties: Dict = None) -> Optional[Dict]:
        """Create or update contact in HubSpot"""
        if not self.is_configured():
            return None

        try:
            # First search for existing contact
            contact_id = self._find_contact(email)
            contact_url = f"/crm/v3/objects/contacts"

            contact_data = {
                "properties": {
                    "email": email,
                    "firstname": first_name,
                    "lastname": last_name,
                    "phone": phone,
                }
            }

            if properties:
                contact_data["properties"].update(properties)

            headers = self._get_headers()

            if contact_id:
                # Update existing contact
                url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
                response = httpx.patch(url, json=contact_data, headers=headers)
            else:
                # Create new contact
                response = httpx.post(self.base_url + contact_url, json=contact_data, headers=headers)

            if response.status_code in [200, 201]:
                return response.json()
            return None
        except Exception as e:
            print(f"HubSpot integration error: {e}")
            return None

    def _find_contact(self, email: str) -> Optional[str]:
        """Find contact by email"""
        try:
            search_url = f"{self.base_url}/crm/v3/objects/contacts/search"
            response = httpx.post(
                search_url,
                json={"filterGroups": [{
                    "filters": [{
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email
                    }]
                }]},
                headers=self._get_headers()
            )

            if response.status_code == 200:
                results = response.json().get("results", [])
                if results:
                    return results[0].get("id")
            return None
        except:
            return None

    def create_deal(self, contact_id: str, deal_stage: str = "qualifiedtobuy",
                   amount: float = 0, properties: Dict = None) -> Optional[Dict]:
        """Create deal in HubSpot"""
        if not self.is_configured():
            return None

        try:
            deal_data = {
                "properties": {
                    "dealname": f"Lead from chat bot - {datetime.now().strftime('%Y-%m-%d')}",
                    "dealstage": deal_stage,
                    "amount": amount,
                    "pipeline": self.portal_id or "default"
                }
            }

            if properties:
                deal_data["properties"].update(properties)

            headers = self._get_headers()
            url = f"{self.base_url}/crm/v3/objects/deals"

            response = httpx.post(url, json=deal_data, headers=headers)

            if response.status_code == 201:
                return response.json()
            return None
        except Exception as e:
            print(f"HubSpot deal creation error: {e}")
            return None


class IntegrationManager:
    """Main integration manager"""

    def __init__(self):
        self.zapier = ZapierIntegration()
        self.slack = SlackIntegration()
        self.hubspot = HubSpotIntegration()

    def broadcast_event(self, event: IntegrationEvent) -> Dict[str, bool]:
        """Broadcast event to all configured integrations"""
        results = {}

        if self.zapier.is_configured():
            results["zapier"] = self.zapier.send_event(event)

        if self.slack.is_configured():
            # Route to appropriate Slack handlers
            if event.event_type == "lead_created":
                results["slack"] = self.slack.notify_lead(event.data)
            elif event.event_type == "fault_reported":
                results["slack"] = self.slack.notify_fault_report(event.data)

        if self.hubspot.is_configured():
            if event.event_type == "lead_created":
                contact_id = event.data.get("hubspot_contact_id")
                if contact_id:
                    results["hubspot_deal"] = self.hubspot.create_deal(
                        contact_id,
                        amount=event.data.get("estimated_value", 0)
                    )
            elif event.event_type == "new_contact":
                results["hubspot_contact"] = self.hubspot.create_contact(
                    email=event.data.get("email", ""),
                    first_name=event.data.get("name", "").split(" ")[0],
                    last_name=" ".join(event.data.get("name", "").split(" ")[1:]),
                    phone=event.data.get("phone", "")
                )

        return results

    def create_lead_event(self, session_id: str, lead_data: Dict[str, Any]) -> IntegrationEvent:
        """Create a lead event"""
        return IntegrationEvent(
            event_type="lead_created",
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            data=lead_data
        )

    def create_fault_event(self, session_id: str, fault_data: Dict[str, Any]) -> IntegrationEvent:
        """Create a fault report event"""
        return IntegrationEvent(
            event_type="fault_reported",
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            data=fault_data
        )


# Singleton instance
_integration_manager = None


def get_integration_manager() -> IntegrationManager:
    """Get or create singleton IntegrationManager instance"""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = IntegrationManager()
    return _integration_manager


if __name__ == "__main__":
    print("Integration Manager Module")
    print("Configure via environment variables:")
    print("  ZAPIER_WEBHOOK_URL")
    print("  SLACK_WEBHOOK_URL")
    print("  HUBSPOT_API_KEY")
    print("  HUBSPOT_PORTAL_ID")
    print("  GOOGLE_SHEET_ID")
