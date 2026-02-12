# app/models/client.py
"""
Client and Branding models
"""

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Client(Base):
    """Client/Customer model"""
    __tablename__ = "clients"
    
    id = Column(String, primary_key=True, index=True)  # e.g., "kunde1"
    company_name = Column(String, nullable=False)
    website_url = Column(String, nullable=True)
    
    # Contact
    contact_email = Column(String, nullable=False)
    contact_phone = Column(String, nullable=True)
    notification_email = Column(String, nullable=True)
    
    # Subscription
    plan = Column(String, default="basic")  # basic, pro, custom
    is_active = Column(Boolean, default=True)
    
    # AI Settings
    use_ai = Column(Boolean, default=False)
    ai_requests_today = Column(Integer, default=0)
    ai_requests_limit = Column(Integer, default=1000)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    branding = relationship("ClientBranding", back_populates="client", uselist=False)
    leads = relationship("Lead", back_populates="client")
    conversations = relationship("Conversation", back_populates="client")
    knowledge_base = relationship("KnowledgeBase", back_populates="client")
    handovers = relationship("Handover", back_populates="client")


class ClientBranding(Base):
    """Visual branding configuration"""
    __tablename__ = "client_branding"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String, ForeignKey("clients.id"), unique=True, nullable=False)
    
    # Colors
    primary_color = Column(String, default="#111827")
    secondary_color = Column(String, default="#ffffff")
    accent_color = Column(String, default="#3b82f6")
    
    # Text colors
    header_text_color = Column(String, default="#ffffff")
    user_bubble_color = Column(String, default="#111827")
    user_text_color = Column(String, default="#ffffff")
    bot_bubble_color = Column(String, default="#f3f4f6")
    bot_text_color = Column(String, default="#111827")
    
    # UI Elements
    border_radius = Column(String, default="12px")
    position = Column(String, default="bottom-right")
    
    # Branding
    company_display_name = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    
    # Messages
    greeting_message = Column(String, default="Hej! Hvordan kan jeg hjælpe dig i dag?")
    offline_message = Column(String, default="Vi er ikke online lige nu. Efterlad en besked!")
    
    # Features
    show_avatar = Column(Boolean, default=True)
    show_company_logo = Column(Boolean, default=False)
    show_powered_by = Column(Boolean, default=True)
    enable_emojis = Column(Boolean, default=False)
    
    # Behavior
    auto_open = Column(Boolean, default=False)
    auto_open_delay = Column(Integer, default=5000)
    
    # Custom CSS (advanced)
    custom_css = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="branding")
