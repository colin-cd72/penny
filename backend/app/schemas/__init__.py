"""Pydantic schemas package."""

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    TokenPayload,
)
from app.schemas.stock import (
    StockResponse,
    StockListResponse,
    StockDetail,
    PriceCandle,
    TechnicalIndicators,
)
from app.schemas.recommendation import (
    RecommendationResponse,
    RecommendationDetail,
)
from app.schemas.trade import (
    TradeCreate,
    TradeConfirm,
    TradeResponse,
    TradeDetail,
)
from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistUpdate,
    WatchlistResponse,
    WatchlistStockAdd,
)
from app.schemas.alert import (
    AlertConfigCreate,
    AlertConfigUpdate,
    AlertConfigResponse,
)
from app.schemas.api_key import (
    APIKeyUpdate,
    APIKeyStatus,
    APIKeyStatusResponse,
    APIKeyTestRequest,
    APIKeyTestResponse,
)

__all__ = [
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenPayload",
    "StockResponse",
    "StockListResponse",
    "StockDetail",
    "PriceCandle",
    "TechnicalIndicators",
    "RecommendationResponse",
    "RecommendationDetail",
    "TradeCreate",
    "TradeConfirm",
    "TradeResponse",
    "TradeDetail",
    "WatchlistCreate",
    "WatchlistUpdate",
    "WatchlistResponse",
    "WatchlistStockAdd",
    "AlertConfigCreate",
    "AlertConfigUpdate",
    "AlertConfigResponse",
    "APIKeyUpdate",
    "APIKeyStatus",
    "APIKeyStatusResponse",
    "APIKeyTestRequest",
    "APIKeyTestResponse",
]
