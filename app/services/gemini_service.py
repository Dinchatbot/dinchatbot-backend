# app/services/gemini_service.py
"""
Google Gemini Integration (GRATIS!)
Erstatter OpenAI - meget billigere (gratis op til 60 req/min)
"""

import google.generativeai as genai
from typing import List, Dict, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    """Google Gemini service for chat responses - GRATIS!"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Gemini Pro 1.5 - Gratis!
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Generation config
        self.generation_config = {
            'temperature': 0.7,
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 500,
        }
    
    async def get_response(
        self,
        message: str,
        client_id: str,
        knowledge_base: List[str] = None,
        conversation_history: List[Dict] = None,
        client_info: Dict = None,
    ) -> Dict:
        """
        Get AI response using Google Gemini
        
        Args:
            message: User's message
            client_id: Client identifier
            knowledge_base: List of knowledge base texts
            conversation_history: Previous messages
            client_info: Client company info
            
        Returns:
            Dict with reply, tokens_used, etc.
        """
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(
                client_id=client_id,
                knowledge_base=knowledge_base or [],
                client_info=client_info or {},
            )
            
            # Build conversation for Gemini
            chat_history = []
            
            # Add conversation history (last 5 messages)
            if conversation_history:
                for msg in conversation_history[-5:]:
                    role = "model" if msg.get("role") == "assistant" else "user"
                    chat_history.append({
                        "role": role,
                        "parts": [msg.get("content", "")],
                    })
            
            # Start chat session
            chat = self.model.start_chat(history=chat_history)
            
            # Build full prompt with system instructions
            full_prompt = f"""{system_prompt}

USER SPØRGSMÅL:
{message}

SVAR (HUSK: Max 100 ord, på dansk):"""
            
            # Generate response
            response = chat.send_message(
                full_prompt,
                generation_config=self.generation_config,
            )
            
            reply = response.text
            
            # Gemini doesn't provide exact token counts, estimate
            tokens_used = len(full_prompt.split()) + len(reply.split())
            
            logger.info(
                f"Gemini response generated",
                extra={
                    "client_id": client_id,
                    "estimated_tokens": tokens_used,
                    "model": "gemini-1.5-pro",
                },
            )
            
            return {
                "reply": reply,
                "is_ai": True,
                "is_fallback": False,
                "intent": "ai_response",
                "tokens_used": tokens_used,
                "model": "gemini-1.5-pro",
                "cost": 0.0,  # GRATIS! 🎉
            }
            
        except Exception as e:
            logger.error(
                f"Gemini service error: {str(e)}",
                extra={"client_id": client_id},
                exc_info=True,
            )
            
            return {
                "reply": "Der opstod en fejl med AI-tjenesten. Lad mig viderestille dig til en medarbejder.",
                "is_ai": False,
                "is_fallback": True,
                "intent": None,
                "error": str(e),
            }
    
    def _build_system_prompt(
        self,
        client_id: str,
        knowledge_base: List[str],
        client_info: Dict,
    ) -> str:
        """Build system prompt with context"""
        
        company_name = client_info.get("company_name", client_id)
        website = client_info.get("website_url", "")
        
        # Base instructions
        prompt = f"""Du er en professionel kundeservice chatbot for {company_name}.

DINE OPGAVER:
1. Svar venligt, præcist og professionelt på kundens spørgsmål
2. Brug ALTID informationen fra videnbasen nedenfor
3. Hvis du ikke ved svaret med sikkerhed, vær ærlig og tilbyd at viderestille til en medarbejder
4. Hold svar korte og præcise (max 100 ord)
5. Skriv ALTID på dansk
6. Vær hjælpsom men aldrig opdigtende

REGLER:
- Giv ALDRIG juridisk, medicinsk eller finansiel rådgivning
- Fortæl ALDRIG om priser du ikke kender med sikkerhed
- Lov ALDRIG noget på vegne af virksomheden
- Hvis usikker: "Lad mig viderestille dig til en medarbejder som kan hjælpe bedre"

TONE:
- Professionel men venlig
- Dansk sprogbrug
- Kort og konkret
"""

        # Add knowledge base
        if knowledge_base:
            prompt += "\n\nVIDENBASE (brug denne information til at svare):\n"
            prompt += "\n\n".join([
                f"--- Side {i+1} ---\n{kb}" 
                for i, kb in enumerate(knowledge_base[:10])  # Max 10 sources
            ])
        
        # Add company info
        if website:
            prompt += f"\n\nVIRKSOMHEDENS HJEMMESIDE: {website}"
        
        prompt += "\n\nHusk: Hvis du ikke kan svare præcist baseret på videnbasen, vær ærlig og tilbyd at viderestille."
        
        return prompt
    
    def estimate_cost(self, tokens: int) -> float:
        """
        Estimate cost in DKK for tokens used
        
        Gemini Pro 1.5 pricing:
        - GRATIS op til 60 requests/minut!
        - $0 per 1k tokens (free tier)
        """
        return 0.0  # GRATIS! 🎉
    
    async def check_rate_limit(self, client_id: str, db) -> bool:
        """
        Check if client has exceeded AI rate limit
        
        Gemini har højere free tier limits end OpenAI!
        - 60 requests/minut (vs OpenAI's 500/min men dyrere)
        - Helt gratis!
        """
        from app.models.client import Client
        
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if not client:
            return False
        
        # Gemini er gratis, men vi beholder rate limiting
        # for at beskytte mod misbrug
        if client.ai_requests_today >= client.ai_requests_limit:
            logger.warning(
                f"AI rate limit exceeded",
                extra={
                    "client_id": client_id,
                    "requests": client.ai_requests_today,
                    "limit": client.ai_requests_limit,
                },
            )
            return False
        
        # Increment counter
        client.ai_requests_today += 1
        db.commit()
        
        return True


# Global instance
gemini_service = GeminiService()
