"""API Key settings schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class APIKeyUpdate(BaseModel):
    """Schema for updating API keys."""
    polygon_api_key: Optional[str] = None
    sec_api_key: Optional[str] = None
    benzinga_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    alpaca_api_key: Optional[str] = None
    alpaca_api_secret: Optional[str] = None
    alpaca_paper_trading: Optional[bool] = True
    sendgrid_api_key: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    # SMTP settings
    smtp_host: Optional[str] = None
    smtp_port: Optional[str] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_use_tls: Optional[bool] = True


class APIKeyStatus(BaseModel):
    """Status of a single API key."""
    configured: bool
    last_tested: Optional[datetime] = None
    test_success: Optional[bool] = None


class APIKeyStatusResponse(BaseModel):
    """Response with status of all API keys."""
    polygon: APIKeyStatus
    sec_api: APIKeyStatus
    benzinga: APIKeyStatus
    alpha_vantage: APIKeyStatus
    reddit: APIKeyStatus
    alpaca: APIKeyStatus
    alpaca_paper_trading: bool
    sendgrid: APIKeyStatus
    twilio: APIKeyStatus
    smtp: APIKeyStatus
    smtp_host: Optional[str] = None
    smtp_port: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_use_tls: bool = True

    class Config:
        from_attributes = True


class APIKeyTestRequest(BaseModel):
    """Request to test a specific API key."""
    service: str  # polygon, sec_api, benzinga, alpaca, sendgrid, twilio


class APIKeyTestResponse(BaseModel):
    """Response from API key test."""
    service: str
    success: bool
    message: str
    details: Optional[dict] = None
