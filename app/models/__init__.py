# app/models/__init__.py
"""
Database models
"""

from app.models.client import Client, ClientBranding
from app.models.conversation import Conversation, Message
from app.models.lead import Lead
from app.models.handover import Handover
from app.models.knowledge import KnowledgeBase

__all__ = [
    "Client",
    "ClientBranding",
    "Conversation",
    "Message",
    "Lead",
    "Handover",
    "KnowledgeBase",
]
