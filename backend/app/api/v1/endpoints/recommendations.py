"""Recommendation endpoints."""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Recommendation, Stock
from app.schemas.recommendation import (
    RecommendationResponse,
    RecommendationDetail,
    RecommendationListResponse,
)
from app.api.v1.deps import get_current_user


router = APIRouter()


@router.get("/", response_model=RecommendationListResponse)
async def list_recommendations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    signal_type: Optional[str] = Query(None, pattern="^(strong_buy|buy|hold|sell|strong_sell)$"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
    symbol: Optional[str] = None,
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List recommendations with filtering."""
    query = (
        select(Recommendation)
        .options(selectinload(Recommendation.stock))
    )

    # Filter active (not expired, no outcome yet)
    if active_only:
        from datetime import datetime
        query = query.where(
            Recommendation.actual_outcome.is_(None),
            (Recommendation.expires_at.is_(None)) | (Recommendation.expires_at > datetime.utcnow()),
        )

    if signal_type:
        query = query.where(Recommendation.signal_type == signal_type)
    if min_confidence is not None:
        query = query.where(Recommendation.confidence >= min_confidence)
    if symbol:
        query = query.join(Stock).where(Stock.symbol == symbol.upper())

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Order by confidence and created_at
    query = query.order_by(desc(Recommendation.confidence), desc(Recommendation.created_at))

    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    recommendations = result.scalars().all()

    items = []
    for rec in recommendations:
        items.append(RecommendationResponse(
            id=rec.id,
            stock_id=rec.stock_id,
            symbol=rec.stock.symbol,
            stock_name=rec.stock.name,
            signal_type=rec.signal_type.value,
            confidence=rec.confidence,
            entry_price=rec.entry_price,
            target_price=rec.target_price,
            stop_loss=rec.stop_loss,
            risk_score=rec.risk_score,
            manipulation_probability=rec.manipulation_probability,
            warnings=rec.warnings or [],
            created_at=rec.created_at,
            expires_at=rec.expires_at,
        ))

    return RecommendationListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.get("/{recommendation_id}", response_model=RecommendationDetail)
async def get_recommendation(
    recommendation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed recommendation information."""
    result = await db.execute(
        select(Recommendation)
        .options(selectinload(Recommendation.stock))
        .where(Recommendation.id == recommendation_id)
    )
    rec = result.scalar_one_or_none()

    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return RecommendationDetail(
        id=rec.id,
        stock_id=rec.stock_id,
        symbol=rec.stock.symbol,
        stock_name=rec.stock.name,
        signal_type=rec.signal_type.value,
        confidence=rec.confidence,
        entry_price=rec.entry_price,
        target_price=rec.target_price,
        stop_loss=rec.stop_loss,
        technical_score=rec.technical_score,
        sentiment_score=rec.sentiment_score,
        social_score=rec.social_score,
        insider_score=rec.insider_score,
        reasoning=rec.reasoning or {},
        risk_score=rec.risk_score,
        manipulation_probability=rec.manipulation_probability,
        warnings=rec.warnings or [],
        created_at=rec.created_at,
        expires_at=rec.expires_at,
        actual_outcome=rec.actual_outcome,
        actual_return_pct=rec.actual_return_pct,
        closed_at=rec.closed_at,
    )


@router.get("/history/", response_model=RecommendationListResponse)
async def get_recommendation_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    outcome: Optional[str] = Query(None, pattern="^(win|loss|expired|cancelled)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get historical recommendations with outcomes."""
    query = (
        select(Recommendation)
        .options(selectinload(Recommendation.stock))
        .where(Recommendation.actual_outcome.is_not(None))
    )

    if outcome:
        query = query.where(Recommendation.actual_outcome == outcome)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Order by closed_at
    query = query.order_by(desc(Recommendation.closed_at))

    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    recommendations = result.scalars().all()

    items = []
    for rec in recommendations:
        items.append(RecommendationResponse(
            id=rec.id,
            stock_id=rec.stock_id,
            symbol=rec.stock.symbol,
            stock_name=rec.stock.name,
            signal_type=rec.signal_type.value,
            confidence=rec.confidence,
            entry_price=rec.entry_price,
            target_price=rec.target_price,
            stop_loss=rec.stop_loss,
            risk_score=rec.risk_score,
            manipulation_probability=rec.manipulation_probability,
            warnings=rec.warnings or [],
            created_at=rec.created_at,
            expires_at=rec.expires_at,
        ))

    return RecommendationListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.get("/performance/stats")
async def get_recommendation_performance(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recommendation performance statistics."""
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=days)

    # Get closed recommendations in the period
    result = await db.execute(
        select(Recommendation)
        .where(
            Recommendation.actual_outcome.is_not(None),
            Recommendation.closed_at >= cutoff,
        )
    )
    recommendations = result.scalars().all()

    if not recommendations:
        return {
            "period_days": days,
            "total_recommendations": 0,
            "win_rate": None,
            "avg_return": None,
        }

    total = len(recommendations)
    wins = sum(1 for r in recommendations if r.actual_outcome == "win")
    returns = [r.actual_return_pct for r in recommendations if r.actual_return_pct is not None]

    return {
        "period_days": days,
        "total_recommendations": total,
        "wins": wins,
        "losses": sum(1 for r in recommendations if r.actual_outcome == "loss"),
        "expired": sum(1 for r in recommendations if r.actual_outcome == "expired"),
        "win_rate": wins / total if total > 0 else 0,
        "avg_return": sum(returns) / len(returns) if returns else 0,
        "max_return": max(returns) if returns else 0,
        "min_return": min(returns) if returns else 0,
    }
