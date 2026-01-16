"""Alert configuration endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, AlertConfig, RecommendationAlert
from app.schemas.alert import (
    AlertConfigCreate,
    AlertConfigUpdate,
    AlertConfigResponse,
    AlertHistoryResponse,
)
from app.api.v1.deps import get_current_user


router = APIRouter()


@router.get("/configs", response_model=List[AlertConfigResponse])
async def list_alert_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's alert configurations."""
    result = await db.execute(
        select(AlertConfig)
        .where(AlertConfig.user_id == current_user.id)
        .order_by(AlertConfig.created_at)
    )
    configs = result.scalars().all()

    return [AlertConfigResponse.model_validate(c) for c in configs]


@router.post("/configs", response_model=AlertConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_config(
    config_data: AlertConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new alert configuration."""
    # Check if similar config exists
    existing = await db.execute(
        select(AlertConfig).where(
            AlertConfig.user_id == current_user.id,
            AlertConfig.alert_type == config_data.alert_type,
            AlertConfig.channel == config_data.channel,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Alert config for {config_data.alert_type} via {config_data.channel} already exists",
        )

    config = AlertConfig(
        user_id=current_user.id,
        alert_type=config_data.alert_type,
        channel=config_data.channel,
        min_confidence=config_data.min_confidence,
        signal_types=config_data.signal_types,
        stocks=config_data.stocks,
        quiet_hours_start=config_data.quiet_hours_start,
        quiet_hours_end=config_data.quiet_hours_end,
    )

    db.add(config)
    await db.flush()
    await db.refresh(config)

    return AlertConfigResponse.model_validate(config)


@router.get("/configs/{config_id}", response_model=AlertConfigResponse)
async def get_alert_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific alert configuration."""
    result = await db.execute(
        select(AlertConfig).where(
            AlertConfig.id == config_id,
            AlertConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")

    return AlertConfigResponse.model_validate(config)


@router.put("/configs/{config_id}", response_model=AlertConfigResponse)
async def update_alert_config(
    config_id: UUID,
    config_data: AlertConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an alert configuration."""
    result = await db.execute(
        select(AlertConfig).where(
            AlertConfig.id == config_id,
            AlertConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")

    if config_data.min_confidence is not None:
        config.min_confidence = config_data.min_confidence
    if config_data.signal_types is not None:
        config.signal_types = config_data.signal_types
    if config_data.stocks is not None:
        config.stocks = config_data.stocks
    if config_data.quiet_hours_start is not None:
        config.quiet_hours_start = config_data.quiet_hours_start
    if config_data.quiet_hours_end is not None:
        config.quiet_hours_end = config_data.quiet_hours_end
    if config_data.is_active is not None:
        config.is_active = config_data.is_active

    await db.flush()
    await db.refresh(config)

    return AlertConfigResponse.model_validate(config)


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an alert configuration."""
    result = await db.execute(
        select(AlertConfig).where(
            AlertConfig.id == config_id,
            AlertConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")

    await db.delete(config)


@router.get("/history", response_model=List[AlertHistoryResponse])
async def get_alert_history(
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List sent alerts history."""
    offset = (page - 1) * per_page

    result = await db.execute(
        select(RecommendationAlert)
        .where(RecommendationAlert.user_id == current_user.id)
        .order_by(desc(RecommendationAlert.sent_at))
        .offset(offset)
        .limit(per_page)
    )
    alerts = result.scalars().all()

    # TODO: Join with recommendation and stock to get symbol and signal_type
    return [
        AlertHistoryResponse(
            id=a.id,
            recommendation_id=a.recommendation_id,
            symbol="",  # Would come from join
            signal_type="",  # Would come from join
            channel=a.channel,
            status=a.status,
            sent_at=a.sent_at,
            clicked_at=a.clicked_at,
            error_message=a.error_message,
        )
        for a in alerts
    ]


@router.post("/test")
async def send_test_alert(
    channel: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a test alert to verify configuration."""
    # TODO: Implement test alert sending
    return {"message": f"Test alert sent via {channel}"}
