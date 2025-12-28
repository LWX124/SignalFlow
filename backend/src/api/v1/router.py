"""API v1 router."""

from fastapi import APIRouter

from src.api.v1.endpoints import auth, users, strategies, subscriptions, signals, notifications, instruments
from src.api.v1 import websocket

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router, tags=["auth"])
router.include_router(users.router, tags=["users"])
router.include_router(strategies.router, tags=["strategies"])
router.include_router(subscriptions.router, tags=["subscriptions"])
router.include_router(signals.router, tags=["signals"])
router.include_router(notifications.router, tags=["notifications"])
router.include_router(instruments.router, tags=["instruments"])
router.include_router(websocket.router, tags=["websocket"])
