# Support Starter AI v2.0

En komplett AI-kundsupportlösning med intelligent routing, lead-scoring och eskalering. Byggd för Vallhamragruppen AB.

## Features

### 1️⃣ Intelligent Router (Intent + Confidence Engine)
- Klassificerar användarens intent med confidence score
- Detekterar sentiment (positiv, neutral, frustrated, angry)
- Lead scoring 1-5 baserat på köpsignaler
- Automatisk eskaleringsbeslut

### 2️⃣ Strukturerad JSON Output
Alla svar returneras som strukturerad JSON:
```json
{
  "reply": "Här är ditt svar...",
  "action": "escalate|book_call|collect_info|none",
  "intent": "pricing_question",
  "confidence": 0.92,
  "sentiment": "neutral",
  "lead_score": 3
}
```

### 3️⃣ RAG (Retrieval Augmented Generation)
- Kunskapsbas med FAQ och företagsinfo
- Hämtar relevant kontext för varje fråga
- Uppdaterbar utan att ändra prompten

### 4️⃣ Konversationsminne
- Kommer ihåg kundens namn och preferenser
- Spårar köpsignaler över hela konversationen
- Personliga svar baserat på historik

### 5️⃣ Lead Scoring Engine
- Automatisk poängsättning 1-5
- Trigger-phrases för köpintresse
- Notifieringar vid high leads

### 6️⃣ Smart Eskalering
- Full kontext till mänskliga agenter
- AI-genererad sammanfattning
- Prioriteringslogik

### 7️⃣ Säkerhet
- Anti-prompt-injection filter
- Rate limiting
- Validering av svar

### 8️⃣ Proaktiv Support
- Inaktivitetsdetektering
- Mikro-konversions-steg
- Smarta CTAs

### 9️⃣ Metrics Engine
- Spårar alla konversationer
- Escalation rate, conversion rate
- Top frågor och köpsignaler

### 🔝 Webhooks & Notiser
- Email-notiser vid eskalering
- Slack-integration
- Automatisk loggning

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy .env file and configure
cp .env.example .env

# Set your Anthropic API key in .env
```

## Usage

### Quick Start

```python
from bot import create_bot

# Create bot instance
bot = create_bot(anthropic_api_key="your-key-here")

# Process a message
response = bot.process_message(
    message="Hur gör jag en felanmälan?",
    session_id="user_123"
)

print(response.reply)
print(f"Intent: {response.intent}, Lead Score: {response.lead_score}")
```

### Start Server

```bash
# Start the API server
python server.py

# Server runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Open Demo

```bash
# Open demo.html in browser
open demo.html
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/chat` | POST | Main chat endpoint |
| `/metrics` | GET | Metrics report |
| `/webhooks/test` | POST | Test webhooks |

## Configuration

Edit `.env`:

```env
# Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-...

# Company Info
COMPANY_NAME=Vallhamragruppen AB
PHONE=0793-006638
CONTACT_EMAIL=info@vallhamragruppen.se

# Email Notifications
EMAIL_ENABLED=true
EMAIL_TO=notifications@vallhamragruppen.se
EMAIL_FROM=noreply@vallhamragruppen.se
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Slack
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

## File Structure

```
support_starter/
├── bot.py              # Main bot system
├── router.py           # Intent classifier
├── schemas.py          # Response schemas
├── rag.py              # Knowledge base (RAG)
├── memory.py           # Conversation memory
├── security.py         # Security & rate limiting
├── proactive.py        # Proactive support
├── metrics.py          # Metrics engine
├── escalation.py       # Escalation system
├── webhooks.py         # Notifications & logging
├── server.py           # FastAPI server
├── demo.html           # Web demo
├── SUPPORT_STARTER_V2.md   # System prompt
├── .env                # Configuration
└── requirements.txt    # Dependencies
```

## Demo

1. Open `demo.html` in your browser
2. Try these questions:
   - "Hur gör jag en felanmälan?"
   - "Vad kostar er förvaltning?"
   - "Jag vill boka ett möte"
   - "Det här fungerar inte alls!"

## License

MIT License - Feel free to use and modify!

---

**Support Starter AI v2.0** - Built for Vallhamragruppen AB
