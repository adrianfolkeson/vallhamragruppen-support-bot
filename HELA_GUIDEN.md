# 📋 HELA FÖRLOPPET - Från start till bot på hemsidan

## Översikt för DIG (som säljer detta)

```
Kund fyller i formulär
      ↓
Du får config-fil
      ↓
Du lägger upp config på GitHub
      ↓
Railway deployar om automatiskt
      ↓
Kunden får en embed-kod
      ↓
Kunden klistrar in koden på sin hemsida
      ↓
KLART! Boten fungerar
```

---

## Steg för steg

### 📝 Steg 1: Kund fyller i setup wizard (2 minuter)

Kunden går till `https://din-bot-url.railway.app/setup` och fyller i:
- Företagsnamn
- Telefon/Email
- Öppettider
- FAQ
- API Key

Kunden klickar **"🚀 Skapa min bot!"** och väljer:
- **"📧 Skicka via email"** - Configfilen skickas till dig

---

### 📧 Steg 2: Du får config-filen (via email)

Du får en JSON-fil som ser ut så här:

```json
{
  "company_name": "Kundens Företag AB",
  "tenant_id": "kundens-foretag-ab",
  "phone": "0793-006638",
  "contact_email": "info@kundensforetag.se",
  "locations": "Stockholm, Göteborg",
  "business_hours": "Mån-Fre 08-17",
  "services": "Vi säljer...",
  "greeting_response": "Hej! Jag är...",
  "faq_data": [...]
}
```

---

### 📤 Steg 3: Du lägger upp config på GitHub (1 minut)

1. Gå till ditt GitHub repo: `https://github.com/adrianfolkeson/vallhamragruppen-support-bot`
2. Gå till `config/` mappen
3. Klicka "Add file" → "Create new file"
4. Namnge filen: `kundens-foretag-ab.json`
5. Klistra in config-innehållet
6. Klicka "Commit changes"

**Railway deployar OM automatiskt inom 1-2 minuter!**

---

### 🔗 Steg 4: Ge kunden embed-koden (klart!)

Ge kunden denna kod att klistra in på sin hemsida:

```html
<!-- Support Starter AI Chat Widget -->
<script src="https://din-bot-url.railway.app/widget.js"></script>
```

**Eller med anpassning:**

```html
<!-- Support Starter AI Chat Widget -->
<script>
  window.CHAT_WIDGET_API_URL = 'https://kundens-bot-url.railway.app/chat';
  window.CHAT_WIDGET_COMPANY_NAME = 'Kundens Företag AB';
</script>
<script src="https://din-bot-url.railway.app/widget.js"></script>
```

---

### 🌐 Steg 5: Kund lägger in på sin hemsida (2 minuter)

**Alternativ A - WordPress/Wix/Squarespace:**
1. Gå till "Embed Code" eller "Custom HTML" widget
2. Klistra in koden ovan
3. Spara
4. Klart!

**Alternativ B - Egen hemsida:**
1. Öppna HTML-filen (t.ex. `index.html`)
2. Klistra in koden före `</body>` taggen
3. Ladda upp filen
4. Klart!

**Alternativ C - Webflow/Shopify:**
1. Lägg till "Custom Code" element i footer
2. Klistra in koden
3. Spara och publicera

---

## ✅ Så här ser det ut för kunden

### Innan:
```
Kundens hemsida
└── Kunder måste ringa eller maila
└── Inget svar på natten
```

### Efter:
```
Kundens hemsida
└── 💬 Chat-widget i bottom-right (som Facebook Messenger)
└── Kunder kan chatta direkt
└── Botten svarar 24/7
└── Eskalering till människa vid behov
```

---

## 📱 Så här ser widgeten ut

```
┌─────────────────────────────┐
│  🤖                         │
│  Hej! Jag hjälper dig!      │
│  [ ] Skriv ett meddelande   │
└─────────────────────────────┘
       ↓ Kunden klickar
┌─────────────────────────────┐
│  🤖 Kundens Företag AI      │
│  ─────────────────────────  │
│  Hej! Vad kan jag hjälpa    │
│  till med idag?             │
│                             │
│  Kund: Hur gör jag en       │
│  felanmälan?                │
│                             │
│  🤖: Berätta vad som hänt   │
│  och var i fastigheten...   │
│                             │
│  Kund: Vattenläcka i kök!   │
│                             │
│  🤖: Vattenläcka! 💧 Stäng   │
│  av vattnet och ring...     │
└─────────────────────────────┘
```

---

## 🎯 Checklista för dig

När en ny kund köper:

| Steg | Vem | Tid |
|------|-----|-----|
| 1. Kund fyller i setup wizard | Kund | 2 min |
| 2. Du får config via email | Du | - |
| 3. Ladda upp config till GitHub | Du | 1 min |
| 4. Vänta på Railway deploy | Auto | 2 min |
| 5. Skicka embed-kod till kund | Du | 1 min |
| 6. Kund lägger in på hemsida | Kund | 2 min |
| **TOTALT** | | **~8 minuter** |

---

## 💡 Proffs-tips

### 1. Använd subdomains för kunder
Istället för `din-bot-url.railway.app`, ge kunden:
- `kund1.dinbot.se`
- `kund2.dinbot.se`
- `kund3.dinbot.se`

Detta ser mer proffsigt ut!

### 2. Vitlabeling
Byt ut "Support Starter AI" till kundens varumärke i config.

### 3. Anpassad widget-färg
Låt kunden välja widget-färg:
```html
<script>
  window.CHAT_WIDGET_COLOR = '#FF5733';  // Kundens färg
</script>
```

### 4. Multi-language
Om kunden vill ha boten på engelska:
```json
{
  "language": "en",
  "greeting_response": "Hello! I'm..."
}
```

---

## 🚀 Färdig embed-kod mall

Spara denna som en mall du kan skicka till kunder:

```
Hej [Kundnamn]!

Nu är din bot klar! 🎉

För att lägga in den på din hemsida, klistra in denna kod:

──────────────────────────────────────────
<!-- Support Starter AI Chat Widget -->
<script src="https://[DIN-BOT-URL].railway.app/widget.js"></script>
──────────────────────────────────────────

Var ska jag klistra in den?
- WordPress: Appearance → Widgets → Custom HTML
- Wix: Settings → Custom Code
- Egen webbplats: Före </body> taggen i index.html
- Shopify: Online Store → Themes → Edit code → theme.liquid

Behöver du hjälp? Svara på detta mail!

Vänligen,
[Ditt Namn]
```

---

## 📞 Support till kunder

Om kunden fastnar:

| Problem | Lösning |
|---------|---------|
| "Widget syns inte" | Kolla att koden ligger före </body> |
| "Boten svarar inte" | Kolla att API key är korrekt |
| "Fel svar på frågor" | Uppdatera FAQ i config-filen |
| "Vill ändra färg" | Lägg till CHAT_WIDGET_COLOR |

---

**Det var allt! Nu kan du sälja och deploya bots på under 10 minuter 🚀**
