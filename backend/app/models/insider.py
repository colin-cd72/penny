"""Insider transaction model."""

import uuid
from datetime import datetime, date

from sqlalchemy import Column, String, Float, BigInteger, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class InsiderTransaction(Base):
    """Insider trading transactions from SEC Form 4."""

    __tablename__ = "insider_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False, index=True)

    # SEC identifiers
    cik = Column(String(10))
    accession_number = Column(String(25), unique=True)

    # Insider information
    insider_name = Column(String(255), nullable=False)
    insider_title = Column(String(100))
    insider_relationship = Column(String(50))  # Officer, Director, 10% Owner

    # Transaction details
    transaction_date = Column(Date, nullable=False, index=True)
    transaction_type = Column(String(10), nullable=False)  # P (purchase), S (sale), A (award)
    shares = Column(BigInteger, nullable=False)
    price_per_share = Column(Float)
    total_value = Column(Float)

    # Post-transaction holdings
    shares_owned_after = Column(BigInteger)
    ownership_type = Column(String(20))  # Direct, Indirect

    # Additional details
    is_10b5_plan = Column(Boolean, default=False)
    footnotes = Column(JSONB)

    # Filing information
    filing_date = Column(DateTime, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    stock = relationship("Stock", back_populates="insider_transactions")

    def __repr__(self):
        return f"<InsiderTransaction {self.insider_name} {self.transaction_type} {self.shares}>"
