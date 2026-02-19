# Config System Guide

The Support Starter AI bot now uses a **config-file based system** that makes it easy to customize the bot for different customers without modifying any Python code.

## Quick Start

1. **Copy the template config:**
   ```bash
   cp config/config.example.json config/config.json
   ```

2. **Edit `config/config.json` with your company data**

3. **Run the bot:**
   ```bash
   python bot.py
   ```

## Configuration Structure

The config file contains:

- **Company Info**: Name, phone, email, website, locations, business hours
- **Services**: Description of what your company offers
- **Pricing**: How pricing works
- **FAQ Data**: All your FAQ entries with placeholders like `{phone}` and `{email}`
- **Knowledge Chunks**: General knowledge about your industry
- **Response Templates**: Pre-configured responses for common scenarios

## Placeholders

Use these placeholders in your FAQ answers and knowledge chunks:

- `{COMPANY_NAME}` - Company name
- `{phone}` - Phone number
- `{email}` - Contact email
- `{locations}` - Service locations
- `{website}` - Website URL
- `{business_hours}` - Business hours

## Multi-Customer Deployment

### Option 1: Separate Config Files

For each customer, create a config file:

```
config/
├── vallhamra.json
├── kund2.json
└── kund3.json
```

Run the bot with specific config:

```bash
export CONFIG_FILE=config/kund2.json
python bot.py
```

Or in Python:

```python
from bot import SupportStarterBot
from config_loader import load_config

config = load_config("config/kund2.json")
bot = SupportStarterBot(config)
```

### Option 2: Cloned Deployments

For full isolation, clone the entire codebase:

```
/customers/
├── vallhamra/
│   ├── bot.py (shared code)
│   ├── config.json (customer-specific)
│   └── logs/
├── kund2/
│   ├── bot.py (shared code)
│   ├── config.json (customer-specific)
│   └── logs/
```

Each customer runs their own bot instance.

## Security

Config files are **NOT tracked in git** (see `.gitignore`). This prevents:
- Customer data from being exposed
- Contact info from being public
- Sensitive business details from leaking

Only `config/config.example.json` is tracked as a template.

## Testing Your Config

```python
from config_loader import load_config

config = load_config("config/config.json")
print(f"Company: {config.COMPANY_NAME}")
print(f"Phone: {config.phone}")
print(f"FAQ entries: {len(config.faq_data)}")
print(f"Knowledge chunks: {len(config.knowledge_chunks)}")
```
