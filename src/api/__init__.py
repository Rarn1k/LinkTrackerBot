from fastapi import APIRouter

from . import bot_api, ping, scrapper_api

__all__ = ("router",)

router = APIRouter()
router.include_router(ping.router, tags=["ping"])
router.include_router(bot_api.router, prefix="/bot", tags=["Bot API"])
router.include_router(scrapper_api.router, prefix="/scrapper", tags=["Scrapper API"])
