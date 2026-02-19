"""
SUPPORT STARTER AI - FASTAPI SERVER
====================================
REST API server for the AI bot with webhooks and logging
"""

import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any
import uvicorn

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import SupportStarterBot, BotConfig, create_bot
from schemas import BotResponse, EscalationPacket, LeadData
from webhooks import WebhookManager, configure_from_env


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: str
    conversation_history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    reply: str
    intent: str
    confidence: float
    sentiment: str
    lead_score: int
    escalate: bool
    action: str
    suggested_responses: Optional[List[str]] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


# Initialize FastAPI app
app = FastAPI(
    title="Support Starter AI",
    description="AI customer support bot with intelligent routing and escalation",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global bot instance
bot_instance: Optional[SupportStarterBot] = None
webhook_manager: Optional[WebhookManager] = None


def get_bot() -> SupportStarterBot:
    """Get or create bot instance"""
    global bot_instance
    if bot_instance is None:
        # Create bot with config from environment
        config = BotConfig(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            COMPANY_NAME=os.getenv("COMPANY_NAME", "Vallhamragruppen AB")
        )
        bot_instance = SupportStarterBot(config)
    return bot_instance


def get_webhooks() -> WebhookManager:
    """Get or create webhook manager"""
    global webhook_manager
    if webhook_manager is None:
        webhook_manager = configure_from_env()
    return webhook_manager


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Support Starter AI",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "metrics": "/metrics",
            "webhooks": "/webhooks"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="2.0.0"
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Main chat endpoint

    Processes a user message and returns a structured response with:
    - AI-generated reply
    - Intent classification
    - Sentiment analysis
    - Lead score
    - Escalation flag
    - Suggested actions
    """
    try:
        bot = get_bot()
        webhooks = get_webhooks()

        # Process the message
        response = bot.process_message(
            message=request.message,
            session_id=request.session_id,
            conversation_history=request.conversation_history
        )

        # Log conversation
        webhooks.log_conversation(
            session_id=request.session_id,
            messages=[{"role": "user", "content": request.message},
                     {"role": "assistant", "content": response.reply}],
            metadata={
                "intent": response.intent,
                "sentiment": response.sentiment,
                "lead_score": response.lead_score
            }
        )

        # Handle escalation in background
        if response.escalate and response.escalation_summary:
            background_tasks.add_task(
                handle_escalation_background,
                request.session_id,
                response
            )

        # Handle high lead in background
        if response.lead_score >= 4:
            background_tasks.add_task(
                handle_lead_background,
                request.session_id,
                response
            )

        return ChatResponse(
            reply=response.reply,
            intent=response.intent,
            confidence=response.confidence,
            sentiment=response.sentiment,
            lead_score=response.lead_score,
            escalate=response.escalate,
            action=response.action,
            suggested_responses=response.suggested_responses
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhooks/test")
async def test_webhook(background_tasks: BackgroundTasks):
    """Test webhook configuration"""
    background_tasks.add_task(send_test_notification)
    return {"status": "Test notification sent"}


@app.get("/metrics")
async def metrics():
    """Get metrics report"""
    bot = get_bot()
    return bot.get_metrics_report()


@app.post("/reset")
async def reset_session(session_id: str):
    """Reset a conversation session"""
    bot = get_bot()
    if session_id in bot.memory.sessions:
        del bot.memory.sessions[session_id]
    return {"status": "Session reset"}


# Background task handlers
def handle_escalation_background(session_id: str, response: BotResponse):
    """Handle escalation in background"""
    try:
        bot = get_bot()
        webhooks = get_webhooks()

        session = bot.memory.sessions.get(session_id)
        if not session:
            return

        # Create escalation packet
        from escalation import EscalationEngine, EscalationReason
        escalation_engine = EscalationEngine()

        escalation_packet = escalation_engine.create_escalation_packet(
            {
                "conversation_id": session_id,
                "current_intent": response.intent,
                "current_sentiment": response.sentiment,
                "lead_score": response.lead_score,
                "customer_name": session.memory.get("customer_name", {}).get("value"),
                "customer_email": session.memory.get("customer_email", {}).get("value"),
                "message_count": len(session.messages),
                "messages": session.messages
            },
            EscalationReason.TECHNICAL_ISSUE  # Determine from context
        )

        # Send notifications
        webhooks.notify_escalation(escalation_packet)

    except Exception as e:
        print(f"Error in escalation background task: {e}")


def handle_lead_background(session_id: str, response: BotResponse):
    """Handle high lead in background"""
    try:
        bot = get_bot()
        webhooks = get_webhooks()

        session = bot.memory.sessions.get(session_id)
        if not session:
            return

        # Create lead data
        from schemas import LeadData, ConversionStage
        lead_data = LeadData(
            conversation_id=session_id,
            lead_score=response.lead_score,
            lead_stage=ConversionStage.READY if response.lead_score >= 5 else ConversionStage.CONSIDERING,
            triggered_signals=[response.intent],
            email=session.memory.get("customer_email", {}).get("value"),
            name=session.memory.get("customer_name", {}).get("value"),
            company=session.memory.get("customer_company", {}).get("value"),
            interested_services=[response.intent] if response.intent else [],
            suggested_action="Kontakta kunden" if response.lead_score >= 4 else None,
            suggested_cta="Boka möte" if response.lead_score >= 4 else None
        )

        # Send notifications
        webhooks.notify_lead(lead_data)

    except Exception as e:
        print(f"Error in lead background task: {e}")


def send_test_notification():
    """Send a test webhook notification"""
    try:
        webhooks = get_webhooks()

        # Create test escalation
        from escalation import EscalationContext, EscalationPriority, EscalationReason
        test_escalation = EscalationContext(
            escalation_id=f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            conversation_id="test_conversation",
            timestamp=datetime.now().isoformat(),
            priority=EscalationPriority.MEDIUM,
            reason=EscalationReason.TECHNICAL_ISSUE,
            summary="Test escalation from webhook system",
            customer_issue="This is a test issue",
            detected_intent="test",
            customer_sentiment="neutral",
            lead_score=2
        )

        webhooks.notify_escalation(test_escalation)

    except Exception as e:
        print(f"Error sending test notification: {e}")


# Run server
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║         SUPPORT STARTER AI - SERVER                      ║
    ║         Version 2.0.0                                    ║
    ║                                                          ║
    ║         Starting server on http://localhost:8000         ║
    ║                                                          ║
    ║         API Docs: http://localhost:8000/docs             ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  WARNING: ANTHROPIC_API_KEY not set. Bot will use fallback responses.")

    uvicorn.run(app, host="0.0.0.0", port=8000)
