"""Stock endpoints."""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Stock, PriceHistory, NewsArticle
from app.schemas.stock import (
    StockResponse,
    StockListResponse,
    StockDetail,
    PriceCandle,
    TechnicalIndicators,
)
from app.api.v1.deps import get_current_user


router = APIRouter()


@router.get("/", response_model=StockListResponse)
async def list_stocks(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sector: Optional[str] = None,
    exchange: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0, le=5),
    min_volume: Optional[int] = Query(None, ge=0),
    signal: Optional[str] = Query(None, pattern="^(strong_buy|buy|hold|sell|strong_sell)$"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
    sort_by: str = Query("signal_confidence", pattern="^(signal_confidence|volume|current_price|symbol)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List penny stocks with filtering and sorting."""
    query = select(Stock).where(Stock.is_active == True, Stock.is_penny_stock == True)

    # Apply filters
    if sector:
        query = query.where(Stock.sector == sector)
    if exchange:
        query = query.where(Stock.exchange == exchange)
    if min_price is not None:
        query = query.where(Stock.current_price >= min_price)
    if max_price is not None:
        query = query.where(Stock.current_price <= max_price)
    if min_volume is not None:
        query = query.where(Stock.volume >= min_volume)
    if signal:
        query = query.where(Stock.latest_signal == signal)
    if min_confidence is not None:
        query = query.where(Stock.signal_confidence >= min_confidence)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Stock.symbol.ilike(search_term)) | (Stock.name.ilike(search_term))
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply sorting
    sort_column = getattr(Stock, sort_by)
    if order == "desc":
        query = query.order_by(desc(sort_column).nulls_last())
    else:
        query = query.order_by(asc(sort_column).nulls_last())

    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    stocks = result.scalars().all()

    return StockListResponse(
        items=[StockResponse.model_validate(s) for s in stocks],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.get("/{symbol}", response_model=StockDetail)
async def get_stock(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed information for a specific stock."""
    result = await db.execute(
        select(Stock).where(Stock.symbol == symbol.upper())
    )
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Get recent price history
    price_query = (
        select(PriceHistory)
        .where(
            PriceHistory.stock_id == stock.id,
            PriceHistory.interval == "1d",
        )
        .order_by(desc(PriceHistory.timestamp))
        .limit(30)
    )
    price_result = await db.execute(price_query)
    prices = price_result.scalars().all()

    # Build response
    stock_detail = StockDetail.model_validate(stock)

    if prices:
        stock_detail.recent_prices = [
            PriceCandle(
                timestamp=p.timestamp,
                open=p.open,
                high=p.high,
                low=p.low,
                close=p.close,
                volume=p.volume,
                vwap=p.vwap,
            )
            for p in reversed(prices)
        ]

    if stock.rsi_14 is not None:
        stock_detail.indicators = TechnicalIndicators(
            symbol=stock.symbol,
            timestamp=stock.last_updated or datetime.utcnow(),
            rsi_14=stock.rsi_14,
            macd=stock.macd,
            macd_signal=stock.macd_signal,
            sma_20=stock.sma_20,
            sma_50=stock.sma_50,
        )

    return stock_detail


@router.get("/{symbol}/price-history", response_model=List[PriceCandle])
async def get_price_history(
    symbol: str,
    interval: str = Query("1d", pattern="^(1m|5m|15m|1h|4h|1d|1w)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(500, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get historical price data for charting."""
    # Get stock
    result = await db.execute(
        select(Stock).where(Stock.symbol == symbol.upper())
    )
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Build query
    query = (
        select(PriceHistory)
        .where(
            PriceHistory.stock_id == stock.id,
            PriceHistory.interval == interval,
        )
    )

    if start_date:
        query = query.where(PriceHistory.timestamp >= start_date)
    if end_date:
        query = query.where(PriceHistory.timestamp <= end_date)

    query = query.order_by(desc(PriceHistory.timestamp)).limit(limit)

    result = await db.execute(query)
    prices = result.scalars().all()

    return [
        PriceCandle(
            timestamp=p.timestamp,
            open=p.open,
            high=p.high,
            low=p.low,
            close=p.close,
            volume=p.volume,
            vwap=p.vwap,
        )
        for p in reversed(prices)
    ]


@router.get("/{symbol}/indicators", response_model=TechnicalIndicators)
async def get_technical_indicators(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current technical indicator values."""
    result = await db.execute(
        select(Stock).where(Stock.symbol == symbol.upper())
    )
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    return TechnicalIndicators(
        symbol=stock.symbol,
        timestamp=stock.last_updated or datetime.utcnow(),
        rsi_14=stock.rsi_14,
        macd=stock.macd,
        macd_signal=stock.macd_signal,
        sma_20=stock.sma_20,
        sma_50=stock.sma_50,
    )


@router.get("/{symbol}/news")
async def get_stock_news(
    symbol: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get news articles with sentiment scores."""
    # Get stock
    result = await db.execute(
        select(Stock).where(Stock.symbol == symbol.upper())
    )
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Get news
    offset = (page - 1) * per_page
    query = (
        select(NewsArticle)
        .where(NewsArticle.stock_id == stock.id)
        .order_by(desc(NewsArticle.published_at))
        .offset(offset)
        .limit(per_page)
    )

    result = await db.execute(query)
    articles = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "title": a.title,
            "summary": a.summary,
            "source": a.source,
            "url": a.url,
            "sentiment_score": a.sentiment_score,
            "sentiment_label": a.sentiment_label,
            "published_at": a.published_at,
        }
        for a in articles
    ]
