# app/api/chat.py
"""
Chat API endpoint
Handles incoming chat messages with AI and rule-based responses
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging

from app.core.database import get_db
from app.services.ai_service import ai_service
from app.services.rule_engine import rule_engine
from app.services.knowledge_service import knowledge_service
from app.models.client import Client
from app.models.conversation import Conversation, Message

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    client_id: str
    session_id: str
    msg_index: Optional[int] = None
    use_ai: bool = True
    context: Optional[Dict] = None


class ChatResponse(BaseModel):
    reply: str
    intent: Optional[str] = None
    is_ai: bool = False
    is_fallback: bool = False
    tokens_used: Optional[int] = None
    suggestions: Optional[List[str]] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request_data: ChatRequest,
    req: Request,
    db: Session = Depends(get_db),
):
    """
    Main chat endpoint
    
    Flow:
    1. Validate message
    2. Try rule-based response first
    3. If fallback and AI enabled → use AI
    4. Log conversation
    5. Return response
    """
    
    # Get request metadata
    request_id = getattr(req.state, "request_id", "unknown")
    start_time = getattr(req.state, "start_time", 0)
    
    try:
        # Validate message
        message = request_data.message.strip()
        if not message:
            return ChatResponse(
                reply="Skriv gerne en besked, så hjælper jeg 😊",
                is_fallback=True,
            )
        
        if len(message) > 1000:
            return ChatResponse(
                reply="Beskeden er for lang. Hold den venligst under 1000 tegn.",
                is_fallback=True,
            )
        
        # Get client
        client = db.query(Client).filter(Client.id == request_data.client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        if not client.is_active:
            raise HTTPException(status_code=403, detail="Client is not active")
        
        # Get or create conversation
        conversation = db.query(Conversation).filter(
            Conversation.session_id == request_data.session_id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                client_id=request_data.client_id,
                session_id=request_data.session_id,
            )
            db.add(conversation)
            db.commit()
        
        # Get conversation history
        previous_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc()).limit(10).all()
        
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(previous_messages)
        ]
        
        # 1. Try rule-based response first
        rule_response = rule_engine.get_response(message, request_data.client_id)
        
        response_data = None
        
        if not rule_response.get("is_fallback"):
            # Rule-based response succeeded
            response_data = rule_response
            logger.info(
                "Rule-based response",
                extra={
                    "request_id": request_id,
                    "client_id": request_data.client_id,
                    "intent": rule_response.get("intent"),
                },
            )
        
        # 2. Use AI if fallback and enabled
        elif request_data.use_ai and client.use_ai:
            # Check AI rate limit
            if not await ai_service.check_rate_limit(request_data.client_id, db):
                return ChatResponse(
                    reply="Du har nået grænsen for AI-forespørgsler i dag. En medarbejder vil kontakte dig snart.",
                    is_fallback=True,
                )
            
            # Get knowledge base
            knowledge_base = await knowledge_service.get_knowledge_texts(
                request_data.client_id,
                db,
            )
            
            # Get AI response
            response_data = await ai_service.get_response(
                message=message,
                client_id=request_data.client_id,
                knowledge_base=knowledge_base,
                conversation_history=conversation_history,
                client_info={
                    "company_name": client.company_name,
                    "website_url": client.website_url,
                },
            )
            
            logger.info(
                "AI response",
                extra={
                    "request_id": request_id,
                    "client_id": request_data.client_id,
                    "tokens": response_data.get("tokens_used", 0),
                },
            )
        
        # 3. Final fallback
        if not response_data:
            response_data = {
                "reply": "Jeg forstod ikke helt. Lad mig viderestille dig til en medarbejder.",
                "is_fallback": True,
                "intent": None,
            }
        
        # Save messages to database
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )
        bot_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_data["reply"],
            intent=response_data.get("intent"),
            is_ai=response_data.get("is_ai", False),
            tokens_used=response_data.get("tokens_used"),
        )
        
        db.add_all([user_message, bot_message])
        db.commit()
        
        return ChatResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Chat error: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True,
        )
        return ChatResponse(
            reply="Der opstod en fejl. Prøv igen senere.",
            is_fallback=True,
        )
