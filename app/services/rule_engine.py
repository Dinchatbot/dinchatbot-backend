# app/services/rule_engine.py
"""
Rule-based response engine
Matches user messages to intents using keywords
"""

import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class RuleEngine:
    """Simple rule-based intent matching"""
    
    def __init__(self):
        # Intent definitions with Danish keywords
        self.intents = [
            {
                "name": "greeting",
                "keywords": [
                    "hej", "goddag", "hello", "hejsa", "halløj", "hey",
                    "godmorgen", "godaften", "hi", "davs", "dav",
                ],
                "response_template": "Hej! Hvordan kan jeg hjælpe dig i dag?",
                "priority": 1,
            },
            {
                "name": "opening_hours",
                "keywords": [
                    "åbningstid", "åbningstider", "åbent", "lukket", "åbner", "lukker",
                    "hvornår åbner", "hvornår lukker", "åben", "lukke",
                    "opening", "hours", "åbent i dag",
                ],
                "response_template": "Vi har åbent mandag-fredag kl. 09:00–17:00, weekend 10:00-14:00.",
                "priority": 2,
            },
            {
                "name": "prices",
                "keywords": [
                    "pris", "priser", "koster", "honorar", "tilbud",
                    "hvad koster", "prisoverslag", "betaling", "betale",
                    "kr", "kroner", "betale", "pris på",
                ],
                "response_template": "Priser afhænger af den konkrete ydelse. Kontakt os gerne for et skræddersyet tilbud.",
                "priority": 2,
            },
            {
                "name": "booking",
                "keywords": [
                    "book", "booking", "bestil", "aftale", "reservation",
                    "tid", "book en tid", "reservere", "time", "bestille",
                ],
                "response_template": "Du kan booke en tid via vores hjemmeside eller ringe til os.",
                "priority": 2,
            },
            {
                "name": "contact",
                "keywords": [
                    "kontakt", "telefon", "email", "mail", "nummer", "ring",
                    "tlf", "ringe", "kontakte", "få fat i",
                ],
                "response_template": "Du kan kontakte os på telefon +45 12 34 56 78 eller via email kontakt@example.dk.",
                "priority": 2,
            },
            {
                "name": "location",
                "keywords": [
                    "adresse", "lokation", "finde jer", "hvor ligger",
                    "parkering", "adresse", "beliggenhed", "hvor er",
                    "placering", "hvordan finder jeg",
                ],
                "response_template": "Vi holder til på Eksempelvej 12, 1234 By. Der er gratis parkering ved bygningen.",
                "priority": 2,
            },
            {
                "name": "services",
                "keywords": [
                    "ydelse", "ydelser", "service", "services", "tilbud",
                    "laver i", "kan i", "gør i", "hvad laver",
                ],
                "response_template": "Vi tilbyder [indsæt jeres ydelser]. Kontakt os for mere information om en specifik ydelse.",
                "priority": 2,
            },
            {
                "name": "shipping",
                "keywords": [
                    "forsendelse", "levering", "fragt", "leveringstid",
                    "track", "tracking", "sendelse", "levere",
                ],
                "response_template": "Vi leverer typisk inden for 1–3 hverdage. Du modtager tracking når pakken er afsendt.",
                "priority": 2,
            },
            {
                "name": "returns",
                "keywords": [
                    "returnering", "retur", "bytte", "refusion", "fortryd",
                    "returnere", "ombytning", "penge retur",
                ],
                "response_template": "Du har 14 dages returret. Kontakt os, så guider vi dig gennem processen.",
                "priority": 2,
            },
            {
                "name": "order_status",
                "keywords": [
                    "ordre", "ordrenummer", "min ordre", "ordrestatus",
                    "bestilling", "min bestilling", "status", "hvor er",
                ],
                "response_template": "Send gerne dit ordrenummer, så kan vi hjælpe dig med at finde din ordre.",
                "priority": 2,
            },
            {
                "name": "payments",
                "keywords": [
                    "betaling", "betalingsmetoder", "kort", "mobilepay",
                    "faktura", "betale", "betalingsmulighed", "betale med",
                ],
                "response_template": "Vi tager imod kortbetaling, MobilePay og faktura.",
                "priority": 2,
            },
            {
                "name": "goodbye",
                "keywords": [
                    "farvel", "hej hej", "tak", "tak for hjælpen",
                    "bye", "goodbye", "ses", "god dag",
                ],
                "response_template": "Tak fordi du skrev! Kontakt os gerne igen hvis du har flere spørgsmål.",
                "priority": 1,
            },
            {
                "name": "help",
                "keywords": [
                    "hjælp", "hjælpe", "support", "kundeservice",
                    "assistance", "problem", "issue",
                ],
                "response_template": "Jeg er her for at hjælpe! Hvad kan jeg gøre for dig?",
                "priority": 2,
            },
            {
                "name": "human_support",
                "keywords": [
                    "menneske", "medarbejder", "tale med", "rigtig person",
                    "agent", "support", "kundeservice", "ikke robot",
                ],
                "response_template": "Selvfølgelig! Du kan kontakte vores kundeservice på telefon +45 12 34 56 78 eller email kontakt@example.dk.",
                "priority": 3,
            },
        ]
        
        # Sort by priority (higher priority first)
        self.intents.sort(key=lambda x: x.get("priority", 0), reverse=True)
    
    def get_response(self, message: str, client_id: str = "default") -> Dict:
        """
        Match message to intent and return response
        
        Args:
            message: User's message
            client_id: Client identifier (for future customization)
            
        Returns:
            Dict with reply, intent, is_fallback
        """
        if not message:
            return {
                "reply": "Skriv gerne en besked, så hjælper jeg 😊",
                "intent": None,
                "is_fallback": True,
            }
        
        # Normalize message
        normalized = self._normalize(message)
        
        # Try to match intent
        matched_intent = self._match_intent(normalized)
        
        if matched_intent:
            return {
                "reply": matched_intent["response_template"],
                "intent": matched_intent["name"],
                "is_fallback": False,
            }
        
        # Fallback response
        return {
            "reply": "Jeg forstod ikke helt. Kan du omformulere, eller vil du gerne tale med en medarbejder?",
            "intent": None,
            "is_fallback": True,
        }
    
    def _normalize(self, text: str) -> str:
        """Normalize text for matching"""
        # Lowercase
        text = text.lower()
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _match_intent(self, normalized_message: str) -> Optional[Dict]:
        """
        Match normalized message to intent
        
        Returns intent dict if match found, None otherwise
        """
        for intent in self.intents:
            for keyword in intent["keywords"]:
                # Check if keyword is in message (whole word match)
                keyword_pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(keyword_pattern, normalized_message):
                    logger.debug(
                        f"Intent matched: {intent['name']} (keyword: {keyword})",
                        extra={"message": normalized_message[:50]},
                    )
                    return intent
        
        return None
    
    def add_custom_intent(self, client_id: str, intent_data: Dict):
        """
        Add custom intent for specific client
        (Future feature - for now, modify intents list directly)
        """
        # TODO: Implement per-client custom intents
        pass
    
    def get_all_intents(self) -> List[Dict]:
        """Get all defined intents"""
        return self.intents


# Global instance
rule_engine = RuleEngine()
