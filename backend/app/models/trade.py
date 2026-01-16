"""Trade model for order tracking."""

import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TradeSide(str, enum.Enum):
    """Trade side enumeration."""
    BUY = "buy"
    SELL = "sell"


class TradeStatus(str, enum.Enum):
    """Trade status enumeration."""
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Trade(Base):
    """Trade model for tracking orders."""

    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False, index=True)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("recommendations.id"))
    broker_account_id = Column(UUID(as_uuid=True), ForeignKey("broker_accounts.id"), nullable=False)

    # Order details
    side = Column(Enum(TradeSide), nullable=False)
    quantity = Column(Integer, nullable=False)
    order_type = Column(String(20), default="limit")  # market, limit, stop, stop_limit
    price = Column(Float)  # Limit price, null for market orders
    stop_price = Column(Float)  # For stop orders
    time_in_force = Column(String(10), default="day")  # day, gtc, ioc, fok

    # Status and execution
    status = Column(Enum(TradeStatus), default=TradeStatus.PENDING_CONFIRMATION, index=True)
    broker_order_id = Column(String(100))

    # Confirmation workflow
    confirmation_token = Column(String(64), unique=True)
    confirmation_channel = Column(String(20))  # email, sms
    confirmed_at = Column(DateTime)

    # Execution details
    submitted_at = Column(DateTime)
    executed_at = Column(DateTime)
    filled_price = Column(Float)
    filled_quantity = Column(Integer)
    commission = Column(Float)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="trades")
    stock = relationship("Stock", back_populates="trades")
    recommendation = relationship("Recommendation", back_populates="trades")
    broker_account = relationship("BrokerAccount", back_populates="trades")

    def __repr__(self):
        return f"<Trade {self.side} {self.quantity} {self.stock_id}>"
