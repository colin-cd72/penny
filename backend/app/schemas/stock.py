"""Stock schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class StockResponse(BaseModel):
    """Schema for stock summary response."""
    id: UUID
    symbol: str
    name: Optional[str]
    exchange: Optional[str]
    current_price: Optional[float]
    previous_close: Optional[float]
    day_high: Optional[float]
    day_low: Optional[float]
    volume: Optional[int]
    avg_volume_20d: Optional[int]
    market_cap: Optional[int]

    # Signal info
    latest_signal: Optional[str]
    signal_confidence: Optional[float]

    # Quick indicators
    rsi_14: Optional[float]

    last_updated: Optional[datetime]

    class Config:
        from_attributes = True


class StockListResponse(BaseModel):
    """Schema for paginated stock list."""
    items: List[StockResponse]
    total: int
    page: int
    per_page: int
    pages: int


class TechnicalIndicators(BaseModel):
    """Schema for technical indicators."""
    symbol: str
    timestamp: datetime

    # RSI
    rsi_14: Optional[float]
    rsi_7: Optional[float]

    # MACD
    macd: Optional[float]
    macd_signal: Optional[float]
    macd_histogram: Optional[float]

    # Moving averages
    sma_20: Optional[float]
    sma_50: Optional[float]
    sma_200: Optional[float]
    ema_9: Optional[float]
    ema_21: Optional[float]

    # Bollinger Bands
    bb_upper: Optional[float]
    bb_middle: Optional[float]
    bb_lower: Optional[float]

    # Volume
    volume_sma_20: Optional[float]
    obv: Optional[float]

    # Other
    atr_14: Optional[float]
    stoch_k: Optional[float]
    stoch_d: Optional[float]


class PriceCandle(BaseModel):
    """Schema for OHLCV price candle."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None


class StockDetail(BaseModel):
    """Schema for detailed stock information."""
    id: UUID
    symbol: str
    name: Optional[str]
    exchange: Optional[str]
    market_tier: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    cik: Optional[str]

    # Market data
    current_price: Optional[float]
    previous_close: Optional[float]
    day_high: Optional[float]
    day_low: Optional[float]
    volume: Optional[int]
    avg_volume_20d: Optional[int]
    market_cap: Optional[int]

    # Signal
    latest_signal: Optional[str]
    signal_confidence: Optional[float]

    # Technical indicators
    indicators: Optional[TechnicalIndicators] = None

    # Recent price history (for quick chart)
    recent_prices: Optional[List[PriceCandle]] = None

    last_updated: Optional[datetime]

    class Config:
        from_attributes = True
