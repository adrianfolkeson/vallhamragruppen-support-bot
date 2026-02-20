# 🚀 Deployment Guide - Support Starter AI

## Steg-för-steg guide för att deploya till ett företag

---

## Översikt

```
Lokalt → Docker → Cloud → Domän → Embedda på kundens hemsida
```

---

## Steg 1: Förbered Config för Kund

### 1.1 Skapa kund-specifik config

Skapa en ny config-fil för varje kund:

```bash
# Multi-tenant: lägg kundens config i tenants-mappen
cp config/config.json config/tenants/kund1.json
```

### 1.2 Redigera kundens config

Redigera `config/tenants/kund1.json`:

```json
{
  "COMPANY_NAME": "Kundens AB",
  "industry": "Fastighetsförvaltning",
  "locations": "Stockholm, Göteborg, Malmö",
  "phone": "08-123 456 78",
  "contact_email": "info@kundens.se",
  "website": "https://kundens.se",
  "business_hours": "Mån-Fre 08:00-17:00",
  "response_time": "24 timmar",

  "services": "Beskriv kundens tjänster här...",
  "pricing": "Prissättning sker individuellt...",

  "faq_data": [
    {
      "question": "Hur gör jag en felanmälan?",
      "answer": "Ring oss på {phone} eller använd formuläret...",
      "keywords": ["felanmälan", "fel", "reparation"]
    }
    // Lägg till fler FAQs...
  ],

  "anthropic_api_key": "",  # Lämna tom, sätts via env var
  "max_requests_per_minute": 60
}
```

---

## Steg 2: Docker Deployment

### 2.1 Bygg Docker image

```bash
cd support_starter
docker build -t support-bot:latest .
```

### 2.2 Testa lokalt med Docker

```bash
docker run -d \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-xxx \
  -e TENANT_ID=kund1 \
  --name support-bot \
  support-bot:latest
```

### 2.3 Tagga och pusha till registry

```bash
# För Docker Hub
docker tag support-bot:latest username/support-bot:latest
docker push username/support-bot:latest

# För GitHub Container Registry
docker tag support-bot:latest ghcr.io/username/support-bot:latest
docker push ghcr.io/username/support-bot:latest
```

---

## Steg 3: Cloud Deployment

### Alternativ A: Railway (enklast)

1. Gå till [railway.app](https://railway.app)
2. Ny projekt → Deploy from Dockerfile
3. Lägg till environment variables:
   ```
   ANTHROPIC_API_KEY=sk-ant-xxx
   TENANT_ID=kund1
   PORT=8000
   ```
4. Deploya → får du en URL: `https://support-bot.railway.app`

### Alternativ B: Render

1. Gå till [render.com](https://render.com)
2. New → Web Service
3. Connect GitHub repo eller anslut Docker image
4. Environment variables:
   ```
   ANTHROPIC_API_KEY=sk-ant-xxx
   TENANT_ID=kund1
   PORT=8000
   ```
5. Deploya → URL: `https://support-bot.onrender.com`

### Alternativ C: AWS ECS

```bash
# Pusha till ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker tag support-bot:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/support-bot:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/support-bot:latest

# Deploya via ECS console eller CLI
```

### Alternativ D: DigitalOcean App Platform

1. Pusha till GitHub
2. DigitalOcean → Apps → Create App
3. Välj repo
4. Add environment variables
5. Deploya

---

## Steg 4: Anslut Egen Domän

### 4.1 I Railway

Settings → Custom Domains → Add domain:
```
bot.kundens.se
```

### 4.2 I kundens DNS

Lägg till CNAME record:
```
Type: CNAME
Name: bot
Value: support-bot.railway.app
```

### 4.3 Vänta på SSL cert

SSL certifikat genereras automatiskt.

---

## Steg 5: Embedda Widget på Kundens Hemsida

### 5.1 Kopiera widget-filen

```bash
# Upload widget till CDN eller kundens server
cp react-widget/chat-widget.js /var/www/html/widget.js
```

### 5.2 Lägg in på kundens hemsida

Lägg till detta kodsnutt INNAN `</body>`-taggen:

```html
<!-- Support Bot Widget -->
<script>
    // Konfigurera widget
    window.CHAT_WIDGET_API_URL = 'https://bot.kundens.se/chat';
    window.CHAT_WIDGET_TENANT_ID = 'kund1';  // Valfritt
    window.CHAT_WIDGET_PRIMARY_COLOR = '#667eea';
    window.CHAT_WIDGET_COMPANY_NAME = 'Kundens AB';
    window.CHAT_WIDGET_WELCOME_MESSAGE = 'Hej! Hur kan jag hjälpa dig idag?';
</script>
<script src="https://bot.kundens.se/chat-widget.js" async></script>
```

### 5.3 Testa

Ladda kundens hemsida och verifiera att widgeten visas.

---

## Steg 6: Production Checklist

### Environment Variables

| Variable | Beskrivning | Exempel |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-xxx` |
| `TENANT_ID` | Kund ID (multi-tenant) | `kund1` |
| `PORT` | Server port | `8000` |
| `SLACK_WEBHOOK_URL` | Slack notifications | `https://hooks.slack.com/...` |
| `HUBSPOT_API_KEY` | HubSpot integration | `pat-xxx` |
| `GOOGLE_SHEET_ID` | Sheets admin | `1BxiM...` |

### Säkerhet

- [ ] API key i environment variables (aldrig i config)
- [ ] CORS konfigurerad för kundens domän
- [ ] Rate limiting aktiverat
- [ ] HTTPS aktiverat
- [ ] GDPR endpoints tillgängliga

### Monitoring

- [ ] Health check: `https://bot.kundens.se/health`
- [ ] Metrics: `https://bot.kundens.se/metrics`
- [ ] Dashboard: `https://bot.kundens.se/dashboard`

---

## Steg 7: Underhåll

### Uppdatera config

```bash
# Redigera kundens config
nano config/tenants/kund1.json

# Eller via Google Sheets admin
# Set GOOGLE_SHEET_ID env var
```

### Se logs

```bash
# Railway
railway logs

# Render
# Dashboard → Logs

# Docker
docker logs support-bot
```

### Restart

```bash
# Railway
railway up

# Render
# Automatic deploy vid git push

# Docker
docker restart support-bot
```

---

## Exempel: Full Production Config

```json
{
  "COMPANY_NAME": "Kundens Fastighets AB",
  "industry": "Fastighetsförvaltning",
  "locations": "Stockholm, Göteborg, Malmö",
  "phone": "08-123 456 78",
  "contact_email": "support@kundens.se",
  "website": "https://kundens.se",
  "business_hours": "Mån-Fre 07:00-18:00",
  "response_time": "4 timmar",

  "services": "Vi erbjuder helhetslösningar för fastighetsförvaltning...",

  "faq_data": [
    {
      "question": "Hur gör jag en felanmälan?",
      "answer": "Enklast är att ringa oss på {phone}. För akuta ärenden jour dygnet runt.",
      "keywords": ["felanmälan", "fel", "akut", "jour"]
    }
  ]
}
```

---

## Support

Vid problem:
1. Kolla logs: `https://bot.kundens.se/health`
2. Testa API: `curl -X POST https://bot.kundens.se/chat`
3. Dashboard: `https://bot.kundens.se/dashboard`

---

## Prisuppskattning för Kund

| Tjänst | Månadskostnad |
|--------|---------------|
| Cloud hosting (Railway/Render) | ~$5-20/mån |
| Anthropic Claude API | ~$10-50/mån (beroende på volym) |
| Domain | ~$10-15/år |
| **Totalt** | **~500-1000 kr/mån** |

Föreslå 2000-5000 kr/mån för setup + underhåll till kund.
