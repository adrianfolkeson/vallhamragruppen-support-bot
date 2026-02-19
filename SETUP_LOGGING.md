# Setup Guide: Chat Logging & Integrations

This guide explains how to set up chat logging, email notifications, and Google Sheets integration for the Support Starter AI bot.

---

## 1. Chat Logging (File-based)

Chat logging is **enabled by default** and requires no setup. Conversations are automatically saved to the `chat_logs/` directory:

```
chat_logs/
├── sessions/        # Individual session JSON files
├── daily/           # Daily JSONL log files
└── exports/         # CSV exports
```

### How it works:
- Every message (user and bot) is logged automatically
- Sessions are saved when the conversation ends
- Daily logs append all conversations to a date-stamped file
- CSV exports can be generated for external analysis

---

## 2. Email Notifications

Send chat transcripts to customers and admin notifications for escalations.

### Step 1: Get SMTP credentials

You need an SMTP server. Options:
- **Gmail** (for testing): Use App Password
- **SendGrid**: Free tier available
- **Mailgun**: Free tier available
- **Your email provider**: Check their SMTP settings

### Step 2: Configure environment variables

Create a `.env` file in the project root:

```bash
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=info@vallhamragruppen.se
FROM_NAME=Vallhamragruppen

# Admin email (receives escalation notifications)
ADMIN_EMAIL=admin@vallhamragruppen.se
```

### Gmail App Password Setup:
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to "App passwords" → Generate
4. Use the 16-character password as `SMTP_PASSWORD`

### What gets sent:
1. **Customer transcripts**: When conversation ends, if customer email is known
2. **Admin notifications**: When conversations are escalated (urgency: high/critical)

---

## 3. Google Sheets Integration

Automatically log conversations to a Google Sheet for analysis and tracking.

### Step 1: Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable Google Sheets API:
   - Search "Google Sheets API"
   - Click "Enable"

### Step 2: Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Name: `support-bot-logger`
4. Click "Create and Continue"
5. Skip granting roles (not needed for Sheets)
6. Click "Done"

### Step 3: Create and Download Key

1. Click on the service account you created
2. Go to "Keys" tab → "Add Key" → "Create new key"
3. Key type: **JSON**
4. Click "Create" - this downloads a JSON file
5. Rename it to `google-credentials.json`
6. Move it to your project root (NOT in git!)

### Step 4: Install Google Libraries

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Step 5: Create Google Sheet

1. Go to https://sheets.google.com
2. Create a new sheet (e.g., "Support Bot Chat Logs")
3. Copy the **spreadsheet ID** from the URL:
   - URL: `https://docs.google.com/spreadsheets/d/1BxiM.../edit`
   - ID: `1BxiM...`

### Step 6: Share Sheet with Service Account

1. Open the credentials JSON file you downloaded
2. Find the `client_email` field (looks like: `support-bot-logger@....iam.gserviceaccount.com`)
3. In your Google Sheet, click "Share"
4. Paste the service account email
5. Give it "Editor" permission

### Step 7: Configure Environment Variables

Add to your `.env` file:

```bash
# Google Sheets Configuration
GOOGLE_SHEETS_ID=1BxiM...your-spreadsheet-id
GOOGLE_SHEETS_CREDENTIALS=./google-credentials.json
```

### Step 8: Initialize Sheet (One-time)

Run this once to create the sheet with headers:

```python
from chat_logger import get_log_manager

log_mgr = get_log_manager()
log_mgr.sheets.create_sheet_if_not_exists()
```

### What gets logged:
| Field | Description |
|-------|-------------|
| Session ID | Unique conversation identifier |
| Starttid | When conversation started |
| Kundnamn | Customer name (if collected) |
| Email | Customer email (if collected) |
| Telefon | Customer phone (if collected) |
| Status | active/resolved/escalated |
| Eskalerad | Yes/No |
| Antal meddelanden | Message count |
| Senaste meddelande | Last message preview |

---

## 4. Example .env File

Copy this to `.env` and fill in your values:

```bash
# ============================================
# EMAIL CONFIGURATION
# ============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=info@vallhamragruppen.se
FROM_NAME=Vallhamragruppen
ADMIN_EMAIL=admin@vallhamragruppen.se

# ============================================
# GOOGLE SHEETS CONFIGURATION
# ============================================
GOOGLE_SHEETS_ID=your-spreadsheet-id-here
GOOGLE_SHEETS_CREDENTIALS=./google-credentials.json

# ============================================
# ANTHROPIC API (Optional)
# ============================================
ANTHROPIC_API_KEY=your-anthropic-api-key
```

---

## 5. Testing Your Setup

### Test Email:
```python
from chat_logger import get_log_manager

log_mgr = get_log_manager()
print(f"Email configured: {log_mgr.email.is_configured()}")
```

### Test Google Sheets:
```python
from chat_logger import get_log_manager

log_mgr = get_log_manager()
print(f"Sheets configured: {log_mgr.sheets.is_configured()}")
```

### Test Full Logging:
```python
from chat_logger import get_log_manager

log_mgr = get_log_manager()

# Start conversation
conv = log_mgr.start_conversation("test_session", {
    "name": "Test Testsson",
    "email": "test@example.com"
})

# Add messages
log_mgr.log_message("test_session", "user", "Hej, jag har en fråga")
log_mgr.log_message("test_session", "assistant", "Vad kan jag hjälpa med?")

# End conversation (sends email, logs to sheets)
log_mgr.end_conversation("test_session", status="resolved")
```

---

## 6. Troubleshooting

### Email not sending:
- Check SMTP credentials are correct
- For Gmail, make sure you're using an **App Password**, not your regular password
- Check `SMTP_PORT` (587 for TLS, 465 for SSL)

### Google Sheets not working:
- Verify credentials file path is correct
- Check that sheet is shared with the service account email
- Make sure Google Sheets API is enabled in your project

### Logs not appearing:
- Check that `chat_logs/` directory exists and is writable
- Check console output for error messages

---

## 7. Production Deployment

For production, consider:

1. **Use a proper transactional email service** (SendGrid, Mailgun, AWS SES)
2. **Store credentials securely** (use environment variables, never commit credentials)
3. **Set up rate limiting** to avoid hitting API quotas
4. **Monitor error logs** for failed email/sheet operations
5. **Add `.env` and `google-credentials.json` to `.gitignore`**

Add to `.gitignore`:
```
.env
google-credentials.json
chat_logs/
```

---

## 8. API Endpoints (for web integration)

The bot's `/chat` endpoint automatically uses the logging system. No extra code needed.

```bash
# Start the server
python bot.py

# Send a request (logging happens automatically)
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hej, jag har en fråga",
    "session_id": "session_123"
  }'
```

---

## Support

For issues or questions, contact:
- Email: info@vallhamragruppen.se
- Phone: 0793-006638
