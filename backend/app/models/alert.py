"""Alert configuration and history models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Boolean, DateTime, Time, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class AlertConfig(Base):
    """User's alert configuration."""

    __tablename__ = "alert_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Alert type and channel
    alert_type = Column(String(50), nullable=False)  # signal, price_alert, volume_spike
    channel = Column(String(20), nullable=False)  # email, sms, push

    # Filters
    min_confidence = Column(Float, default=0.7)
    signal_types = Column(ARRAY(String))  # List of signal types to alert on
    stocks = Column(ARRAY(String))  # List of symbols, null for all

    # Quiet hours
    quiet_hours_start = Column(Time)
    quiet_hours_end = Column(Time)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="alert_configs")

    def __repr__(self):
        return f"<AlertConfig {self.alert_type} {self.channel}>"


class RecommendationAlert(Base):
    """Record of sent alerts."""

    __tablename__ = "recommendation_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=False)

    channel = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)  # sent, failed, clicked

    sent_at = Column(DateTime, default=datetime.utcnow)
    clicked_at = Column(DateTime)

    error_message = Column(String(500))

    # Relationships
    recommendation = relationship("Recommendation", back_populates="alerts")

    def __repr__(self):
        return f"<RecommendationAlert {self.recommendation_id} {self.status}>"
