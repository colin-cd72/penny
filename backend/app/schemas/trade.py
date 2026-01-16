"""Trade schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TradeCreate(BaseModel):
    """Schema for creating a new trade."""
    symbol: str
    side: str = Field(..., pattern="^(buy|sell)$")
    quantity: int = Field(..., gt=0)
    order_type: str = Field(default="limit", pattern="^(market|limit|stop|stop_limit)$")
    price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)
    time_in_force: str = Field(default="day", pattern="^(day|gtc|ioc|fok)$")
    recommendation_id: Optional[UUID] = None
    broker_account_id: Optional[UUID] = None


class TradeConfirm(BaseModel):
    """Schema for confirming a trade."""
    confirmation_token: str


class TradeResponse(BaseModel):
    """Schema for trade response."""
    id: UUID
    user_id: UUID
    stock_id: UUID
    symbol: str
    stock_name: Optional[str]

    side: str
    quantity: int
    order_type: str
    price: Optional[float]
    status: str

    # Confirmation
    confirmation_token: Optional[str]
    confirmed_at: Optional[datetime]

    # Execution
    filled_price: Optional[float]
    filled_quantity: Optional[int]
    executed_at: Optional[datetime]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TradeDetail(BaseModel):
    """Schema for detailed trade information."""
    id: UUID
    user_id: UUID
    stock_id: UUID
    symbol: str
    stock_name: Optional[str]
    recommendation_id: Optional[UUID]
    broker_account_id: UUID

    side: str
    quantity: int
    order_type: str
    price: Optional[float]
    stop_price: Optional[float]
    time_in_force: str

    status: str
    broker_order_id: Optional[str]

    # Confirmation
    confirmation_token: Optional[str]
    confirmation_channel: Optional[str]
    confirmed_at: Optional[datetime]

    # Execution
    submitted_at: Optional[datetime]
    executed_at: Optional[datetime]
    filled_price: Optional[float]
    filled_quantity: Optional[int]
    commission: Optional[float]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PositionSizeRequest(BaseModel):
    """Schema for position size calculation request."""
    symbol: str
    entry_price: float = Field(..., gt=0)
    stop_loss: float = Field(..., gt=0)
    strategy: str = Field(default="fixed_risk", pattern="^(fixed_risk|kelly|fixed_amount)$")
    risk_percent: float = Field(default=0.01, gt=0, le=0.1)
    confidence: Optional[float] = Field(None, ge=0, le=1)


class PositionSizeResponse(BaseModel):
    """Schema for position size calculation response."""
    shares: int
    total_cost: float
    risk_amount: float
    percent_of_portfolio: float
    rationale: str
