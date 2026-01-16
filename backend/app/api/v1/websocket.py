"""WebSocket endpoint for real-time updates."""

import json
import asyncio
from typing import Dict, Set
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import User
from app.core.security import decode_token


router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and subscriptions."""

    def __init__(self):
        # user_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # symbol -> set of user_ids watching
        self.symbol_subscribers: Dict[str, Set[str]] = {}
        # websocket -> user_id mapping
        self.connection_users: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        self.connection_users[websocket] = user_id

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        user_id = self.connection_users.get(websocket)
        if not user_id:
            return

        # Remove from active connections
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        # Remove from symbol subscriptions
        for symbol in list(self.symbol_subscribers.keys()):
            self.symbol_subscribers[symbol].discard(user_id)
            if not self.symbol_subscribers[symbol]:
                del self.symbol_subscribers[symbol]

        # Remove from connection mapping
        del self.connection_users[websocket]

    async def subscribe_to_symbols(self, user_id: str, symbols: list[str]):
        """Subscribe a user to symbol updates."""
        for symbol in symbols:
            symbol = symbol.upper()
            if symbol not in self.symbol_subscribers:
                self.symbol_subscribers[symbol] = set()
            self.symbol_subscribers[symbol].add(user_id)

    async def unsubscribe_from_symbols(self, user_id: str, symbols: list[str]):
        """Unsubscribe a user from symbol updates."""
        for symbol in symbols:
            symbol = symbol.upper()
            if symbol in self.symbol_subscribers:
                self.symbol_subscribers[symbol].discard(user_id)
                if not self.symbol_subscribers[symbol]:
                    del self.symbol_subscribers[symbol]

    async def broadcast_price_update(self, symbol: str, data: dict):
        """Broadcast price update to all subscribers of a symbol."""
        symbol = symbol.upper()
        if symbol not in self.symbol_subscribers:
            return

        message = json.dumps({
            "type": "price_update",
            "symbol": symbol,
            "data": data,
        })

        for user_id in self.symbol_subscribers[symbol]:
            if user_id in self.active_connections:
                for websocket in self.active_connections[user_id]:
                    try:
                        await websocket.send_text(message)
                    except Exception:
                        pass  # Connection may be closed

    async def broadcast_signal_alert(self, symbol: str, signal: dict):
        """Broadcast a new signal alert."""
        symbol = symbol.upper()
        if symbol not in self.symbol_subscribers:
            return

        message = json.dumps({
            "type": "signal_alert",
            "symbol": symbol,
            "signal": signal,
        })

        for user_id in self.symbol_subscribers[symbol]:
            if user_id in self.active_connections:
                for websocket in self.active_connections[user_id]:
                    try:
                        await websocket.send_text(message)
                    except Exception:
                        pass

    async def send_trade_update(self, user_id: str, trade_id: str, status: str, data: dict = None):
        """Send trade status update to a specific user."""
        if user_id not in self.active_connections:
            return

        message = json.dumps({
            "type": "trade_update",
            "trade_id": trade_id,
            "status": status,
            "data": data or {},
        })

        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(message)
            except Exception:
                pass


# Global connection manager
manager = ConnectionManager()


async def verify_ws_token(token: str) -> User | None:
    """Verify WebSocket authentication token."""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.id == UUID(user_id))
        )
        return result.scalar_one_or_none()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time updates.

    Message types received from client:
    - {"type": "subscribe", "symbols": ["AAPL", "TSLA"]}
    - {"type": "unsubscribe", "symbols": ["AAPL"]}
    - {"type": "ping"}

    Message types sent to client:
    - {"type": "price_update", "symbol": "...", "data": {...}}
    - {"type": "signal_alert", "symbol": "...", "signal": {...}}
    - {"type": "trade_update", "trade_id": "...", "status": "..."}
    - {"type": "pong"}
    - {"type": "error", "message": "..."}
    """
    # Verify token
    user = await verify_ws_token(token)
    if not user:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # Connect
    await manager.connect(websocket, str(user.id))

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON",
                }))
                continue

            message_type = message.get("type")

            if message_type == "subscribe":
                symbols = message.get("symbols", [])
                await manager.subscribe_to_symbols(str(user.id), symbols)
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "symbols": [s.upper() for s in symbols],
                }))

            elif message_type == "unsubscribe":
                symbols = message.get("symbols", [])
                await manager.unsubscribe_from_symbols(str(user.id), symbols)
                await websocket.send_text(json.dumps({
                    "type": "unsubscribed",
                    "symbols": [s.upper() for s in symbols],
                }))

            elif message_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                }))

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        await manager.disconnect(websocket)
        raise


# Export manager for use in other modules
def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager."""
    return manager
