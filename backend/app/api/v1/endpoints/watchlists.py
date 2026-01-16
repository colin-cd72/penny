"""Watchlist endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Watchlist, WatchlistStock, Stock
from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistUpdate,
    WatchlistResponse,
    WatchlistStockAdd,
    WatchlistStockResponse,
    WatchlistListResponse,
)
from app.api.v1.deps import get_current_user


router = APIRouter()


@router.get("/", response_model=WatchlistListResponse)
async def list_watchlists(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's watchlists."""
    result = await db.execute(
        select(Watchlist)
        .options(selectinload(Watchlist.stocks).selectinload(WatchlistStock.stock))
        .where(Watchlist.user_id == current_user.id)
        .order_by(Watchlist.created_at)
    )
    watchlists = result.scalars().all()

    items = []
    for wl in watchlists:
        stocks = []
        for ws in wl.stocks:
            stocks.append(WatchlistStockResponse(
                id=ws.id,
                symbol=ws.stock.symbol,
                stock_name=ws.stock.name,
                current_price=ws.stock.current_price,
                latest_signal=ws.stock.latest_signal,
                signal_confidence=ws.stock.signal_confidence,
                notes=ws.notes,
                alert_on_signal=ws.alert_on_signal,
                added_at=ws.added_at,
            ))

        items.append(WatchlistResponse(
            id=wl.id,
            name=wl.name,
            description=wl.description,
            stocks=stocks,
            stock_count=len(stocks),
            created_at=wl.created_at,
            updated_at=wl.updated_at,
        ))

    return WatchlistListResponse(items=items, total=len(items))


@router.post("/", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    watchlist_data: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new watchlist."""
    watchlist = Watchlist(
        user_id=current_user.id,
        name=watchlist_data.name,
        description=watchlist_data.description,
    )

    db.add(watchlist)
    await db.flush()
    await db.refresh(watchlist)

    return WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        description=watchlist.description,
        stocks=[],
        stock_count=0,
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
    )


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific watchlist with stocks."""
    result = await db.execute(
        select(Watchlist)
        .options(selectinload(Watchlist.stocks).selectinload(WatchlistStock.stock))
        .where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == current_user.id,
        )
    )
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    stocks = []
    for ws in watchlist.stocks:
        stocks.append(WatchlistStockResponse(
            id=ws.id,
            symbol=ws.stock.symbol,
            stock_name=ws.stock.name,
            current_price=ws.stock.current_price,
            latest_signal=ws.stock.latest_signal,
            signal_confidence=ws.stock.signal_confidence,
            notes=ws.notes,
            alert_on_signal=ws.alert_on_signal,
            added_at=ws.added_at,
        ))

    return WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        description=watchlist.description,
        stocks=stocks,
        stock_count=len(stocks),
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
    )


@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(
    watchlist_id: UUID,
    watchlist_data: WatchlistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a watchlist."""
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == current_user.id,
        )
    )
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    if watchlist_data.name is not None:
        watchlist.name = watchlist_data.name
    if watchlist_data.description is not None:
        watchlist.description = watchlist_data.description

    await db.flush()
    await db.refresh(watchlist)

    return WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        description=watchlist.description,
        stocks=[],
        stock_count=0,
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
    )


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    watchlist_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a watchlist."""
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == current_user.id,
        )
    )
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    await db.delete(watchlist)


@router.post("/{watchlist_id}/stocks", response_model=WatchlistStockResponse, status_code=status.HTTP_201_CREATED)
async def add_stock_to_watchlist(
    watchlist_id: UUID,
    stock_data: WatchlistStockAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a stock to a watchlist."""
    # Check watchlist exists and belongs to user
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == current_user.id,
        )
    )
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Get stock
    stock_result = await db.execute(
        select(Stock).where(Stock.symbol == stock_data.symbol.upper())
    )
    stock = stock_result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Check if already in watchlist
    existing = await db.execute(
        select(WatchlistStock).where(
            WatchlistStock.watchlist_id == watchlist_id,
            WatchlistStock.stock_id == stock.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Stock already in watchlist")

    # Add stock
    watchlist_stock = WatchlistStock(
        watchlist_id=watchlist_id,
        stock_id=stock.id,
        notes=stock_data.notes,
        alert_on_signal=stock_data.alert_on_signal,
    )

    db.add(watchlist_stock)
    await db.flush()
    await db.refresh(watchlist_stock)

    return WatchlistStockResponse(
        id=watchlist_stock.id,
        symbol=stock.symbol,
        stock_name=stock.name,
        current_price=stock.current_price,
        latest_signal=stock.latest_signal,
        signal_confidence=stock.signal_confidence,
        notes=watchlist_stock.notes,
        alert_on_signal=watchlist_stock.alert_on_signal,
        added_at=watchlist_stock.added_at,
    )


@router.delete("/{watchlist_id}/stocks/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_stock_from_watchlist(
    watchlist_id: UUID,
    symbol: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a stock from a watchlist."""
    # Check watchlist exists and belongs to user
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == current_user.id,
        )
    )
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Get stock
    stock_result = await db.execute(
        select(Stock).where(Stock.symbol == symbol.upper())
    )
    stock = stock_result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Find and delete watchlist stock entry
    ws_result = await db.execute(
        select(WatchlistStock).where(
            WatchlistStock.watchlist_id == watchlist_id,
            WatchlistStock.stock_id == stock.id,
        )
    )
    watchlist_stock = ws_result.scalar_one_or_none()

    if not watchlist_stock:
        raise HTTPException(status_code=404, detail="Stock not in watchlist")

    await db.delete(watchlist_stock)
