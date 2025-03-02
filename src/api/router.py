from fastapi import APIRouter

from src.api.bot_api.handlers import router as bot_api_router
from src.api.scrapper_api.handlers import router as scrapper_api_router

router = APIRouter()

router.include_router(bot_api_router, prefix="/bot", tags=["Bot API"])
router.include_router(scrapper_api_router, prefix="/scrapper", tags=["Scrapper API"])
