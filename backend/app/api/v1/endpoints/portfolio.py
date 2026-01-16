"""Portfolio endpoints."""

from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Trade, Stock, BrokerAccount, TradeStatus, TradeSide
from app.api.v1.deps import get_current_user


router = APIRouter()


@router.get("/positions")
async def get_positions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current portfolio positions.

    This aggregates filled trades to calculate current holdings.
    For real-time positions, this would query the broker API.
    """
    # Get all filled trades for the user
    result = await db.execute(
        select(Trade)
        .options(selectinload(Trade.stock))
        .where(
            Trade.user_id == current_user.id,
            Trade.status == TradeStatus.FILLED,
        )
    )
    trades = result.scalars().all()

    # Aggregate by stock
    positions = {}
    for trade in trades:
        symbol = trade.stock.symbol
        if symbol not in positions:
            positions[symbol] = {
                "symbol": symbol,
                "name": trade.stock.name,
                "quantity": 0,
                "total_cost": Decimal("0"),
                "current_price": trade.stock.current_price or 0,
            }

        qty = trade.filled_quantity or trade.quantity
        price = trade.filled_price or trade.price or 0

        if trade.side == TradeSide.BUY:
            positions[symbol]["quantity"] += qty
            positions[symbol]["total_cost"] += Decimal(str(qty * price))
        else:  # SELL
            positions[symbol]["quantity"] -= qty
            positions[symbol]["total_cost"] -= Decimal(str(qty * price))

    # Filter out zero positions and calculate metrics
    result_positions = []
    for symbol, pos in positions.items():
        if pos["quantity"] <= 0:
            continue

        avg_cost = float(pos["total_cost"]) / pos["quantity"] if pos["quantity"] > 0 else 0
        current_price = pos["current_price"]
        market_value = pos["quantity"] * current_price
        unrealized_pnl = market_value - float(pos["total_cost"])
        unrealized_pnl_pct = (unrealized_pnl / float(pos["total_cost"]) * 100) if pos["total_cost"] > 0 else 0

        result_positions.append({
            "symbol": symbol,
            "name": pos["name"],
            "quantity": pos["quantity"],
            "avg_cost": round(avg_cost, 4),
            "current_price": current_price,
            "market_value": round(market_value, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
        })

    return {
        "positions": result_positions,
        "total_positions": len(result_positions),
        "total_market_value": sum(p["market_value"] for p in result_positions),
        "total_unrealized_pnl": sum(p["unrealized_pnl"] for p in result_positions),
    }


@router.get("/summary")
async def get_portfolio_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get portfolio summary including account balance."""
    # Get positions
    positions_response = await get_positions(db=db, current_user=current_user)

    # Get broker account info
    broker_result = await db.execute(
        select(BrokerAccount).where(
            BrokerAccount.user_id == current_user.id,
            BrokerAccount.is_default == True,
            BrokerAccount.is_active == True,
        )
    )
    broker_account = broker_result.scalar_one_or_none()

    # Placeholder values (would come from broker API)
    cash_balance = 10000.0
    buying_power = 10000.0

    total_value = positions_response["total_market_value"] + cash_balance

    return {
        "cash_balance": cash_balance,
        "buying_power": buying_power,
        "positions_value": positions_response["total_market_value"],
        "total_value": total_value,
        "unrealized_pnl": positions_response["total_unrealized_pnl"],
        "position_count": positions_response["total_positions"],
        "broker_connected": broker_account is not None,
        "is_paper": broker_account.is_paper if broker_account else True,
    }


@router.get("/performance")
async def get_portfolio_performance(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get portfolio performance over time."""
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=days)

    # Get closed trades in the period
    result = await db.execute(
        select(Trade)
        .options(selectinload(Trade.stock))
        .where(
            Trade.user_id == current_user.id,
            Trade.status == TradeStatus.FILLED,
            Trade.executed_at >= cutoff,
        )
        .order_by(Trade.executed_at)
    )
    trades = result.scalars().all()

    # Calculate realized P&L
    realized_pnl = Decimal("0")
    trades_won = 0
    trades_lost = 0

    # Group buy/sell pairs by stock
    stock_trades = {}
    for trade in trades:
        symbol = trade.stock.symbol
        if symbol not in stock_trades:
            stock_trades[symbol] = {"buys": [], "sells": []}

        if trade.side == TradeSide.BUY:
            stock_trades[symbol]["buys"].append(trade)
        else:
            stock_trades[symbol]["sells"].append(trade)

    # Calculate P&L for each closed position (simplified FIFO)
    for symbol, data in stock_trades.items():
        for sell in data["sells"]:
            sell_qty = sell.filled_quantity or sell.quantity
            sell_price = sell.filled_price or sell.price or 0

            # Find matching buy
            for buy in data["buys"]:
                buy_qty = buy.filled_quantity or buy.quantity
                buy_price = buy.filled_price or buy.price or 0

                if buy_qty > 0:
                    matched_qty = min(buy_qty, sell_qty)
                    pnl = matched_qty * (sell_price - buy_price)
                    realized_pnl += Decimal(str(pnl))

                    if pnl > 0:
                        trades_won += 1
                    elif pnl < 0:
                        trades_lost += 1

                    sell_qty -= matched_qty
                    buy.filled_quantity = buy_qty - matched_qty

                    if sell_qty <= 0:
                        break

    total_trades = trades_won + trades_lost
    win_rate = (trades_won / total_trades * 100) if total_trades > 0 else 0

    return {
        "period_days": days,
        "realized_pnl": float(realized_pnl),
        "total_trades": len(trades),
        "trades_won": trades_won,
        "trades_lost": trades_lost,
        "win_rate": round(win_rate, 1),
    }


@router.get("/broker-accounts")
async def list_broker_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's broker accounts."""
    result = await db.execute(
        select(BrokerAccount).where(BrokerAccount.user_id == current_user.id)
    )
    accounts = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "broker_name": a.broker_name,
            "account_id": a.account_id,
            "is_paper": a.is_paper,
            "is_active": a.is_active,
            "is_default": a.is_default,
            "last_sync_at": a.last_sync_at,
            "sync_error": a.sync_error,
        }
        for a in accounts
    ]
