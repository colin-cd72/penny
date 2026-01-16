"""Watchlist schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class WatchlistCreate(BaseModel):
    """Schema for creating a watchlist."""
    name: str
    description: Optional[str] = None


class WatchlistUpdate(BaseModel):
    """Schema for updating a watchlist."""
    name: Optional[str] = None
    description: Optional[str] = None


class WatchlistStockAdd(BaseModel):
    """Schema for adding a stock to watchlist."""
    symbol: str
    notes: Optional[str] = None
    alert_on_signal: Optional[str] = None


class WatchlistStockResponse(BaseModel):
    """Schema for watchlist stock entry."""
    id: UUID
    symbol: str
    stock_name: Optional[str]
    current_price: Optional[float]
    latest_signal: Optional[str]
    signal_confidence: Optional[float]
    notes: Optional[str]
    alert_on_signal: Optional[str]
    added_at: datetime

    class Config:
        from_attributes = True


class WatchlistResponse(BaseModel):
    """Schema for watchlist response."""
    id: UUID
    name: str
    description: Optional[str]
    stocks: List[WatchlistStockResponse] = []
    stock_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WatchlistListResponse(BaseModel):
    """Schema for watchlist list."""
    items: List[WatchlistResponse]
    total: int
