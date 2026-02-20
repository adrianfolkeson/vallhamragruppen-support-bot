"""
SUPPORT STARTER AI - CONFIG LOADER
===================================
Load configuration from JSON files for multi-tenant deployment
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class BotConfig:
    """Configuration for the bot - loaded from JSON file"""
    # Company info
    COMPANY_NAME: str = "Företag AB"
    industry: str = "Fastighetsförvaltning"
    locations: str = "Stad, Ort, Område"
    phone: str = "07X-XXX XX XX"
    contact_email: str = "info@foretag.se"
    website: str = "https://foretag.se"
    business_hours: str = "Mån-Fre 08:00-17:00"
    response_time: str = "24 timmar"

    # Services
    services: str = "Beskriv era tjänster här"

    # Pricing
    pricing: str = "Prissättning sker individuellt"

    # FAQ (short version for system prompt)
    faq_list: str = "Q: Vanlig fråga?\\nA: Svar här"

    # Policies
    refund_policy: str = "Ej tillämpligt"
    cancellation_policy: str = "Enligt avtal"

    # Style
    tone_style: str = "Professionell, vänlig"
    booking_link: str = "https://foretag.se/kontakt"
    contact_form: str = "https://foretag.se/kontakt"

    # API
    anthropic_api_key: str = ""

    # Rate limiting
    max_requests_per_minute: int = 60

    # Fault report responses (templates)
    fault_water_critical: str = "Vattenläcka! 💧 Stäng av vattnet under diskhon om möjligt. Ring jour på {phone} direkt."
    fault_lockout: str = "Utelåst? 🔑 Ring jour på {phone} nu. Vilken adress?"
    fault_general_critical: str = "Akut ärende! 🚨 Ring jour på {phone} direkt. Vad har hänt?"
    fault_water_high: str = "Inget vatten. 💧 Gäller det hela fastigheten eller bara din lägenhet? Ring {phone}."
    fault_heating_high: str = "Ingen värme. 🌡️ Kollat termostaten? Ring {phone} om det inte hjälper."
    fault_electric_high: str = "Strömproblem. ⚡ Kolla säkringsskärmet först. Ring {phone}."
    fault_general_high: str = "Viktigt ärende. Ring {phone} och berätta vad som hänt."
    fault_water_medium: str = "Vattenproblem. 💧 Läcka eller droppande kran? Var i lägenheten?"
    fault_appliance_medium: str = "Vitvaror. 🏠 Köpt av dig eller ingår i fastigheten? Ring {phone}."
    fault_noise_medium: str = "Störningar från grannar! 👂 Jag hjälper dig göra en felanmälan. För att kunna hjälpa dig bäst behöver jag:\n\n1. Beskriv vad problemet är\n2. Din adress och lägenhetsnummer\n3. Ditt telefonnummer eller e-post"
    fault_general_medium: str = "Beskriv problemet. Var i fastigheten? Är det akut eller kan vänta?"
    fault_general_low: str = "Vad gäller? 🤔 Berätta vad som hänt så hjälper jag dig göra en felanmälan. Jag behöver:\n1. Beskrivning av problemet\n2. Adress och lägenhetsnummer\n3. Dina kontaktuppgifter"

    # Local model responses (templates)
    greeting_response: str = "Hej! 👋 {company_name} här. Jag hjälper med frågor om fastigheter och förvaltning."
    contact_response: str = "Ring oss på {phone} eller mejla {email}. Vi finns i {locations}. 📍"
    hours_response: str = "{business_hours}. Akuta ärenden dygnet runt: ring jour på {phone}. ⏰"
    emergency_critical_response: str = "Akut läge! 🚨 Ring 112 först vid fara för liv. Ring sedan jour på {phone}."
    lockout_emergency_response: str = "Utelåst? 🔑 Ring jour {phone} nu. Vilken adress?"
    how_to_report_response: str = "Felanmälan: ring {phone} eller använd formulär på hemsidan. 🛠️"

    # FAQ data and knowledge chunks (optional)
    faq_data: list = None
    knowledge_chunks: list = None

    # Escalation configuration
    escalation_rules: dict = None
    escalation_triggers: dict = None

    def __post_init__(self):
        """Handle default mutable values"""
        if self.faq_data is None:
            self.faq_data = []
        if self.knowledge_chunks is None:
            self.knowledge_chunks = []
        if self.escalation_rules is None:
            self.escalation_rules = {}
        if self.escalation_triggers is None:
            self.escalation_triggers = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BotConfig':
        """Create BotConfig from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        from dataclasses import asdict
        return asdict(self)


def load_config(config_path: Optional[str] = None) -> BotConfig:
    """
    Load configuration from JSON file

    Args:
        config_path: Path to config file. If None, uses CONFIG_FILE env var or default path

    Returns:
        BotConfig instance

    Raises:
        FileNotFoundError: If config file not found
        json.JSONDecodeError: If config file is invalid JSON
    """
    if config_path is None:
        config_path = os.getenv("CONFIG_FILE", "config/config.json")

    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\\n"
            f"Create a config file or set CONFIG_FILE environment variable.\\n"
            f"See config/config.example.json for reference."
        )

    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return BotConfig.from_dict(data)


def load_config_or_default(config_path: Optional[str] = None) -> BotConfig:
    """
    Load configuration from JSON file, return default if not found

    Args:
        config_path: Path to config file

    Returns:
        BotConfig instance (default if file not found)
    """
    try:
        return load_config(config_path)
    except FileNotFoundError:
        print(f"Warning: Config file not found, using default configuration")
        return BotConfig()


# For convenience
def get_config(config_path: Optional[str] = None) -> BotConfig:
    """Get configuration - alias for load_config_or_default"""
    return load_config_or_default(config_path)


if __name__ == "__main__":
    # Test the config loader
    print("=" * 60)
    print("CONFIG LOADER - TEST")
    print("=" * 60)

    try:
        config = load_config()
        print(f"\\nLoaded config for: {config.COMPANY_NAME}")
        print(f"Phone: {config.phone}")
        print(f"Email: {config.contact_email}")
        print(f"Locations: {config.locations}")
    except FileNotFoundError as e:
        print(f"\\n{e}")
