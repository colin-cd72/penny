"""Settings API endpoints for managing API keys."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.database import get_db
from app.models import User, APIKeySettings
from app.schemas.api_key import (
    APIKeyUpdate,
    APIKeyStatus,
    APIKeyStatusResponse,
    APIKeyTestRequest,
    APIKeyTestResponse,
)
from app.api.v1.endpoints.auth import get_current_user
from app.core.security import encrypt_credential, decrypt_credential

router = APIRouter()


def mask_key(key: Optional[str]) -> bool:
    """Check if key is configured (non-empty)."""
    return bool(key and len(key) > 0)


async def get_or_create_settings(db: AsyncSession, user: User) -> APIKeySettings:
    """Get existing settings or create new ones for user."""
    result = await db.execute(
        select(APIKeySettings).where(APIKeySettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = APIKeySettings(user_id=user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@router.get("/api-keys", response_model=APIKeyStatusResponse)
async def get_api_key_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get status of all configured API keys."""
    settings = await get_or_create_settings(db, current_user)

    return APIKeyStatusResponse(
        polygon=APIKeyStatus(
            configured=mask_key(settings.polygon_api_key),
            last_tested=settings.polygon_tested_at,
            test_success=settings.polygon_test_success,
        ),
        sec_api=APIKeyStatus(
            configured=mask_key(settings.sec_api_key),
            last_tested=settings.sec_tested_at,
            test_success=settings.sec_test_success,
        ),
        benzinga=APIKeyStatus(
            configured=mask_key(settings.benzinga_api_key),
            last_tested=settings.benzinga_tested_at,
            test_success=settings.benzinga_test_success,
        ),
        alpha_vantage=APIKeyStatus(
            configured=mask_key(settings.alpha_vantage_api_key),
        ),
        reddit=APIKeyStatus(
            configured=mask_key(settings.reddit_client_id) and mask_key(settings.reddit_client_secret),
        ),
        alpaca=APIKeyStatus(
            configured=mask_key(settings.alpaca_api_key) and mask_key(settings.alpaca_api_secret),
            last_tested=settings.alpaca_tested_at,
            test_success=settings.alpaca_test_success,
        ),
        alpaca_paper_trading=settings.alpaca_paper_trading or True,
        sendgrid=APIKeyStatus(
            configured=mask_key(settings.sendgrid_api_key),
            last_tested=settings.sendgrid_tested_at,
            test_success=settings.sendgrid_test_success,
        ),
        twilio=APIKeyStatus(
            configured=mask_key(settings.twilio_account_sid) and mask_key(settings.twilio_auth_token),
            last_tested=settings.twilio_tested_at,
            test_success=settings.twilio_test_success,
        ),
        smtp=APIKeyStatus(
            configured=mask_key(settings.smtp_host) and mask_key(settings.smtp_username),
            last_tested=settings.smtp_tested_at,
            test_success=settings.smtp_test_success,
        ),
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_from_email=settings.smtp_from_email,
        smtp_use_tls=settings.smtp_use_tls or True,
    )


@router.put("/api-keys", response_model=APIKeyStatusResponse)
async def update_api_keys(
    keys: APIKeyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update API keys. Only provided keys will be updated."""
    settings = await get_or_create_settings(db, current_user)

    # Update only provided keys
    if keys.polygon_api_key is not None:
        settings.polygon_api_key = keys.polygon_api_key
        settings.polygon_test_success = None
        settings.polygon_tested_at = None

    if keys.sec_api_key is not None:
        settings.sec_api_key = keys.sec_api_key
        settings.sec_test_success = None
        settings.sec_tested_at = None

    if keys.benzinga_api_key is not None:
        settings.benzinga_api_key = keys.benzinga_api_key
        settings.benzinga_test_success = None
        settings.benzinga_tested_at = None

    if keys.alpha_vantage_api_key is not None:
        settings.alpha_vantage_api_key = keys.alpha_vantage_api_key

    if keys.reddit_client_id is not None:
        settings.reddit_client_id = keys.reddit_client_id

    if keys.reddit_client_secret is not None:
        settings.reddit_client_secret = keys.reddit_client_secret

    if keys.alpaca_api_key is not None:
        settings.alpaca_api_key = keys.alpaca_api_key
        settings.alpaca_test_success = None
        settings.alpaca_tested_at = None

    if keys.alpaca_api_secret is not None:
        settings.alpaca_api_secret = keys.alpaca_api_secret
        settings.alpaca_test_success = None
        settings.alpaca_tested_at = None

    if keys.alpaca_paper_trading is not None:
        settings.alpaca_paper_trading = keys.alpaca_paper_trading

    if keys.sendgrid_api_key is not None:
        settings.sendgrid_api_key = keys.sendgrid_api_key
        settings.sendgrid_test_success = None
        settings.sendgrid_tested_at = None

    if keys.twilio_account_sid is not None:
        settings.twilio_account_sid = keys.twilio_account_sid
        settings.twilio_test_success = None
        settings.twilio_tested_at = None

    if keys.twilio_auth_token is not None:
        settings.twilio_auth_token = keys.twilio_auth_token
        settings.twilio_test_success = None
        settings.twilio_tested_at = None

    if keys.twilio_phone_number is not None:
        settings.twilio_phone_number = keys.twilio_phone_number

    # SMTP settings
    if keys.smtp_host is not None:
        settings.smtp_host = keys.smtp_host
        settings.smtp_test_success = None
        settings.smtp_tested_at = None

    if keys.smtp_port is not None:
        settings.smtp_port = keys.smtp_port

    if keys.smtp_username is not None:
        settings.smtp_username = keys.smtp_username
        settings.smtp_test_success = None
        settings.smtp_tested_at = None

    if keys.smtp_password is not None:
        settings.smtp_password = keys.smtp_password
        settings.smtp_test_success = None
        settings.smtp_tested_at = None

    if keys.smtp_from_email is not None:
        settings.smtp_from_email = keys.smtp_from_email

    if keys.smtp_use_tls is not None:
        settings.smtp_use_tls = keys.smtp_use_tls

    await db.commit()
    await db.refresh(settings)

    # Return updated status
    return await get_api_key_status(db, current_user)


@router.post("/api-keys/test", response_model=APIKeyTestResponse)
async def test_api_key(
    request: APIKeyTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test a specific API key."""
    settings = await get_or_create_settings(db, current_user)
    service = request.service.lower()

    try:
        if service == "polygon":
            return await test_polygon(settings, db)
        elif service == "sec_api":
            return await test_sec_api(settings, db)
        elif service == "benzinga":
            return await test_benzinga(settings, db)
        elif service == "alpaca":
            return await test_alpaca(settings, db)
        elif service == "sendgrid":
            return await test_sendgrid(settings, db)
        elif service == "twilio":
            return await test_twilio(settings, db)
        elif service == "smtp":
            return await test_smtp(settings, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown service: {service}"
            )
    except HTTPException:
        raise
    except Exception as e:
        return APIKeyTestResponse(
            service=service,
            success=False,
            message=f"Test failed: {str(e)}",
        )


async def test_polygon(settings: APIKeySettings, db: AsyncSession) -> APIKeyTestResponse:
    """Test Polygon.io API key."""
    if not settings.polygon_api_key:
        return APIKeyTestResponse(
            service="polygon",
            success=False,
            message="Polygon API key not configured",
        )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.polygon.io/v3/reference/tickers",
            params={"apiKey": settings.polygon_api_key, "limit": 1},
            timeout=10.0,
        )

    success = response.status_code == 200
    settings.polygon_tested_at = datetime.utcnow()
    settings.polygon_test_success = success
    await db.commit()

    if success:
        data = response.json()
        return APIKeyTestResponse(
            service="polygon",
            success=True,
            message="Polygon API key is valid",
            details={"results_count": data.get("count", 0)},
        )
    else:
        return APIKeyTestResponse(
            service="polygon",
            success=False,
            message=f"Polygon API error: {response.status_code}",
        )


async def test_sec_api(settings: APIKeySettings, db: AsyncSession) -> APIKeyTestResponse:
    """Test SEC API key."""
    if not settings.sec_api_key:
        return APIKeyTestResponse(
            service="sec_api",
            success=False,
            message="SEC API key not configured",
        )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.sec-api.io/filing-extractor",
            params={"token": settings.sec_api_key},
            timeout=10.0,
        )

    # SEC API returns 400 for missing params but validates the key
    success = response.status_code in [200, 400]
    settings.sec_tested_at = datetime.utcnow()
    settings.sec_test_success = success
    await db.commit()

    if success:
        return APIKeyTestResponse(
            service="sec_api",
            success=True,
            message="SEC API key is valid",
        )
    else:
        return APIKeyTestResponse(
            service="sec_api",
            success=False,
            message=f"SEC API error: {response.status_code}",
        )


async def test_benzinga(settings: APIKeySettings, db: AsyncSession) -> APIKeyTestResponse:
    """Test Benzinga API key."""
    if not settings.benzinga_api_key:
        return APIKeyTestResponse(
            service="benzinga",
            success=False,
            message="Benzinga API key not configured",
        )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.benzinga.com/api/v2/news",
            params={"token": settings.benzinga_api_key, "pageSize": 1},
            timeout=10.0,
        )

    success = response.status_code == 200
    settings.benzinga_tested_at = datetime.utcnow()
    settings.benzinga_test_success = success
    await db.commit()

    if success:
        return APIKeyTestResponse(
            service="benzinga",
            success=True,
            message="Benzinga API key is valid",
        )
    else:
        return APIKeyTestResponse(
            service="benzinga",
            success=False,
            message=f"Benzinga API error: {response.status_code}",
        )


async def test_alpaca(settings: APIKeySettings, db: AsyncSession) -> APIKeyTestResponse:
    """Test Alpaca API key."""
    if not settings.alpaca_api_key or not settings.alpaca_api_secret:
        return APIKeyTestResponse(
            service="alpaca",
            success=False,
            message="Alpaca API credentials not configured",
        )

    base_url = "https://paper-api.alpaca.markets" if settings.alpaca_paper_trading else "https://api.alpaca.markets"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{base_url}/v2/account",
            headers={
                "APCA-API-KEY-ID": settings.alpaca_api_key,
                "APCA-API-SECRET-KEY": settings.alpaca_api_secret,
            },
            timeout=10.0,
        )

    success = response.status_code == 200
    settings.alpaca_tested_at = datetime.utcnow()
    settings.alpaca_test_success = success
    await db.commit()

    if success:
        data = response.json()
        return APIKeyTestResponse(
            service="alpaca",
            success=True,
            message=f"Alpaca API connected ({'Paper' if settings.alpaca_paper_trading else 'Live'} Trading)",
            details={
                "account_number": data.get("account_number"),
                "buying_power": data.get("buying_power"),
                "portfolio_value": data.get("portfolio_value"),
            },
        )
    else:
        return APIKeyTestResponse(
            service="alpaca",
            success=False,
            message=f"Alpaca API error: {response.status_code}",
        )


async def test_sendgrid(settings: APIKeySettings, db: AsyncSession) -> APIKeyTestResponse:
    """Test SendGrid API key."""
    if not settings.sendgrid_api_key:
        return APIKeyTestResponse(
            service="sendgrid",
            success=False,
            message="SendGrid API key not configured",
        )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.sendgrid.com/v3/user/profile",
            headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
            timeout=10.0,
        )

    success = response.status_code == 200
    settings.sendgrid_tested_at = datetime.utcnow()
    settings.sendgrid_test_success = success
    await db.commit()

    if success:
        return APIKeyTestResponse(
            service="sendgrid",
            success=True,
            message="SendGrid API key is valid",
        )
    else:
        return APIKeyTestResponse(
            service="sendgrid",
            success=False,
            message=f"SendGrid API error: {response.status_code}",
        )


async def test_twilio(settings: APIKeySettings, db: AsyncSession) -> APIKeyTestResponse:
    """Test Twilio API credentials."""
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        return APIKeyTestResponse(
            service="twilio",
            success=False,
            message="Twilio credentials not configured",
        )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}.json",
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            timeout=10.0,
        )

    success = response.status_code == 200
    settings.twilio_tested_at = datetime.utcnow()
    settings.twilio_test_success = success
    await db.commit()

    if success:
        data = response.json()
        return APIKeyTestResponse(
            service="twilio",
            success=True,
            message="Twilio credentials are valid",
            details={"account_name": data.get("friendly_name")},
        )
    else:
        return APIKeyTestResponse(
            service="twilio",
            success=False,
            message=f"Twilio API error: {response.status_code}",
        )


async def test_smtp(settings: APIKeySettings, db: AsyncSession) -> APIKeyTestResponse:
    """Test SMTP connection."""
    import aiosmtplib

    if not settings.smtp_host or not settings.smtp_username:
        return APIKeyTestResponse(
            service="smtp",
            success=False,
            message="SMTP settings not configured",
        )

    try:
        port = int(settings.smtp_port or "587")
        smtp = aiosmtplib.SMTP(
            hostname=settings.smtp_host,
            port=port,
            use_tls=settings.smtp_use_tls,
            timeout=10,
        )

        await smtp.connect()
        await smtp.login(settings.smtp_username, settings.smtp_password or "")
        await smtp.quit()

        settings.smtp_tested_at = datetime.utcnow()
        settings.smtp_test_success = True
        await db.commit()

        return APIKeyTestResponse(
            service="smtp",
            success=True,
            message=f"SMTP connection successful to {settings.smtp_host}:{port}",
        )

    except Exception as e:
        settings.smtp_tested_at = datetime.utcnow()
        settings.smtp_test_success = False
        await db.commit()

        return APIKeyTestResponse(
            service="smtp",
            success=False,
            message=f"SMTP connection failed: {str(e)}",
        )
