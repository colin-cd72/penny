"""Watchlist models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Watchlist(Base):
    """Watchlist model for user's stock lists."""

    __tablename__ = "watchlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="watchlists")
    stocks = relationship("WatchlistStock", back_populates="watchlist", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Watchlist {self.name}>"


class WatchlistStock(Base):
    """Association table for watchlist-stock relationship."""

    __tablename__ = "watchlist_stocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    watchlist_id = Column(UUID(as_uuid=True), ForeignKey("watchlists.id"), nullable=False, index=True)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False, index=True)

    notes = Column(Text)
    alert_on_signal = Column(String(20))  # Signal type to alert on

    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    watchlist = relationship("Watchlist", back_populates="stocks")
    stock = relationship("Stock", back_populates="watchlist_entries")

    def __repr__(self):
        return f"<WatchlistStock {self.watchlist_id} {self.stock_id}>"
