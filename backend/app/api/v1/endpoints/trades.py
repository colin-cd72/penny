"""Trade endpoints."""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks, status
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Trade, Stock, BrokerAccount, TradeStatus, TradeSide
from app.schemas.trade import (
    TradeCreate,
    TradeConfirm,
    TradeResponse,
    TradeDetail,
    PositionSizeRequest,
    PositionSizeResponse,
)
from app.core.security import generate_confirmation_token
from app.api.v1.deps import get_current_user


router = APIRouter()


@router.post("/", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def create_trade(
    trade_data: TradeCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new trade order (requires confirmation).

    This initiates the semi-automated trading workflow:
    1. Validates the order parameters
    2. Generates a confirmation token
    3. Sends confirmation request via email/SMS
    4. Returns pending trade with confirmation details
    """
    # Get stock
    result = await db.execute(
        select(Stock).where(Stock.symbol == trade_data.symbol.upper())
    )
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Get broker account
    if trade_data.broker_account_id:
        broker_result = await db.execute(
            select(BrokerAccount).where(
                BrokerAccount.id == trade_data.broker_account_id,
                BrokerAccount.user_id == current_user.id,
            )
        )
        broker_account = broker_result.scalar_one_or_none()
    else:
        # Get default broker account
        broker_result = await db.execute(
            select(BrokerAccount).where(
                BrokerAccount.user_id == current_user.id,
                BrokerAccount.is_default == True,
                BrokerAccount.is_active == True,
            )
        )
        broker_account = broker_result.scalar_one_or_none()

    if not broker_account:
        raise HTTPException(
            status_code=400,
            detail="No broker account configured. Please add a broker account first.",
        )

    # Generate confirmation token
    confirmation_token = generate_confirmation_token()
    confirmation_channel = current_user.settings.get("trade_confirm_channel", "email")

    # Create trade
    trade = Trade(
        user_id=current_user.id,
        stock_id=stock.id,
        broker_account_id=broker_account.id,
        recommendation_id=trade_data.recommendation_id,
        side=TradeSide(trade_data.side),
        quantity=trade_data.quantity,
        order_type=trade_data.order_type,
        price=trade_data.price,
        stop_price=trade_data.stop_price,
        time_in_force=trade_data.time_in_force,
        status=TradeStatus.PENDING_CONFIRMATION,
        confirmation_token=confirmation_token,
        confirmation_channel=confirmation_channel,
    )

    db.add(trade)
    await db.flush()
    await db.refresh(trade)

    # Queue notification task
    # background_tasks.add_task(send_trade_confirmation, str(trade.id))

    return TradeResponse(
        id=trade.id,
        user_id=trade.user_id,
        stock_id=trade.stock_id,
        symbol=stock.symbol,
        stock_name=stock.name,
        side=trade.side.value,
        quantity=trade.quantity,
        order_type=trade.order_type,
        price=trade.price,
        status=trade.status.value,
        confirmation_token=confirmation_token,
        confirmed_at=None,
        filled_price=None,
        filled_quantity=None,
        executed_at=None,
        created_at=trade.created_at,
        updated_at=trade.updated_at,
    )


@router.post("/{trade_id}/confirm", response_model=TradeResponse)
async def confirm_trade(
    trade_id: UUID,
    confirmation: TradeConfirm,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Confirm a pending trade for execution."""
    result = await db.execute(
        select(Trade)
        .options(selectinload(Trade.stock))
        .where(
            Trade.id == trade_id,
            Trade.user_id == current_user.id,
        )
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade.status != TradeStatus.PENDING_CONFIRMATION:
        raise HTTPException(
            status_code=400,
            detail=f"Trade is not pending confirmation. Current status: {trade.status.value}",
        )

    if trade.confirmation_token != confirmation.confirmation_token:
        raise HTTPException(status_code=400, detail="Invalid confirmation token")

    # Update trade status
    trade.status = TradeStatus.CONFIRMED
    trade.confirmed_at = datetime.now(timezone.utc)
    trade.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(trade)

    # Queue broker submission task
    # background_tasks.add_task(submit_trade_to_broker, str(trade.id))

    return TradeResponse(
        id=trade.id,
        user_id=trade.user_id,
        stock_id=trade.stock_id,
        symbol=trade.stock.symbol,
        stock_name=trade.stock.name,
        side=trade.side.value,
        quantity=trade.quantity,
        order_type=trade.order_type,
        price=trade.price,
        status=trade.status.value,
        confirmation_token=None,
        confirmed_at=trade.confirmed_at,
        filled_price=trade.filled_price,
        filled_quantity=trade.filled_quantity,
        executed_at=trade.executed_at,
        created_at=trade.created_at,
        updated_at=trade.updated_at,
    )


@router.delete("/{trade_id}", response_model=TradeResponse)
async def cancel_trade(
    trade_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending or open order."""
    result = await db.execute(
        select(Trade)
        .options(selectinload(Trade.stock))
        .where(
            Trade.id == trade_id,
            Trade.user_id == current_user.id,
        )
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    cancellable_statuses = [
        TradeStatus.PENDING_CONFIRMATION,
        TradeStatus.CONFIRMED,
        TradeStatus.SUBMITTED,
    ]

    if trade.status not in cancellable_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel trade with status: {trade.status.value}",
        )

    # If already submitted to broker, cancel with broker first
    if trade.status == TradeStatus.SUBMITTED and trade.broker_order_id:
        # TODO: Cancel with broker
        pass

    trade.status = TradeStatus.CANCELLED
    trade.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(trade)

    return TradeResponse(
        id=trade.id,
        user_id=trade.user_id,
        stock_id=trade.stock_id,
        symbol=trade.stock.symbol,
        stock_name=trade.stock.name,
        side=trade.side.value,
        quantity=trade.quantity,
        order_type=trade.order_type,
        price=trade.price,
        status=trade.status.value,
        confirmation_token=None,
        confirmed_at=trade.confirmed_at,
        filled_price=trade.filled_price,
        filled_quantity=trade.filled_quantity,
        executed_at=trade.executed_at,
        created_at=trade.created_at,
        updated_at=trade.updated_at,
    )


@router.get("/", response_model=List[TradeResponse])
async def list_trades(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's trade history."""
    query = (
        select(Trade)
        .options(selectinload(Trade.stock))
        .where(Trade.user_id == current_user.id)
    )

    if status:
        query = query.where(Trade.status == TradeStatus(status))

    query = query.order_by(desc(Trade.created_at))

    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    trades = result.scalars().all()

    return [
        TradeResponse(
            id=t.id,
            user_id=t.user_id,
            stock_id=t.stock_id,
            symbol=t.stock.symbol,
            stock_name=t.stock.name,
            side=t.side.value,
            quantity=t.quantity,
            order_type=t.order_type,
            price=t.price,
            status=t.status.value,
            confirmation_token=None,
            confirmed_at=t.confirmed_at,
            filled_price=t.filled_price,
            filled_quantity=t.filled_quantity,
            executed_at=t.executed_at,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in trades
    ]


@router.get("/{trade_id}", response_model=TradeDetail)
async def get_trade(
    trade_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed trade information."""
    result = await db.execute(
        select(Trade)
        .options(selectinload(Trade.stock))
        .where(
            Trade.id == trade_id,
            Trade.user_id == current_user.id,
        )
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    return TradeDetail(
        id=trade.id,
        user_id=trade.user_id,
        stock_id=trade.stock_id,
        symbol=trade.stock.symbol,
        stock_name=trade.stock.name,
        recommendation_id=trade.recommendation_id,
        broker_account_id=trade.broker_account_id,
        side=trade.side.value,
        quantity=trade.quantity,
        order_type=trade.order_type,
        price=trade.price,
        stop_price=trade.stop_price,
        time_in_force=trade.time_in_force,
        status=trade.status.value,
        broker_order_id=trade.broker_order_id,
        confirmation_token=None,
        confirmation_channel=trade.confirmation_channel,
        confirmed_at=trade.confirmed_at,
        submitted_at=trade.submitted_at,
        executed_at=trade.executed_at,
        filled_price=trade.filled_price,
        filled_quantity=trade.filled_quantity,
        commission=trade.commission,
        created_at=trade.created_at,
        updated_at=trade.updated_at,
    )


@router.post("/position-size", response_model=PositionSizeResponse)
async def calculate_position_size(
    request: PositionSizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate recommended position size based on risk management."""
    # This would integrate with the broker to get portfolio value
    # For now, return a placeholder response

    risk_per_share = abs(request.entry_price - request.stop_loss)
    if risk_per_share == 0:
        raise HTTPException(status_code=400, detail="Stop loss cannot equal entry price")

    # Get user's risk settings
    risk_percent = current_user.settings.get("default_risk_percent", request.risk_percent)

    # Placeholder portfolio value (would come from broker)
    portfolio_value = 10000.0

    risk_amount = portfolio_value * risk_percent
    shares = int(risk_amount / risk_per_share)
    shares = max(1, shares)

    total_cost = shares * request.entry_price
    actual_risk = shares * risk_per_share
    position_percent = total_cost / portfolio_value

    return PositionSizeResponse(
        shares=shares,
        total_cost=total_cost,
        risk_amount=actual_risk,
        percent_of_portfolio=position_percent,
        rationale=f"Based on {risk_percent*100:.1f}% risk per trade with ${portfolio_value:,.0f} portfolio",
    )
