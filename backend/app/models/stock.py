"""Stock model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, BigInteger, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Stock(Base):
    """Stock model representing penny stocks in the universe."""

    __tablename__ = "stocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255))

    # Exchange and classification
    exchange = Column(String(20))  # NYSE, NASDAQ, OTC, etc.
    market_tier = Column(String(20))  # OTCQX, OTCQB, Pink, etc.
    sector = Column(String(100))
    industry = Column(String(100))

    # SEC identifier
    cik = Column(String(10))

    # Current market data
    current_price = Column(Float)
    previous_close = Column(Float)
    day_high = Column(Float)
    day_low = Column(Float)
    volume = Column(BigInteger)
    avg_volume_20d = Column(BigInteger)
    market_cap = Column(BigInteger)

    # Technical indicators (cached)
    rsi_14 = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    sma_20 = Column(Float)
    sma_50 = Column(Float)

    # Latest signal
    latest_signal = Column(String(20))  # strong_buy, buy, hold, sell, strong_sell
    signal_confidence = Column(Float)

    # Status
    is_active = Column(Boolean, default=True)
    is_penny_stock = Column(Boolean, default=True)

    # Extra data
    extra_data = Column(JSONB, default=dict)

    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recommendations = relationship("Recommendation", back_populates="stock")
    trades = relationship("Trade", back_populates="stock")
    watchlist_entries = relationship("WatchlistStock", back_populates="stock")
    news_articles = relationship("NewsArticle", back_populates="stock")
    insider_transactions = relationship("InsiderTransaction", back_populates="stock")

    def __repr__(self):
        return f"<Stock {self.symbol}>"
