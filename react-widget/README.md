# REACT CHAT WIDGET - INSTALLATION
# ====================================

## Quick Setup (Embed on Any Website)

Add this code to your website's HTML before the closing `</body>` tag:

```html
<!-- Chat Widget -->
<script>
    // Optional: Customize these settings
    window.CHAT_WIDGET_API_URL = 'https://your-api.com/chat';
    window.CHAT_WIDGET_TENANT_ID = 'your-tenant-id';  // Optional
    window.CHAT_WIDGET_PRIMARY_COLOR = '#667eea';  // Your brand color
    window.CHAT_WIDGET_COMPANY_NAME = 'Your Company';
    window.CHAT_WIDGET_WELCOME_MESSAGE = 'Hej! Hur kan jag hjälpa dig idag?';
</script>
<script src="https://your-cdn.com/chat-widget.js" async></script>
```

## Local Testing

```html
<!DOCTYPE html>
<html>
<head>
    <title>Chat Widget Test</title>
</head>
<body>
    <h1>My Website</h1>
    <p>This is my awesome website.</p>

    <!-- Chat Widget -->
    <script>
        window.CHAT_WIDGET_API_URL = 'http://localhost:8001/chat';
        window.CHAT_WIDGET_COMPANY_NAME = 'Vallhamragruppen';
    </script>
    <script src="./react-widget/chat-widget.js"></script>
</body>
</html>
```

## Features

- ✅ Fully responsive (mobile-friendly)
- ✅ No framework dependencies (vanilla JS)
- ✅ Customizable colors and branding
- ✅ Typing indicators
- ✅ Suggested actions
- ✅ Fallback responses when API unavailable
- ✅ Session-based conversations
- ✅ Multi-tenant support

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `CHAT_WIDGET_API_URL` | `http://localhost:8001/chat` | Bot API endpoint |
| `CHAT_WIDGET_TENANT_ID` | `null` | Tenant ID for multi-tenant |
| `CHAT_WIDGET_PRIMARY_COLOR` | `#667eea` | Brand color |
| `CHAT_WIDGET_COMPANY_NAME` | `Vallhamragruppen` | Company name |
| `CHAT_WIDGET_WELCOME_MESSAGE` | `Hej! Hur kan jag...` | Welcome message |
| `CHAT_WIDGET_POSITION` | `bottom-right` | Button position |

## CDN Deployment

1. Upload `chat-widget.js` to your CDN or static file host
2. Reference it in the script tag
3. Optionally minify for production:

```bash
# Minify with terser
npx terser chat-widget.js -o chat-widget.min.js
```
