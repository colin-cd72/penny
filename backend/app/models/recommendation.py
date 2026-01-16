"""Recommendation model for buy/sell signals."""

import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class SignalType(str, enum.Enum):
    """Signal type enumeration."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class Recommendation(Base):
    """Recommendation model for generated trading signals."""

    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False, index=True)

    # Signal details
    signal_type = Column(Enum(SignalType), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0

    # Price targets
    entry_price = Column(Float, nullable=False)
    target_price = Column(Float)
    stop_loss = Column(Float)

    # Analysis breakdown
    technical_score = Column(Float)
    sentiment_score = Column(Float)
    social_score = Column(Float)
    insider_score = Column(Float)

    # Detailed reasoning stored as JSON
    reasoning = Column(JSONB, default=dict)

    # Risk assessment
    risk_score = Column(Float)
    manipulation_probability = Column(Float)

    # Warnings
    warnings = Column(JSONB, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)

    # Outcome tracking (for historical analysis)
    actual_outcome = Column(String(50))  # win, loss, expired, cancelled
    actual_return_pct = Column(Float)
    closed_at = Column(DateTime)

    # Relationships
    stock = relationship("Stock", back_populates="recommendations")
    trades = relationship("Trade", back_populates="recommendation")
    alerts = relationship("RecommendationAlert", back_populates="recommendation")

    def __repr__(self):
        return f"<Recommendation {self.stock_id} {self.signal_type}>"
