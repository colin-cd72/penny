"""Recommendation schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    """Schema for recommendation summary."""
    id: UUID
    stock_id: UUID
    symbol: str
    stock_name: Optional[str]

    signal_type: str
    confidence: float

    entry_price: float
    target_price: Optional[float]
    stop_loss: Optional[float]

    # Risk assessment
    risk_score: Optional[float]
    manipulation_probability: Optional[float]

    warnings: List[str] = []

    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class RecommendationDetail(BaseModel):
    """Schema for detailed recommendation."""
    id: UUID
    stock_id: UUID
    symbol: str
    stock_name: Optional[str]

    signal_type: str
    confidence: float

    entry_price: float
    target_price: Optional[float]
    stop_loss: Optional[float]

    # Score breakdown
    technical_score: Optional[float]
    sentiment_score: Optional[float]
    social_score: Optional[float]
    insider_score: Optional[float]

    # Detailed reasoning
    reasoning: dict = {}

    # Risk assessment
    risk_score: Optional[float]
    manipulation_probability: Optional[float]

    warnings: List[str] = []

    # Timestamps
    created_at: datetime
    expires_at: Optional[datetime]

    # Outcome (if closed)
    actual_outcome: Optional[str]
    actual_return_pct: Optional[float]
    closed_at: Optional[datetime]

    class Config:
        from_attributes = True


class RecommendationListResponse(BaseModel):
    """Schema for paginated recommendation list."""
    items: List[RecommendationResponse]
    total: int
    page: int
    per_page: int
    pages: int
