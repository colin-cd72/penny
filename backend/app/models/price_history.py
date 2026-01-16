"""Price history model for time-series data."""

import uuid
from datetime import datetime

from sqlalchemy import Column, Float, BigInteger, DateTime, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class PriceHistory(Base):
    """OHLCV price history - optimized for time-series queries with TimescaleDB."""

    __tablename__ = "price_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False)

    # OHLCV data
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)

    # Additional data
    vwap = Column(Float)  # Volume-weighted average price
    trade_count = Column(BigInteger)

    # Interval (1m, 5m, 15m, 1h, 1d, etc.)
    interval = Column(String(10), nullable=False, default="1d")

    # Composite index for efficient time-series queries
    __table_args__ = (
        Index('ix_price_history_stock_time', 'stock_id', 'timestamp', 'interval'),
    )

    def __repr__(self):
        return f"<PriceHistory {self.stock_id} {self.timestamp}>"
