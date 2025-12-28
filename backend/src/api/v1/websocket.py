"""WebSocket endpoint for real-time updates."""

import asyncio
import json
from typing import Dict, Set
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from src.core.security import verify_access_token
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        # user_id -> set of websockets
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(websocket)
        logger.info("WebSocket connected", user_id=user_id)

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        async with self._lock:
            if user_id in self._connections:
                self._connections[user_id].discard(websocket)
                if not self._connections[user_id]:
                    del self._connections[user_id]
        logger.info("WebSocket disconnected", user_id=user_id)

    async def send_to_user(self, user_id: str, message: dict) -> None:
        """Send message to all connections of a user."""
        async with self._lock:
            connections = self._connections.get(user_id, set()).copy()

        for websocket in connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
            except Exception as e:
                logger.error("Failed to send WebSocket message", error=str(e))

    async def broadcast(self, message: dict) -> None:
        """Broadcast message to all connected users."""
        async with self._lock:
            all_connections = [
                ws for conns in self._connections.values() for ws in conns
            ]

        for websocket in all_connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
            except Exception as e:
                logger.error("Failed to broadcast WebSocket message", error=str(e))

    def get_connection_count(self) -> int:
        """Get total number of connections."""
        return sum(len(conns) for conns in self._connections.values())

    def get_user_count(self) -> int:
        """Get number of connected users."""
        return len(self._connections)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    user_id: str | None = None

    try:
        # Get token from query params
        token = websocket.query_params.get("token")

        if not token:
            await websocket.close(code=4001, reason="Missing token")
            return

        # Verify token
        payload = verify_access_token(token)
        if not payload:
            await websocket.close(code=4002, reason="Invalid token")
            return

        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4003, reason="Invalid token payload")
            return

        # Connect
        await manager.connect(websocket, user_id)

        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to SignalFlow",
        })

        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle ping
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

                # Handle subscription to specific channels
                elif message.get("type") == "subscribe":
                    channel = message.get("channel")
                    await websocket.send_json({
                        "type": "subscribed",
                        "channel": channel,
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                })

    except WebSocketDisconnect:
        if user_id:
            await manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        if user_id:
            await manager.disconnect(websocket, user_id)


async def notify_user_signal(user_id: str, signal_data: dict) -> None:
    """Send signal notification to a user."""
    await manager.send_to_user(user_id, {
        "type": "signal",
        "data": signal_data,
    })


async def notify_user_notification(user_id: str, notification_data: dict) -> None:
    """Send notification to a user."""
    await manager.send_to_user(user_id, {
        "type": "notification",
        "data": notification_data,
    })


async def broadcast_market_update(data: dict) -> None:
    """Broadcast market update to all users."""
    await manager.broadcast({
        "type": "market_update",
        "data": data,
    })
