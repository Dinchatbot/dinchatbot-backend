# app/models/lead.py
"""
Lead capture model - GDPR compliant
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Lead(Base):
    """Customer lead model"""
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Client reference
    client_id = Column(String, ForeignKey("clients.id"), nullable=False, index=True)
    
    # Session tracking
    session_id = Column(String, nullable=False, index=True)
    
    # Lead information
    name = Column(String, nullable=True)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    message = Column(Text, nullable=True)
    
    # Lead status
    status = Column(
        String,
        default="new",
        nullable=False,
    )  # new, contacted, qualified, converted, lost
    
    # Source
    source = Column(String, default="chatbot")
    landing_page = Column(String, nullable=True)
    referrer = Column(String, nullable=True)
    
    # GDPR
    gdpr_consent = Column(Boolean, default=True)
    ip_address = Column(String, nullable=True)  # Anonymized
    user_agent = Column(String, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    contacted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    client = relationship("Client", back_populates="leads")
    
    def __repr__(self):
        return f"<Lead(id={self.id}, email={self.email}, status={self.status})>"
