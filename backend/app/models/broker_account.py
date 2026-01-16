"""Broker account model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class BrokerAccount(Base):
    """User's broker account configuration."""

    __tablename__ = "broker_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Broker identification
    broker_name = Column(String(50), nullable=False)  # alpaca, td_ameritrade, etc.
    account_id = Column(String(100))  # External account ID

    # Encrypted credentials
    api_key_encrypted = Column(String(500))
    api_secret_encrypted = Column(String(500))

    # Account settings
    is_paper = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Sync status
    last_sync_at = Column(DateTime)
    sync_error = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="broker_accounts")
    trades = relationship("Trade", back_populates="broker_account")

    def __repr__(self):
        return f"<BrokerAccount {self.broker_name} {'paper' if self.is_paper else 'live'}>"
