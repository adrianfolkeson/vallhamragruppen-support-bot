"""
Support Starter AI - Prompt Generator

This module loads the SUPPORT_STARTER.md template and dynamically
injects company-specific configuration to create a customized system prompt.
"""

from pathlib import Path
from typing import Dict, Any


def generate_prompt(config: Dict[str, Any]) -> str:
    """
    Generate a customized Support Starter system prompt by injecting
    company configuration into the template.

    Args:
        config: Dictionary containing company-specific values with the following keys:
            - COMPANY_NAME (str): Name of the company
            - industry (str): Industry/sector
            - services (str): Description of services offered
            - pricing (str): Pricing information
            - faq_list (str): FAQ entries
            - business_hours (str): Business operating hours
            - refund_policy (str): Refund policy details
            - contact_email (str): Support contact email
            - booking_link (str): Link for booking calls/appointments
            - tone_style (str): Brand tone/style guidelines
            - response_time (str): Expected support response time

    Returns:
        str: The fully customized system prompt with all placeholders replaced.

    Example:
        >>> config = {
        ...     "COMPANY_NAME": "Acme Corp",
        ...     "industry": "SaaS",
        ...     "services": "Project management software",
        ...     "pricing": "$29/month basic, $99/month pro",
        ...     "faq_list": "Q: How do I cancel? A: Go to settings...",
        ...     "business_hours": "9AM-5PM EST, Mon-Fri",
        ...     "refund_policy": "30-day money-back guarantee",
        ...     "contact_email": "support@acme.com",
        ...     "booking_link": "https://acme.com/book",
        ...     "tone_style": "Professional, friendly, direct",
        ...     "response_time": "24 hours"
        ... }
        >>> prompt = generate_prompt(config)
    """
    # Get the template file path
    template_path = Path(__file__).parent / "SUPPORT_STARTER.md"

    # Read the template
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Replace all placeholders with config values
    prompt = template
    for key, value in config.items():
        placeholder = f"{{{key}}}"
        prompt = prompt.replace(placeholder, str(value))

    return prompt


# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    example_config = {
        "COMPANY_NAME": "Acme Corporation",
        "industry": "B2B SaaS - Project Management",
        "services": "Team collaboration, task tracking, time reporting, and project analytics.",
        "pricing": "Starter: $29/month, Professional: $99/month, Enterprise: Custom pricing.",
        "faq_list": """
        Q: How do I cancel my subscription?
        A: Go to Settings > Billing > Cancel Subscription.

        Q: Do you offer a free trial?
        A: Yes, 14-day free trial on all plans.

        Q: Can I upgrade or downgrade anytime?
        A: Yes, changes take effect immediately.
        """,
        "business_hours": "Monday-Friday, 9:00 AM - 6:00 PM EST",
        "refund_policy": "30-day money-back guarantee for all new subscriptions.",
        "contact_email": "support@acmecorp.com",
        "booking_link": "https://acmecorp.com/demo",
        "tone_style": "Professional, friendly, direct, no emojis",
        "response_time": "within 24 hours"
    }

    # Generate and print the prompt
    generated_prompt = generate_prompt(example_config)
    print(generated_prompt)
