"""Alert configuration schemas."""

from datetime import datetime, time
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class AlertConfigCreate(BaseModel):
    """Schema for creating an alert configuration."""
    alert_type: str = Field(..., pattern="^(signal|price_alert|volume_spike)$")
    channel: str = Field(..., pattern="^(email|sms|push)$")
    min_confidence: float = Field(default=0.7, ge=0, le=1)
    signal_types: Optional[List[str]] = None
    stocks: Optional[List[str]] = None
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None


class AlertConfigUpdate(BaseModel):
    """Schema for updating an alert configuration."""
    min_confidence: Optional[float] = Field(None, ge=0, le=1)
    signal_types: Optional[List[str]] = None
    stocks: Optional[List[str]] = None
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    is_active: Optional[bool] = None


class AlertConfigResponse(BaseModel):
    """Schema for alert configuration response."""
    id: UUID
    alert_type: str
    channel: str
    min_confidence: float
    signal_types: Optional[List[str]]
    stocks: Optional[List[str]]
    quiet_hours_start: Optional[time]
    quiet_hours_end: Optional[time]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertHistoryResponse(BaseModel):
    """Schema for alert history."""
    id: UUID
    recommendation_id: UUID
    symbol: str
    signal_type: str
    channel: str
    status: str
    sent_at: datetime
    clicked_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True
