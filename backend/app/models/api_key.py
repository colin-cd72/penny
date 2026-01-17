"""API Key settings model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class APIKeySettings(Base):
    """Store encrypted API keys for external services."""

    __tablename__ = "api_key_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # API Keys (encrypted)
    polygon_api_key = Column(Text)
    sec_api_key = Column(Text)
    benzinga_api_key = Column(Text)
    alpha_vantage_api_key = Column(Text)
    reddit_client_id = Column(Text)
    reddit_client_secret = Column(Text)
    alpaca_api_key = Column(Text)
    alpaca_api_secret = Column(Text)
    alpaca_paper_trading = Column(Boolean, default=True)
    sendgrid_api_key = Column(Text)
    twilio_account_sid = Column(Text)
    twilio_auth_token = Column(Text)
    twilio_phone_number = Column(String(20))

    # SMTP settings
    smtp_host = Column(String(255))
    smtp_port = Column(String(10))
    smtp_username = Column(Text)
    smtp_password = Column(Text)
    smtp_from_email = Column(String(255))
    smtp_use_tls = Column(Boolean, default=True)

    # Test status
    polygon_tested_at = Column(DateTime)
    polygon_test_success = Column(Boolean)
    sec_tested_at = Column(DateTime)
    sec_test_success = Column(Boolean)
    benzinga_tested_at = Column(DateTime)
    benzinga_test_success = Column(Boolean)
    alpaca_tested_at = Column(DateTime)
    alpaca_test_success = Column(Boolean)
    sendgrid_tested_at = Column(DateTime)
    sendgrid_test_success = Column(Boolean)
    twilio_tested_at = Column(DateTime)
    twilio_test_success = Column(Boolean)
    smtp_tested_at = Column(DateTime)
    smtp_test_success = Column(Boolean)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="api_key_settings")

    def __repr__(self):
        return f"<APIKeySettings user_id={self.user_id}>"
