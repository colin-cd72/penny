"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, stocks, recommendations, trades, alerts, watchlists, portfolio, settings
from app.api.v1 import websocket

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(watchlists.router, prefix="/watchlists", tags=["Watchlists"])
api_router.include_router(trades.router, prefix="/trades", tags=["Trades"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])

# WebSocket endpoint
api_router.include_router(websocket.router, tags=["WebSocket"])
