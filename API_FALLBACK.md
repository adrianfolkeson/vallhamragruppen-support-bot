# 🛡️ API Fallback & Backup Plan

## Vad händer när Claude API ligger nere?

Systemet har **flera lager av fallbacks** för att garantera att botten alltid fungerar.

---

## Fallback Arkitektur

```
User Message
      │
      ▼
┌─────────────────────────────────────────────────────┐
│ 1. FAULT REPORTS (Alltid fungerar)                  │
│    Vattenläcka, utelåsning, elproblem →            │
│    Regelbaserade responses, inget API behövs        │
└─────────────────────────────────────────────────────┘
      │ Ej fault report?
      ▼
┌─────────────────────────────────────────────────────┐
│ 2. LOCAL MODEL (Enkla frågor)                       │
│    Hej, tack, kontakt, öppettider →                │
│    Regex-matching, inget API behövs                 │
└─────────────────────────────────────────────────────┘
      │ Komplex fråga?
      ▼
┌─────────────────────────────────────────────────────┐
│ 3. VECTOR STORE (ChromaDB)                          │
│    Semantisk sök i FAQ/knowledge base              │
│    Lokal vektordatabas, inget API behövs            │
└─────────────────────────────────────────────────────┘
      │ Ingen match?
      ▼
┌─────────────────────────────────────────────────────┐
│ 4. KEYWORD RAG (Fallback)                           │
│    Keyword-baserad sök i FAQ                       │
│    Lokal knowledge base, inget API behövs          │
└─────────────────────────────────────────────────────┘
      │ Ingen match?
      ▼
┌─────────────────────────────────────────────────────┐
│ 5. CLAUDE API (Primär AI)                           │
│    Anthropic Claude 3.5 Sonnet                     │
│    ← KRITISKA API:et                                │
└─────────────────────────────────────────────────────┘
      │ API nere?
      ▼
┌─────────────────────────────────────────────────────┐
│ 6. FALLBACK RESPONSE (Alltid fungerar)              │
│    "Ring {phone} eller mejla {email}"              │
│    Aldrig nere, alltid kontaktinfo                 │
└─────────────────────────────────────────────────────┘
```

---

## Lager-för-lager Förklaring

### Lager 1: Fault Reports (Alltid upp)
```python
# fault_reports.py - Inget API krävs
Vattenläcka → "Stäng av vattnet! Ring jour på 0793-006638"
Utelåsning → "Ring jour på 0793-006638 nu"
Elsproblem → "Kolla säkringsskärmet. Ring 0793-006638"
```

### Lager 2: Local Model (Enkla frågor)
```python
# local_model.py - Inget API krävs
"Hej!" → "Hej! Jag är Vallhamragruppens digitala kundtjänst."
"Tack!" → "Varsågod! Fler frågor - bara fråga."
"Kontakt" → "Ring 0793-006638 eller mejla info@vallhamragruppen.se"
```

### Lager 3: Vector Store (ChromaDB)
```python
# vector_store.py - Lokal vektordatabas
User: "Hur gör jag en felanmälan?"
→ Söker i ChromaDB efter semantiskt liknande frågor
→ Returnerar svar från config/faq_data
→ Inget API krävs
```

### Lager 4: Keyword RAG
```python
# rag.py - Keyword matching
User: "Vilka områden verkar ni i?"
→ Matchar keywords ["område", "verkar", "var"]
→ Returnerar: "Vi verkar främst i Johanneberg, Partille och Mölndal"
```

### Lager 5: Claude API (Primär AI)
```python
# bot.py - API call
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1500,
    ...
)
```

### Lager 6: Final Fallback (Alltid fungerar)
```python
# bot.py - Garanterat svar
"Vad gäller? Ring 0793-006638 eller info@vallhamragruppen.se"
```

---

## Testa Fallbacks

### Test 1: Utan API Key
```bash
# Starta utan API key
unset ANTHROPIC_API_KEY
python server.py

# Boten fungerar fortfarande med:
# - Fault reports
# - Local model
# - Vector store
# - Keyword RAG
# - Final fallback
```

### Test 2: Simulera API Error
```python
# I bot.py _generate_response()
try:
    response = self.client.messages.create(...)
except Exception as e:
    print(f"API Error: {e}")
    # Fall through to _get_fallback_response()
    return self._get_fallback_response(message, router_result, session)
```

---

## Uptime Garanti

| Scenario | Vad händer? | Uptime |
|----------|-------------|--------|
| Claude API nere | Fallback till local + RAG | 99.9% |
| ChromaDB nere | Fallback till keyword RAG | 99.9% |
| Allt nere | Final fallback med kontaktinfo | 100% |
| Fault reports | Alltid upp (regelbaserad) | 100% |

---

## Fallback Exempel

### Exempel 1: Felanmälan (Alltid fungerar)
```
User: "Vattenläcka i köket!"
Bot: "Vattenläcka! 💧 Stäng av vattnet under diskhon om möjligt.
      Ring jour på 0793-006638 direkt. Var i lägenheten läcker det?"
```
✅ Inget API krävs

### Exempel 2: Enkel fråga
```
User: "Hej!"
Bot: "Hej! Jag är Vallhamragruppens digitala kundtjänst.
      Hur kan jag hjälpa dig idag?"
```
✅ Inget API krävs (local model)

### Exempel 3: FAQ match
```
User: "Hur gör jag en felanmälan?"
Bot: "Berätta vad som har hänt så hjälper jag dig göra en
      felanmälan direkt. Vilken typ av problem gäller det
      och var i fastigheten?"
```
✅ Inget API krävs (vector store / keyword RAG)

### Exempel 4: Komplex fråga (API krävs)
```
User: "Jag är en familj på fyra personer, behöver 3–4 rok i
      Partille, max 13 000 kr/mån – vad har ni?"

MED API: "Jag hjälper dig hitta en lägenhet som matchar dina
          behov. Ring 0793-006638 så diskuterar vi vad som finns
          tillgängligt i Partille..."

UTAN API: "För specifika frågor om lediga lägenheter och priser,
          ring oss på 0793-006638 eller mejla
          info@vallhamragroupen.se så hjälper vi dig."
```
⚠️ Fallback ger kontaktinfo istället för intelligent svar

---

## Förbättra Fallbacks

### Lägg till fler Local Patterns
```python
# local_model.py
self.patterns.update({
    r"^pris(er|erna)?[\s ?!]*$": {
        "response": "Prissättning sker individuellt. Ring {phone} för offert.",
        "intent": "pricing",
        "lead_score": 2,
        "confidence": 0.8
    }
})
```

### Lägg till fler FAQs
```json
// config.json
{
  "faq_data": [
    {
      "question": "Hur ansöker jag om en lägenhet?",
      "answer": "Ring {phone} eller {email}. Vi ställer frågor om dina behov...",
      "keywords": ["ansöka", "ansökan", "söka", "hyra"]
    }
  ]
}
```

---

## Production Tips

### 1. Övervaka API Status
```python
# Lägg till i bot.py
def check_api_health(self) -> bool:
    """Check if Claude API is accessible"""
    try:
        self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1,
            messages=[{"role": "user", "content": "test"}]
        )
        return True
    except:
        return False
```

### 2. Alert vid API Problem
```python
# Skicka notis om API nere
if not self.check_api_health():
    # Send Slack webhook
    # Send email
    # Log error
```

### 3. Cache Frequently Asked Questions
```python
# Spara svar på vanliga frågor
faq_cache = {
    "hur gör jag en felanmälan": "Berätta vad som hänt...",
    "vilka områden verkar ni i": "Vi verkar i...",
    # ...
}
```

---

## Sammanfattning

✅ **Boten fungerar ALWAYS** - även utan Claude API
✅ **Fault reports är 100% resilient** - kritiska akuta ärenden
✅ **Enkla frågor hanteras lokalt** - hej, tack, kontakt
✅ **FAQ via vector store** - semantisk sök utan API
✅ **Final fallback** - alltid kontaktinfo tillgänglig

🎯 **Rekommendation**: Lägg till 20-30 väl formulerade FAQs i config
för att minimera beroendet av Claude API.
