"""News article model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.database import Base
from sqlalchemy.orm import relationship


class NewsArticle(Base):
    """News article with sentiment analysis."""

    __tablename__ = "news_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False, index=True)

    # Article content
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    content = Column(Text)

    # Source information
    source = Column(String(100))
    author = Column(String(255))
    url = Column(String(1000), unique=True)
    image_url = Column(String(1000))

    # Sentiment analysis
    sentiment_score = Column(Float)  # -1.0 to 1.0
    sentiment_label = Column(String(20))  # positive, negative, neutral
    sentiment_confidence = Column(Float)

    # Relevance
    relevance_score = Column(Float)

    # Tags and categories
    tags = Column(ARRAY(String))

    # Timestamps
    published_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    stock = relationship("Stock", back_populates="news_articles")

    def __repr__(self):
        return f"<NewsArticle {self.title[:50]}...>"
